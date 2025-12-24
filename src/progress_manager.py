import json
import logging
import os
from typing import Set

logger = logging.getLogger(__name__)

class ProgressManager:
    """Manages the progress of file processing to allow resuming after interruption."""

    def __init__(self, work_dir: str):
        self.progress_file = os.path.join(work_dir, "progress.json")
        self.processed_files: Set[str] = set()
        self._load()

    def _load(self) -> None:
        """Load progress from file if it exists."""
        if os.path.exists(self.progress_file):
            try:
                with open(self.progress_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.processed_files = set(data.get("processed_files", []))
                logger.debug(f"Loaded progress: {len(self.processed_files)} files already processed.")
            except Exception as e:
                logger.error(f"Failed to load progress file: {e}")

    def save(self) -> None:
        """Save current progress to file."""
        data = {
            "processed_files": list(self.processed_files)
        }
        try:
            with open(self.progress_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save progress file: {e}")

    def mark_processed(self, file_path: str) -> None:
        """Mark a file as processed and save."""
        self.processed_files.add(file_path)
        self.save()

    def is_processed(self, file_path: str) -> bool:
        """Check if a file has already been processed."""
        return file_path in self.processed_files
