"""Read BHPetrol "PRODUCT DELIVERY NOTE" scans with OCR and fixed rules. Runs offline, no AI model.

Layout (every page): right column "Delivery Note : 2201328377", "Delivery Date : 08.01.2025", "Page : 1 / 1";
left column: customer name and 12-digit reg. no. on the first two lines under "Delivery Information:".
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pypdfium2 as pdfium

from .extractor import DocumentInfo

MIN_SCORE = 0.90  # below this, a field goes to review instead of being trusted

# one OCR line: (text, x, y, score), x/y = top-left corner as a fraction of the page width/height
Line = tuple[str, float, float, float]


def _value_right_of(lines: list[Line], label: str, pattern: str) -> tuple[re.Match | None, float]:
    """The value printed to the right of a right-column label, on the same row."""
    for text, x, y, _ in lines:
        if text.strip().lower() == label and x > 0.5:
            for vtext, vx, vy, vscore in lines:
                if vx > x + 0.05 and abs(vy - y) < 0.012:
                    m = re.fullmatch(pattern, vtext.replace(" ", "").lstrip(":"))
                    if m:
                        return m, vscore
    return None, 0.0


def _customer(lines: list[Line]) -> tuple[str, str, float]:
    """(name, reg. no., lowest score) from the first two lines under "Delivery Information:"."""
    for text, x, y, _ in lines:
        if text.strip().lower().startswith("delivery information") and x < 0.4:
            below = sorted((ln for ln in lines if ln[1] < 0.4 and 0 < ln[2] - y < 0.06), key=lambda ln: ln[2])
            if len(below) >= 2 and re.fullmatch(r"\d{12}", below[1][0].replace(" ", "")):
                return below[0][0].strip(), below[1][0].replace(" ", ""), min(below[0][3], below[1][3])
            return (below[0][0].strip() if below else ""), "", 0.0
    return "", "", 0.0


def parse_page(lines: list[Line]) -> dict:
    """Pull the fields out of one page's OCR lines."""
    m_dn, s_dn = _value_right_of(lines, "delivery note", r"\d{10}")
    m_date, s_date = _value_right_of(lines, "delivery date", r"(\d{2})\.(\d{2})\.(\d{4})")
    m_page, _ = _value_right_of(lines, "page", r"(\d+)/(\d+)")
    dn = m_dn[0] if m_dn else ""
    date = f"{m_date[3]}-{m_date[2]}-{m_date[1]}" if m_date else ""  # DD.MM.YYYY -> YYYY-MM-DD
    name, reg, s_cust = _customer(lines)
    missing = [f for f, v in (("DN number", dn), ("date", date), ("customer", name), ("reg. no.", reg)) if not v]
    weak = [f for f, v, s in (("DN number", dn, s_dn), ("date", date, s_date), ("customer", name, s_cust))
            if v and s < MIN_SCORE]
    n, total = (int(m_page[1]), int(m_page[2])) if m_page else (1, 1)
    return {"dn": dn, "date": date, "name": name, "reg": reg, "n": n, "total": total,
            "missing": missing, "weak": weak}


def group_pages(pages: list[dict]) -> list[DocumentInfo]:
    """Turn per-page results into delivery notes. "Page 2/2" with the same DN joins the page before."""
    docs: list[tuple[int, int, dict]] = []  # (first page, last page, fields of first page)
    for i, p in enumerate(pages, 1):
        if docs and p["n"] > 1 and p["dn"] and p["dn"] == docs[-1][2]["dn"] and docs[-1][1] == i - 1:
            docs[-1] = (docs[-1][0], i, docs[-1][2])
        else:
            docs.append((i, i, p))
    out = []
    for first, last, p in docs:
        problems = []
        if not p["dn"]:
            problems.append("no DN number found")
        problems += [f"{f} not found" for f in p["missing"] if f != "DN number"]
        problems += [f"{f} hard to read" for f in p["weak"]]
        if p["n"] != 1 or last - first + 1 != p["total"]:
            problems.append(f"pages incomplete (page {p['n']}/{p['total']}, {last - first + 1} page(s) in scan)")
        out.append(DocumentInfo(
            is_delivery_note=bool(p["dn"] or p["date"] or p["name"]),
            page_start=first, page_end=last, dn_number=p["dn"], date=p["date"], date_as_printed=p["date"],
            customer_name=p["name"], matched_known_customer="", customer_reg=p["reg"],
            confidence="low" if problems else "high", notes="; ".join(problems),
        ))
    return out


class BhpReader:
    """Same interface as ClaudeExtractor: extract(pdf, known_customers) -> list[DocumentInfo]."""

    def __init__(self):
        from rapidocr import RapidOCR  # slow import; only when the local engine is used
        self.ocr = RapidOCR(params={"Global.log_level": "warning"})

    def read_lines(self, image: np.ndarray) -> list[Line]:
        h, w = image.shape[:2]
        r = self.ocr(image)
        if r.txts is None:
            return []
        return [(t, float(b[0][0]) / w, float(b[0][1]) / h, float(s)) for t, b, s in zip(r.txts, r.boxes, r.scores)]

    def read_page(self, page) -> dict:
        image = np.array(page.render(scale=200 / 72).to_pil().convert("RGB"))
        fields = parse_page(self.read_lines(image))
        if not fields["dn"]:  # maybe scanned upside down
            turned = parse_page(self.read_lines(np.ascontiguousarray(image[::-1, ::-1])))
            if turned["dn"]:
                fields = turned
        return fields

    def extract(self, pdf_path: Path, known_customers: list[str]) -> list[DocumentInfo]:
        pdf = pdfium.PdfDocument(str(pdf_path))
        try:
            return group_pages([self.read_page(pdf[i]) for i in range(len(pdf))])
        finally:
            pdf.close()
