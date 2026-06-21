# PDF Visual Review — Kiro Power

A Kiro Power that uses **Gemini vision** to detect layout issues in PDF pages. Designed for IEEE-style two-column academic papers, but works with any PDF.

## What it does

Renders PDF pages as images and sends them to Gemini's vision model to identify layout problems like a human reviewer would:

- **Table rule overflow** — horizontal lines extending into the adjacent column
- **Text-figure overlap** — content colliding with figures
- **Column boundary violation** — content crossing the column gap
- **Caption truncation** — captions cut off at page edges
- **Margin overflow** — content beyond page margins

## Why

LaTeX compilers (`pdflatex`, `xelatex`) report `Overfull \hbox` for text overflow, but do **not** detect when `booktabs` table rules extend into adjacent columns in two-column layouts. This is a common undetected issue that requires manual visual inspection — until now.

## Installation

### Prerequisites

```bash
pip install PyMuPDF google-genai
```

### Install in Kiro

1. Open Kiro Powers panel (Command Palette → "Powers")
2. Click "Add Custom Power"
3. Select "Local Directory" or "GitHub Repository"
4. Provide the path/URL to this directory

### Configure API Key

Set your Google Gemini API key as an environment variable:

```bash
export GOOGLE_API_KEY="your-api-key-here"
```

Or update the `env` section in `mcp.json` after installation.

Get a key at: https://aistudio.google.com/apikey

## Usage

Once installed, the power provides the `review_pdf_layout` tool:

```
Tool: review_pdf_layout
Input:
  pdf_path: "path/to/your/paper.pdf"
  pages: "5,6,8"  (optional, defaults to all pages)
```

Returns a JSON array of detected issues with severity, location, description, and LaTeX fix suggestions.

## File Structure

```
pdf-visual-review/
├── POWER.md           # Power documentation (required by Kiro)
├── mcp.json           # MCP server configuration
├── README.md          # This file
├── .gitignore
└── server/
    ├── main.py        # Gemini vision MCP server
    └── mcp_server.py  # Minimal STDIO MCP protocol implementation
```

## Cost

Each page costs approximately 1 Gemini API call (~0.01 USD with Flash model). Specify page numbers to minimize cost.

## License

MIT
