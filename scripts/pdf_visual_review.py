"""
PDF Visual Review - Gemini Vision Layout Checker
Usage: python pdf_visual_review.py <pdf_path> [page_numbers]

Examples:
  python pdf_visual_review.py paper.pdf          # Check all pages
  python pdf_visual_review.py paper.pdf 5,6,8    # Check specific pages

Requires:
  pip install PyMuPDF google-genai
  Environment variable: GOOGLE_API_KEY
"""
import json
import sys
import os
import base64

import pymupdf
from google import genai


REVIEW_PROMPT = """You are a professional PDF layout quality reviewer.
Analyze this PDF page image carefully for ANY layout issues.

Check for these specific issues (in priority order):

1. **Text overlap / occlusion (文字重叠/遮挡)**: Look VERY carefully for any text characters that overlap, collide, or occlude each other. This includes:
   - Adjacent lines of text where characters from one line intrude into the space of another line
   - Text that is partially hidden behind other text
   - Characters that touch or overlap vertically (line spacing too tight)
   - Bullet points or list items where text from adjacent items overlaps
   This is the MOST IMPORTANT check. Even slight overlap (1-2 pixels) should be reported.

2. **Text-figure/image overlap**: Any text overlapping with figures, images, charts, or decorative elements.

3. **Content overflow**: Text or graphics extending beyond page margins or designated content areas.

4. **Table rule overflow**: Lines or borders extending beyond their intended boundaries.

5. **Column boundary violation**: Content crossing column gaps (for multi-column layouts).

6. **Truncation**: Any text, caption, or content cut off at edges.

7. **Abnormal spacing**: Visibly uneven or inconsistent spacing between lines or paragraphs.

IMPORTANT INSTRUCTIONS:
- Look at EVERY line of text carefully. Zoom in mentally on dense text areas, tables, and lists.
- Pay special attention to CJK (Chinese/Japanese/Korean) text which often has tighter spacing.
- Even MINOR overlap that might be barely visible should be reported.
- For multi-column or two-column academic papers: `table*` and `figure*` full-width elements are intentional, NOT errors.
- Page headers/footers spanning full width are normal.

If you find issues, return a JSON array. If no issues found, return an empty array [].

Each issue should be:
{
  "page": <page_number>,
  "severity": "high" | "medium" | "low",
  "location": "<description of where on the page, quote the affected text if possible>",
  "issue": "<what the problem is>",
  "suggestion": "<how to fix it>"
}

Return ONLY the JSON array, no other text."""


def review_pdf(pdf_path: str, pages: str = "") -> list:
    """Review PDF pages for layout issues using Gemini vision."""
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        print("ERROR: GOOGLE_API_KEY not set", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(pdf_path):
        print(f"ERROR: File not found: {pdf_path}", file=sys.stderr)
        sys.exit(1)

    doc = pymupdf.open(pdf_path)
    total_pages = len(doc)
    doc.close()

    if pages.strip():
        page_nums = [int(p.strip()) - 1 for p in pages.split(",") if p.strip().isdigit()]
        page_nums = [p for p in page_nums if 0 <= p < total_pages]
    else:
        page_nums = list(range(total_pages))

    client = genai.Client(api_key=api_key)
    all_issues = []

    for page_num in page_nums:
        print(f"  Checking page {page_num + 1}/{total_pages}...", file=sys.stderr)
        doc = pymupdf.open(pdf_path)
        page = doc[page_num]
        zoom = 200 / 72.0
        mat = pymupdf.Matrix(zoom, zoom)
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()

        img_b64 = base64.b64encode(img_bytes).decode("utf-8")

        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[{
                    "role": "user",
                    "parts": [
                        {"text": f"This is page {page_num + 1} of the PDF. " + REVIEW_PROMPT},
                        {"inline_data": {"mime_type": "image/png", "data": img_b64}}
                    ]
                }]
            )
            result_text = response.text.strip()
            if result_text.startswith("```"):
                lines = result_text.split("\n")
                result_text = "\n".join(lines[1:-1])
            issues = json.loads(result_text)
            if isinstance(issues, list):
                for issue in issues:
                    issue["page"] = page_num + 1
                all_issues.extend(issues)
        except json.JSONDecodeError:
            pass
        except Exception as e:
            all_issues.append({
                "page": page_num + 1,
                "severity": "low",
                "location": "N/A",
                "issue": f"Error: {str(e)}",
                "suggestion": "Check API key and network"
            })

    return all_issues


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python pdf_visual_review.py <pdf_path> [pages]")
        print("  pages: comma-separated page numbers (e.g., 5,6,8)")
        sys.exit(1)

    pdf_path = sys.argv[1]
    pages = sys.argv[2] if len(sys.argv) > 2 else ""

    print(f"PDF Visual Review: {pdf_path}", file=sys.stderr)
    issues = review_pdf(pdf_path, pages)

    if not issues:
        print("PASS: No layout issues detected.")
    else:
        print(f"ISSUES FOUND: {len(issues)}")
        for i in issues:
            sev = i.get("severity", "?")
            loc = i.get("location", "?")
            desc = i.get("issue", "?")
            fix = i.get("suggestion", "")
            print(f"  [{sev}] P{i['page']} {loc}: {desc}")
            if fix:
                print(f"         Fix: {fix}")
