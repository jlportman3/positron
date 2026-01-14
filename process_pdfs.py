#!/usr/bin/env python3
"""
PDF Processing and Knowledge Extraction Script
Processes GAM documentation PDFs and extracts key information
"""

import os
import json
from pathlib import Path
from typing import List, Dict
import PyPDF2

DOCS_DIR = Path("docs")
OUTPUT_DIR = Path("knowledge_extracted")
CHUNK_SIZE_PAGES = 10  # Process PDFs in 10-page chunks


def extract_pdf_metadata(pdf_path: Path) -> Dict:
    """Extract basic metadata from PDF"""
    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        return {
            "filename": pdf_path.name,
            "total_pages": len(reader.pages),
            "size_bytes": pdf_path.stat().st_size,
            "size_mb": round(pdf_path.stat().st_size / (1024 * 1024), 2)
        }


def extract_text_from_pdf(pdf_path: Path, start_page: int = 0, end_page: int = None) -> str:
    """Extract text from PDF pages"""
    text_content = []

    with open(pdf_path, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        total_pages = len(reader.pages)

        if end_page is None:
            end_page = total_pages
        else:
            end_page = min(end_page, total_pages)

        for page_num in range(start_page, end_page):
            try:
                page = reader.pages[page_num]
                text = page.extract_text()
                text_content.append(f"--- Page {page_num + 1} ---\n{text}\n")
            except Exception as e:
                text_content.append(f"--- Page {page_num + 1} (Error: {str(e)}) ---\n")

    return "\n".join(text_content)


def process_pdf_in_chunks(pdf_path: Path) -> List[Dict]:
    """Process a PDF file in chunks"""
    metadata = extract_pdf_metadata(pdf_path)
    total_pages = metadata["total_pages"]

    chunks = []
    for start_page in range(0, total_pages, CHUNK_SIZE_PAGES):
        end_page = min(start_page + CHUNK_SIZE_PAGES, total_pages)

        chunk_text = extract_text_from_pdf(pdf_path, start_page, end_page)

        chunks.append({
            "chunk_id": len(chunks) + 1,
            "pages": f"{start_page + 1}-{end_page}",
            "content": chunk_text
        })

    return {
        "metadata": metadata,
        "chunks": chunks
    }


def main():
    """Main processing function"""
    OUTPUT_DIR.mkdir(exist_ok=True)

    # Get all PDF files
    pdf_files = sorted(DOCS_DIR.glob("*.pdf"))

    print(f"Found {len(pdf_files)} PDF files to process\n")

    all_metadata = []

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        try:
            result = process_pdf_in_chunks(pdf_path)
            metadata = result["metadata"]
            chunks = result["chunks"]

            all_metadata.append(metadata)

            # Save chunks to individual files
            output_filename = pdf_path.stem.replace(" ", "_")
            output_file = OUTPUT_DIR / f"{output_filename}.json"

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, indent=2, ensure_ascii=False)

            print(f"  ✓ Extracted {len(chunks)} chunks ({metadata['total_pages']} pages, {metadata['size_mb']} MB)")
            print(f"  ✓ Saved to: {output_file}\n")

        except Exception as e:
            print(f"  ✗ Error processing {pdf_path.name}: {str(e)}\n")

    # Save summary
    summary_file = OUTPUT_DIR / "_summary.json"
    with open(summary_file, 'w', encoding='utf-8') as f:
        json.dump({
            "total_files": len(pdf_files),
            "files": all_metadata
        }, f, indent=2)

    print(f"\n✓ Processing complete! Summary saved to {summary_file}")


if __name__ == "__main__":
    main()
