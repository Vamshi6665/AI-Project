"""The pipeline: PDF bytes -> text -> LLM -> JSON -> schema validation (-> one repair retry) -> record."""
import json
import logging
import time
import uuid
from datetime import datetime, timezone

from pydantic import ValidationError

from ..config import Settings
from ..errors import LLMOutputError
from ..schemas import ClinicalExtraction, DocumentMeta, ExtractionRecord, InferenceMeta
from .llm.base import LLMClient
from .pdf_text import extract_text
from .prompts import build_messages, build_repair_messages

logger = logging.getLogger("app.extractor")


def parse_model_json(raw: str) -> ClinicalExtraction:
    """Find the JSON object in the model's answer and validate it.

    Models sometimes wrap JSON in ```fences``` or add a sentence before it, so we try the whole
    string first, then every '{' position, and keep the largest object that parses.
    Raises ValueError with a readable message (fed back to the model on retry).
    """
    raw = (raw or "").strip()
    if not raw:
        raise ValueError("Empty response")
    candidates = []
    try:
        candidates.append(json.loads(raw))
    except json.JSONDecodeError:
        decoder = json.JSONDecoder()
        for i, ch in enumerate(raw):
            if ch == "{":
                try:
                    obj, end = decoder.raw_decode(raw, i)
                    if isinstance(obj, dict):
                        candidates.append(obj)
                except json.JSONDecodeError:
                    continue
    if not candidates:
        raise ValueError("No JSON object found in response")
    best = max(candidates, key=lambda d: len(json.dumps(d)))
    try:
        return ClinicalExtraction.model_validate(best)
    except ValidationError as exc:
        raise ValueError(exc.json(include_url=False)) from exc


def _warnings(data: ClinicalExtraction, truncated: bool, provider: str) -> list[str]:
    w = []
    if truncated:
        w.append("Document was longer than the processing limit; only the first part was analysed.")
    if not data.patient.name:
        w.append("No patient name found.")
    if not (data.diagnoses or data.medications or data.lab_results):
        w.append("No diagnoses, medications or lab results found.")
    if provider == "mock":
        w.append("Mock provider: heuristic extraction, not an LLM.")
    return w


async def run_extraction(filename: str, data: bytes, settings: Settings, llm: LLMClient) -> ExtractionRecord:
    pdf = extract_text(data, settings.max_pages, settings.max_chars_to_llm)

    start = time.perf_counter()
    attempts = 1
    result = await llm.complete(build_messages(pdf.text))
    in_tok, out_tok = result.input_tokens, result.output_tokens
    try:
        extraction = parse_model_json(result.text)
    except ValueError as first_error:
        logger.warning("llm_invalid_output_retrying", extra={"error": str(first_error)[:300]})
        attempts = 2
        retry = await llm.complete(build_repair_messages(pdf.text, result.text, str(first_error)))
        if retry.input_tokens is not None:
            in_tok = (in_tok or 0) + retry.input_tokens
            out_tok = (out_tok or 0) + (retry.output_tokens or 0)
        try:
            extraction = parse_model_json(retry.text)
        except ValueError as second_error:
            raise LLMOutputError("The model did not return valid structured data", details=str(second_error)[:500])
    latency_ms = round((time.perf_counter() - start) * 1000, 1)

    record = ExtractionRecord(
        id=uuid.uuid4().hex[:10],
        created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        document=DocumentMeta(filename=filename, size_bytes=len(data), pages=pdf.pages,
                              chars_extracted=pdf.chars, truncated=pdf.truncated),
        inference=InferenceMeta(provider=llm.provider, model=llm.model, latency_ms=latency_ms,
                                attempts=attempts, input_tokens=in_tok, output_tokens=out_tok),
        data=extraction,
        warnings=_warnings(extraction, pdf.truncated, llm.provider),
    )
    # Log metadata only. Never log document text or extracted values: in a real system that is PHI.
    logger.info("extraction_complete", extra={
        "extraction_id": record.id, "provider": llm.provider, "pages": pdf.pages,
        "latency_ms": latency_ms, "attempts": attempts, "output_tokens": out_tok,
    })
    return record
