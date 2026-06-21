---
name: "pdf-visual-review"
displayName: "PDF Visual Review"
description: "Uses Gemini vision to detect layout issues in PDF pages — table rule overflow, text-figure overlap, and column boundary violations in IEEE two-column papers."
keywords: ["pdf", "layout", "review", "gemini", "latex", "IEEE", "排版检查"]
author: "hill-hu"
---

# PDF Visual Review

## Overview

This power provides a Gemini-powered visual PDF layout reviewer. Instead of relying on geometric heuristics (which struggle with complex LaTeX layouts), it sends rendered PDF pages to Gemini's vision model and asks it to identify layout problems like a human reviewer would.

Designed primarily for IEEE-style two-column academic papers, but works with any PDF.

## When to Use

After compiling a LaTeX paper (pdflatex, xelatex, latexmk), run the visual review on pages containing tables and figures to catch:

- Table rules extending into adjacent columns (undetectable by LaTeX compiler)
- Figures overflowing column boundaries
- Text truncation at page breaks
- Caption and content overlap

## Onboarding

### Prerequisites

- Python 3.10+
- PyMuPDF and google-genai libraries
- Google Gemini API key

### Installation

```bash
pip install PyMuPDF google-genai
```

### Deploy the Script

Copy `scripts/pdf_visual_review.py` from this power to your project (e.g., `scripts/` directory).

### Get API Key

1. Go to https://aistudio.google.com/apikey
2. Create or copy your API key
3. Set as environment variable before running:

```bash
# Windows PowerShell
$env:GOOGLE_API_KEY="your-key-here"

# Linux/macOS
export GOOGLE_API_KEY="your-key-here"
```

## Usage

### Command Line

```bash
# Check specific pages (recommended - saves API cost)
python scripts/pdf_visual_review.py path/to/paper.pdf 5,6,8

# Check all pages
python scripts/pdf_visual_review.py path/to/paper.pdf
```

### Output Format

```
ISSUES FOUND: 2
  [high] P5 Bottom of right column: Text truncated at page break
         Fix: Use \pagebreak or \enlargethispage
  [high] P6 Figure 4: Figure extends into adjacent column
         Fix: Use \includegraphics[width=\columnwidth]{...}
```

### Integrate with Kiro Hook

Create a hook that runs after PDF compilation:

```json
{
  "name": "PDF Visual Review",
  "version": "1.0.0",
  "when": {
    "type": "postToolUse",
    "toolTypes": ["shell"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "If this was a PDF compilation (pdflatex/xelatex/latexmk), run: python scripts/pdf_visual_review.py <pdf_path> <pages_with_tables_and_figures>"
  }
}
```

## Detection Capabilities

| Issue Type | Description | Typical Cause |
|-----------|-------------|---------------|
| Table rule overflow | Horizontal lines extend into adjacent column | booktabs rules wider than \columnwidth |
| Text-figure overlap | Text runs over figure or vice versa | Float placement issues |
| Column boundary violation | Content crosses the column gap | Overfull boxes, wide equations |
| Caption truncation | Caption cut off at page boundary | Insufficient page space |
| Margin overflow | Content extends beyond page margins | Wide tables or figures |
| Page break truncation | Text/heading cut off at bottom | Poor page break placement |

## Best Practices

1. **Check pages with tables first** — table rule overflow is the most common undetected issue
2. **Specify page numbers** to minimize API cost (each page ≈ 1 API call)
3. **Run after major layout changes** — adding/removing figures, tables, or large text blocks
4. **Trust the visual result** — Gemini vision > geometric heuristics for complex layouts
5. **Set GOOGLE_API_KEY** before running — the script will exit with error if not set

## Troubleshooting

### Error: "GOOGLE_API_KEY not set"
Set the environment variable before running the script.

### Error: "Model not available"
Ensure your API key has access to `gemini-2.5-flash` model.

### Slow response
Each page takes 3-8 seconds. Specify only the pages you need to check.

### False positives on full-width elements
The prompt tells Gemini that `table*` and `figure*` are intentionally full-width. If false positives persist, the prompt can be customized in the script.
