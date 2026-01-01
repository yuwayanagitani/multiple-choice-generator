from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Tuple

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.qt import QAction, QApplication
from aqt.utils import showInfo

from .mcq_builder import McqBuilderDialog

ADDON_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(ADDON_DIR, "config.json")

DEFAULT_CONFIG: Dict[str, Any] = {
    "ui": {
        "editor_button_label": "MCQ Builder",
        "tools_menu_label": "MCQ Builder...",
    },
    "display": {
        "correct_format": "index",
        "choice_prefix": "letter",
        "unanswered_text": "Unanswered.",
        "wrong_mark": "×",
        "correct_mark": "✓",
        "explanation_position": "bottom",
    },
}

_current_editor = None


def _deep_merge(defaults: Dict[str, Any], overrides: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(defaults)
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config() -> Dict[str, Any]:
    if not os.path.exists(CONFIG_PATH):
        return DEFAULT_CONFIG
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as handle:
            loaded = json.load(handle)
        if isinstance(loaded, dict):
            return _deep_merge(DEFAULT_CONFIG, loaded)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_CONFIG
    return DEFAULT_CONFIG


CONFIG = load_config()


def _field_names() -> List[str]:
    return [
        "Question",
        "Choice1",
        "Choice2",
        "Choice3",
        "Choice4",
        "Choice5",
        "Choice6",
        "Correct",
        "Mode",
        "Explanation",
    ]


def _build_templates(config: Dict[str, Any]) -> Tuple[str, str, str]:
    display = config["display"]
    choice_prefix = json.dumps(display["choice_prefix"])
    correct_format = json.dumps(display["correct_format"])
    unanswered_text = json.dumps(display["unanswered_text"])
    wrong_mark = json.dumps(display["wrong_mark"])
    correct_mark = json.dumps(display["correct_mark"])
    explanation_position = json.dumps(display["explanation_position"])

    front_template = f"""
<div id="mcq-question">{{{{Question}}}}</div>
<div id="mcq-choices" class="mcq-choices"></div>

<div id="mcq-hidden" style="display:none;">
  <div data-index="1">{{{{Choice1}}}}</div>
  <div data-index="2">{{{{Choice2}}}}</div>
  <div data-index="3">{{{{Choice3}}}}</div>
  <div data-index="4">{{{{Choice4}}}}</div>
  <div data-index="5">{{{{Choice5}}}}</div>
  <div data-index="6">{{{{Choice6}}}}</div>
</div>

<div id="mcq-meta"
     data-mode="{{{{Mode}}}}"
     data-card-id="{{{{CardId}}}}">
</div>

<script>
(() => {{
  const choicePrefix = {choice_prefix};
  const meta = document.getElementById("mcq-meta");
  const mode = (meta.dataset.mode || "").trim();
  const cardId = meta.dataset.cardId || "";
  const storageKey = `mcq_addon:v1:${{cardId}}`;

  const rawChoices = [];
  document.querySelectorAll("#mcq-hidden > div").forEach((el) => {{
    const html = el.innerHTML.trim();
    if (html) {{
      rawChoices.push({{
        index: parseInt(el.dataset.index, 10),
        html,
      }});
    }}
  }});

  const container = document.getElementById("mcq-choices");
  const inputType = mode === "multi" ? "checkbox" : "radio";

  const indexToLabel = (index) => {{
    if (choicePrefix === "none") {{
      return "";
    }}
    if (choicePrefix === "index") {{
      return `${{index}}.`;
    }}
    const letter = String.fromCharCode("A".charCodeAt(0) + index - 1);
    return `${{letter}}.`;
  }};

  const readStored = () => {{
    try {{
      const raw = localStorage.getItem(storageKey);
      if (!raw) {{
        return [];
      }}
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.selected)) {{
        return [];
      }}
      return parsed.selected.map((value) => parseInt(value, 10)).filter((value) => !Number.isNaN(value));
    }} catch (error) {{
      return [];
    }}
  }};

  const stored = new Set(readStored());

  rawChoices.forEach((choice) => {{
    const wrapper = document.createElement("label");
    wrapper.className = "mcq-choice";

    const input = document.createElement("input");
    input.type = inputType;
    input.name = "mcq-choice";
    input.value = String(choice.index);
    if (stored.has(choice.index)) {{
      input.checked = true;
    }}

    const prefix = document.createElement("span");
    prefix.className = "mcq-prefix";
    prefix.textContent = indexToLabel(choice.index);

    const content = document.createElement("span");
    content.className = "mcq-content";
    content.innerHTML = choice.html;

    wrapper.appendChild(input);
    wrapper.appendChild(prefix);
    wrapper.appendChild(content);
    container.appendChild(wrapper);
  }});

  const saveSelection = () => {{
    const selected = Array.from(container.querySelectorAll("input:checked"))
      .map((input) => parseInt(input.value, 10))
      .filter((value) => !Number.isNaN(value));
    const payload = {{
      selected,
      ts: Math.floor(Date.now() / 1000),
    }};
    localStorage.setItem(storageKey, JSON.stringify(payload));
  }};

  container.addEventListener("change", saveSelection);
}})();
</script>
"""

    back_template = f"""
<div id="mcq-question">{{{{Question}}}}</div>
<div id="mcq-result"></div>
<div id="mcq-choices" class="mcq-choices"></div>

<div id="mcq-hidden" style="display:none;">
  <div data-index="1">{{{{Choice1}}}}</div>
  <div data-index="2">{{{{Choice2}}}}</div>
  <div data-index="3">{{{{Choice3}}}}</div>
  <div data-index="4">{{{{Choice4}}}}</div>
  <div data-index="5">{{{{Choice5}}}}</div>
  <div data-index="6">{{{{Choice6}}}}</div>
</div>

<div id="mcq-explanation" style="display:none;">{{{{Explanation}}}}</div>

<div id="mcq-meta"
     data-mode="{{{{Mode}}}}"
     data-correct="{{{{Correct}}}}"
     data-card-id="{{{{CardId}}}}">
</div>

<script>
(() => {{
  const choicePrefix = {choice_prefix};
  const correctFormat = {correct_format};
  const unansweredText = {unanswered_text};
  const wrongMark = {wrong_mark};
  const correctMark = {correct_mark};
  const explanationPosition = {explanation_position};

  const meta = document.getElementById("mcq-meta");
  const rawMode = (meta.dataset.mode || "").trim();
  const rawCorrect = (meta.dataset.correct || "").trim();
  const cardId = meta.dataset.cardId || "";
  const storageKey = `mcq_addon:v1:${{cardId}}`;

  const resultEl = document.getElementById("mcq-result");
  const container = document.getElementById("mcq-choices");

  const showError = (message) => {{
    resultEl.innerHTML = `
      <div class="mcq-error">
        <div class="mcq-error-title">${{message}}</div>
        <div class="mcq-error-details">
          <div>Raw Mode: <span class="mcq-raw">${{rawMode || "(empty)"}}</span></div>
          <div>Raw Correct: <span class="mcq-raw">${{rawCorrect || "(empty)"}}</span></div>
        </div>
      </div>
    `;
  }};

  const parseCorrect = () => {{
    const pieces = rawCorrect.split(",")
      .map((part) => part.trim())
      .filter((part) => part.length > 0);
    if (pieces.length === 0) {{
      return null;
    }}
    const values = [];
    const seen = new Set();
    for (const part of pieces) {{
      const parsed = parseInt(part, 10);
      if (Number.isNaN(parsed)) {{
        return null;
      }}
      if (parsed < 1 || parsed > 6) {{
        return null;
      }}
      if (!seen.has(parsed)) {{
        seen.add(parsed);
        values.push(parsed);
      }}
    }}
    return values;
  }};

  if (rawMode !== "single" && rawMode !== "multi") {{
    showError("Invalid Mode field.");
    return;
  }}

  const correctValues = parseCorrect();
  if (!correctValues) {{
    showError("Invalid Correct field.");
    return;
  }}

  if (rawMode === "single" && correctValues.length > 1) {{
    showError("Invalid Correct field (single mode cannot have multiple answers).");
    return;
  }}

  const readStored = () => {{
    try {{
      const raw = localStorage.getItem(storageKey);
      if (!raw) {{
        return [];
      }}
      const parsed = JSON.parse(raw);
      if (!parsed || !Array.isArray(parsed.selected)) {{
        return [];
      }}
      return parsed.selected.map((value) => parseInt(value, 10)).filter((value) => !Number.isNaN(value));
    }} catch (error) {{
      return [];
    }}
  }};

  const selectedValues = readStored();
  const selectedSet = new Set(selectedValues);
  const correctSet = new Set(correctValues);
  const isUnanswered = selectedValues.length === 0;

  if (isUnanswered) {{
    resultEl.textContent = unansweredText;
  }}

  const rawChoices = [];
  document.querySelectorAll("#mcq-hidden > div").forEach((el) => {{
    const html = el.innerHTML.trim();
    if (html) {{
      rawChoices.push({{
        index: parseInt(el.dataset.index, 10),
        html,
      }});
    }}
  }});

  const indexToLabel = (index) => {{
    if (choicePrefix === "none") {{
      return "";
    }}
    if (choicePrefix === "index") {{
      return `${{index}}.`;
    }}
    const letter = String.fromCharCode("A".charCodeAt(0) + index - 1);
    return `${{letter}}.`;
  }};

  rawChoices.forEach((choice) => {{
    const wrapper = document.createElement("div");
    wrapper.className = "mcq-choice";

    const prefix = document.createElement("span");
    prefix.className = "mcq-prefix";
    prefix.textContent = indexToLabel(choice.index);

    const content = document.createElement("span");
    content.className = "mcq-content";
    content.innerHTML = choice.html;

    if (!isUnanswered) {{
      if (correctSet.has(choice.index)) {{
        wrapper.classList.add("mcq-correct");
        if (selectedSet.has(choice.index)) {{
          const mark = document.createElement("span");
          mark.className = "mcq-mark";
          mark.textContent = correctMark;
          wrapper.appendChild(mark);
        }}
      }} else if (selectedSet.has(choice.index)) {{
        wrapper.classList.add("mcq-wrong");
        const mark = document.createElement("span");
        mark.className = "mcq-mark";
        mark.textContent = wrongMark;
        wrapper.appendChild(mark);
      }}
    }}

    wrapper.appendChild(prefix);
    wrapper.appendChild(content);
    container.appendChild(wrapper);
  }});

  const formatCorrectAnswers = () => {{
    const sorted = [...correctValues].sort((a, b) => a - b);
    if (correctFormat === "letter") {{
      return sorted.map((index) => String.fromCharCode("A".charCodeAt(0) + index - 1)).join(",");
    }}
    return sorted.join(",");
  }};

  const summary = document.createElement("div");
  summary.className = "mcq-summary";
  summary.textContent = `Correct answers: ${{formatCorrectAnswers()}}`;

  const explanation = document.getElementById("mcq-explanation");
  const explanationHtml = explanation ? explanation.innerHTML.trim() : "";

  if (explanationPosition === "top" && explanationHtml) {{
    const explanationBlock = document.createElement("div");
    explanationBlock.className = "mcq-explanation";
    explanationBlock.innerHTML = explanationHtml;
    resultEl.appendChild(explanationBlock);
  }}

  resultEl.appendChild(summary);

  if (explanationPosition === "bottom" && explanationHtml) {{
    const explanationBlock = document.createElement("div");
    explanationBlock.className = "mcq-explanation";
    explanationBlock.innerHTML = explanationHtml;
    resultEl.appendChild(explanationBlock);
  }}
}})();
</script>
"""

    css = """
.mcq-choices {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.mcq-choice {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.mcq-choice input {
  margin-top: 0.2rem;
}

.mcq-prefix {
  font-weight: bold;
}

.mcq-correct {
  background: #d6f5d6;
}

.mcq-wrong {
  background: #f8d7da;
}

.mcq-mark {
  margin-left: auto;
  font-weight: bold;
}

.mcq-summary {
  margin-top: 0.75rem;
  font-weight: bold;
}

.mcq-explanation {
  margin-top: 0.75rem;
}

.mcq-error {
  border: 1px solid #d9534f;
  background: #f8d7da;
  padding: 0.75rem;
  border-radius: 4px;
}

.mcq-error-title {
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.mcq-raw {
  font-family: monospace;
}
"""

    return front_template, back_template, css


def ensure_note_type() -> None:
    model = mw.col.models.byName("MCQ (Addon)")
    if model:
        return

    model = mw.col.models.new("MCQ (Addon)")
    for field_name in _field_names():
        mw.col.models.addField(model, mw.col.models.newField(field_name))

    front_template, back_template, css = _build_templates(CONFIG)
    template = mw.col.models.newTemplate("Card 1")
    template["qfmt"] = front_template
    template["afmt"] = back_template
    mw.col.models.addTemplate(model, template)
    model["css"] = css
    mw.col.models.add(model)


def _get_active_editor() -> Optional[Any]:
    return _current_editor


def _get_target_note():
    editor = _get_active_editor()
    if editor and editor.note:
        return editor.note, editor

    active = QApplication.activeWindow()
    if isinstance(active, Browser):
        selected = active.selectedNotes()
        if selected:
            note = mw.col.get_note(selected[0])
            return note, None

    return None, None


def open_builder() -> None:
    ensure_note_type()
    note, editor = _get_target_note()
    if not note:
        showInfo("Open the Add/Edit window or select a note in the Browser.")
        return

    dialog = McqBuilderDialog(note, editor, CONFIG, mw)
    dialog.exec()


def _add_editor_button(editor) -> None:
    global _current_editor
    _current_editor = editor

    button = editor.addButton(
        icon=None,
        cmd="mcq_builder",
        func=open_builder,
        tip=CONFIG["ui"]["editor_button_label"],
        label=CONFIG["ui"]["editor_button_label"],
    )
    button.setEnabled(True)


def _add_menu_action() -> None:
    action = QAction(CONFIG["ui"]["tools_menu_label"], mw)
    action.triggered.connect(open_builder)
    mw.form.menuTools.addAction(action)


def _init_addon() -> None:
    _add_menu_action()
    gui_hooks.profile_did_open.append(lambda: ensure_note_type())


gui_hooks.editor_did_init_buttons.append(_add_editor_button)

_init_addon()
