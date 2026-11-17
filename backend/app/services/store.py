"""Recent extractions, kept in memory (last 50). Good enough for a demo; lost on restart.
Next step for production: DynamoDB for records + S3 for the original PDFs."""
from collections import OrderedDict
from threading import Lock

from ..schemas import ExtractionRecord, ExtractionSummary


class ExtractionStore:
    def __init__(self, max_items: int = 50):
        self._items: OrderedDict[str, ExtractionRecord] = OrderedDict()
        self._max = max_items
        self._lock = Lock()

    def add(self, record: ExtractionRecord) -> None:
        with self._lock:
            self._items[record.id] = record
            while len(self._items) > self._max:
                self._items.popitem(last=False)

    def get(self, record_id: str) -> ExtractionRecord | None:
        return self._items.get(record_id)

    def list(self) -> list[ExtractionSummary]:
        return [
            ExtractionSummary(
                id=r.id, created_at=r.created_at, filename=r.document.filename,
                document_type=r.data.document_type, patient_name=r.data.patient.name,
                provider=r.inference.provider,
            )
            for r in reversed(self._items.values())
        ]
