from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from aqt.qt import (
    QButtonGroup,
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QRadioButton,
    QVBoxLayout,
    QWidget,
    QCheckBox,
)


class McqBuilderDialog(QDialog):
    """Helper dialog that writes Mode/Correct fields for the MCQ note type."""

    def __init__(
        self,
        note,
        editor,
        config: Dict[str, Any],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.note = note
        self.editor = editor
        self.config = config
        self.mode = "single"
        self.choice_widgets: List[Tuple[int, QWidget]] = []
        self.choice_group: Optional[QButtonGroup] = None

        self.setWindowTitle("MCQ Builder")

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mode"))

        mode_layout = QHBoxLayout()
        self.single_radio = QRadioButton("Single")
        self.multi_radio = QRadioButton("Multiple")
        self.single_radio.toggled.connect(self._on_mode_changed)
        self.multi_radio.toggled.connect(self._on_mode_changed)
        mode_layout.addWidget(self.single_radio)
        mode_layout.addWidget(self.multi_radio)
        layout.addLayout(mode_layout)

        self.choice_container = QVBoxLayout()
        layout.addWidget(QLabel("Correct answers"))
        layout.addLayout(self.choice_container)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._apply)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

        self._load_initial_state()

    def _load_initial_state(self) -> None:
        raw_mode = (self.note["Mode"] or "").strip()
        if raw_mode in {"single", "multi"}:
            self.mode = raw_mode

        if self.mode == "multi":
            self.multi_radio.setChecked(True)
        else:
            self.single_radio.setChecked(True)

        self._render_choices()

    def _read_choices(self) -> List[Tuple[int, str]]:
        choices: List[Tuple[int, str]] = []
        for index in range(1, 7):
            value = (self.note[f"Choice{index}"] or "").strip()
            if value:
                choices.append((index, value))
        return choices

    def _read_correct(self) -> List[int]:
        raw_correct = (self.note["Correct"] or "").strip()
        if not raw_correct:
            return []
        values: List[int] = []
        for part in raw_correct.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                parsed = int(part)
            except ValueError:
                continue
            if parsed not in values:
                values.append(parsed)
        return values

    def _clear_choice_widgets(self) -> None:
        while self.choice_container.count():
            item = self.choice_container.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        self.choice_widgets.clear()
        self.choice_group = None

    def _render_choices(self) -> None:
        self._clear_choice_widgets()
        choices = self._read_choices()
        selected = set(self._read_correct())

        if self.mode == "single":
            group = QButtonGroup(self)
            group.setExclusive(True)
            self.choice_group = group

        for index, text in choices:
            if self.mode == "single":
                widget = QRadioButton(f"{index}. {text}")
                if index in selected:
                    widget.setChecked(True)
                if self.choice_group:
                    self.choice_group.addButton(widget, index)
            else:
                widget = QCheckBox(f"{index}. {text}")
                widget.setChecked(index in selected)

            self.choice_container.addWidget(widget)
            self.choice_widgets.append((index, widget))

        if not choices:
            self.choice_container.addWidget(QLabel("No choices found."))

    def _on_mode_changed(self) -> None:
        if self.multi_radio.isChecked():
            self.mode = "multi"
        else:
            self.mode = "single"
        self._render_choices()

    def _apply(self) -> None:
        selected: List[int] = []
        for index, widget in self.choice_widgets:
            checked = False
            if isinstance(widget, (QRadioButton, QCheckBox)):
                checked = widget.isChecked()
            if checked:
                selected.append(index)

        correct_value = ",".join(str(index) for index in selected)
        self.note["Mode"] = self.mode
        self.note["Correct"] = correct_value
        self.note.flush()

        if self.editor:
            self.editor.loadNote()

        self.accept()
