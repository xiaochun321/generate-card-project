---
name: generate-card-project
description: Create reusable, batchable visual card projects from structured text data, especially Chinese educational cards with dense text and optional AI illustrations. Use when Codex needs to turn Word/Markdown source notes into a local card-generation project, parse card data, design a fixed background plus deterministic PIL text layout, integrate cached AI illustrations, enforce idempotent batch generation, or adapt the idiom-card workflow to poetry, solar terms, herbal medicine, history, math, or similar printable card products.
---

# Generate Card Project

## Core Rule

Separate uncertain and deterministic layers:

- Render text, pinyin, labels, sections, numbering, and layout with Pillow so the content is exact.
- Generate only the illustration layer with AI, then cache and quality-check it.
- Use one fixed base background per series so all cards look consistent.

For detailed ratios, algorithms, prompts, and failure fixes, read `references/card-project-playbook.md` before implementing or modifying a generator.

## Workflow

1. Start with 3-5 sample records and run the whole pipeline before completing the full dataset.
2. Normalize source content into JSON records with stable fields. For idiom cards, use `idiom`, `pinyin`, `explanation`, `story`, `tip`, and `series_number`.
3. Build the project structure:

```text
project/
├── remoteapi/                 # AI image API wrapper, optional
├── scripts/                   # card generator and data tools
├── styles/
│   ├── assets/                # fixed background, signature, ornaments
│   └── fonts/                 # title and body fonts
├── json/                      # parsed data
├── output_cards/              # final PNG files
│   └── illustrations/         # cached AI illustrations
└── .env                       # API keys, never commit
```

4. Implement the deterministic renderer first with a placeholder illustration.
5. Add AI illustration generation only after text layout, overflow control, and output naming are stable.
6. Make batch generation idempotent: skip existing final cards, reuse existing illustration cache, and continue after single-card failures.
7. Inspect a contact sheet or a small random sample before producing the whole set.

## Data Preparation

Use `scripts/parse_idiom_markdown.py` when the source follows this structure:

```markdown
## 东窗事发
### 简单解释
...
### 故事讲述
...
### 家长提示
...
```

Run:

```bash
python scripts/parse_idiom_markdown.py source.md json/idioms.json --series-prefix E01
```

Generate pinyin with `pypinyin`, then manually review polyphonic characters. Do not trust AI-generated pinyin or tone marks without review.

## Rendering Requirements

- Base size: default to `1530x2741` unless the user gives another fixed production size.
- Use percentage-based coordinates so the layout can survive background replacement.
- Align each pinyin syllable to the center of its matching character cell; do not center the whole pinyin line as one string.
- Draw idiom/title characters in individual grid cells; visually move Chinese characters upward by about 10% of measured text height.
- Use character-by-character Chinese wrapping, not space-based wrapping.
- Fit dense body text by shrinking label and body font sizes together until the estimated total height fits the available area.
- Use system font fallback if a bundled font misses glyphs.

Reusable helper functions for wrapping, text detection, and illustration blending live in `scripts/card_render_helpers.py`.

## AI Illustration Requirements

- Keep the prompt in English and avoid including user-visible Chinese text from the card title.
- Include strong no-text constraints, but rely on detection and retry because negative prompts alone are not enough.
- Generate at most a small number of candidates per card, score them with a text-suspicion heuristic, then keep the lowest-scoring result.
- Composite with irregular corner radii, feathered alpha, and paper-tone blending. Use real alpha transparency over the card background, not a flat fill color.
- Never use a global `np.minimum` signed-distance check for all corners; process each corner only inside its own bounding box.

## Batch Semantics

Use three levels of idempotency:

1. If the final card already exists, skip the record.
2. If the illustration cache already exists, reuse it instead of calling the API.
3. If one record fails, log it and keep processing the remaining records.

This is essential for long card runs because API calls, downloads, and manual interruptions are expected.

## Adaptation Guide

Preserve the reusable core for new card series:

- Keep the API wrapper, retrying downloads, illustration cache, text detection, illustration blending, Chinese wrapping, adaptive font sizing, and idempotent batch loop.
- Replace the background, color palette, section schema, prompt theme, and field names.
- For non-illustrated cards such as math practice cards, remove the AI layer and keep the deterministic PIL renderer.

Common adaptations:

- Poetry cards: replace grid with dynasty/author and poem sections.
- Herbal cards: use medicine nature, effects, and contraindication sections.
- Solar-term cards: use seasonal scene prompts and 24 records.
- History-person cards: use biography, achievement, and quote sections.
- Math cards: use problem, answer, and solution sections; pure PIL is usually enough.

## Validation

Before handing off a generated project:

- Run the parser on a small fixture.
- Render at least one short-text card and one long-text card.
- Confirm no text overflows the bottom margin.
- Confirm pinyin and grid-cell alignment on idiom cards.
- Confirm illustration cache reuse by running the batch command twice.
- If AI illustrations are enabled, inspect text-suspicion scores and keep prompt text out of the image.
