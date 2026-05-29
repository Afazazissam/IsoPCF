# PyInstaller Notes

Phase 1 is structured so the app can be packaged as a single executable later.

## Suggested Command

```powershell
cd iso_to_pcf_phase1
pyinstaller --name IsoToPcfPhase1 --onefile --windowed --add-data "resources/styles.qss;resources" main.py
```

## Runtime Dependencies

- PySide6
- PyMuPDF
- matplotlib

## Notes

- Keep `main.py` as the application entry point.
- Keep resources under `resources/` and include them with `--add-data`.
- Project JSON files are user data and should not be bundled into the executable.
