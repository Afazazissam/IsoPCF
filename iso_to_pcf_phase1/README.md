# AI-Assisted Isometric-to-PCF Generator - Phase 1

Phase 1 is a manual engineering reconstruction tool for selectable-text isometric PDFs. It stores clicked geometry in PDF-native coordinates and builds structured data for future PCF generation.

## Run

```powershell
cd iso_to_pcf_phase1
python -m pip install -r requirements.txt
python main.py
```

## Current Phase 1 Features

- Open, render, zoom, pan, fit, and navigate PDF pages with PyMuPDF.
- Track mouse position in PDF-native coordinates.
- Extract nearby selectable PDF text using PyMuPDF text extraction.
- Add nodes, pipe segments, elbows, tees, supports, dimension constraints, and coordinate/elevation tags.
- Choose the active reconstruction tool from the PDF viewer right-click menu.
- Draw PDF overlays from stored PDF coordinates.
- Save and load reconstruction projects as JSON.

## Data Model

The project JSON stores engineering reconstruction entities, not generic image labels:

- Nodes are topology/reference points.
- Pipe segments connect nodes.
- Elbows, tees, supports, dimensions, and coordinate tags reference nodes or segments.
- Every manual entity includes verification metadata and timestamps where applicable.

## Packaging Notes

See `build/pyinstaller_notes.md` for PyInstaller guidance.
