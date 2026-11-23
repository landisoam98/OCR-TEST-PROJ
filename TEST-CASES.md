# BHP Scanner v2: Test Cases

**Pass bar for go-live:** **0 wrong filings** on the golden set and the trial week. Sending to review is acceptable; filing in the wrong place is not.
Each case says how it's run: **Auto** = automated test (runs on every build), **VM** = scripted on a clean Windows VM, **Manual** = a person checks.

---

## A. Reading the BHPetrol delivery note (rules)

| ID | Case | Expected | How |
|---|---|---|---|
| A1 | Golden batch (50 pages) | DN, date, customer and reg. no. match `expected.csv` on 50/50 pages | Auto (golden) |
| A2 | Rubber stamp "8 JAN'25" near the header | Ignored; the printed Delivery Date is used | Auto (golden) |
| A3 | "Reprint Copy" page | Read like an original | Auto (golden, page 3) |
| A4 | Faint or tilted scan | Read correctly, or review. Never wrong. | Auto (extra batch) |
| A5 | Page upside down | Rotated and read | Auto |
| A6 | A page that isn't a delivery note (cover sheet, blank, other form) in the batch | That page goes to review; the rest are filed | Auto |
| A7 | A field missing or cut off | Review naming the missing field | Auto |
| A8 | OCR confidence on a field below 0.90 | Review | Auto |
| A9 | "Page 1/2" + "Page 2/2", same DN number | One 2-page file | Auto |
| A10 | "Page 1/2" with no page 2 | Review | Auto |
| A11 | Customer stamp / handwriting overlapping the printed name | Printed name read, or review | Auto (golden) |

## B. Dates

| ID | Case | Expected | How |
|---|---|---|---|
| B1 | `08.01.2025` | 8 January 2025 → `2025\01 January 2025\` | Auto |
| B2 | `31.02.2025` (impossible) | Review | Auto |
| B3 | More than 7 days in the future | Review | Auto |
| B4 | Last day of the month / 29.02 in a leap year | Right month folder | Auto |

## C. Customer folders

| ID | Case | Expected | How |
|---|---|---|---|
| C1 | First time a customer appears | New folder created | Auto ✓ (v1) |
| C2 | Same customer, different spelling ("SDN. BHD." vs "Sdn Bhd") | Same folder | Auto ✓ (v1) |
| C3 | Known reg. no., name with an OCR slip | Existing folder | Auto |
| C3b | New reg. no., same name as an existing customer | Review | Auto |
| C3c | Iman Razhan Enterprise / Trading / Resources (different reg. nos.) | 3 separate folders, no review | Auto (golden) |
| C3d | Taipanco Petroleum, 4 notes in one batch | All 4 in one folder | Auto (golden) |
| C5 | Name contains `/ : * ? "` | Safe folder name | Auto |
| C6 | Person renames or merges a customer folder by hand | The tool uses the new folder from then on | Auto |

## D. Filing

| ID | Case | Expected | How |
|---|---|---|---|
| D1 | Normal file | `Year\MM Month Year\Customer\date DN.pdf` | Auto ✓ (v1) |
| D2 | 50-page batch | 50 files, each in its customer's folder | Auto (golden) |
| D3 | Exact same scan twice | Second one goes to `_Duplicates`, no model call | Auto ✓ (v1) |
| D4 | Original and Reprint of the same DN | Second saved as `… (2).pdf`, never overwritten | Auto ✓ (v1) |
| D5 | Inbox and output on different drives (C: → D:) | Moved correctly | VM |
| D6 | Folder path with spaces / Chinese characters / > 260 characters | Works (or a clear review note) | VM |
| D7 | Every file has a row in `log.csv`, and the log opens correctly in Excel | Yes | Auto + Manual |

## E. Watching the inbox

| ID | Case | Expected | How |
|---|---|---|---|
| E1 | Scanner still writing a large PDF | Waits until finished | Auto ✓ (v1) + VM |
| E2 | Scanner holds the file locked | Waits, retries, no error loop | VM |
| E3 | 100 PDFs dropped at once | All processed; memory stays under 8 GB; no file lost | VM |
| E4 | Temporary files (`~$`, `.tmp`) | Ignored | Auto |
| E5 | Non-PDF file (JPG) | Review | Auto ✓ (v1) |
| E6 | The same file fails 5 times | Review with the reason | Auto ✓ (v1) |
| E7 | Power cut / process killed in the middle of a move | On restart: no file lost, no half file, nothing filed twice | VM |
| E8 | Batch PDF where filing part 2 of 3 fails | Original goes to review with "part 1 already filed"; nothing filed twice | Auto |

## F. Background task

| ID | Case | Expected | How |
|---|---|---|---|
| F1 | Server reboots | Task starts by itself, nobody logged in | VM |
| F3 | `BHP Scanner` process killed | Task Scheduler restarts it within 1 minute | VM |
| F4 | Inbox or output folder unreachable | `!! BHP SCANNER STOPPED` note in the review folder; files wait | VM |
| F4b | Problem fixed after F4 | Note removed, waiting files processed | VM |
| F6 | No internet at all | Everything works | VM |
| F9 | Runs 7 days non-stop | No memory growth, log files rotate | VM (trial) |

## G. Installer

| ID | Case | Expected | How |
|---|---|---|---|
| G1 | Fresh install on a clean VM with the server's Windows version, and Windows 11 | Installs, task running, self-test "Ready ✓" | VM |
| G2 | Install without admin rights | Asks for admin (UAC) | VM |
| G3 | Inbox or output folder doesn't exist / isn't writable | Wizard says so, offers to create it | VM |
| G5 | Upgrade v2.0 → v2.1 while the tool is running | Task stopped first, no "file in use" error; settings, customers and log kept; task restarted | VM |
| G6 | Uninstall | Program + task removed; asks about data (default keep); filed documents untouched | VM |
| G7 | Reinstall after uninstall with data kept | Picks up the old settings and customers | VM |
| G8 | Install to a non-default drive (D:\Apps) | Works | VM |
| G9 | Start-menu shortcuts (review folder, log, settings) | All work | Manual |
| G10 | Windows Defender / SmartScreen | No virus warning; SmartScreen shows only the expected "Run anyway" (unsigned) or the publisher name (signed) | VM |

## H. Speed and accuracy on real scans

| ID | Measure | Target |
|---|---|---|
| H1 | Wrong filings | **0** |
| H2 | Pages filed automatically | ≥ 95% (clean scans of the fixed layout) |
| H3 | Seconds per page on the real server | ≤ 10 s |
| H4 | 50-page batch end to end | ≤ 10 minutes |

**Note:** 0 wrong filings out of 50 still allows a real error rate of up to about 6%. That's why the 1-week trial is part of sign-off.
