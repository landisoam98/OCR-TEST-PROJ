"""BHPetrol layout reader: rules, page grouping, reg.-no. matching, and the real 50-page golden batch."""
from __future__ import annotations

import csv
import shutil
from pathlib import Path

import pytest

from dnfiler.bhp_reader import group_pages, parse_page
from dnfiler.watcher import STOP_NOTE, Watcher
from test_filing import doc, env, make_pdf  # noqa: F401  (env is a fixture)

GOLDEN = Path(__file__).parent / "golden"


def page_lines(dn="2201328377", date="08.01.2025", page="1 / 1", name="Klang Bahagia Trading",
               reg="200903147325", score=1.0):
    """OCR lines laid out like the real page (x, y as fractions of the page)."""
    lines = [("PRODUCT DELIVERY NOTE", 0.32, 0.18, 1.0), ("Delivery Information:", 0.04, 0.21, 1.0),
             ("Delivery Note", 0.65, 0.235, 1.0), ("Delivery Date", 0.65, 0.265, 1.0), ("Page", 0.65, 0.28, 1.0)]
    if name:
        lines.append((name, 0.04, 0.233, score))
    if reg:
        lines.append((reg, 0.04, 0.245, 1.0))
    if dn:
        lines.append((f":{dn}", 0.82, 0.236, score))
    if date:
        lines.append((f":{date}", 0.82, 0.266, 1.0))
    if page:
        lines.append((f":{page}", 0.82, 0.281, 1.0))
    return lines


def test_reads_all_fields():
    p = parse_page(page_lines())
    assert (p["dn"], p["date"], p["name"], p["reg"], p["n"], p["total"]) == \
        ("2201328377", "2025-01-08", "Klang Bahagia Trading", "200903147325", 1, 1)
    assert not p["missing"] and not p["weak"]


def test_title_is_not_mistaken_for_the_dn_label():
    lines = [ln for ln in page_lines() if ln[0] != "Delivery Note"]
    assert parse_page(lines)["dn"] == ""


def test_impossible_date_is_passed_on_for_the_date_check():
    assert parse_page(page_lines(date="31.02.2025"))["date"] == "2025-02-31"  # processor rejects it


@pytest.mark.parametrize("kwargs, problem", [
    ({"date": ""}, "date not found"),
    ({"reg": ""}, "reg. no. not found"),
    ({"name": "", "reg": ""}, "customer not found"),
    ({"score": 0.7}, "hard to read"),
])
def test_missing_or_unclear_fields_mark_the_note_low(kwargs, problem):
    [d] = group_pages([parse_page(page_lines(**kwargs))])
    assert d.confidence == "low" and problem in d.notes


def test_two_page_note_is_one_document():
    docs = group_pages([parse_page(page_lines(page="1 / 2")), parse_page(page_lines(page="2 / 2"))])
    assert [(d.page_start, d.page_end, d.confidence) for d in docs] == [(1, 2, "high")]


def test_missing_second_page_goes_to_review():
    docs = group_pages([parse_page(page_lines(page="1 / 2")), parse_page(page_lines(dn="2201328378"))])
    assert [d.confidence for d in docs] == ["low", "high"] and "incomplete" in docs[0].notes


def test_other_page_in_batch_is_not_a_delivery_note():
    docs = group_pages([parse_page(page_lines()), parse_page([("Cover sheet", 0.1, 0.1, 1.0)])])
    assert [d.is_delivery_note for d in docs] == [True, False]


# ---------- customers by reg. no. ----------

def reg_doc(name, reg, dn):
    d = doc(customer=name, dn=dn)
    d.customer_reg = reg
    return d


def test_reg_no_decides_the_customer(env):  # noqa: F811
    cfg, fake, proc = env
    fake.answers = {
        "a.pdf": [reg_doc("Iman Razhan Enterprise", "201603041751", "1")],
        "b.pdf": [reg_doc("Iman Razhan Trading Sdn. Bhd.", "201501027159", "2")],  # similar name, other company
        "c.pdf": [reg_doc("lman Razhan Enterprlse", "201603041751", "3")],          # OCR slips, same company
        "d.pdf": [reg_doc("Iman Razhan Enterprise", "201603041999", "4")],          # same name, other reg
    }
    out = {n: proc.process(make_pdf(cfg.inbox / n, text=n))[0] for n in fake.answers}
    assert out["a.pdf"].saved_as.parent.name == "Iman Razhan Enterprise"
    assert out["b.pdf"].saved_as.parent.name == "Iman Razhan Trading Sdn. Bhd"
    assert out["c.pdf"].saved_as.parent.name == "Iman Razhan Enterprise"
    assert out["d.pdf"].result == "review" and "reg. no." in out["d.pdf"].reason


# ---------- STOPPED note ----------

def test_stopped_note_appears_and_clears(env):  # noqa: F811
    cfg, fake, proc = env
    w = Watcher(cfg, proc)
    w.set_stopped("Inbox not reachable")
    assert "Inbox not reachable" in (cfg.review_folder / STOP_NOTE).read_text()
    w.set_stopped(None)
    assert not (cfg.review_folder / STOP_NOTE).exists()


# ---------- the real 50-page scan (local only; holds customer data, not in git) ----------

@pytest.mark.skipif(not (GOLDEN / "expected.csv").exists(), reason="golden scans not present")
def test_golden_batch_files_every_note_correctly(env):  # noqa: F811
    from dnfiler.bhp_reader import BhpReader
    from dnfiler.processor import Processor
    cfg, _, _ = env
    proc = Processor(cfg, BhpReader())
    expected = list(csv.DictReader(open(GOLDEN / "expected.csv", encoding="utf-8")))
    for pdf in sorted({row["file"] for row in expected}):
        shutil.copy(GOLDEN / pdf, cfg.inbox / pdf)
        proc.process(cfg.inbox / pdf)
    filed = list(csv.DictReader(open(cfg.log_file, encoding="utf-8-sig")))
    assert len(filed) == len(expected)
    for want, got in zip(expected, filed):
        y, m, d = got["date"].split("-")
        assert (got["result"], got["dn_number"], f"{d}.{m}.{y}") == ("filed", want["dn_number"], want["date"])
        assert got["customer_printed"] == want["customer"], want["page"]
    folders = {f.name for f in (cfg.output_root / "2025" / "01 January 2025").iterdir()}
    assert len(list((cfg.output_root / "2025" / "01 January 2025" / "Taipanco Petroleum Sdn Bhd").iterdir())) == 4
    assert {"Iman Razhan Enterprise", "Iman Razhan Trading Sdn. Bhd", "Iman Razhan Resources"} <= folders


def test_selftest_command_as_the_installer_calls_it(tmp_path):
    from dnfiler.__main__ import main
    cfg = tmp_path / "config.yaml"
    cfg.write_text(f"inbox: '{tmp_path / 'in'}'\noutput_root: '{tmp_path / 'out'}'\n", encoding="utf-8")
    assert main(["--config", str(cfg), "selftest"]) == 0  # same argument order as installer + task
