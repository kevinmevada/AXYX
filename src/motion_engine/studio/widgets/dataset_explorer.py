"""Cohort filter list for the sidebar dataset explorer."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from PySide6.QtCore import QSize, Qt, Signal
from PySide6.QtWidgets import QAbstractItemView, QListWidget, QListWidgetItem, QVBoxLayout, QWidget

import yaml

from motion_engine.studio.models.subject_model import SubjectModel
from motion_engine.studio.theme import DEFAULT_THEME


def _cohort_catalog_path() -> Path:
    return Path(__file__).resolve().parents[4] / "config" / "subject_cohorts.yaml"


class DatasetExplorer(QWidget):
    """Clinical cohort list: Dataset / Healthy / Parkinson's / …

    Selection uses ``currentItemChanged`` so keyboard + click both work.
    """

    cohortSelected = Signal(object)  # str | None

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._cohorts: dict[str, dict[str, Any]] = {}
        self._load_catalog()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._list = QListWidget()
        self._list.setObjectName("CohortList")
        self._list.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self._list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list.setUniformItemSizes(True)
        self._list.setFrameShape(QListWidget.Shape.NoFrame)
        self._list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._list.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self._list.setAutoFillBackground(True)
        self._list.currentItemChanged.connect(self._on_current)
        layout.addWidget(self._list)
        _ = DEFAULT_THEME

    def _load_catalog(self) -> None:
        path = _cohort_catalog_path()
        if not path.exists():
            self._cohorts = {}
            return
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        self._cohorts = dict(raw.get("cohorts") or {})

    def set_subjects(self, subjects: list[SubjectModel]) -> None:
        """Rebuild rows with live subject counts."""
        present = {s.subject_id for s in subjects}
        self._list.blockSignals(True)
        self._list.clear()
        all_item = QListWidgetItem(f"Dataset ({len(subjects)})")
        all_item.setData(Qt.ItemDataRole.UserRole, None)
        all_item.setSizeHint(QSize(0, 36))
        self._list.addItem(all_item)
        for name, body in self._cohorts.items():
            ids = [str(s) for s in (body or {}).get("subjects") or []]
            count = sum(1 for sid in ids if sid in present)
            item = QListWidgetItem(f"  {name} ({count})")
            item.setData(Qt.ItemDataRole.UserRole, name)
            item.setToolTip(str((body or {}).get("diagnosis") or name))
            item.setSizeHint(QSize(0, 36))
            self._list.addItem(item)
        if self._list.count():
            self._list.setCurrentRow(0)
        self._list.blockSignals(False)
        if self._list.currentItem() is not None:
            self._on_current(self._list.currentItem(), None)

    def subject_ids_for_cohort(self, cohort: str | None) -> set[str] | None:
        """Return subject IDs for ``cohort``, or ``None`` for the full dataset."""
        if cohort is None:
            return None
        body = self._cohorts.get(cohort) or {}
        return {str(s) for s in body.get("subjects") or []}

    def _on_current(self, current: QListWidgetItem | None, _prev: QListWidgetItem | None) -> None:
        if current is None:
            return
        self.cohortSelected.emit(current.data(Qt.ItemDataRole.UserRole))
