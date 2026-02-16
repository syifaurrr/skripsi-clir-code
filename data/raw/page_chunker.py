

# import re
# import os
# from pathlib import Path

# def chunk_text_into_pages(text):
#     """
#     Chunk text file into pages based on page markers.
#     Returns a list of dictionaries with page_number and content.
#     """
#     lines = text.split('\n')
#     page_chunks = []
#     current_page = None
#     current_content = []
#     page_markers_found = []
    
#     for i, line in enumerate(lines):
#         # Match page markers like: # PageV01P031, #PageV01P031, etc.
#         page_match = re.match(r'^#\s*PageV(\d+)P(\d+)', line, re.IGNORECASE)
        
#         if page_match:
#             volume = page_match.group(1).zfill(2)
#             page = page_match.group(2).zfill(3)
#             page_markers_found.append(f"V{volume}P{page} at line {i + 1}")
            
#             # Save previous page if it exists
#             if current_page is not None and current_content:
#                 page_chunks.append({
#                     'page_number': current_page,
#                     'content': '\n'.join(current_content).strip()
#                 })
            
#             # Start new page
#             current_page = f"V{volume}P{page}"
#             current_content = []
#         else:
#             # Add line to current page content
#             if current_page is not None:
#                 current_content.append(line)
    
#     # Add the last page
#     if current_page is not None and current_content:
#         page_chunks.append({
#             'page_number': current_page,
#             'content': '\n'.join(current_content).strip()
#         })
    
#     return page_chunks, page_markers_found

# def process_file(input_file, output_dir='pages'):
#     """
#     Process a text file and save each page as a separate file.
    
#     Args:
#         input_file: Path to the input text file
#         output_dir: Directory to save the page files (default: 'pages')
#     """
#     # Create output directory if it doesn't exist
#     Path(output_dir).mkdir(parents=True, exist_ok=True)
    
#     # Read the input file
#     print(f"Reading file: {input_file}")
#     with open(input_file, 'r', encoding='utf-8') as f:
#         text = f.read()
    
#     # Chunk the text into pages
#     print("Processing pages...")
#     pages, markers = chunk_text_into_pages(text)
    
#     # Print debug information
#     print(f"\nFound {len(markers)} page markers:")
#     for marker in markers[:10]:  # Show first 10
#         print(f"  - {marker}")
#     if len(markers) > 10:
#         print(f"  ... and {len(markers) - 10} more")
    
#     print(f"\nCreated {len(pages)} pages")
    
#     # Save each page to a separate file
#     for page in pages:
#         output_file = os.path.join(output_dir, f"Page_{page['page_number']}.txt")
#         with open(output_file, 'w', encoding='utf-8') as f:
#             f.write(page['content'])
#         print(f"Saved: {output_file} ({len(page['content'])} characters)")
    
#     print(f"\nAll pages saved to '{output_dir}/' directory")
#     return pages

# if __name__ == "__main__":
#     import sys
    
#     # Check command line arguments
#     if len(sys.argv) < 2:
#         print("Usage: python page_chunker.py <input_file> [output_dir]")
#         print("Example: python page_chunker.py input.txt pages")
#         sys.exit(1)
    
#     input_file = sys.argv[1]
#     output_dir = sys.argv[2] if len(sys.argv) > 2 else 'pages'
    
#     # Check if input file exists
#     if not os.path.exists(input_file):
#         print(f"Error: File '{input_file}' not found!")
#         sys.exit(1)
    
#     # Process the file
#     try:
#         process_file(input_file, output_dir)
#     except Exception as e:
#         print(f"Error: {e}")
#         sys.exit(1)

import re
import os
from pathlib import Path

# file_name = '0987ZaynDinMalibari.FathMucin.cleaned.txt'
file_name = 'fath_muin_no_dupe.txt'

# def chunk_text_into_pages(text):
#     """
#     Chunk text file into pages based on page markers.
#     Page markers can appear anywhere in the text (beginning, middle, or end of lines).
#     Returns a list of dictionaries with page_number and content.
#     """
#     # Find all page markers with their positions
#     # Match PageV##P### anywhere in the text
#     pattern = r'PageV(\d+)P(\d+)'
#     matches = list(re.finditer(pattern, text, re.IGNORECASE))
    
#     if not matches:
#         print("No page markers found!")
#         return [], []
    
#     page_chunks = []
#     page_markers_found = []
    
#     # Process each page
#     for i, match in enumerate(matches):
#         volume = match.group(1).zfill(2)
#         page_num = match.group(2).zfill(3)
#         page_number = f"V{volume}P{page_num}"
        
#         # Calculate line number for debugging
#         line_num = text[:match.start()].count('\n') + 1
#         page_markers_found.append(f"{page_number} at position {match.start()} (line ~{line_num})")
        
#         # Get content from end of current marker to start of next marker
#         start_pos = match.end()
        
#         if i < len(matches) - 1:
#             # Not the last page - content until next marker
#             end_pos = matches[i + 1].start()
#         else:
#             # Last page - content until end of file
#             end_pos = len(text)
        
#         content = text[start_pos:end_pos].strip()
        
#         if content:  # Only add if there's content
#             page_chunks.append({
#                 'page_number': page_number,
#                 'content': content
#             })
    
#     return page_chunks, page_markers_found

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

        # Debug info
        line_num = text[:next_marker.start()].count('\n') + 1
        page_markers_found.append(
            f"{page_number} starts at position {next_marker.start()} (line ~{line_num})"
        )

        # Content BETWEEN current and next marker
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
    
    Args:
        input_file: Path to the input text file
        output_dir: Directory to save the page files (default: 'pages')
    """
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # Read the input file
    print(f"Reading file: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        text = f.read()
    
    # Chunk the text into pages
    print("Processing pages...")
    pages, markers = chunk_text_into_pages(text)
    
    # Print debug information
    print(f"\nFound {len(markers)} page markers:")
    for marker in markers[:10]:  # Show first 10
        print(f"  - {marker}")
    if len(markers) > 10:
        print(f"  ... and {len(markers) - 10} more")
    
    print(f"\nCreated {len(pages)} pages")
    
    if len(pages) == 0:
        print("\nNo pages created. Showing first 500 characters of file:")
        print(text[:500])
        return []
    
    # Save each page to a separate file
    for page in pages:
        output_file = os.path.join(output_dir, f"Page_{page['page_number']}.txt")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page['content'])
        print(f"Saved: {output_file} ({len(page['content'])} characters)")
    
    print(f"\nAll pages saved to '{output_dir}/' directory")
    return pages

if __name__ == "__main__":
    import sys
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print("Usage: python page_chunker.py <input_file> [output_dir]")
        print("Example: python page_chunker.py input.txt pages")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else 'pages'
    
    # Check if input file exists
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found!")
        sys.exit(1)
    
    # Process the file
    try:
        process_file(input_file, output_dir)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)