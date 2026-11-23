# BHP Scanner v2: Local OCR + Windows Installer (Plan)

**Goal:** one small `BHP-Scanner-Setup.exe`. Someone double-clicks it on the Windows server, picks the folders, clicks Next, and it's running. No Python, no command line, no internet, no AI model. The v1 filing logic (Year / Month / Customer folders, review folder, duplicates, log) stays as it is.

**What changed (23 Nov 2026):** the sample scan shows every delivery note uses the **same BHPetrol "PRODUCT DELIVERY NOTE" layout**. So the fields can be read with fixed rules. The AI models from the research (Qwen, llama-server, a 2.7 GB model) are **not needed**. Simpler, faster, and no model can invent values.

---

## 1. What the sample shows (`tests/golden/batch-2025-01-08.pdf`)

- 50 pages, one Konica Minolta batch scan, no text layer, so OCR is needed. **Every page is one delivery note** ("Page : 1 / 1").
- Fixed printed fields, always in the same place:

| Field | Printed as | Example |
|---|---|---|
| DN number | `Delivery Note : 2201328377` (right column) | 10 digits |
| Date | `Delivery Date : 08.01.2025` | always DD.MM.YYYY, so no day/month mix-up |
| Page | `Page : 1 / 1` | tells us when a note runs over several pages |
| Customer | first line under `Delivery Information:` | `Klang Bahagia Trading` |
| Customer reg. no. | the line under the name | `200903147325` (12 digits) |

- **Prototype result:** RapidOCR + rules read the DN number, date, customer and reg. no. on **50 / 50 pages**. 5 pages were checked by eye against the image, all correct. OCR took about 1.7 s per page on a MacBook (M1 Pro), so roughly 2–5 s per page is expected on the server.

## 2. How a scan is read

```
batch PDF ──► each page ──► RapidOCR (200 dpi) ──► rules:
     "Delivery Note" → DN number (10 digits)
     "Delivery Date" → date (DD.MM.YYYY)
     "Page"          → n / total
     under "Delivery Information:" → customer name + reg. no.
──► group pages: "Page 1/2" + "Page 2/2" with the same DN number = one file
──► v1 filing: 2025\01 January 2025\Klang Bahagia Trading\2025-01-08 2201328377.pdf
```

**Goes to `_Needs Review` (with the reason) when:**
- a field is missing or doesn't match its pattern (e.g. a cover sheet or a different document in the batch)
- the OCR confidence on a field is below 0.90
- the date is impossible or more than 7 days in the future
- the page numbers don't add up (e.g. "Page 1/2" with no page 2)
- **customer check:** the **reg. no. is the customer's ID**. The customer list maps reg. no. → folder.
  - known reg. no. → that customer's folder, even if the name has an OCR slip
  - new reg. no. and new name → new folder
  - new reg. no. but **the same name as an existing customer** → review (likely an OCR slip in the number)

This replaces v1's "similar name" check for this layout. "Iman Razhan Enterprise", "Iman Razhan Trading" and "Iman Razhan Resources" have different reg. nos., so they correctly get their own folders instead of going to review.

**Reprint copies:** "Reprint Copy" pages are filed like originals. If the original was already filed, the reprint becomes `… (2).pdf` next to it. Nothing is lost.

**Engine setting** in `config.yaml`: `engine: local` (default, the rules above) or `claude` (v1, already built, for a different layout later).

## 3. What gets installed (about 150 MB)

```
C:\Program Files\BHP Scanner\     ← the app (PyInstaller one-folder build: Python + RapidOCR models inside)
C:\ProgramData\BHP Scanner\       ← config.yaml + data\ (customers.json, log.csv, logs) — kept on upgrade/uninstall
```

- **Runs in the background** as the "BHP Scanner" scheduled task (v1): starts at boot, restarts on crash, runs with nobody logged in. The task passes `--config "C:\ProgramData\BHP Scanner\config.yaml"`.
- **If it stops working** (e.g. the folder becomes unreachable), it writes `!! BHP SCANNER STOPPED - read me.txt` into the review folder, and removes it when it's fixed.

## 4. Installer (Inno Setup)

1. Welcome
2. **Folders:** scanner inbox and output root. It checks they're writable and offers to create them.
3. Install → start the task → read a built-in sample page → "Ready ✓" or the exact problem

- Start-menu shortcuts: *Open review folder*, *Open log (Excel)*, *Settings*
- **Upgrade:** stops the task, replaces the program, starts it again. Data is kept.
- **Uninstall:** removes the task and the program, and asks whether to delete the settings and log (default: keep). Filed documents are never touched.

## 5. Build steps

| # | Step | Done when |
|---|---|---|
| 1 | **Golden set:** `tests/golden/expected.csv` (50 pages, made from the prototype). **You check the remaining 45 rows** against the scans. Add 1–2 more batches if you have them (bad scans, a 2-page note, a non-DN page). | Rows confirmed |
| 2 | **`dnfiler/bhp_reader.py`:** OCR + rules + page grouping, returning the same `DocumentInfo` list the Claude engine returns, so `processor.py` stays the same | Golden set 50/50, unit tests pass |
| 3 | **Reg.-no. customer matching** in `customers.py` | Tests pass |
| 4 | **"STOPPED" note** | Tests pass |
| 5 | **Package:** PyInstaller + Inno Setup, built on Windows (GitHub Actions or a Windows PC) | `BHP-Scanner-Setup.exe` |
| 6 | **Install test** on a clean VM with the server's Windows version | Installer test cases pass |
| 7 | **Trial:** 1 week alongside manual filing | Signed off |

## 6. Decisions needed

1. **Build machine:** a GitHub repo (GitHub Actions builds on Windows for free) or a Windows PC/VM I can use.
2. **Server's Windows version** (Server 2019 / 2022 / 2025, Windows 10 / 11).
3. **Customer folder name:** just the name (`Klang Bahagia Trading`) or the name + reg. no. (`Klang Bahagia Trading (200903147325)`)? Just the name is easier to read. The reg. no. is still used for matching either way.
4. **Code signing:** without a certificate, Windows shows "Run anyway" once on first install. That's fine for one server.

## 7. Left out on purpose
- AI models (Qwen, GLM-OCR, llama-server): the fixed layout makes them unnecessary. `engine: claude` remains for a different layout.
- Day/month guessing: the date is always printed DD.MM.YYYY.
- A Windows Service wrapper, a web dashboard, extra wizard pages, testing on every Windows version.
