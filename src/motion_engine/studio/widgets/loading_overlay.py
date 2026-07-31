"""Premium loading overlay — dimmed backdrop + floating stage card."""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from motion_engine.studio.theme.wordmark import (
    WORDMARK_WEIGHT_UI,
    apply_wordmark_label,
)

# Cap displayed progress until the job truly finishes — never idle at 100%.
_DISPLAY_CAP = 98

_DATASET_STAGES: tuple[tuple[int, str], ...] = (
    (8, "Reading dataset…"),
    (22, "Validating motion capture…"),
    (42, "Building skeleton…"),
    (62, "Preparing visualization…"),
    (80, "Initializing workspace…"),
    (94, "Finalizing workspace…"),
)

_SESSION_STAGES: tuple[tuple[int, str], ...] = (
    (12, "Loading session…"),
    (36, "Reconstructing skeleton…"),
    (64, "Preparing visualization…"),
    (88, "Finalizing workspace…"),
)


class LoadingOverlay(QWidget):
    """Dimmed backdrop with a centered loading card and staged progress.

    Intentionally avoids QGraphicsEffect (opacity/blur/shadow) — nested
    effects crash Qt on Windows when combined with the welcome surface.
    """

    finished = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("LoadingOverlay")
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        self._stages: tuple[tuple[int, str], ...] = _DATASET_STAGES
        self._stage_index = 0
        self._display_progress = 0
        self._job_done = False
        self._completing = False
        self._completed_labels: list[str] = []

        self._stage_timer = QTimer(self)
        self._stage_timer.setInterval(380)
        self._stage_timer.timeout.connect(self._advance_stage)

        root = QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._card = QFrame()
        self._card.setObjectName("LoadingCard")
        self._card.setFixedWidth(360)

        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(28, 28, 28, 24)
        card_layout.setSpacing(0)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._brand = QLabel()
        apply_wordmark_label(
            self._brand,
            pixel_size=22,
            weight=WORDMARK_WEIGHT_UI,
            object_name="LoadingBrand",
        )
        self._brand.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._title = QLabel("Loading Motion Database")
        self._title.setObjectName("LoadingTitle")
        self._title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._title.setWordWrap(True)

        self._stage = QLabel("Reading dataset…")
        self._stage.setObjectName("LoadingStage")
        self._stage.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._stage.setWordWrap(True)

        self._done_host = QWidget()
        self._done_layout = QVBoxLayout(self._done_host)
        self._done_layout.setContentsMargins(0, 8, 0, 0)
        self._done_layout.setSpacing(2)
        self._done_host.hide()

        self._bar = QProgressBar()
        self._bar.setObjectName("LoadingBar")
        self._bar.setRange(0, 100)
        self._bar.setValue(0)
        self._bar.setTextVisible(False)
        self._bar.setFixedHeight(5)
        self._bar.setFixedWidth(280)

        self._percent = QLabel("0%")
        self._percent.setObjectName("LoadingPercent")
        self._percent.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._meta = QLabel("")
        self._meta.setObjectName("LoadingMeta")
        self._meta.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._meta.setWordWrap(True)
        self._meta.hide()

        card_layout.addWidget(self._brand)
        card_layout.addSpacing(14)
        card_layout.addWidget(self._title)
        card_layout.addSpacing(6)
        card_layout.addWidget(self._stage)
        card_layout.addWidget(self._done_host)
        card_layout.addSpacing(18)
        card_layout.addWidget(self._bar, alignment=Qt.AlignmentFlag.AlignCenter)
        card_layout.addSpacing(8)
        card_layout.addWidget(self._percent)
        card_layout.addSpacing(14)
        card_layout.addWidget(self._meta)

        root.addWidget(self._card, alignment=Qt.AlignmentFlag.AlignCenter)
        self.hide()

    @property
    def job_finished(self) -> bool:
        return self._job_done

    def begin(
        self,
        *,
        title: str = "Loading Motion Database",
        kind: str = "dataset",
        meta_lines: list[str] | None = None,
    ) -> None:
        """Show the card and start staged progress (capped below 100%)."""
        self._job_done = False
        self._completing = False
        self._stage_index = 0
        self._display_progress = 0
        self._completed_labels.clear()
        self._clear_done_rows()
        self._done_host.hide()

        self._stages = _SESSION_STAGES if kind == "session" else _DATASET_STAGES
        self._title.setText(title)
        apply_wordmark_label(
            self._brand,
            pixel_size=22,
            weight=WORDMARK_WEIGHT_UI,
            object_name="LoadingBrand",
        )
        first = self._stages[0][1] if self._stages else "Working…"
        self._stage.setText(first)
        self._set_progress_ui(0)
        self._apply_meta(meta_lines)

        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        self.raise_()
        self.show()
        self._stage_timer.start()

    def show_message(self, message: str) -> None:
        kind = "dataset"
        title = "Loading Motion Database"
        lower = message.lower()
        if "skeleton" in lower or "building" in lower or "session" in lower:
            kind = "session"
            title = "Preparing Session"
        elif "motion" in lower or "dataset" in lower or "database" in lower:
            kind = "dataset"
            title = "Loading Motion Database"
        else:
            title = message.strip() or "Loading"
        self.begin(title=title, kind=kind)

    def set_indeterminate(self, indeterminate: bool) -> None:
        _ = indeterminate

    def set_progress(self, value: int, message: str | None = None) -> None:
        if self._completing:
            return
        if message:
            self._stage.setText(message)
        raw = max(0, min(100, int(value)))
        if raw >= 100:
            self._job_done = True
            self._set_progress_ui(max(self._display_progress, _DISPLAY_CAP))
            if self._stages:
                self._stage.setText(self._stages[-1][1])
            return
        target = min(raw, _DISPLAY_CAP)
        if target > self._display_progress:
            self._set_progress_ui(target)

    def complete_and_hide(self) -> None:
        if self._completing:
            return
        self._completing = True
        self._stage_timer.stop()
        self._job_done = True
        self._set_progress_ui(100)
        self._stage.setText("Workspace initialized")
        self._title.setText("Ready")
        self._brand.setText("✓")
        QTimer.singleShot(180, self.hide_overlay)

    def hide_overlay(self) -> None:
        self._stage_timer.stop()
        self.hide()
        self._completing = False
        self.finished.emit()

    def set_meta_lines(self, lines: list[str] | None) -> None:
        self._apply_meta(lines)

    def _apply_meta(self, lines: list[str] | None) -> None:
        if not lines:
            self._meta.clear()
            self._meta.hide()
            return
        self._meta.setText("  ·  ".join(lines))
        self._meta.show()

    def _set_progress_ui(self, value: int) -> None:
        self._display_progress = max(0, min(100, int(value)))
        self._bar.setValue(self._display_progress)
        self._percent.setText(f"{self._display_progress}%")

    def _advance_stage(self) -> None:
        if self._completing or self._job_done:
            return
        if self._stage_index >= len(self._stages):
            if self._display_progress < _DISPLAY_CAP:
                self._set_progress_ui(min(_DISPLAY_CAP, self._display_progress + 1))
            return

        target, label = self._stages[self._stage_index]
        if self._stage_index > 0:
            prev_label = self._stages[self._stage_index - 1][1]
            self._push_done(prev_label)

        self._stage.setText(label)
        self._set_progress_ui(max(self._display_progress, min(target, _DISPLAY_CAP)))
        self._stage_index += 1
        self._stage_timer.setInterval(360 + self._stage_index * 35)

    def _push_done(self, label: str) -> None:
        clean = label.rstrip("…").rstrip(".")
        if clean in self._completed_labels:
            return
        self._completed_labels.append(clean)
        row = QLabel(f"✓  {clean}")
        row.setObjectName("LoadingDoneRow")
        row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._done_layout.addWidget(row)
        self._done_host.show()
        while self._done_layout.count() > 3:
            item = self._done_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def _clear_done_rows(self) -> None:
        while self._done_layout.count():
            item = self._done_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()

    def resizeEvent(self, event) -> None:  # noqa: N802 - Qt API
        if self.parentWidget() is not None:
            self.setGeometry(self.parentWidget().rect())
        super().resizeEvent(event)
