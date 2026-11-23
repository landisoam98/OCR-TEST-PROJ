"""Check the inbox folder over and over, and hand finished scans to the processor."""
from __future__ import annotations

import logging
import time
from pathlib import Path

from .config import Config
from .extractor import ExtractionError
from .processor import Processor

log = logging.getLogger("dnfiler")

IGNORE_PREFIXES = ("~", ".", "_")
IGNORE_SUFFIXES = (".tmp", ".part", ".crdownload", ".lock")
STOP_NOTE = "!! BHP SCANNER STOPPED - read me.txt"  # in the review folder, which people check daily


class Watcher:
    def __init__(self, cfg: Config, processor: Processor):
        self.cfg = cfg
        self.processor = processor
        self.sizes: dict[Path, tuple[int, float, float]] = {}  # path -> (size, mtime, unchanged since)
        self.attempts: dict[Path, int] = {}
        self.retry_at: dict[Path, float] = {}
        self.paused_until = 0.0  # set when the API/internet is down

    def candidates(self) -> list[Path]:
        files = []
        for f in sorted(self.cfg.inbox.iterdir()):
            if not f.is_file() or f.name.startswith(IGNORE_PREFIXES) or f.name.lower().endswith(IGNORE_SUFFIXES):
                continue
            files.append(f)
        return files

    def is_ready(self, f: Path, now: float) -> bool:
        """Ready = size and modified time unchanged for stable_seconds, and nobody holds the file open."""
        try:
            st = f.stat()
        except FileNotFoundError:
            return False
        key = (st.st_size, st.st_mtime)
        prev = self.sizes.get(f)
        if prev is None or prev[:2] != key:
            self.sizes[f] = (*key, now)
            return False
        if st.st_size == 0 or now - prev[2] < self.cfg.stable_seconds:
            return False
        try:
            # On Windows this fails while the scanner is still writing the file.
            with open(f, "r+b"):
                pass
        except OSError:
            return False
        return True

    def tick(self) -> int:
        """One pass over the inbox. Returns how many files were handled."""
        now = time.time()
        if now < self.paused_until:
            return 0
        handled = 0
        present = set()
        for f in self.candidates():
            present.add(f)
            if now < self.retry_at.get(f, 0) or not self.is_ready(f, now):
                continue
            try:
                self.processor.process(f)
                handled += 1
                self._forget(f)
            except ExtractionError as e:
                if not e.file_specific:
                    log.error("Paused 60s: %s. Files stay in the inbox.", e)
                    self.paused_until = now + 60
                    self.set_stopped(str(e))
                    break
                n = self.attempts.get(f, 0) + 1
                self.attempts[f] = n
                if n >= self.cfg.max_attempts:
                    self.processor.give_up(f, f"Failed {n} times: {e}")
                    self._forget(f)
                else:
                    self.retry_at[f] = now + 30 * 2 ** (n - 1)
                    log.warning("Attempt %d failed for %s: %s", n, f.name, e)
            except PermissionError as e:
                log.warning("File busy, will retry: %s (%s)", f.name, e)
                self.retry_at[f] = now + 30
            except Exception:
                log.exception("Unexpected error with %s; will retry", f.name)
                n = self.attempts.get(f, 0) + 1
                self.attempts[f] = n
                self.retry_at[f] = now + 60
                if n >= self.cfg.max_attempts and f.exists():
                    try:
                        self.processor.give_up(f, "Unexpected error, see dnfiler.log")
                    except Exception:
                        log.exception("Could not move %s to review", f.name)
                    self._forget(f)
        for gone in set(self.sizes) - present:
            self._forget(gone)
        return handled

    def _forget(self, f: Path) -> None:
        self.sizes.pop(f, None)
        self.attempts.pop(f, None)
        self.retry_at.pop(f, None)

    def set_stopped(self, reason: str | None) -> None:
        """Show (reason) or clear (None) the STOPPED note, so a stuck tool doesn't go unnoticed."""
        note = self.cfg.review_folder / STOP_NOTE
        try:
            if reason:
                note.write_text(
                    f"BHP Scanner can't file new scans right now. They are waiting in the inbox.\n\n"
                    f"Problem: {reason}\nSince: {time.strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"This note disappears by itself when it works again. Details: dnfiler.log\n",
                    encoding="utf-8")
            elif note.exists():
                note.unlink()
        except OSError:
            log.exception("Could not update %s", note)

    def run_forever(self) -> None:
        log.info("Watching %s every %ss", self.cfg.inbox, self.cfg.poll_seconds)
        while True:
            try:
                self.tick()
                if time.time() >= self.paused_until:
                    self.set_stopped(None)
            except Exception as e:
                log.exception("Error while checking the inbox")
                self.set_stopped(str(e))
            time.sleep(self.cfg.poll_seconds)
