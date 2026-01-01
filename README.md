# MCQ Builder (Anki Add-on)

**MCQ Builder** is an Anki add-on that lets you create and review multiple-choice questions (MCQs) with a highly optimized review UI.

It is designed for *exam-oriented learning*, focusing on:
- Instant recognition of correctness
- Clear comparison between **your answer** and **correct answers**
- Minimal visual clutter
- Safe handling of answer state across reviews

---

## Features

### 🧠 Review UI optimized for MCQs
- Supports **single-choice** and **multiple-choice** questions
- Left-side indicator columns:
  - 👤 *Your answer*
  - 🎯 *Correct answer*
- Row-level color coding:
  - 🟩 Green: correctly selected answer
  - 🟥 Red: incorrect selection or missed correct answer
- In **single-choice mode**, the 👤 column is automatically hidden to reduce clutter

### 🔁 Safe answer state handling
- User selections are temporarily stored during review
- Optionally **auto-cleared when the back side is shown**, preventing accidental reuse of old answers

### 🧩 Flexible explanation placement
- Explanations can be shown above or below the results
- No redundant “Correct answers: …” text unless you want it

### 🛠 Builder integration
- One-click access via:
  - Editor toolbar button
  - Tools menu
- Works from both **Add/Edit** window and **Browser**

---

## Note Type: MCQ (Addon)

This add-on creates (or updates) a note type called:

> **MCQ (Addon)**

### Fields
- `Question`
- `Choice1` – `Choice6`
- `Correct` (comma-separated indices, e.g. `2,3`)
- `Mode` (`single` or `multi`)
- `Explanation`

---

## How Review Works

1. On the front side, select your answer(s)
2. Flip the card
3. Instantly see:
   - Which options you chose (👤)
   - Which options were correct (🎯)
4. Understand mistakes via color and explanation
5. (Optional) Selection state is cleared automatically

---

## Installation

1. Download the add-on files
2. Place them in a new folder under:
   ```
   Anki2/addons21/
   ```
3. Restart Anki

---

## Philosophy

This add-on is built with the idea that:

> **MCQ review should feel like a real exam review screen, not a flashcard hack.**

Everything unnecessary is removed.  
Everything useful is aligned, consistent, and predictable.

---

## License

MIT License
