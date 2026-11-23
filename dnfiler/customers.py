"""The customer list the tool builds by itself.

Known customers = names in customers.json + customer folders that already exist under the output root
(so a folder a person creates or renames by hand is picked up too).
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

from rapidfuzz import fuzz

LEGAL_SUFFIXES = re.compile(
    r"\b(SDN\s*BHD|SENDIRIAN\s+BERHAD|BERHAD|BHD|PTE\s*LTD|PTE|PRIVATE\s+LIMITED|LIMITED|LTD|PLC|INC|LLC|CORP|CO)\b"
)
BAD_FOLDER_CHARS = re.compile(r'[<>:"/\\|?*\x00-\x1f]')


def normalise(name: str) -> str:
    """'ABC Trading Sdn. Bhd.' and 'abc trading sdn bhd' both become 'ABC TRADING'."""
    s = name.upper().replace("&", " AND ")
    s = re.sub(r"[^\w\s]", " ", s)
    s = LEGAL_SUFFIXES.sub(" ", s)
    return re.sub(r"\s+", " ", s).strip()


def folder_name(name: str) -> str:
    """Make a printed name safe as a Windows folder name."""
    s = BAD_FOLDER_CHARS.sub(" ", name)
    s = re.sub(r"\s+", " ", s).strip().rstrip(". ")
    return s[:80].rstrip(". ") or "Unknown"


@dataclass
class Match:
    status: str  # "known" | "new" | "review"
    folder: str  # customer folder to use ("" when status is review)
    reason: str = ""


class CustomerBook:
    def __init__(self, path: Path, output_root: Path, review_threshold: int):
        self.path = path
        self.output_root = output_root
        self.review_threshold = review_threshold
        self.data: dict[str, dict] = {}
        if path.exists():
            self.data = json.loads(path.read_text(encoding="utf-8")).get("customers", {})

    def known(self) -> list[str]:
        names = set(self.data)
        # <root>\<year>\<month>\<customer>
        for year in self.output_root.iterdir() if self.output_root.exists() else []:
            if not (year.is_dir() and year.name.isdigit()):
                continue
            for month in year.iterdir():
                if month.is_dir():
                    names.update(c.name for c in month.iterdir() if c.is_dir())
        return sorted(names)

    def resolve(self, printed: str, claude_match: str, reg: str = "") -> Match:
        printed = printed.strip()
        if not printed:
            return Match("review", "", "No customer name found")
        known = self.known()
        if claude_match and claude_match in known:
            return Match("known", claude_match)

        if reg:  # the reg. no. identifies the company; the name may have OCR slips
            for name in known:
                if self.data.get(name, {}).get("reg") == reg:
                    return Match("known", name)

        target = normalise(printed)
        for name in known:
            aliases = [name, *self.data.get(name, {}).get("aliases", [])]
            if any(normalise(a) == target for a in aliases):
                other = self.data.get(name, {}).get("reg")
                if reg and other and other != reg:
                    return Match("review", "", f'"{printed}" has reg. no. {reg}, but folder "{name}" '
                                               f"belongs to reg. no. {other} (OCR slip or a different company)")
                return Match("known", name)
        if reg:  # different reg. no. = different company, even with a similar name
            return Match("new", folder_name(printed))

        best, best_score = "", 0.0
        for name in known:
            score = fuzz.token_sort_ratio(target, normalise(name))
            if score > best_score:
                best, best_score = name, score
        if best_score >= self.review_threshold:
            return Match(
                "review", "",
                f'Customer "{printed}" looks like existing folder "{best}" ({best_score:.0f}% similar) '
                "but may be a different company",
            )
        return Match("new", folder_name(printed))

    def remember(self, folder: str, printed: str, reg: str = "") -> None:
        entry = self.data.setdefault(folder, {"aliases": []})
        if reg:
            entry.setdefault("reg", reg)
        if printed and printed != folder and printed not in entry["aliases"]:
            entry["aliases"].append(printed)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"customers": self.data}, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(self.path)
