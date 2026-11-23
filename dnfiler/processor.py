"""Decide where one scanned PDF goes, and put it there."""
from __future__ import annotations

import calendar
import csv
import hashlib
import logging
import re
import shutil
import sqlite3
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from pypdf import PdfReader, PdfWriter

from .config import Config
from .customers import CustomerBook, folder_name
from .extractor import DocumentInfo, ExtractionRefused

log = logging.getLogger("dnfiler")

LOG_COLUMNS = [
    "time", "source_file", "pages", "result", "dn_number", "date", "customer_printed",
    "customer_folder", "confidence", "saved_as", "reason",
]


@dataclass
class Outcome:
    result: str  # filed | review | duplicate
    saved_as: Path
    reason: str = ""


class Processor:
    def __init__(self, cfg: Config, extractor):
        self.cfg = cfg
        self.extractor = extractor
        self.customers = CustomerBook(cfg.customers_file, cfg.output_root, cfg.customer_match_review)
        self.db = sqlite3.connect(cfg.state_db)
        self.db.execute("CREATE TABLE IF NOT EXISTS seen (sha256 TEXT PRIMARY KEY, source TEXT, at TEXT)")
        self.db.commit()

    # ---------- public ----------

    def process(self, src: Path) -> list[Outcome]:
        """File one PDF from the inbox. Raises ExtractionError if it should be retried later."""
        if src.suffix.lower() != ".pdf":
            return [self._to_review(src, src.name, "Not a PDF file", None)]

        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        seen = self.db.execute("SELECT source, at FROM seen WHERE sha256=?", (digest,)).fetchone()
        if seen:
            dest = self._unique(self.cfg.duplicates_folder / src.name)
            shutil.move(str(src), dest)
            reason = f"Exact copy of {seen[0]} (processed {seen[1]})"
            self._log(src.name, "", "duplicate", None, "", dest, reason)
            return [Outcome("duplicate", dest, reason)]

        try:
            page_count = len(PdfReader(str(src)).pages)
        except Exception as e:  # corrupt / password-protected PDF
            return [self._to_review(src, src.name, f"Could not open PDF: {e}", None)]

        try:
            docs = self.extractor.extract(src, self.customers.known())
        except ExtractionRefused as e:
            return [self._to_review(src, src.name, str(e), None)]

        docs = self._clean_ranges(docs, page_count)
        if not docs:
            return [self._to_review(src, src.name, "No document found in the scan", None)]

        if len(docs) == 1:
            outcomes = [self._place(src, src.name, docs[0], page_count, move=True)]
        else:
            outcomes = []
            try:
                for i, doc in enumerate(docs, 1):
                    part = self._extract_pages(src, doc.page_start, doc.page_end, i)
                    outcomes.append(self._place(part, src.name, doc, page_count, move=True))
                src.unlink()
            except Exception as e:
                if not outcomes:
                    raise  # nothing filed yet: a plain retry is safe
                # Some parts are already filed; a retry would file them twice. Hand the rest to a person.
                done = ", ".join(str(o.saved_as) for o in outcomes)
                outcomes.append(self._to_review(
                    src, src.name, f"Split stopped at part {len(outcomes) + 1} ({e}). Already filed: {done}", None))

        self.db.execute(
            "INSERT OR IGNORE INTO seen VALUES (?,?,?)",
            (digest, src.name, datetime.now().isoformat(timespec="seconds")),
        )
        self.db.commit()
        return outcomes

    def give_up(self, src: Path, reason: str) -> Outcome:
        """Too many failed attempts: hand the file to a person."""
        return self._to_review(src, src.name, reason, None)

    # ---------- deciding ----------

    def _place(self, file: Path, source_name: str, doc: DocumentInfo, page_count: int, move: bool) -> Outcome:
        pages = f"{doc.page_start}-{doc.page_end} of {page_count}"
        if not doc.is_delivery_note:
            return self._to_review(file, source_name, f"Pages {pages} are not a delivery note. {doc.notes}", doc)
        if doc.confidence == "low":
            return self._to_review(file, source_name, f"Low confidence reading. {doc.notes}", doc)

        dn_date, problem = self._check_date(doc.date)
        if problem:
            return self._to_review(file, source_name, problem, doc)

        match = self.customers.resolve(doc.customer_name, doc.matched_known_customer, doc.customer_reg)
        if match.status == "review":
            return self._to_review(file, source_name, match.reason, doc)

        folder = (
            self.cfg.output_root
            / self.cfg.year_folder_format.format(year=dn_date.year)
            / self.cfg.month_folder_format.format(
                year=dn_date.year, month=dn_date.month, month_name=calendar.month_name[dn_date.month]
            )
            / match.folder
        )
        folder.mkdir(parents=True, exist_ok=True)
        stem = self.cfg.file_name_format.format(
            date=dn_date.isoformat(), dn_number=doc.dn_number or Path(source_name).stem
        )
        dest = self._unique(folder / f"{folder_name(stem)}.pdf")
        shutil.move(str(file), dest)
        self.customers.remember(match.folder, doc.customer_name, doc.customer_reg)
        reason = "New customer folder" if match.status == "new" else ""
        self._log(source_name, pages, "filed", doc, match.folder, dest, reason)
        log.info("Filed %s -> %s", source_name, dest)
        return Outcome("filed", dest, reason)

    def _check_date(self, text: str) -> tuple[date | None, str]:
        if not text:
            return None, "No delivery note date found"
        try:
            d = datetime.strptime(text, "%Y-%m-%d").date()
        except ValueError:
            return None, f'Date "{text}" is not a valid date'
        today = date.today()
        if d > today + timedelta(days=self.cfg.max_days_in_future):
            return None, f"Date {d} is in the future (day and month may be swapped)"
        if d < today - timedelta(days=366 * self.cfg.max_years_in_past):
            return None, f"Date {d} is more than {self.cfg.max_years_in_past} years old"
        return d, ""

    @staticmethod
    def _clean_ranges(docs: list[DocumentInfo], page_count: int) -> list[DocumentInfo]:
        """Keep page ranges inside the PDF. If the ranges don't make sense, treat the PDF as one document."""
        docs = sorted(docs, key=lambda d: d.page_start)
        valid = all(1 <= d.page_start <= d.page_end <= page_count for d in docs)
        overlap = any(a.page_end >= b.page_start for a, b in zip(docs, docs[1:]))
        if docs and (not valid or overlap):
            first = docs[0]
            first.page_start, first.page_end = 1, page_count
            first.confidence = "low"
            first.notes = (first.notes + " Page ranges were unclear.").strip()
            return [first]
        if len(docs) == 1:
            docs[0].page_start, docs[0].page_end = 1, page_count  # stray blank pages stay with the note
        return docs

    # ---------- moving ----------

    def _to_review(self, file: Path, source_name: str, reason: str, doc: DocumentInfo | None) -> Outcome:
        dest = self._unique(self.cfg.review_folder / file.name)
        shutil.move(str(file), dest)
        lines = [f"Why this needs a person: {reason}", f"Original scan: {source_name}"]
        if doc:
            lines += [
                f"Pages: {doc.page_start}-{doc.page_end}",
                f"DN number read: {doc.dn_number or '-'}",
                f"Date read: {doc.date or '-'} (printed as: {doc.date_as_printed or '-'})",
                f"Customer read: {doc.customer_name or '-'}",
                f"Confidence: {doc.confidence}",
            ]
        lines += ["", "To fix: move the PDF into the right folder by hand."]
        dest.with_suffix(".txt").write_text("\n".join(lines), encoding="utf-8")
        self._log(source_name, f"{doc.page_start}-{doc.page_end}" if doc else "", "review", doc, "", dest, reason)
        log.warning("Review: %s (%s)", source_name, reason)
        return Outcome("review", dest, reason)

    def _extract_pages(self, src: Path, start: int, end: int, n: int) -> Path:
        reader = PdfReader(str(src))
        writer = PdfWriter()
        for i in range(start - 1, end):
            writer.add_page(reader.pages[i])
        out = self.cfg.data_folder / "work" / f"{src.stem} part{n}.pdf"
        out.parent.mkdir(exist_ok=True)
        with open(out, "wb") as f:
            writer.write(f)
        return out

    @staticmethod
    def _unique(path: Path) -> Path:
        """Never overwrite: 'x.pdf' -> 'x (2).pdf' -> 'x (3).pdf'. The .txt note follows the same name."""
        candidate, n = path, 1
        while candidate.exists() or candidate.with_suffix(".txt").exists():
            n += 1
            candidate = path.with_name(f"{path.stem} ({n}){path.suffix}")
        return candidate

    def _log(self, source, pages, result, doc, customer_folder, saved_as, reason) -> None:
        new = not self.cfg.log_file.exists()
        with open(self.cfg.log_file, "a", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            if new:
                w.writerow(LOG_COLUMNS)
            w.writerow([
                datetime.now().isoformat(timespec="seconds"), source, pages, result,
                doc.dn_number if doc else "", doc.date if doc else "",
                doc.customer_name if doc else "", customer_folder,
                doc.confidence if doc else "", str(saved_as), re.sub(r"\s+", " ", reason).strip(),
            ])
