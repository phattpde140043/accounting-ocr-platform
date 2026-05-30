from dataclasses import dataclass
from typing import Protocol

from app.core.config import settings


@dataclass(frozen=True)
class FileScanResult:
    status: str
    scanner: str

    @property
    def is_clean(self) -> bool:
        return self.status == "clean"


class FileScanner(Protocol):
    async def scan(self, *, content: bytes, mime_type: str) -> FileScanResult:
        """Scan validated content before it becomes eligible for OCR."""


class LocalNoOpFileScanner:
    async def scan(self, *, content: bytes, mime_type: str) -> FileScanResult:
        return FileScanResult(status="clean", scanner="local-noop")


def get_file_scanner() -> FileScanner:
    if settings.file_scanner_mode == "local-noop" and settings.environment in {
        "local",
        "test",
    }:
        return LocalNoOpFileScanner()
    raise RuntimeError("A production antivirus file scanner must be configured.")
