from fastapi import APIRouter, Depends, File, UploadFile

from ..config import Settings, get_settings
from ..errors import FileTooLargeError, InvalidFileError, NotFoundError
from ..security import require_user
from ..services.extractor import run_extraction
from ..services.llm.base import LLMClient
from ..services.store import ExtractionStore
from .common import get_llm, get_store, ok

router = APIRouter(tags=["extraction"])

ALLOWED_TYPES = {"application/pdf", "application/x-pdf", "application/octet-stream"}


async def read_limited(upload: UploadFile, max_bytes: int) -> bytes:
    """Read in 1 MB chunks and stop as soon as the limit is passed (never buffer a huge file)."""
    chunks, total = [], 0
    while chunk := await upload.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise FileTooLargeError(f"File exceeds {max_bytes // (1024 * 1024)} MB")
        chunks.append(chunk)
    return b"".join(chunks)


@router.post("/extract")
async def extract(
    file: UploadFile = File(..., description="A text-based clinical PDF"),
    user: str = Depends(require_user),
    settings: Settings = Depends(get_settings),
    llm: LLMClient = Depends(get_llm),
    store: ExtractionStore = Depends(get_store),
):
    if not (file.filename or "").lower().endswith(".pdf") or (file.content_type or "") not in ALLOWED_TYPES:
        raise InvalidFileError("Only PDF files are accepted")
    data = await read_limited(file, settings.max_upload_mb * 1024 * 1024)
    record = await run_extraction(file.filename, data, settings, llm)
    store.add(record)
    return ok(record)


@router.get("/extractions")
def list_extractions(user: str = Depends(require_user), store: ExtractionStore = Depends(get_store)):
    return ok(store.list())


@router.get("/extractions/{record_id}")
def get_extraction(record_id: str, user: str = Depends(require_user), store: ExtractionStore = Depends(get_store)):
    record = store.get(record_id)
    if record is None:
        raise NotFoundError(f"Extraction {record_id} not found")
    return ok(record)
