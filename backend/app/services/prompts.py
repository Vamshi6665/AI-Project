"""Prompt construction. The JSON Schema comes straight from the Pydantic model, so the prompt and
the validator can never drift apart."""
import json

from ..schemas import ClinicalExtraction

_SCHEMA = json.dumps(ClinicalExtraction.model_json_schema(), separators=(",", ":"))

SYSTEM_PROMPT = f"""You are a clinical document information-extraction engine.
Extract structured data from the clinical document the user provides.

Rules:
- Return ONLY one JSON object. No markdown, no code fences, no commentary.
- The JSON must validate against this JSON Schema:
{_SCHEMA}
- Use null (or an empty list) when the document does not state a value. Never guess or invent values.
- Copy medication names, doses and lab values exactly as written.
- Dates as YYYY-MM-DD when the full date is present.
- Lab "flag": "high"/"low"/"critical" only if the document marks it (H, L, HIGH, LOW, critical) or the
  value is clearly outside the stated reference range; otherwise "normal" or null.
- "summary": 2-3 plain sentences a clinician would find useful."""


def build_messages(document_text: str) -> list[dict]:
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Clinical document:\n<<<\n{document_text}\n>>>"},
    ]


def build_repair_messages(document_text: str, bad_output: str, error: str) -> list[dict]:
    """Second attempt: show the model its invalid output and the validation error."""
    return build_messages(document_text) + [
        {"role": "assistant", "content": bad_output[:4000]},
        {
            "role": "user",
            "content": f"That output was not valid for the schema. Error: {error[:1000]}\n"
            "Return the corrected JSON object only.",
        },
    ]
