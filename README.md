# BHP Scanner

Watches the folder your scanner saves to. Each BHPetrol **Product Delivery Note** in a scan is read offline (OCR, no internet, no AI model), split into its own PDF and filed:

```
D:\Delivery Notes\2025\01 January 2025\Klang Bahagia Trading\2025-01-08 2201328377.pdf
```

Anything unclear goes to `_Needs Review` with a `.txt` note saying why. Nothing is ever overwritten.

## Install (Windows 10/11 or Server 2016+)

1. Run `BHP-Scanner-Setup-2.0.0.exe` as Administrator. Without code signing, Windows may show "Windows protected your PC". Click **More info → Run anyway**.
2. Choose the **scanner inbox** folder and the **filed delivery notes** folder.
3. Done. The installer checks the folders and the OCR engine, then starts BHP Scanner in the background. It starts with Windows, restarts itself if it stops, and needs nobody logged in.

- **Upgrade:** run the newer Setup.exe. Settings, the customer list and the log are kept.
- **Uninstall:** Windows Settings → Apps → BHP Scanner. Filed documents are never touched.

## Daily use

| You want to… | Do this |
|---|---|
| See what was filed | Start menu → BHP Scanner → **Filing log (Excel)** |
| Handle unclear scans | Start menu → **Open review folder**. Read the `.txt` note, move the PDF to the right folder, delete the note. |
| Notice if it stopped | A file `!! BHP SCANNER STOPPED - read me.txt` appears in the review folder. It disappears by itself when the problem is fixed. |
| Change settings | Start menu → **Settings**, save, then restart the server (or the "BHP Scanner" task) |

## What it reads

| Field | From the printed note |
|---|---|
| DN number | `Delivery Note : 2201328377` |
| Date | `Delivery Date : 08.01.2025` (always day.month.year) |
| Customer | first line under `Delivery Information:` |
| Customer reg. no. | the 12-digit number under the name |
| Pages | `Page : 1 / 2` + `2 / 2` → one 2-page file |

**Customers are matched by reg. no.**, so a small OCR slip in a name still lands in the right folder. Companies with similar names but different reg. nos. get separate folders. `C:\ProgramData\BHP Scanner\data\customers.json` keeps the reg. no. → folder list. If you rename a customer folder, change its name there too.

**Goes to review:** a missing or hard-to-read field, an impossible date or one more than 7 days in the future, a missing page of a multi-page note, a page that isn't a delivery note, or a new reg. no. with the same name as an existing customer.

Exact duplicate scans go to `_Duplicates`. A reprint of a note that's already filed is saved next to it as `… (2).pdf`.

## Files on the server

```
C:\Program Files\BHP Scanner\        program (about 230 MB, OCR models included)
C:\ProgramData\BHP Scanner\
    config.yaml                       settings (all options: config.example.yaml)
    data\log.csv                      one row per filed or reviewed note
    data\customers.json               reg. no. → customer folder
    data\dnfiler.log                  technical log
```

## For developers

```
python -m venv .venv && .venv/bin/pip install -r requirements.txt pytest reportlab
.venv/bin/python -m pytest                                   # 32 tests; the golden one needs tests/golden/ (local only, real customer data)
.venv/bin/python -m dnfiler --config my-config.yaml check scan.pdf   # what would be read, moves nothing
```

**Building the installer:** push to GitHub. `.github/workflows/build-windows.yml` runs the tests, builds `BHP Scanner.exe` with PyInstaller, smoke-tests it, and makes `BHP-Scanner-Setup-<version>.exe` with Inno Setup (download it from the run's Artifacts). The version comes from `dnfiler/__init__.py`.

**Code:**
- `bhp_reader.py`: OCR and layout rules
- `processor.py`: decides where each note goes and moves it
- `customers.py`: reg.-no. matching
- `watcher.py`: watches the inbox and writes the STOPPED note
- `extractor.py`: Claude engine for other layouts (`engine: claude`)
- `installer/bhp-scanner.iss`: the installer
- `windows/register-task.ps1`: registers the background task
