"""Command line.

    python -m dnfiler run            keep watching the inbox (what the Windows task runs)
    python -m dnfiler once           file everything in the inbox now, then stop
    python -m dnfiler check X.pdf    show what would be read from one PDF; moves nothing
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from dataclasses import asdict
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .config import load_config
from .customers import CustomerBook
from .extractor import ClaudeExtractor, ExtractionError
from .processor import Processor
from .watcher import Watcher

APP_DIR = Path(__file__).resolve().parent.parent


def setup_logging(data_folder: Path) -> None:
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(message)s", "%Y-%m-%d %H:%M:%S")
    root = logging.getLogger("dnfiler")
    root.setLevel(logging.INFO)
    file_handler = RotatingFileHandler(data_folder / "dnfiler.log", maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(fmt)
    root.addHandler(file_handler)
    if sys.stdout:  # pythonw has no console
        console = logging.StreamHandler(sys.stdout)
        console.setFormatter(fmt)
        root.addHandler(console)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="dnfiler", description="File scanned delivery notes automatically.")
    parser.add_argument("--config", type=Path, default=APP_DIR / "config.yaml")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="keep watching the inbox")
    sub.add_parser("once", help="file everything in the inbox now, then stop")
    check = sub.add_parser("check", help="show what would be read from one PDF; moves nothing")
    check.add_argument("pdf", type=Path)
    sub.add_parser("selftest", help="check the folders and the OCR engine work (the installer runs this)")
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    setup_logging(cfg.data_folder)
    log = logging.getLogger("dnfiler")
    if cfg.engine == "claude":
        if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
            log.error("No API key. Put ANTHROPIC_API_KEY=... in %s", args.config.parent / ".env")
            return 2
        extractor = ClaudeExtractor(cfg.model, cfg.date_order, cfg.own_company_names)
    else:
        from .bhp_reader import BhpReader
        extractor = BhpReader()

    if args.command == "selftest":
        for folder in (cfg.inbox, cfg.output_root, cfg.review_folder, cfg.data_folder):
            probe = folder / ".bhp-write-test"
            probe.write_text("ok")  # raises if the folder isn't writable
            probe.unlink()
        if cfg.engine != "claude":
            import numpy as np
            extractor.read_lines(np.full((200, 600, 3), 255, np.uint8))  # loads the bundled OCR models
        print("Ready")
        return 0

    if args.command == "check":
        known = CustomerBook(cfg.customers_file, cfg.output_root, cfg.customer_match_review).known()
        docs = extractor.extract(args.pdf, known)
        print(json.dumps([asdict(d) for d in docs], indent=2, ensure_ascii=False))
        return 0

    processor = Processor(cfg, extractor)
    watcher = Watcher(cfg, processor)
    if args.command == "once":
        failed = 0
        for f in watcher.candidates():
            try:
                processor.process(f)
            except ExtractionError as e:
                log.error("Left in inbox: %s (%s)", f.name, e)
                failed += 1
        return 1 if failed else 0

    watcher.run_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
