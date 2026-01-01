# MCQ Builder — Configuration Reference

This document explains all available options in `config.json`.

---

## UI Settings

```json
{
  "ui": {
    "editor_button_label": "MCQ Builder",
    "tools_menu_label": "MCQ Builder...",
    "force_update_templates": false
  }
}
```

### `editor_button_label`
- Text shown on the editor toolbar button

### `tools_menu_label`
- Text shown in the Tools menu

### `force_update_templates`
- **false (default)**:  
  Existing note templates and CSS are respected  
- **true**:  
  Always overwrite templates and CSS with the add-on defaults  
  (useful during development)

---

## Display Settings

```json
{
  "display": {
    "choice_prefix": "letter",
    "correct_format": "index",
    "unanswered_text": "Unanswered.",
    "correct_mark": "✓",
    "wrong_mark": "×",
    "explanation_position": "bottom",
    "clear_selection_on_back": true
  }
}
```

### `choice_prefix`
- `"letter"` → A., B., C. …
- `"index"` → 1., 2., 3. …
- `"none"` → no prefix

### `correct_format`
- Controls internal formatting (currently not shown in UI)

### `unanswered_text`
- Text displayed when no option was selected

### `correct_mark`
- Symbol used to mark correct selections (default: ✓)

### `wrong_mark`
- Symbol used for wrong selections (kept for compatibility)

### `explanation_position`
- `"top"` → explanation above results
- `"bottom"` → explanation below results

### `clear_selection_on_back`
- **true (default)**:  
  Clear stored selections after the back side is shown
- **false**:  
  Keep selections across reviews (not recommended)

---

## Recommended Defaults

For most users:

```json
{
  "ui": {
    "force_update_templates": false
  },
  "display": {
    "clear_selection_on_back": true,
    "explanation_position": "bottom"
  }
}
```

---

## Notes

- After changing `config.json`, **restart Anki**
- If templates do not update as expected, temporarily set:
  ```json
  "force_update_templates": true
  ```

---

If you customize templates manually, keep `force_update_templates` set to `false`.
