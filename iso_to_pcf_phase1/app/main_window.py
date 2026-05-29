from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QAction, QIntValidator
from PySide6.QtWidgets import (
    QDialog,
    QFileDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSplitter,
    QToolBar,
)

from app.dialogs import (
    CoordinateTagDialog,
    DimensionDialog,
    ElbowDialog,
    NodeDialog,
    PipeSegmentDialog,
    SupportDialog,
    TeeDialog,
)
from app.entity_panel import EntityPanel
from app.pdf_viewer import PdfViewer
from app.tool_panel import (
    TOOL_ADD_COORDINATE_TAG,
    TOOL_ADD_DIMENSION,
    TOOL_ADD_ELBOW,
    TOOL_ADD_NODE,
    TOOL_ADD_PIPE_SEGMENT,
    TOOL_ADD_SUPPORT,
    TOOL_ADD_TEE,
    TOOL_PAN,
    TOOL_SELECT,
    TOOLS,
)
from core.pdf_document import PdfDocument
from core.reconstruction_manager import ReconstructionManager
from models.project import Project
from storage.json_project_store import JsonProjectStore


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("AI-Assisted Isometric-to-PCF Generator - Phase 1")
        self.resize(1400, 900)

        self.pdf_document = PdfDocument()
        self.manager = ReconstructionManager()
        self.store = JsonProjectStore()
        self.current_project_path: Path | None = None
        self.current_tool = TOOL_SELECT
        self.current_page_count = 0
        self.pending_segment_node_id: str | None = None
        self.pending_dimension_node_id: str | None = None

        self.viewer = PdfViewer()
        self.viewer.set_reconstruction_manager(self.manager)
        self.entity_panel = EntityPanel()
        self.entity_panel.set_project(self.manager.project)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(self.viewer)
        splitter.addWidget(self.entity_panel)
        splitter.setSizes([1040, 360])
        self.setCentralWidget(splitter)

        self._build_toolbar()
        self._connect_signals()
        self._update_status_text()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        toolbar.setMovable(False)
        self.addToolBar(toolbar)

        self.open_pdf_action = QAction("Open PDF", self)
        self.save_project_action = QAction("Save Project JSON", self)
        self.load_project_action = QAction("Load Project JSON", self)
        self.previous_page_action = QAction("Previous Page", self)
        self.next_page_action = QAction("Next Page", self)
        self.zoom_in_action = QAction("Zoom In", self)
        self.zoom_out_action = QAction("Zoom Out", self)
        self.fit_page_action = QAction("Fit Page", self)

        toolbar.addAction(self.open_pdf_action)
        toolbar.addAction(self.save_project_action)
        toolbar.addAction(self.load_project_action)
        toolbar.addSeparator()
        toolbar.addAction(self.previous_page_action)
        toolbar.addWidget(QLabel("Page"))

        self.page_number_input = QLineEdit()
        self.page_number_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.page_number_input.setFixedWidth(58)
        self.page_number_input.setValidator(QIntValidator(1, 999999, self))
        toolbar.addWidget(self.page_number_input)

        self.page_count_label = QLabel("/ 0")
        self.page_count_label.setMinimumWidth(48)
        toolbar.addWidget(self.page_count_label)
        toolbar.addAction(self.next_page_action)

        toolbar.addSeparator()
        toolbar.addAction(self.zoom_in_action)
        toolbar.addAction(self.zoom_out_action)
        toolbar.addAction(self.fit_page_action)

        toolbar.addSeparator()
        self.current_tool_label = QLabel()
        self.current_tool_label.setMinimumWidth(220)
        toolbar.addWidget(self.current_tool_label)
        self._sync_tool_label()
        self._sync_page_controls(0, 0)

    def _connect_signals(self) -> None:
        self.open_pdf_action.triggered.connect(self.open_pdf)
        self.save_project_action.triggered.connect(self.save_project)
        self.load_project_action.triggered.connect(self.load_project)
        self.previous_page_action.triggered.connect(self.viewer.previous_page)
        self.next_page_action.triggered.connect(self.viewer.next_page)
        self.zoom_in_action.triggered.connect(self.viewer.zoom_in)
        self.zoom_out_action.triggered.connect(self.viewer.zoom_out)
        self.fit_page_action.triggered.connect(self.viewer.fit_page)
        self.page_number_input.returnPressed.connect(self._jump_to_typed_page)

        self.viewer.mouse_pdf_position_changed.connect(self._mouse_moved_on_pdf)
        self.viewer.pdf_clicked.connect(self._pdf_clicked)
        self.viewer.page_changed.connect(self._page_changed)
        self.viewer.tool_menu_requested.connect(self._show_tool_menu)

    def open_pdf(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Open isometric PDF",
            str(Path.cwd()),
            "PDF Files (*.pdf)",
        )
        if not path:
            return
        self._open_pdf_as_new_project(Path(path))

    def save_project(self) -> None:
        if self.pdf_document.path is not None:
            self.manager.project.metadata["source_pdf_path"] = str(self.pdf_document.path)
            self.manager.project.pages = self.pdf_document.page_infos()

        target = self.current_project_path
        if target is None:
            default_path = self._default_project_path()
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Save reconstruction project",
                str(default_path),
                "JSON Files (*.json)",
            )
            if not path:
                return
            target = Path(path)

        try:
            self.store.save(self.manager.project, target)
        except Exception as exc:
            self._show_error("Save failed", str(exc))
            return

        self.current_project_path = target
        self.statusBar().showMessage(f"Saved project JSON: {target}", 6000)
        self._refresh_entities()

    def load_project(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Load reconstruction project",
            str(Path.cwd()),
            "JSON Files (*.json)",
        )
        if not path:
            return

        project_path = Path(path)
        try:
            project = self.store.load(project_path)
        except Exception as exc:
            self._show_error("Load failed", str(exc))
            return

        self.manager.set_project(project)
        self.current_project_path = project_path

        pdf_path = self._resolve_pdf_path(project, project_path)
        if pdf_path is not None:
            try:
                self.pdf_document.open(pdf_path)
                if not project.pages:
                    project.pages = self.pdf_document.page_infos()
                project.metadata["source_pdf_path"] = str(pdf_path)
                self.viewer.set_document(self.pdf_document)
            except Exception as exc:
                self._show_error("PDF load failed", str(exc))
                self.pdf_document.close()
                self.viewer.clear_document()
                self._sync_page_controls(0, 0)
        else:
            self.pdf_document.close()
            self.viewer.clear_document()
            self._sync_page_controls(0, 0)

        self._clear_pending()
        self._refresh_entities()
        self.statusBar().showMessage(f"Loaded project JSON: {project_path}", 6000)

    def _open_pdf_as_new_project(self, pdf_path: Path) -> None:
        try:
            self.pdf_document.open(pdf_path)
        except Exception as exc:
            self._show_error("PDF open failed", str(exc))
            return

        self.manager.new_project_for_pdf(pdf_path, self.pdf_document.page_infos())
        self.current_project_path = None
        self.viewer.set_document(self.pdf_document)
        self._clear_pending()
        self._refresh_entities()
        self.statusBar().showMessage(f"Opened PDF: {pdf_path}", 6000)

    def _resolve_pdf_path(self, project: Project, project_path: Path) -> Path | None:
        candidates: list[Path] = []
        source_path = project.metadata.get("source_pdf_path")
        if source_path:
            candidates.append(Path(source_path))
        if project.drawing_file:
            candidates.append(project_path.parent / project.drawing_file)
            candidates.append(Path.cwd() / project.drawing_file)

        for candidate in candidates:
            if candidate.exists():
                return candidate

        if project.drawing_file:
            path, _ = QFileDialog.getOpenFileName(
                self,
                f"Locate {project.drawing_file}",
                str(project_path.parent),
                "PDF Files (*.pdf)",
            )
            if path:
                return Path(path)
        return None

    def _tool_changed(self, tool_name: str) -> None:
        self.current_tool = tool_name
        self.viewer.set_tool(tool_name)
        self._clear_pending()
        self._sync_tool_label()
        self._update_status_text()

    def _show_tool_menu(self, global_pos: QPoint) -> None:
        menu = QMenu(self)
        for tool_name in TOOLS:
            action = QAction(tool_name, menu)
            action.setCheckable(True)
            action.setChecked(tool_name == self.current_tool)
            action.triggered.connect(
                lambda checked=False, selected_tool=tool_name: self._tool_changed(selected_tool)
            )
            menu.addAction(action)
        menu.exec(global_pos)

    def _mouse_moved_on_pdf(self, page_number: int, pdf_x: float, pdf_y: float) -> None:
        self.statusBar().showMessage(
            f"Page {page_number} | PDF x={pdf_x:.2f}, y={pdf_y:.2f} | Tool: {self.current_tool}"
        )

    def _page_changed(self, page_number: int, page_count: int) -> None:
        self._sync_page_controls(page_number, page_count)
        self.statusBar().showMessage(
            f"Page {page_number} of {page_count} | Tool: {self.current_tool}",
            4000,
        )

    def _jump_to_typed_page(self) -> None:
        if not self.pdf_document.is_open or self.current_page_count <= 0:
            return

        requested_text = self.page_number_input.text().strip()
        if not requested_text:
            self._sync_page_controls(self.viewer.current_page_number(), self.current_page_count)
            return

        requested_page = int(requested_text)
        page_number = max(1, min(requested_page, self.current_page_count))
        if page_number != requested_page:
            self.statusBar().showMessage(
                f"Page {requested_page} is outside this PDF. Jumped to page {page_number}.",
                5000,
            )

        self.viewer.set_current_page(page_number - 1)
        self.page_number_input.selectAll()

    def _pdf_clicked(self, page_number: int, pdf_x: float, pdf_y: float, nearby_text: str) -> None:
        tool = self.current_tool
        if tool == TOOL_SELECT:
            self._handle_select(page_number, pdf_x, pdf_y)
        elif tool == TOOL_ADD_NODE:
            self._handle_add_node(page_number, pdf_x, pdf_y, nearby_text)
        elif tool == TOOL_ADD_PIPE_SEGMENT:
            self._handle_add_pipe_segment(page_number, pdf_x, pdf_y)
        elif tool == TOOL_ADD_ELBOW:
            self._handle_add_elbow(page_number, pdf_x, pdf_y)
        elif tool == TOOL_ADD_TEE:
            self._handle_add_tee(page_number, pdf_x, pdf_y)
        elif tool == TOOL_ADD_SUPPORT:
            self._handle_add_support(page_number, pdf_x, pdf_y, nearby_text)
        elif tool == TOOL_ADD_DIMENSION:
            self._handle_add_dimension(page_number, pdf_x, pdf_y, nearby_text)
        elif tool == TOOL_ADD_COORDINATE_TAG:
            self._handle_add_coordinate_tag(page_number, pdf_x, pdf_y, nearby_text)
        elif tool == TOOL_PAN:
            return

    def _handle_select(self, page_number: int, pdf_x: float, pdf_y: float) -> None:
        node = self.manager.find_nearest_node(
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            tolerance=self.viewer.pick_tolerance_pdf(),
        )
        if node:
            self.entity_panel.select_entity("nodes", node.id)
            self.viewer.set_highlights(node_ids={node.id})
            return

        segment = self.manager.find_nearest_segment(
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            tolerance=self.viewer.pick_tolerance_pdf() * 1.5,
        )
        if segment:
            self.entity_panel.select_entity("pipe_segments", segment.id)
            self.viewer.set_highlights(segment_ids={segment.id})
            return

        self.viewer.set_highlights()

    def _handle_add_node(
        self,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        nearby_text: str,
    ) -> None:
        dialog = NodeDialog(nearby_text, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        node = self.manager.add_node(
            node_role=str(values["node_role"]),
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            nearby_text=str(values["nearby_text"]),
            notes=str(values["notes"]),
        )
        self._refresh_and_select("nodes", node.id, node_ids={node.id})
        self.statusBar().showMessage(f"Created node {node.id}", 5000)

    def _handle_add_pipe_segment(self, page_number: int, pdf_x: float, pdf_y: float) -> None:
        node = self._nearest_node_or_status(page_number, pdf_x, pdf_y)
        if node is None:
            return

        if self.pending_segment_node_id is None:
            self.pending_segment_node_id = node.id
            self.viewer.set_highlights(node_ids={node.id})
            self.statusBar().showMessage(f"Pipe segment start: {node.id}. Select the end node.", 6000)
            return

        start_node = self.manager.get_node(self.pending_segment_node_id)
        if start_node is None:
            self.pending_segment_node_id = None
            return
        if start_node.id == node.id:
            self.statusBar().showMessage("Select a different end node for the pipe segment.", 5000)
            return
        if start_node.page_number != node.page_number:
            self.statusBar().showMessage("Pipe segments must stay on one PDF page in Phase 1.", 5000)
            return

        dialog = PipeSegmentDialog(self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        segment = self.manager.add_pipe_segment(
            from_node=start_node.id,
            to_node=node.id,
            line_number=str(values["line_number"]),
            nominal_diameter=values["nominal_diameter"],
            spec=str(values["spec"]),
            notes=str(values["notes"]),
        )
        self.pending_segment_node_id = None
        self._refresh_and_select(
            "pipe_segments",
            segment.id,
            node_ids={start_node.id, node.id},
            segment_ids={segment.id},
        )
        self.statusBar().showMessage(f"Created pipe segment {segment.id}", 5000)

    def _handle_add_elbow(self, page_number: int, pdf_x: float, pdf_y: float) -> None:
        node = self._nearest_node_or_status(page_number, pdf_x, pdf_y)
        if node is None:
            return
        connected = [segment.id for segment in self.manager.segments_for_node(node.id)]
        defaults = connected + ["", ""]
        dialog = ElbowDialog(defaults[0], defaults[1], self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        elbow = self.manager.add_elbow(center_node=node.id, **values)
        self._refresh_and_select("elbows", elbow.id, node_ids={node.id})
        self.statusBar().showMessage(f"Created elbow {elbow.id}", 5000)

    def _handle_add_tee(self, page_number: int, pdf_x: float, pdf_y: float) -> None:
        node = self._nearest_node_or_status(page_number, pdf_x, pdf_y)
        if node is None:
            return
        connected = [segment.id for segment in self.manager.segments_for_node(node.id)]
        dialog = TeeDialog(connected, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        tee = self.manager.add_tee(center_node=node.id, **values)
        self._refresh_and_select("tees", tee.id, node_ids={node.id})
        self.statusBar().showMessage(f"Created tee {tee.id}", 5000)

    def _handle_add_support(
        self,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        nearby_text: str,
    ) -> None:
        segment = self.manager.find_nearest_segment(
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            tolerance=self.viewer.pick_tolerance_pdf() * 1.8,
        )
        if segment is None:
            self.statusBar().showMessage("Click near a pipe segment to place a support.", 5000)
            return

        dialog = SupportDialog(segment.id, [segment.from_node, segment.to_node], self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        node = self.manager.add_node(
            node_role="support_point",
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            nearby_text=nearby_text,
        )
        support = self.manager.add_support(
            support_node=node.id,
            host_segment=segment.id,
            support_type=str(values["support_type"]),
            distance_from_node=str(values["distance_from_node"]),
            distance_value=values["distance_value"],
            distance_unit=str(values["distance_unit"]),
            notes=str(values["notes"]),
        )
        self._refresh_and_select(
            "supports",
            support.id,
            node_ids={node.id},
            segment_ids={segment.id},
        )
        self.statusBar().showMessage(f"Created support {support.id}", 5000)

    def _handle_add_dimension(
        self,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        nearby_text: str,
    ) -> None:
        node = self._nearest_node_or_status(page_number, pdf_x, pdf_y)
        if node is None:
            return

        if self.pending_dimension_node_id is None:
            self.pending_dimension_node_id = node.id
            self.viewer.set_highlights(node_ids={node.id})
            self.statusBar().showMessage(f"Dimension start: {node.id}. Select the end node.", 6000)
            return

        start_node = self.manager.get_node(self.pending_dimension_node_id)
        if start_node is None:
            self.pending_dimension_node_id = None
            return
        if start_node.id == node.id:
            self.statusBar().showMessage("Select a different end node for the dimension.", 5000)
            return

        dialog = DimensionDialog(nearby_text, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        dimension = self.manager.add_dimension(
            from_node=start_node.id,
            to_node=node.id,
            value=values["value"],
            unit=str(values["unit"]),
            dimension_kind=str(values["dimension_kind"]),
            source_text=str(values["source_text"]),
            page_number=page_number,
            notes=str(values["notes"]),
        )
        self.pending_dimension_node_id = None
        self._refresh_and_select(
            "dimensions",
            dimension.id,
            node_ids={start_node.id, node.id},
        )
        self.statusBar().showMessage(f"Created dimension {dimension.id}", 5000)

    def _handle_add_coordinate_tag(
        self,
        page_number: int,
        pdf_x: float,
        pdf_y: float,
        nearby_text: str,
    ) -> None:
        node = self.manager.find_nearest_node(
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            tolerance=self.viewer.pick_tolerance_pdf() * 2.0,
        )
        dialog = CoordinateTagDialog(nearby_text, self)
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        values = dialog.values()
        if node is None:
            node = self.manager.add_node(
                node_role="coordinate_reference",
                page_number=page_number,
                pdf_x=pdf_x,
                pdf_y=pdf_y,
                nearby_text=nearby_text,
            )
        tag = self.manager.add_coordinate_tag(
            attached_node=node.id,
            east=values["east"],
            north=values["north"],
            elevation=values["elevation"],
            source_text=str(values["source_text"]),
            unit=str(values["unit"]),
            notes=str(values["notes"]),
        )
        self._refresh_and_select("coordinate_tags", tag.id, node_ids={node.id})
        self.statusBar().showMessage(f"Created coordinate tag {tag.id}", 5000)

    def _nearest_node_or_status(self, page_number: int, pdf_x: float, pdf_y: float):
        node = self.manager.find_nearest_node(
            page_number=page_number,
            pdf_x=pdf_x,
            pdf_y=pdf_y,
            tolerance=self.viewer.pick_tolerance_pdf() * 1.5,
        )
        if node is None:
            self.statusBar().showMessage("Click near an existing node for this tool.", 5000)
        return node

    def _refresh_entities(self) -> None:
        self.entity_panel.set_project(self.manager.project)
        self.viewer.update()

    def _refresh_and_select(
        self,
        collection_name: str,
        entity_id: str,
        node_ids: set[str] | None = None,
        segment_ids: set[str] | None = None,
    ) -> None:
        self._refresh_entities()
        self.entity_panel.select_entity(collection_name, entity_id)
        self.viewer.set_highlights(node_ids=node_ids, segment_ids=segment_ids)

    def _clear_pending(self) -> None:
        self.pending_segment_node_id = None
        self.pending_dimension_node_id = None
        self.viewer.set_highlights()

    def _default_project_path(self) -> Path:
        base_dir = Path(__file__).resolve().parents[1] / "data" / "projects"
        name = self.manager.project.project_name or "Untitled Reconstruction"
        safe_name = "".join(char if char.isalnum() or char in "-_" else "_" for char in name)
        return base_dir / f"{safe_name}.json"

    def _update_status_text(self) -> None:
        self.statusBar().showMessage(f"Tool: {self.current_tool}")

    def _sync_tool_label(self) -> None:
        self.current_tool_label.setText(f"Tool: {self.current_tool}")

    def _sync_page_controls(self, page_number: int, page_count: int) -> None:
        self.current_page_count = page_count
        has_pages = page_count > 0

        self.page_number_input.setEnabled(has_pages)
        self.previous_page_action.setEnabled(has_pages and page_number > 1)
        self.next_page_action.setEnabled(has_pages and page_number < page_count)

        self.page_number_input.blockSignals(True)
        self.page_number_input.setText(str(page_number) if has_pages else "")
        self.page_number_input.blockSignals(False)
        self.page_count_label.setText(f"/ {page_count}" if has_pages else "/ 0")

    def _show_error(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)
