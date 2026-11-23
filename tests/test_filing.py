"""End-to-end tests with a fake reader in place of Claude (no API key or internet needed)."""
from __future__ import annotations

import csv
from datetime import date, timedelta
from pathlib import Path

import pytest
from reportlab.pdfgen import canvas

from dnfiler.config import load_config
from dnfiler.extractor import DocumentInfo, ExtractionError
from dnfiler.processor import Processor
from dnfiler.watcher import Watcher

TODAY = date.today()
D1 = (TODAY - timedelta(days=3)).isoformat()


def doc(customer="ABC Trading Sdn Bhd", d=D1, dn="DN-1001", pages=(1, 1), match="", conf="high", is_dn=True):
    return DocumentInfo(is_dn, pages[0], pages[1], dn, d, d, customer, match, conf, "")


class FakeExtractor:
    """Returns pre-set answers keyed by file name."""

    def __init__(self):
        self.answers: dict[str, object] = {}
        self.calls = 0

    def extract(self, pdf: Path, known):
        self.calls += 1
        answer = self.answers[pdf.name]
        if isinstance(answer, Exception):
            raise answer
        return answer


def make_pdf(path: Path, pages=1, text="Delivery Note"):
    c = canvas.Canvas(str(path))
    for i in range(pages):
        c.drawString(72, 720, f"{text} page {i + 1}")
        c.showPage()
    c.save()
    return path


@pytest.fixture
def env(tmp_path):
    (tmp_path / "config.yaml").write_text(
        f"inbox: '{tmp_path / 'inbox'}'\noutput_root: '{tmp_path / 'out'}'\ndata_folder: '{tmp_path / 'data'}'\n"
        "stable_seconds: 0\n",
        encoding="utf-8",
    )
    cfg = load_config(tmp_path / "config.yaml")
    fake = FakeExtractor()
    return cfg, fake, Processor(cfg, fake)


def month_dir(cfg, d: str) -> Path:
    y, m = int(d[:4]), int(d[5:7])
    import calendar
    return cfg.output_root / str(y) / f"{m:02d} {calendar.month_name[m]} {y}"


def test_files_into_year_month_customer(env):
    cfg, fake, proc = env
    src = make_pdf(cfg.inbox / "scan001.pdf")
    fake.answers["scan001.pdf"] = [doc()]
    out = proc.process(src)
    assert out[0].result == "filed"
    assert out[0].saved_as == month_dir(cfg, D1) / "ABC Trading Sdn Bhd" / f"{D1} DN-1001.pdf"
    assert out[0].saved_as.exists() and not src.exists()


def test_same_customer_spelled_differently_shares_folder(env):
    cfg, fake, proc = env
    fake.answers["a.pdf"] = [doc()]
    fake.answers["b.pdf"] = [doc(customer="ABC TRADING SDN. BHD.", dn="DN-1002")]
    proc.process(make_pdf(cfg.inbox / "a.pdf"))
    out = proc.process(make_pdf(cfg.inbox / "b.pdf", text="other"))
    assert out[0].saved_as.parent.name == "ABC Trading Sdn Bhd"


def test_claude_match_to_existing_folder_is_used(env):
    cfg, fake, proc = env
    (month_dir(cfg, D1) / "Hup Seng Hardware").mkdir(parents=True)
    fake.answers["a.pdf"] = [doc(customer="HUP SENG HARDWARE (KLANG BRANCH)", match="Hup Seng Hardware")]
    out = proc.process(make_pdf(cfg.inbox / "a.pdf"))
    assert out[0].saved_as.parent.name == "Hup Seng Hardware"


def test_near_duplicate_customer_goes_to_review(env):
    cfg, fake, proc = env
    fake.answers["a.pdf"] = [doc(customer="Sinar Jaya Trading")]
    fake.answers["b.pdf"] = [doc(customer="Sinar Jaya Tradings", dn="DN-2")]
    proc.process(make_pdf(cfg.inbox / "a.pdf"))
    out = proc.process(make_pdf(cfg.inbox / "b.pdf", text="b"))
    assert out[0].result == "review"
    note = out[0].saved_as.with_suffix(".txt").read_text()
    assert "Sinar Jaya Trading" in note and "similar" in note


def test_batch_scan_is_split(env):
    cfg, fake, proc = env
    src = make_pdf(cfg.inbox / "batch.pdf", pages=3)
    fake.answers["batch.pdf"] = [
        doc(customer="Alpha Sdn Bhd", dn="DN-1", pages=(1, 2)),
        doc(customer="Beta Enterprise", dn="DN-2", pages=(3, 3)),
    ]
    out = proc.process(src)
    assert [o.result for o in out] == ["filed", "filed"]
    from pypdf import PdfReader
    assert len(PdfReader(str(out[0].saved_as)).pages) == 2
    assert len(PdfReader(str(out[1].saved_as)).pages) == 1
    assert out[1].saved_as.parent.name == "Beta Enterprise"
    assert not src.exists()


def test_batch_split_failing_halfway_never_files_twice(env, monkeypatch):
    cfg, fake, proc = env
    src = make_pdf(cfg.inbox / "batch.pdf", pages=2)
    fake.answers["batch.pdf"] = [doc(dn="DN-1", pages=(1, 1)), doc(dn="DN-2", pages=(2, 2))]
    real = proc._extract_pages
    monkeypatch.setattr(proc, "_extract_pages", lambda s, a, b, n: real(s, a, b, n) if n == 1 else 1 / 0)
    out = proc.process(src)
    assert [o.result for o in out] == ["filed", "review"]
    assert "Already filed" in out[1].reason and not src.exists()
    make_pdf(cfg.inbox / "again.pdf")  # the tool keeps going
    fake.answers["again.pdf"] = [doc(dn="DN-3")]
    assert proc.process(cfg.inbox / "again.pdf")[0].result == "filed"


def test_duplicate_scan_is_set_aside(env):
    cfg, fake, proc = env
    content = make_pdf(cfg.inbox / "a.pdf").read_bytes()
    fake.answers["a.pdf"] = [doc()]
    proc.process(cfg.inbox / "a.pdf")
    (cfg.inbox / "a.pdf").write_bytes(content)  # same scan dropped in again
    out = proc.process(cfg.inbox / "a.pdf")
    assert out[0].result == "duplicate" and out[0].saved_as.parent == cfg.duplicates_folder
    assert fake.calls == 1  # no second API call


@pytest.mark.parametrize("bad", [
    doc(d=""),
    doc(d=(TODAY + timedelta(days=40)).isoformat()),
    doc(d="2027-02-30"),
    doc(customer=""),
    doc(conf="low"),
    doc(is_dn=False),
])
def test_unclear_documents_go_to_review(env, bad):
    cfg, fake, proc = env
    fake.answers["x.pdf"] = [bad]
    out = proc.process(make_pdf(cfg.inbox / "x.pdf"))
    assert out[0].result == "review"
    assert out[0].saved_as.parent == cfg.review_folder
    assert out[0].saved_as.with_suffix(".txt").exists()


def test_never_overwrites(env):
    cfg, fake, proc = env
    fake.answers["a.pdf"] = [doc()]
    fake.answers["b.pdf"] = [doc()]  # same DN number and date
    first = proc.process(make_pdf(cfg.inbox / "a.pdf"))[0].saved_as
    second = proc.process(make_pdf(cfg.inbox / "b.pdf", text="b"))[0].saved_as
    assert first != second and second.name == f"{D1} DN-1001 (2).pdf"


def test_log_csv_has_a_row_per_file(env):
    cfg, fake, proc = env
    fake.answers["a.pdf"] = [doc()]
    fake.answers["b.pdf"] = [doc(d="")]
    proc.process(make_pdf(cfg.inbox / "a.pdf"))
    proc.process(make_pdf(cfg.inbox / "b.pdf", text="b"))
    rows = list(csv.DictReader(open(cfg.log_file, encoding="utf-8-sig")))
    assert [r["result"] for r in rows] == ["filed", "review"]


def test_watcher_waits_for_stable_file_and_pauses_when_offline(env):
    cfg, fake, proc = env
    w = Watcher(cfg, proc)
    src = make_pdf(cfg.inbox / "a.pdf")
    fake.answers["a.pdf"] = ExtractionError("No connection")
    assert w.tick() == 0  # first sighting: not stable yet
    assert w.tick() == 0  # stable, but API is down -> paused, file stays
    assert src.exists() and w.paused_until > 0
    w.paused_until = 0
    fake.answers["a.pdf"] = [doc()]
    assert w.tick() == 1 and not src.exists()


def test_watcher_gives_up_after_repeated_file_errors(env):
    cfg, fake, proc = env
    cfg.max_attempts = 2
    w = Watcher(cfg, proc)
    src = make_pdf(cfg.inbox / "a.pdf")
    fake.answers["a.pdf"] = ExtractionError("cut off", file_specific=True)
    w.tick(); w.tick()  # sighting, attempt 1
    w.retry_at.clear(); w.tick()  # attempt 2 -> review
    assert not src.exists() and (cfg.review_folder / "a.pdf").exists()


def test_non_pdf_goes_to_review(env):
    cfg, fake, proc = env
    f = cfg.inbox / "photo.jpg"
    f.write_bytes(b"jpg")
    assert proc.process(f)[0].result == "review"
