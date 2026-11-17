"""Pydantic models = the contract between backend, LLM and frontend.

`ClinicalExtraction` is what the LLM must return. Its JSON Schema is also embedded in the prompt,
and the model's answer is validated against it before anything reaches the UI.
"""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class _Lenient(BaseModel):
    # LLMs sometimes add extra keys; ignore them instead of failing the whole extraction.
    model_config = ConfigDict(extra="ignore")


class Patient(_Lenient):
    name: str | None = None
    date_of_birth: str | None = Field(None, description="YYYY-MM-DD if the document gives a full date")
    age: int | None = None
    sex: str | None = None
    mrn: str | None = Field(None, description="Medical record number")


class Encounter(_Lenient):
    date: str | None = Field(None, description="YYYY-MM-DD")
    facility: str | None = None
    provider: str | None = None
    department: str | None = None


class Diagnosis(_Lenient):
    description: str
    icd10_code: str | None = None
    status: str | None = Field(None, description="e.g. primary, secondary, resolved, chronic")


class Medication(_Lenient):
    name: str
    dose: str | None = None
    route: str | None = None
    frequency: str | None = None
    status: str | None = Field(None, description="e.g. new, continued, discontinued")


class LabResult(_Lenient):
    test: str
    value: str
    unit: str | None = None
    reference_range: str | None = None
    flag: Literal["high", "low", "normal", "critical"] | None = None


class Vital(_Lenient):
    name: str
    value: str
    unit: str | None = None


class ClinicalExtraction(_Lenient):
    document_type: str | None = Field(None, description="e.g. discharge summary, lab report, referral letter")
    patient: Patient = Field(default_factory=Patient)
    encounter: Encounter = Field(default_factory=Encounter)
    diagnoses: list[Diagnosis] = Field(default_factory=list)
    medications: list[Medication] = Field(default_factory=list)
    allergies: list[str] = Field(default_factory=list)
    lab_results: list[LabResult] = Field(default_factory=list)
    vitals: list[Vital] = Field(default_factory=list)
    procedures: list[str] = Field(default_factory=list)
    follow_up: list[str] = Field(default_factory=list)
    summary: str | None = Field(None, description="2-3 sentence clinical summary")


# ---------- API response models ----------

class DocumentMeta(BaseModel):
    filename: str
    size_bytes: int
    pages: int
    chars_extracted: int
    truncated: bool


class InferenceMeta(BaseModel):
    provider: str
    model: str
    latency_ms: float
    attempts: int
    input_tokens: int | None = None
    output_tokens: int | None = None


class ExtractionRecord(BaseModel):
    id: str
    created_at: str
    document: DocumentMeta
    inference: InferenceMeta
    data: ClinicalExtraction
    warnings: list[str] = Field(default_factory=list)


class ExtractionSummary(BaseModel):
    id: str
    created_at: str
    filename: str
    document_type: str | None
    patient_name: str | None
    provider: str


class ApiResponse(BaseModel):
    """Success envelope. Errors use the same shape with success=false (see errors.py)."""
    success: bool = True
    data: object
    request_id: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
