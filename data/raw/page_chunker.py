import re
import os
from pathlib import Path

file_name = 'fath_muin_no_dupe.txt'


def chunk_text_into_pages(text):
    """
    Chunk text so that content between Page markers
    belongs to the *next* page marker.
    """
    pattern = r'PageV(\d+)P(\d+)'
    matches = list(re.finditer(pattern, text, re.IGNORECASE))

    if len(matches) < 2:
        print("Not enough page markers found!")
        return [], []

    page_chunks = []
    page_markers_found = []

    for i in range(len(matches) - 1):
        current_marker = matches[i]
        next_marker = matches[i + 1]

        volume = next_marker.group(1).zfill(2)
        page_num = next_marker.group(2).zfill(3)
        page_number = f"V{volume}P{page_num}"

        line_num = text[:next_marker.start()].count('\n') + 1
        page_markers_found.append(
            f"{page_number} starts at position {next_marker.start()} (line ~{line_num})"
        )

        content = text[current_marker.end():next_marker.start()].strip()

        if content:
            page_chunks.append({
                "page_number": page_number,
                "content": content
            })

    return page_chunks, page_markers_found


def process_file(input_file, output_dir='pages'):
    """
    Process a text file and save each page as a separate file.
    """
    Path(output_dir).mkdir(parents=True, exist_ok=True)

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

    for page in pages:
        output_file = os.path.join(output_dir, f"Page_{page['page_number']}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page['content'])
        print(f"Saved: {output_file} ({len(page['content'])} characters)")

    print(f"\nAll pages saved to '{output_dir}/' directory")
    return pages


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python page_chunker.py <input_file> [output_dir]")
        print("Example: python page_chunker.py input.txt pages")
        sys.exit(1)

    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'pages'

    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)

    try:
        process_file(input_file, output_dir)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
