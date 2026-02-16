import re
import os
import json
from pathlib import Path


def chunk_text_into_pages(text):
    """
    Chunk text file into pages based on page markers.
    Returns a list of dicts with page_number and content.
    """
    pattern = r'PageV(\d+)P(\d+)'
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    if not matches:
        print("No page markers found!")
        return [], []

    page_chunks = []
    page_markers_found = []

    for i, match in enumerate(matches):
        volume = match.group(1).zfill(2)
        page_num = match.group(2).zfill(3)
        page_number = f"V{volume}P{page_num}"

        line_num = text[:match.start()].count('\n') + 1
        page_markers_found.append(f"{page_number} at position {match.start()} (line ~{line_num})")

        # Content BEFORE this marker (back to end of previous marker)
        end_pos = match.start()
        start_pos = matches[i - 1].end() if i > 0 else 0

        content = text[start_pos:end_pos].strip()

        if content:
            page_chunks.append({
                'page_number': page_number,
                'content': content
            })

    # Handle content AFTER the last marker as page (last_page_num + 1)
    last_match = matches[-1]
    last_volume = last_match.group(1).zfill(2)
    last_page_num = int(last_match.group(2)) + 1
    last_page_number = f"V{last_volume}P{str(last_page_num).zfill(3)}"
    trailing_content = text[last_match.end():].strip()
    if trailing_content:
        page_chunks.append({
            'page_number': last_page_number,
            'content': trailing_content
        })

    return page_chunks, page_markers_found


def normalize_line(line):
    """Join continuation lines marked with ~~ and strip leading # markers."""
    # Remove leading # and whitespace
    line = re.sub(r'^#+\s*', '', line)
    return line.strip()


def parse_page_content(content):
    """
    Parse a page's raw content into a list of paragraph strings.
    - Joins ~~ continuation lines
    - Splits on # paragraph markers
    - Strips HTML span tags to extract matn vs syarh
    """
    # Join continuation lines: if a line ends or next starts with ~~, join them
    # First, normalize line endings
    raw = content.replace('\r\n', '\n').replace('\r', '\n')

    # Split into paragraph blocks by lines starting with #
    # Each block is separated by lines beginning with #
    # We'll reconstruct paragraphs by joining ~~ continuations first
    lines = raw.split('\n')

    paragraphs = []
    current_para_lines = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        if stripped.startswith('~~'):
            # Continuation of previous line
            if current_para_lines:
                current_para_lines.append(stripped.lstrip('~~').strip())
            else:
                current_para_lines.append(stripped.lstrip('~~').strip())
        elif stripped.startswith('#'):
            # New paragraph marker — save previous paragraph
            if current_para_lines:
                paragraphs.append(' '.join(current_para_lines))
            # Start new paragraph, stripping the leading #
            new_line = re.sub(r'^#+\s*', '', stripped).strip()
            if new_line:
                current_para_lines = [new_line]
            else:
                current_para_lines = []
        else:
            # Plain line (no # or ~~)
            if current_para_lines:
                current_para_lines.append(stripped)
            else:
                current_para_lines = [stripped]

    # Don't forget the last paragraph
    if current_para_lines:
        paragraphs.append(' '.join(current_para_lines))

    return paragraphs


def extract_matn_syarh(paragraph):
    """
    Given a paragraph string (possibly containing HTML span tags),
    extract matn and syarh portions.

    Matn is inside <span class="matn">...</span>
    Syarh is everything outside those spans (after stripping the matn-hr span).
    Returns (matn, syarh) tuple — either may be empty string.
    """
    # Extract all matn spans
    matn_pattern = r'<span\s+class=["\']matn["\']>(.*?)</span>'
    matn_matches = re.findall(matn_pattern, paragraph, re.IGNORECASE | re.DOTALL)
    matn_text = ' '.join(m.strip() for m in matn_matches).strip()

    # Remove matn spans and matn-hr spans to get syarh
    syarh = re.sub(r'<span\s+class=["\']matn["\']>.*?</span>', '', paragraph, flags=re.IGNORECASE | re.DOTALL)
    syarh = re.sub(r'<span\s+class=["\']matn-hr["\']>.*?</span>', '', syarh, flags=re.IGNORECASE | re.DOTALL)
    syarh = syarh.strip()

    return matn_text, syarh


def page_number_to_doc_id(page_number):
    """
    Convert page_number like 'V01P032' to doc_id like 'FM_01_032'.
    """
    match = re.match(r'V(\d+)P(\d+)', page_number)
    if match:
        vol = match.group(1).zfill(2)
        page = match.group(2).zfill(3)
        return f"FM_{vol}_{page}"
    return f"FM_{page_number}"


def pages_to_json(pages):
    """
    Convert list of page dicts into JSON-ready list of dicts
    with doc_id, matn, syarh.
    """
    records = []

    for page in pages:
        # Skip OpenITI metadata header pages
        if 'META#' in page['content'] or 'OpenITI#' in page['content']:
            print(f"  Skipping metadata page: {page['page_number']}")
            continue

        doc_id = page_number_to_doc_id(page['page_number'])
        paragraphs = parse_page_content(page['content'])

        if not paragraphs:
            print(f"  Skipping empty page: {page['page_number']}")
            continue

        # Check if any paragraph has matn spans
        has_matn_spans = any(
            re.search(r'<span\s+class=["\']matn["\']>', p, re.IGNORECASE)
            for p in paragraphs
        )

        if has_matn_spans:
            full_content = ' '.join(paragraphs)
            matn, syarh = extract_matn_syarh(full_content)
        else:
            matn = paragraphs[0]
            syarh = ' '.join(paragraphs[1:]).strip() if len(paragraphs) > 1 else ""

        # Skip artifact-only records: short matn with no syarh
        # (e.g. bare page refs like "ms361", "end", lone numbers)
        if not syarh and re.fullmatch(r'[a-zA-Z]{0,3}\d+', matn.strip()):
            print(f"  Skipping artifact page: {page['page_number']} (matn='{matn}')")
            continue

        # Skip completely empty records
        if not matn and not syarh:
            print(f"  Skipping empty record: {page['page_number']}")
            continue

        records.append({
            "doc_id": doc_id,
            "matn": matn,
            "syarh": syarh
        })

    return records


def process_file(input_file, output_file='data.json'):
    """
    Process a text file and output a JSON file with doc_id, matn, syarh.
    """
    print(f"Reading file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print("Processing pages...")
    pages, markers = chunk_text_into_pages(text)

    print(f"\nFound {len(markers)} page markers:")
    for marker in markers[:10]:
        print(f"  - {marker}")
    if len(markers) > 10:
        print(f"  ... and {len(markers) - 10} more")

    print(f"\nCreated {len(pages)} pages")

    if len(pages) == 0:
        print("\nNo pages created. Showing first 500 characters of file:")
        print(text[:500])
        return []

    records = pages_to_json(pages)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

    print(f"\nSaved {len(records)} records to '{output_file}'")
    return records


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python page_chunker.py <input_file> [output.json]")
        print("Example: python page_chunker.py input.txt data.json")
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'data.json'

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)

    try:
        process_file(input_file, output_file)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)