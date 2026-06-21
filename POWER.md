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

## Available MCP Servers

- **pdf-visual-review** — Provides the `review_pdf_layout` tool

## Onboarding

### Prerequisites

- Python 3.10+
- Google Gemini API key (with vision model access)
- PyMuPDF library for PDF page rendering

### Installation

```bash
pip install PyMuPDF google-genai
```

### Install in Kiro

1. Clone or download this repository
2. Open Kiro Powers panel (Command Palette → "Powers")
3. Click "Add Custom Power" → "Local Directory" or "GitHub Repository"
4. After installation, edit `~/.kiro/settings/mcp.json` to fix the server path:

```json
"power-pdf-visual-review-pdf-visual-review": {
  "command": "python",
  "args": ["<FULL_PATH_TO_REPO>/pdf-visual-review/server/main.py"],
  "env": {
    "GOOGLE_API_KEY": "YOUR_GOOGLE_API_KEY"
  }
}
```

Replace `<FULL_PATH_TO_REPO>` with the absolute path to where you have this repository, and `YOUR_GOOGLE_API_KEY` with your actual key from https://aistudio.google.com/apikey

### Configuration

Set your Google API key in the `env` section of `~/.kiro/settings/mcp.json` as shown above.

## Tool Reference

### `review_pdf_layout`

Renders specified PDF pages as images and sends them to Gemini for visual layout review.

**Parameters:**
- `pdf_path` (string, required): Absolute path to the PDF file
- `pages` (string, optional): Comma-separated page numbers to check (e.g., "1,3,5"). Defaults to all pages.

**Returns:** JSON list of issues found, each with:
- `page`: Page number
- `severity`: "high" | "medium" | "low"
- `location`: Description of where the issue is on the page
- `issue`: What the problem is
- `suggestion`: How to fix it

**Example output:**
```json
[
  {
    "page": 5,
    "severity": "high",
    "location": "Table IV, left column",
    "issue": "Table horizontal rules (\\toprule, \\midrule, \\bottomrule) extend beyond the left column boundary into the right column area",
    "suggestion": "Use tabular* with \\columnwidth or wrap with \\resizebox{\\columnwidth}{!}{...} to constrain table width"
  }
]
```

## Common Workflows

### Workflow 1: Check specific pages after compilation

After compiling a LaTeX paper, check pages that contain tables/figures:

```
Use tool review_pdf_layout with pdf_path="path/to/paper.pdf" and pages="4,5,6"
```

### Workflow 2: Full document review

Check all pages (costs more tokens but comprehensive):

```
Use tool review_pdf_layout with pdf_path="path/to/paper.pdf"
```

## Detection Capabilities

| Issue Type | Description | Typical Cause |
|-----------|-------------|---------------|
| Table rule overflow | Horizontal lines extend into adjacent column | booktabs rules in single-column table wider than \columnwidth |
| Text-figure overlap | Text runs over figure or vice versa | Float placement issues |
| Column boundary violation | Content crosses the column gap | Overfull boxes, wide equations |
| Caption truncation | Figure/table caption cut off at page boundary | Insufficient page space |
| Margin overflow | Content extends beyond page margins | Wide tables or figures |

## Best Practices

1. **Check pages with tables first** — table rule overflow is the most common undetected issue in IEEE papers
2. **Use specific page numbers** to reduce API cost — don't check all 10+ pages unless needed
3. **Combine with geometric pre-check** — use the fast Python script as a pre-filter, then Gemini for confirmation
4. **Trust the visual result** — if Gemini says it looks fine, it probably is (vision > geometry heuristics for complex layouts)

## Troubleshooting

### Error: "API key not configured"
Set `GOOGLE_API_KEY` environment variable or update mcp.json env section.

### Error: "Model not available"
Ensure your API key has access to `gemini-2.5-flash` model.

### Slow response
Each page takes 3-8 seconds. For faster results, specify only the pages you need to check.

## MCP Config Placeholders

- **`GOOGLE_API_KEY`**: Your Google Gemini API key.
  - **How to get it:** Go to https://aistudio.google.com/apikey and create/copy a key.
