# PDF Visual Review — Kiro Power

A Kiro Power that uses **Gemini vision** to detect layout issues in PDF pages. Designed for IEEE-style two-column academic papers.

## What it does

Renders PDF pages as images and sends them to Gemini for visual layout review:

- **Table rule overflow** — horizontal lines extending into the adjacent column
- **Text-figure overlap** — content colliding with figures
- **Column boundary violation** — content crossing the column gap
- **Caption truncation** — captions cut off at page edges
- **Page break issues** — text/headings truncated at page bottom

## Why

LaTeX compilers report `Overfull \hbox` for text overflow, but do **not** detect when `booktabs` table rules or figures extend into adjacent columns. This requires manual visual inspection — or Gemini vision.

## Quick Start

```bash
# Install dependencies
pip install PyMuPDF google-genai

# Set API key
$env:GOOGLE_API_KEY="your-key-here"  # PowerShell
export GOOGLE_API_KEY="your-key-here"  # bash

# Run on specific pages
python scripts/pdf_visual_review.py paper.pdf 5,6,8
```

## Install as Kiro Power

1. Open Kiro Powers panel
2. Click "Add Custom Power" → "GitHub Repository"
3. Enter: `https://github.com/hill-hu/kiro-power-pdf-visual-review`

The power documentation will guide Kiro's agent on when and how to run the script.

## File Structure

```
kiro-power-pdf-visual-review/
├── POWER.md                      # Kiro Power documentation
├── README.md                     # This file
├── .gitignore
└── scripts/
    └── pdf_visual_review.py      # Gemini vision review script
```

## Cost

Each page ≈ 1 Gemini Flash API call (~$0.01). Specify page numbers to minimize cost.

## License

MIT
