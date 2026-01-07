from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional, Tuple

from aqt import gui_hooks, mw
from aqt.browser import Browser
from aqt.qt import QAction, QApplication, QWidget
from aqt.utils import showInfo

from .mcq_builder import McqBuilderDialog

DEFAULT_CONFIG: Dict[str, Any] = {
    "ui": {
        "editor_button_label": "MCQ Builder",
        "tools_menu_label": "MCQ Builder...",
        "force_update_templates": False,
    },
    "display": {
        "correct_format": "index",
        "choice_prefix": "letter",
        "unanswered_text": "Unanswered.",
        "wrong_mark": "×",
        "correct_mark": "✓",
        "explanation_position": "bottom",
        "clear_selection_on_back": True,
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
    """
    Load config from Anki add-on config (Tools -> Add-ons -> Config).
    Anki will provide defaults from the add-on's config.json automatically.
    """
    cfg = mw.addonManager.getConfig(__name__) or {}
    return _deep_merge(DEFAULT_CONFIG, cfg)


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
    clear_selection_on_back = json.dumps(display["clear_selection_on_back"])

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
     data-cid="" data-nid="" data-ord="">
</div>
<div id="mcq-runtime" data-cid="" data-nid="" data-ord=""></div>

<script>
(() => {{
  const choicePrefix = {choice_prefix};
  const meta = document.getElementById("mcq-meta");
  const raw = (meta.dataset.mode || "").trim().toLowerCase();
  const mode = (raw === "single") ? "single" : "multi";
  const runtime = document.getElementById("mcq-runtime");
  const cid = runtime ? (runtime.dataset.cid || "") : "";
  const nid = runtime ? (runtime.dataset.nid || "") : "";
  const ord = runtime ? (runtime.dataset.ord || "") : "";
  const storageKey = `mcq_addon:v1:${{nid}}:${{ord}}`;

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
    wrapper.className = "mcq-choice mcq-front-choice";

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

    const inputBox = document.createElement("span");
    inputBox.className = "mcq-inputbox";
    inputBox.appendChild(input);

    wrapper.appendChild(inputBox);
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
     data-cid="" data-nid="" data-ord="">
</div>
<div id="mcq-runtime" data-cid="" data-nid="" data-ord=""></div>

<script>
(() => {{
  const choicePrefix = {choice_prefix};
  const correctFormat = {correct_format}; // kept for compatibility (unused in summary now)
  const unansweredText = {unanswered_text};
  const wrongMark = {wrong_mark};         // kept for compatibility
  const correctMark = {correct_mark};
  const explanationPosition = {explanation_position};
  const clearSelectionOnBack = {clear_selection_on_back};

  const meta = document.getElementById("mcq-meta");
  const raw = (meta.dataset.mode || "").trim().toLowerCase();
  const rawMode = (raw === "single") ? "single" : "multi";
  const rawCorrect = (meta.dataset.correct || "").trim();
  const runtime = document.getElementById("mcq-runtime");
  const cid = runtime ? (runtime.dataset.cid || "") : "";
  const nid = runtime ? (runtime.dataset.nid || "") : "";
  const ord = runtime ? (runtime.dataset.ord || "") : "";
  const storageKey = `mcq_addon:v1:${{nid}}:${{ord}}`;

  const resultEl = document.getElementById("mcq-result");
  const container = document.getElementById("mcq-choices");

  if (rawMode === "single") {{
    container.classList.add("mcq-single-mode");
  }}

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
  if (clearSelectionOnBack && selectedValues.length > 0) {{
    try {{
      localStorage.removeItem(storageKey);
    }} catch (error) {{
      // Ignore storage errors
    }}
  }}
  const selectedSet = new Set(selectedValues);
  const correctSet = new Set(correctValues);
  const isUnanswered = selectedValues.length === 0;

  // Show only minimal result message (no "Correct answers: ..." summary)
  resultEl.textContent = isUnanswered ? unansweredText : "";

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

  // Minimal header row: only "Your" and "Correct" (no "Choices")
  const header = document.createElement("div");
  header.className = "mcq-choice mcq-judge-header";
  header.innerHTML = `
    <span class="mcq-judge-head" aria-label="Your">👤</span>
    <span class="mcq-judge-head" aria-label="Correct">🎯</span>
    <span class="mcq-prefix"></span>
    <span class="mcq-content"></span>
  `;
  container.appendChild(header);

  rawChoices.forEach((choice) => {{
    const wrapper = document.createElement("div");
    wrapper.className = "mcq-choice";

    const isSelected = selectedSet.has(choice.index);
    const isCorrect = correctSet.has(choice.index);

    const yourCol = document.createElement("span");
    yourCol.className = "mcq-judge";
    yourCol.textContent = (!isUnanswered && isSelected) ? correctMark : "";

    const correctCol = document.createElement("span");
    correctCol.className = "mcq-judge";
    correctCol.textContent = (!isUnanswered && isCorrect) ? correctMark : "";

    const prefix = document.createElement("span");
    prefix.className = "mcq-prefix";
    prefix.textContent = indexToLabel(choice.index);

    const content = document.createElement("span");
    content.className = "mcq-content";
    content.innerHTML = choice.html;

    if (!isUnanswered) {{
      if (isSelected && isCorrect) {{
        wrapper.classList.add("mcq-row-correct");
      }} else if (isSelected || isCorrect) {{
        wrapper.classList.add("mcq-row-wrong");
      }}
    }}

    wrapper.appendChild(yourCol);
    wrapper.appendChild(correctCol);
    wrapper.appendChild(prefix);
    wrapper.appendChild(content);
    container.appendChild(wrapper);
  }});

  const explanation = document.getElementById("mcq-explanation");
  const explanationHtml = explanation ? explanation.innerHTML.trim() : "";

  if (explanationHtml) {{
    const explanationBlock = document.createElement("div");
    explanationBlock.className = "mcq-explanation";
    explanationBlock.innerHTML = explanationHtml;

    if (explanationPosition === "top") {{
      resultEl.appendChild(explanationBlock);
    }} else {{
      container.after(explanationBlock); // ★ ここが重要
    }}
  }}
}})();
</script>
"""

    css = """
/* ===== Global font unification (avoid Anki theme mismatches) ===== */
html, body, #anki {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans JP", "Hiragino Sans", "Yu Gothic", "Meiryo", Arial, sans-serif;
  font-size: 16px;
  line-height: 1.45;
}

/* Container */
.mcq-choices {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  align-items: center;
}

/* Question: add vertical margins */
#mcq-question {
  font-size: 18px;
  max-width: 700px;
  width: 100%;
  margin: 3rem auto 2rem auto;  /* ★ 上下マージン増やす */
  text-align: center;
  box-sizing: border-box;
}

/* Result block alignment */
#mcq-result,
.mcq-explanation,
.mcq-error {
  max-width: 700px;
  width: 100%;
  margin-left: auto;
  margin-right: auto;
  text-align: left;
  box-sizing: border-box;
}

/* When result is empty, keep spacing subtle */
#mcq-result {
  min-height: 0.5rem;
  margin-top: 0.25rem;
  margin-bottom: 0.25rem;
}

/* Front choices keep original layout */
.mcq-front-choice {
  display: grid;
  grid-template-columns: 1.6em auto 1fr; /* ★ 1列目を固定幅に */
  align-items: center;          /* ★ start → center */
  column-gap: 0.6rem;
  width: 100%;
  max-width: 700px;
  padding: 0.45rem 0.65rem;
  border-radius: 6px;
  box-sizing: border-box;
  text-align: left;
}

/* input を“箱”で中央揃え */
.mcq-inputbox{
  width:1.6em;
  height:1.6em;
  display:flex;
  align-items:center;
  justify-content:center;
}

.mcq-front-choice input {
  margin:0;
  padding:0;
  line-height:1;
}

/* Back choices: [Your][Correct][prefix][content] */
.mcq-choice {
  display: grid;
  grid-template-columns: 1.6em 1.6em auto 1fr;
  align-items: start;
  column-gap: 0.6rem;

  width: 100%;
  max-width: 700px;
  padding: 0.45rem 0.65rem;
  border-radius: 6px;
  box-sizing: border-box;
  text-align: left;
}

/* Prefix + content */
.mcq-prefix {
  font-weight: 600;
  white-space: nowrap;
}

.mcq-content {
  word-break: break-word;
}

/* Judge columns */
.mcq-judge {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.05em;   /* 絵文字を少しだけ見やすく */
  line-height: 1;
}

/* Minimal header row */
.mcq-judge-header {
  padding-top: 0.2rem;
  padding-bottom: 0.2rem;
  background: transparent;
}

.mcq-judge-head {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.8em;
  opacity: 0.65;
  font-weight: 600;
  text-align: center;
  white-space: nowrap; /* ★ 折り返し防止 */
}

/* Error block */
.mcq-error {
  padding: 0.75rem;
  border-radius: 6px;
}

/* Row coloring rule */
.mcq-row-correct {
  background: #d6f5d6;
}

.mcq-row-wrong {
  background: #f8d7da;
}

/* Explanation block */
.mcq-explanation {
  margin: 2.5rem auto;
}

/* ===== Single mode: hide "Your" (👤) column ===== 一旦復活させてます。
.mcq-single-mode .mcq-choice {
  grid-template-columns: 1.6em auto 1fr;
}

.mcq-single-mode .mcq-choice > .mcq-judge:first-child {
  display: none;
}

.mcq-single-mode .mcq-judge-header > .mcq-judge-head:first-child {
  display: none;
}
*/

"""

    return front_template, back_template, css


def ensure_note_type() -> None:
    """
    Ensure the 'MCQ (Addon)' note type exists and is valid.

    Fixes:
    - When creating a new model, set qfmt/afmt BEFORE mw.col.models.add(model),
      otherwise Anki may throw:
        CardTypeError: Expected to find a field replacement on the front...
    - For existing users, auto-repair broken templates (e.g., empty qfmt).
    """
    cfg = load_config()
    front_template, back_template, css = _build_templates(cfg)

    def front_has_field_replacement(qfmt: str) -> bool:
        """
        Anki requires at least one field replacement on the *front* template.
        We'll treat any {{...}} as a field replacement (good enough here).
        """
        qfmt = (qfmt or "").strip()
        if not qfmt:
            return False
        return re.search(r"{{[^}]+}}", qfmt) is not None

    model = mw.col.models.byName("MCQ (Addon)")
    updated = False

    # -----------------------
    # Create new model (safe)
    # -----------------------
    if not model:
        model = mw.col.models.new("MCQ (Addon)")

        # Fields
        for field_name in _field_names():
            mw.col.models.addField(model, mw.col.models.newField(field_name))

        # Template (IMPORTANT: fill qfmt/afmt before adding model)
        tmpl = mw.col.models.newTemplate("Card 1")
        tmpl["qfmt"] = front_template
        tmpl["afmt"] = back_template
        mw.col.models.addTemplate(model, tmpl)

        # CSS
        model["css"] = css

        # Add model to collection AFTER templates are valid
        mw.col.models.add(model)
        updated = True

    # -----------------------
    # Update / repair existing
    # -----------------------
    else:
        force_update = bool(cfg.get("ui", {}).get("force_update_templates", False))

        # Ensure all fields exist
        field_names = {f.get("name") for f in model.get("flds", [])}
        for field_name in _field_names():
            if field_name not in field_names:
                mw.col.models.addField(model, mw.col.models.newField(field_name))
                updated = True

        # Ensure at least one template exists
        if not model.get("tmpls"):
            tmpl = mw.col.models.newTemplate("Card 1")
            tmpl["qfmt"] = front_template
            tmpl["afmt"] = back_template
            model["tmpls"] = [tmpl]
            model["css"] = css
            updated = True
        else:
            # Validate and auto-repair broken qfmt
            tmpl0 = model["tmpls"][0] or {}
            qfmt0 = tmpl0.get("qfmt", "")

            broken_front = not front_has_field_replacement(qfmt0)

            # Repair if:
            # - user forced update OR
            # - template is broken OR
            # - afmt missing (rare, but fixable) OR
            # - css missing/empty (optional, but nice to keep consistent)
            needs_update = (
                force_update
                or broken_front
                or not (tmpl0.get("afmt") or "").strip()
            )

            if needs_update:
                model["tmpls"][0]["qfmt"] = front_template
                model["tmpls"][0]["afmt"] = back_template
                model["css"] = css
                updated = True
            else:
                # If not forcing/repairing templates, still ensure CSS exists once
                if not (model.get("css") or "").strip():
                    model["css"] = css
                    updated = True

    if updated:
        mw.col.models.save(model)


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


def open_builder(editor=None) -> None:
    ensure_note_type()
    cfg = load_config()
    note, editor = _get_target_note()
    if not note:
        showInfo("Open the Add/Edit window or select a note in the Browser.")
        return

    # ★ 親は「今操作しているウィンドウ」
    parent = None
    if editor is not None:
        # Add/Edit の親ウィンドウ（=エディタのウィンドウ）を親にする
        try:
            parent = editor.parentWindow()
        except Exception:
            parent = None

    if parent is None:
        # Browser などから開いた場合はアクティブウィンドウを親に
        parent = QApplication.activeWindow()

    if parent is None:
        parent = mw  # 最後の保険

    dialog = McqBuilderDialog(note, editor, cfg, parent)
    dialog.exec()

def _add_editor_button(buttons, editor) -> None:
    global _current_editor
    _current_editor = editor
    cfg = load_config()

    btn_html = editor.addButton(
        icon=None,
        cmd="mcq_builder",
        func=open_builder,
        tip=cfg["ui"]["editor_button_label"],
        label=cfg["ui"]["editor_button_label"],
    )
    if isinstance(btn_html, str):
        buttons.append(btn_html)


def _add_menu_action() -> None:
    cfg = load_config()
    action = QAction(cfg["ui"]["tools_menu_label"], mw)
    action.triggered.connect(open_builder)
    mw.form.menuTools.addAction(action)


def _init_addon() -> None:
    # _add_menu_action() 一旦要らない
    gui_hooks.profile_did_open.append(lambda: ensure_note_type())


def _inject_runtime_ids(html: str, card, kind: str) -> str:
    try:
        nid = str(card.nid)
        ord_ = str(card.ord)
        cid = str(card.id)
    except Exception:
        return html

    if 'id="mcq-runtime"' not in html:
        return html

    def repl(match):
        tag = match.group(0)
        tag = re.sub(r'data-cid="[^"]*"', f'data-cid="{cid}"', tag)
        tag = re.sub(r'data-nid="[^"]*"', f'data-nid="{nid}"', tag)
        tag = re.sub(r'data-ord="[^"]*"', f'data-ord="{ord_}"', tag)
        return tag

    try:
        return re.sub(r'<div\s+id="mcq-runtime"[^>]*>', repl, html, count=1)
    except Exception:
        return html


gui_hooks.card_will_show.append(_inject_runtime_ids)
gui_hooks.editor_did_init_buttons.append(_add_editor_button)
_init_addon()
