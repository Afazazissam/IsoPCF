# Phase 1 — Interactive Isometric Reconstruction Foundation

## Project Name

**AI-Assisted Isometric-to-PCF Generator for CAESAR II**

## Core Objective

Build a professional Python desktop application that allows an engineer to open a selectable-text isometric PDF and manually retrace the piping system into structured engineering data that can later generate a valid PCF file for CAESAR II import.

This is not just a drawing annotation tool.

This is the foundation of an **Interactive Isometric Reconstruction System**.

The goal is to eventually skip the manual CadWorx 3D modeling step:

```text
Current workflow:
Isometric PDF -> Manual CadWorx 3D Model -> PCF Export -> CAESAR II

Target workflow:
Isometric PDF -> Interactive Reconstruction -> PCF Generation -> CAESAR II
```

## Phase 1 Scope

Phase 1 must build the reliable application foundation only.

Do **not** implement AI yet.
Do **not** implement PCF generation yet.
Do **not** implement OCR yet.
Do **not** implement OpenCV detection yet.

The immediate goal is to let the user manually create clean, machine-readable engineering reconstruction data from a PDF.

---

# Technology Stack

Use:

- Python 3.11+
- PySide6
- PyMuPDF / fitz
- JSON storage

The app must be modular and later compilable to a single `.exe` using PyInstaller.

---

# Phase 1 Functional Requirements

## 1. PDF Viewer

The application must allow the user to:

- Open isometric PDF drawings
- Render PDF pages smoothly
- Navigate pages
- Zoom in/out
- Pan
- Fit page to window
- Track mouse position in PDF coordinates
- Handle selectable PDF text using PyMuPDF text extraction

Only PDF input is required for now.
No image input.
No OCR.

---

## 2. Coordinate Strategy

The application must clearly separate:

```text
Screen/widget coordinates
Rendered image coordinates
PDF-native coordinates
Engineering coordinates
```

For Phase 1, all clicked points must be stored in **PDF-native coordinates**.

Do not store screen coordinates as source data.

The coordinate mapper must support future handling of:

- zoom
- pan
- page offset
- PDF rotation
- multiple pages

---

## 3. Selectable Text Extraction

Use PyMuPDF text extraction, not OCR.

When the user clicks a point, the app should be able to extract nearby selectable text using a search radius around the clicked PDF coordinate.

This is useful for:

- pipe tags
- line numbers
- dimensions
- coordinates
- elevation text
- notes

---

# Engineering Reconstruction Concept

The user is not simply labeling images.

The user is retracing engineering meaning on top of the isometric.

The app must eventually understand entities such as:

- nodes
- pipe segments
- elbows
- tees
- reducers
- flanges
- valves
- supports
- instruments
- continuation points
- dimensions
- coordinate/elevation tags
- relationships between these entities

The key idea:

```text
PDF + retraced engineering entities + dimension constraints = future PCF model
```

---

# Phase 1 Entity Types

Implement the data model so it can support these entity categories.

## Node

A node is an interaction point or engineering reference point.

Examples:

- pipe endpoint
- elbow center
- tee center
- valve center
- support location
- branch point
- continuation point
- coordinate reference point

Required fields:

```json
{
  "id": "N001",
  "type": "node",
  "node_role": "elbow_center",
  "page_number": 1,
  "pdf_x": 100.0,
  "pdf_y": 200.0,
  "drawing_file": "ISO-001.pdf",
  "nearby_text": "",
  "notes": "",
  "manual_verified": true
}
```

Suggested node roles:

```text
pipe_endpoint
elbow_center
tee_center
reducer_center
flange_center
valve_center
support_point
instrument_point
continuation_point
dimension_reference
coordinate_reference
elevation_reference
unknown
```

---

## Pipe Segment

A pipe segment connects two nodes.

Example:

```json
{
  "id": "P001",
  "type": "pipe_segment",
  "from_node": "N001",
  "to_node": "N002",
  "page_number": 1,
  "line_number": "",
  "nominal_diameter": null,
  "spec": "",
  "notes": "",
  "manual_verified": true
}
```

---

## Elbow

For standard 90-degree elbows, the user should normally identify the elbow center point.

The elbow can later be reconstructed from:

- elbow center node
- incoming pipe direction
- outgoing pipe direction
- angle
- radius type or radius value

Example:

```json
{
  "id": "E001",
  "type": "elbow",
  "center_node": "N002",
  "angle_deg": 90,
  "radius_type": "LR",
  "radius_value": null,
  "incoming_segment": "P001",
  "outgoing_segment": "P002",
  "manual_verified": true
}
```

Radius types:

```text
LR
SR
custom
unknown
```

---

## Tee

A tee must capture run and branch relationships.

Example:

```json
{
  "id": "T001",
  "type": "tee",
  "center_node": "N010",
  "run_in_segment": "P010",
  "run_out_segment": "P011",
  "branch_segment": "P012",
  "tee_type": "equal",
  "manual_verified": true
}
```

Tee types:

```text
equal
reducing
unknown
```

---

## Support

A support is located on a host pipe segment or at a node.

A support may be defined by its physical click location on the PDF and later by a dimension constraint.

Example:

```json
{
  "id": "S001",
  "type": "support",
  "support_node": "N020",
  "host_segment": "P001",
  "support_type": "unknown",
  "distance_from_node": "N001",
  "distance_value": 1500.0,
  "distance_unit": "mm",
  "manual_verified": true
}
```

---

## Dimension Constraint

Dimensions are critical.

They are not only labels. They are constraints used to solve geometry.

Example:

```json
{
  "id": "D001",
  "type": "dimension",
  "from_node": "N001",
  "to_node": "N002",
  "value": 4000.0,
  "unit": "mm",
  "dimension_kind": "linear",
  "source_text": "4000",
  "page_number": 1,
  "manual_verified": true
}
```

Dimension kinds:

```text
linear
east_west
north_south
elevation
slope
angle
unknown
```

---

## Coordinate / Elevation Tag

Example:

```json
{
  "id": "C001",
  "type": "coordinate_tag",
  "attached_node": "N001",
  "east": null,
  "north": null,
  "elevation": 12500.0,
  "source_text": "EL. +12500",
  "unit": "mm",
  "manual_verified": true
}
```

---

# Phase 1 Application Features

## Required UI

Main window must include:

- top toolbar
- PDF viewer area
- right-side reconstruction/entity panel
- status bar

Toolbar should include:

- Open PDF
- Save Project JSON
- Load Project JSON
- Previous Page
- Next Page
- Zoom In
- Zoom Out
- Fit Page
- Current tool selector

Suggested current tools:

```text
Select
Add Node
Add Pipe Segment
Add Elbow
Add Tee
Add Support
Add Dimension
Add Coordinate/Elevation Text
Pan
```

---

# Minimum Phase 1 Behavior

At minimum, the first working build must support:

1. Open PDF
2. Render PDF
3. Zoom/pan/page navigation
4. Click to create nodes
5. Select node role
6. Create pipe segment by selecting two nodes
7. Create elbow entity from selected center node
8. Create support entity on a pipe segment
9. Create dimension constraint between two nodes
10. Extract nearby selectable text
11. Save project JSON
12. Load project JSON
13. Show created entities in side panel
14. Draw visible markers on top of PDF

---

# Project Folder Structure

Use this structure:

```text
iso_to_pcf_phase1/
│
├─ main.py
├─ requirements.txt
├─ README.md
│
├─ app/
│  ├─ __init__.py
│  ├─ main_window.py
│  ├─ pdf_viewer.py
│  ├─ entity_panel.py
│  ├─ tool_panel.py
│  └─ dialogs.py
│
├─ core/
│  ├─ __init__.py
│  ├─ pdf_document.py
│  ├─ pdf_renderer.py
│  ├─ coordinate_mapper.py
│  ├─ text_extractor.py
│  ├─ reconstruction_manager.py
│  └─ id_generator.py
│
├─ models/
│  ├─ __init__.py
│  ├─ project.py
│  ├─ node.py
│  ├─ pipe_segment.py
│  ├─ elbow.py
│  ├─ tee.py
│  ├─ support.py
│  ├─ dimension.py
│  └─ coordinate_tag.py
│
├─ storage/
│  ├─ __init__.py
│  └─ json_project_store.py
│
├─ resources/
│  └─ styles.qss
│
├─ data/
│  ├─ projects/
│  └─ samples/
│
└─ build/
   └─ pyinstaller_notes.md
```

---

# JSON Project Schema

Save the entire reconstruction project as JSON.

Recommended top-level schema:

```json
{
  "project_name": "ISO-001 Reconstruction",
  "application": "AI-Assisted Isometric-to-PCF Generator",
  "phase": "1",
  "drawing_file": "ISO-001.pdf",
  "created_at": "2026-05-29T10:00:00",
  "updated_at": "2026-05-29T10:30:00",
  "units": "mm",
  "pages": [
    {
      "page_number": 1,
      "width": 841.89,
      "height": 595.28,
      "rotation": 0
    }
  ],
  "nodes": [],
  "pipe_segments": [],
  "elbows": [],
  "tees": [],
  "supports": [],
  "dimensions": [],
  "coordinate_tags": [],
  "metadata": {
    "manual_verified": true,
    "training_ready": true,
    "notes": ""
  }
}
```

---

# Rendering Requirements

Use PyMuPDF rendering:

```python
matrix = fitz.Matrix(zoom, zoom)
pix = page.get_pixmap(matrix=matrix, alpha=False)
```

Convert pixmap to `QImage` and then to `QPixmap` for painting in PySide6.

Do not render using screenshots.
Do not rasterize the PDF outside PyMuPDF.

---

# Overlay Drawing Requirements

The PDF viewer must draw overlays after drawing the PDF pixmap.

Overlay items:

- node marker circles
- node IDs
- pipe segment lines
- elbow markers
- support markers
- dimension lines

Overlay geometry must be drawn by converting PDF coordinates back to widget coordinates.

---

# Saving and Loading

The user must be able to save the reconstruction project to JSON and reload it.

When loading:

- restore nodes
- restore pipe segments
- restore elbows
- restore supports
- restore dimensions
- restore coordinate tags
- redraw overlays
- repopulate side panel

---

# AI Training Consideration

Every manual action should create training-quality data.

For each entity, save:

- entity type
- PDF page number
- PDF coordinates
- drawing file
- timestamp
- nearby selectable text when available
- manual_verified = true
- notes when available

Do not train AI in Phase 1.

But design the data so future AI can learn from it.

---

# Development Priorities

Build in this order:

## Step 1
Create project structure and empty modules.

## Step 2
Implement PDF open/render/zoom/pan/page navigation.

## Step 3
Implement coordinate conversion.

## Step 4
Implement selectable nearby text extraction.

## Step 5
Implement Node creation and visible node markers.

## Step 6
Implement side entity panel.

## Step 7
Implement pipe segment creation between two selected nodes.

## Step 8
Implement elbow/support/dimension entity creation.

## Step 9
Implement JSON save/load.

## Step 10
Polish UI and prepare for PyInstaller.

---

# Acceptance Tests

Phase 1 is valid only if:

- App starts without errors
- PDF opens correctly
- Zoom works
- Pan works
- Fit works
- Page navigation works
- Mouse PDF coordinates are correct
- User can create nodes
- User can create pipe segments
- User can create elbow entities
- User can create support entities
- User can create dimension constraints
- Nearby selectable text is extracted
- Visible overlays appear correctly
- Project JSON saves correctly
- Project JSON loads correctly
- Data is clear enough for future PCF generation

---

# Important Design Rule

Do not make this a generic image-labeling tool.

The application must be built as an engineering reconstruction tool.

Every feature should move toward this final pipeline:

```text
Isometric PDF
  -> manually reconstructed topology graph
  -> dimension constraint solver
  -> PCF generation
  -> CAESAR II import
```

