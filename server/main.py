"""
PDF Visual Review MCP Server
Uses Gemini vision to detect layout issues in PDF pages.
"""
import json
import sys
import os
import base64
import traceback

# Add server directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp_server import MCPServer

import pymupdf
from google import genai


REVIEW_PROMPT = """You are a professional academic paper layout reviewer. 
Analyze this PDF page image for layout issues. This is from an IEEE-style two-column paper.

Check for these specific issues:
1. **Table rule overflow**: Horizontal lines (from \\toprule, \\midrule, \\bottomrule) that extend beyond their column boundary into the adjacent column. This is the MOST IMPORTANT check.
2. **Text-figure overlap**: Any text overlapping with figures or vice versa.
3. **Column boundary violation**: Any content that crosses the gap between left and right columns (except for intentional full-width elements like table* or figure*).
4. **Caption truncation**: Captions cut off at page edges.
5. **Margin overflow**: Content extending beyond page margins.

IMPORTANT CONTEXT:
- In IEEE two-column papers, `table*` and `figure*` environments are INTENTIONALLY full-width (spanning both columns). These are NOT errors.
- The page header/footer lines spanning full width are normal.
- Focus on single-column tables/figures whose rules or content accidentally extend into the adjacent column.

If you find issues, return a JSON array. If no issues found, return an empty array [].

Each issue should be:
{
  "page": <page_number>,
  "severity": "high" | "medium" | "low",
  "location": "<description of where on the page>",
  "issue": "<what the problem is>",
  "suggestion": "<how to fix it in LaTeX>"
}

Return ONLY the JSON array, no other text."""


def render_page_to_image(pdf_path: str, page_num: int, dpi: int = 150) -> bytes:
    """Render a PDF page to PNG bytes."""
    doc = pymupdf.open(pdf_path)
    page = doc[page_num]
    # Render at specified DPI
    zoom = dpi / 72.0
    mat = pymupdf.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)
    img_bytes = pix.tobytes("png")
    doc.close()
    return img_bytes


def review_pdf_layout(pdf_path: str, pages: str = "") -> list:
    """
    Review PDF pages for layout issues using Gemini vision.
    
    Args:
        pdf_path: Absolute path to PDF file
        pages: Comma-separated page numbers (1-indexed). Empty = all pages.
    
    Returns:
        List of issue dictionaries
    """
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        return [{"error": "GOOGLE_API_KEY not set in environment"}]

    if not os.path.exists(pdf_path):
        return [{"error": f"File not found: {pdf_path}"}]

    # Determine which pages to check
    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    if pages.strip():
        page_nums = [int(p.strip()) - 1 for p in pages.split(",") if p.strip().isdigit()]
        page_nums = [p for p in page_nums if 0 <= p < total_pages]
    else:
        page_nums = list(range(total_pages))

    if not page_nums:
        return [{"error": "No valid pages specified"}]

    # Initialize Gemini client
    client = genai.Client(api_key=api_key)

    all_issues = []

    for page_num in page_nums:
        try:
            # Render page to image
            img_bytes = render_page_to_image(pdf_path, page_num, dpi=150)
            img_b64 = base64.b64encode(img_bytes).decode("utf-8")

            # Call Gemini vision
            prompt = REVIEW_PROMPT.replace("<page_number>", str(page_num + 1))

            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[
                    {
                        "role": "user",
                        "parts": [
                            {"text": f"This is page {page_num + 1} of the PDF. " + REVIEW_PROMPT},
                            {
                                "inline_data": {
                                    "mime_type": "image/png",
                                    "data": img_b64
                                }
                            }
                        ]
                    }
                ]
            )

            # Parse response
            result_text = response.text.strip()
            # Remove markdown code block if present
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                result_text = "\n".join(lines[1:-1])

            issues = json.loads(result_text)
            if isinstance(issues, list):
                # Ensure page numbers are set
                for issue in issues:
                    issue["page"] = page_num + 1
                all_issues.extend(issues)

        except json.JSONDecodeError:
            # If Gemini returns non-JSON, skip this page
            pass
        except Exception as e:
            all_issues.append({
                "page": page_num + 1,
                "severity": "low",
                "location": "N/A",
                "issue": f"Error processing page: {str(e)}",
                "suggestion": "Check API key and network connection"
            })

    return all_issues


# ============================================================
# MCP Server Setup
# ============================================================

server = MCPServer("pdf-visual-review", "1.0.0")


@server.tool(
    name="review_pdf_layout",
    description="Send PDF pages to Gemini vision for layout quality review. Detects table rule overflow, text-figure overlap, column boundary violations in IEEE two-column papers.",
    parameters={
        "type": "object",
        "properties": {
            "pdf_path": {
                "type": "string",
                "description": "Absolute path to the PDF file to review"
            },
            "pages": {
                "type": "string",
                "description": "Comma-separated page numbers to check (1-indexed). Leave empty to check all pages.",
                "default": ""
            }
        },
        "required": ["pdf_path"]
    }
)
def handle_review_pdf_layout(pdf_path: str, pages: str = "") -> str:
    """MCP tool handler for review_pdf_layout."""
    issues = review_pdf_layout(pdf_path, pages)
    return json.dumps(issues, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    server.run()
