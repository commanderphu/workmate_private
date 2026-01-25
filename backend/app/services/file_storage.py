"""
File storage service
"""

import hashlib
import os
from pathlib import Path
from typing import BinaryIO
from uuid import UUID
import aiofiles

from ..core.config import settings


class FileStorageService:
    """Service for handling file storage"""

    def __init__(self):
        self.storage_path = Path(settings.UPLOAD_DIR)
        self.storage_path.mkdir(parents=True, exist_ok=True)

    async def save_file(
        self,
        file_content: bytes,
        filename: str,
        user_id: UUID,
    ) -> tuple[str, str, int]:
        """
        Save file to storage

        Returns:
            tuple: (file_path, checksum, size_bytes)
        """
        # Create user directory
        user_dir = self.storage_path / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename to avoid collisions
        file_ext = Path(filename).suffix
        checksum = hashlib.sha256(file_content).hexdigest()
        unique_filename = f"{checksum[:16]}{file_ext}"

        file_path = user_dir / unique_filename

        # Save file
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(file_content)

        # Return relative path from storage root
        relative_path = str(file_path.relative_to(self.storage_path))

        return relative_path, checksum, len(file_content)

    async def read_file(self, file_path: str) -> bytes:
        """Read file from storage"""
        full_path = self.storage_path / file_path

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        async with aiofiles.open(full_path, 'rb') as f:
            return await f.read()

    async def delete_file(self, file_path: str) -> None:
        """Delete file from storage"""
        full_path = self.storage_path / file_path

        if full_path.exists():
            full_path.unlink()

    def get_full_path(self, file_path: str) -> Path:
        """Get full system path for a file"""
        return self.storage_path / file_path
