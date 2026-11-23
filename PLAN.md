# BHP Scanner: Delivery Note Auto-Filing Tool (Plan)

## What it does

```
Printer/Scanner ──► \\Scans\Inbox (watched folder)
                          │
                          ▼
                 1. Wait until the file is fully written
                 2. Read text (PDF text layer, or OCR if it's an image)
                 3. Pull out: DN date, customer name, DN number
                 4. Match the customer name against a customer list
                          │
            ┌─────────────┴──────────────┐
       confident                      not sure
            ▼                             ▼
  \\Filed\2027\01 January 2027\     \\Filed\_Needs Review\
      Customer A\DN-12345_2027-01-15.pdf   (+ a note saying why)
```

Folder layout: `<Root>\<Year>\<MM Month Year>\<Customer>\<file>`.
The number in front of the month (`01 January 2027`) keeps the months in order in Windows Explorer. Without it they sort A to Z (April, August, …).

## Parts

| # | Part | What it does | Tool |
|---|------|--------------|------|
| 1 | **Watcher** | Checks the inbox every N seconds and picks up new PDF/JPG/TIFF files. Waits until the file size stops changing and the file isn't locked, because printers write files slowly. | Python `watchdog` + a polling fallback (network shares don't always send events) |
| 2 | **Text reader** | If the PDF already has text, read it directly. If it's only an image, turn the page into an image and OCR it. Fix tilted scans first. | `pypdfium2` / `pdfplumber`, then **Tesseract** (free, runs on the machine) |
| 3 | **Field extractor** | Finds the date, customer, and DN number. Uses label rules first ("Date:", "Deliver To:", "DN No:"), and can handle several date formats (15/01/2027, 15-Jan-27, …). | Rules + `dateparser` |
| 4 | **Customer matcher** | Turns "ABC TRADING SDN. BHD." and "Abc Trading Sdn Bhd" into one folder name using a customer list (CSV). Close-but-not-exact spellings get matched with a confidence score. | `rapidfuzz` |
| 5 | **Filer** | Creates the folders and moves and renames the file. Never overwrites: duplicates get `_2`. Keeps the original file name in the log. | Python `pathlib` / `shutil` |
| 6 | **Review queue** | Anything unclear (no date found, customer match below the threshold, OCR came back empty) goes to `_Needs Review` with a `.txt` note explaining why. | Same as the filer |
| 7 | **Log** | One CSV row per file: time, source file, date found, customer found, confidence, where it went. Lets you search and check later. | CSV + a rotating text log |
| 8 | **Runs in the background** | Starts when Windows starts and runs without anyone logged in. Restarts if it crashes. | Windows Service via **NSSM** (or Task Scheduler "at startup") |
| 9 | **Installer** | One `.exe` plus `config.yaml`. No Python install needed on the server. | PyInstaller + Tesseract bundled |

### Config (`config.yaml`)
```yaml
inbox: "\\\\SERVER\\Scans\\Inbox"
output_root: "\\\\SERVER\\DeliveryNotes"
review_folder: "\\\\SERVER\\DeliveryNotes\\_Needs Review"
poll_seconds: 10
month_folder_format: "{MM} {MonthName} {YYYY}"   # 01 January 2027
file_name_format: "{dn_no}_{date:%Y-%m-%d}"
customer_list: "customers.csv"
match_threshold: 85
date_formats: ["%d/%m/%Y", "%d-%b-%y", "%d.%m.%Y"]   # day before month
```

## The main choice: how to read the fields

| Option | Good | Bad |
|--------|------|-----|
| **A. Tesseract + rules** (recommended to start) | Free, works offline, the documents never leave the server | Needs rules written for each delivery note layout. Breaks if a layout changes |
| **B. AI vision model (e.g. Claude) reading the page image** | Works on any layout, poor scans, handwriting | Needs internet, costs a little per page, documents are sent to a cloud service |
| **C. A then B** | Use rules first and only send the page to AI when the rules aren't sure | Two pieces to look after |

**Recommendation:** If all the delivery notes are your own company's printed template (one layout), use **A**. It will be close to 100% correct. If they come from many suppliers with different layouts, go with **C**.

## Build steps

1. **Samples:** collect 10 to 20 real scanned delivery notes, including bad ones (tilted, faint, several pages). Write down the correct date and customer for each. This is the test set.
2. **Reader + extractor:** run them on the samples until 95% or more are correct. Anything wrong should end up in review, never in the wrong folder.
3. **Customer list + matcher:** build `customers.csv` from your ERP/accounting customer list.
4. **Filer + review queue + log:** test on a copy of the folders.
5. **Watcher + Windows Service:** run it on the server and drop files in the inbox.
6. **Package:** `.exe` + install script + one-page "how to" guide.
7. **Trial run (1 week):** run it alongside the current manual filing, compare the results, then switch over.

## Edge cases already handled in the design
- A file is still being written when it's found → wait until it stops changing.
- One PDF holds several delivery notes (batch scan) → *needs your decision*: split by page, or file the whole thing as one.
- The same file is scanned twice → add `_2`, plus an optional hash check to skip exact copies.
- Characters Windows doesn't allow in folder names (`/ \ : * ? " < > |`) or names that are too long → remove them.
- Network share is down → retry, and the file stays in the inbox (nothing lost).
- Day/month mix-up (01/02/2027) → the date order is set in the config, and a date in the future goes to review.

## Decisions (from your answers, 23 Nov 2026)
| Question | Answer | What it means for the build |
|---|---|---|
| Layouts | Many | **Option B**: Claude reads each PDF directly. No Tesseract, no per-layout rules. |
| Internet | Yes | Calls the Claude API. Needs an API key on the server. |
| File type | PDF | Claude reads the PDF as-is (text layer and page images). |
| Batches | Not answered | Handled anyway: Claude says which pages belong to which delivery note, and batch PDFs are split. |
| Folders | Local | Watches the folder every 10 seconds. |
| Customer list | None | The tool **builds its own list** (`customers.json`) as it files. A new name that is *almost* the same as a known one goes to review, so it can't create near-duplicate folders. |
| Folder name | Yes | `2027\01 January 2027\Customer A\` |
| Runs as | | Windows Task Scheduler task: starts at boot, runs without login, restarts on crash. No extra tools to install. |
