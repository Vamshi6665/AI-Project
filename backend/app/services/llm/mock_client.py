"""Mock LLM: regex heuristics, no network, no cost.

Lets you build and demo the whole UI + API before any keys or AWS exist, and keeps tests fast.
It handles the "Label: value" + bulleted-section layout of the sample PDFs well and prose letters
poorly, which is exactly the gap a real LLM closes (try samples/03 with both providers).
"""
import asyncio
import json
import re

from .base import LLMResult

FIELD_PATTERNS = {
    "name": r"^(?:patient name|patient|name)\s*:\s*(.+)$",
    "dob": r"^(?:date of birth|dob)\s*:\s*(.+)$",
    "sex": r"^(?:sex|gender)\s*:\s*(.+)$",
    "mrn": r"^(?:mrn|medical record number|patient id)\s*:\s*(.+)$",
    "date": r"^(?:admission date|collection date|date of service|visit date|date)\s*:\s*(.+)$",
    "provider": r"^(?:attending physician|ordering provider|referring physician|provider|physician)\s*:\s*(.+)$",
    "department": r"^(?:department|service)\s*:\s*(.+)$",
}

SECTION_KEYS = [
    ("diagnos", "diagnoses"), ("reason for", "diagnoses"), ("medication", "medications"),
    ("allerg", "allergies"), ("lab", "lab_results"), ("result", "lab_results"), ("vital", "vitals"),
    ("procedure", "procedures"), ("follow", "follow_up"), ("social", "social_history"),
]

DX_RE = re.compile(r"^(.*?)\s*\(([A-Z]\d{2}(?:\.\d{1,4})?)\)\s*(?:[-–]\s*(\w+))?$")
MED_RE = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z\- ]*?)\s+(?P<dose>\d[\d.,]*\s*(?:mg|mcg|g|mEq|units?|mL|puffs?))\s*"
    r"(?P<route>PO|IV|IM|SC|SL|inhaled|topical)?\s*(?P<freq>.*?)\s*(?:\((?P<status>[a-z]+)\))?$",
    re.IGNORECASE,
)
LAB_RE = re.compile(
    r"^(?P<test>.+?):\s*(?P<value>[<>]?[\d.]+)\s*(?P<unit>[^\s(]+)?\s*(?:\(ref\s*(?P<ref>[^)]+)\))?\s*(?P<flag>[HLC])?$"
)
VITAL_RE = re.compile(r"^(?P<name>.+?):\s*(?P<value>[\d./]+)\s*(?P<unit>mmHg|bpm|F|C|%|breaths/min|kg|lbs)?$")
FLAGS = {"H": "high", "L": "low", "C": "critical"}


def _document_text(messages: list[dict]) -> str:
    content = messages[1]["content"] if len(messages) > 1 else messages[-1]["content"]
    match = re.search(r"<<<\n(.*)\n>>>", content, re.DOTALL)
    return match.group(1) if match else content


def heuristic_extract(text: str) -> dict:
    lines = [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.startswith("--- Page")]
    fields: dict[str, str] = {}
    sections: dict[str, list[str]] = {}
    current = None

    for line in lines:
        for key, pattern in FIELD_PATTERNS.items():
            m = re.match(pattern, line, re.IGNORECASE)
            if m and key not in fields:
                fields[key] = m.group(1).strip()
        if line.endswith(":") and len(line) < 60:
            header = line[:-1].lower()
            current = next((sec for kw, sec in SECTION_KEYS if kw in header), None)
            continue
        if current and line[:2] in ("- ", "• "):
            sections.setdefault(current, []).append(line[2:].strip())
        elif current and not line.startswith(("-", "•")) and line.endswith(":"):
            current = None

    upper = text.upper()
    doc_type = next(
        (label for kw, label in [("DISCHARGE SUMMARY", "discharge summary"), ("LABORATORY", "lab report"),
                                 ("REFERRAL", "referral letter")] if kw in upper),
        "clinical document",
    )

    diagnoses = []
    for item in sections.get("diagnoses", []):
        m = DX_RE.match(item)
        diagnoses.append(
            {"description": m.group(1), "icd10_code": m.group(2), "status": m.group(3)} if m else {"description": item}
        )

    meds = []
    for item in sections.get("medications", []):
        m = MED_RE.match(item)
        if m:
            meds.append({"name": m["name"].strip(), "dose": m["dose"], "route": m["route"],
                         "frequency": m["freq"] or None, "status": m["status"]})
        else:
            meds.append({"name": item})

    labs = []
    for item in sections.get("lab_results", []):
        m = LAB_RE.match(item)
        if m:
            flag = FLAGS.get(m["flag"] or "", "normal" if m["ref"] else None)
            labs.append({"test": m["test"], "value": m["value"], "unit": m["unit"],
                         "reference_range": m["ref"], "flag": flag})

    vitals = []
    for item in sections.get("vitals", []):
        m = VITAL_RE.match(item)
        if m:
            vitals.append({"name": m["name"], "value": m["value"], "unit": m["unit"]})

    return {
        "document_type": doc_type,
        "patient": {"name": fields.get("name"), "date_of_birth": fields.get("dob"),
                    "sex": fields.get("sex"), "mrn": fields.get("mrn")},
        "encounter": {"date": fields.get("date"), "facility": lines[0] if lines else None,
                      "provider": fields.get("provider"), "department": fields.get("department")},
        "diagnoses": diagnoses,
        "medications": meds,
        "allergies": sections.get("allergies", []),
        "lab_results": labs,
        "vitals": vitals,
        "procedures": sections.get("procedures", []),
        "follow_up": sections.get("follow_up", []),
        "social_history": sections.get("social_history", []),
        "summary": f"Mock extraction of a {doc_type}. Set LLM_PROVIDER=openai or sagemaker "
                   "for a model-written summary and better results on free-text documents.",
    }


class MockClient:
    provider = "mock"
    model = "mock-heuristic"

    def __init__(self, latency_seconds: float = 1.0):
        self.latency_seconds = latency_seconds

    async def complete(self, messages: list[dict]) -> LLMResult:
        await asyncio.sleep(self.latency_seconds)  # so the UI's "processing" state is visible
        result = heuristic_extract(_document_text(messages))
        return LLMResult(text=json.dumps(result), input_tokens=None, output_tokens=None)
