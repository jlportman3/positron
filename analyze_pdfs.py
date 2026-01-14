#!/usr/bin/env python3
"""
Analyze extracted PDF content and create knowledge summaries
"""

import json
import re
from pathlib import Path
from typing import Dict, List

KNOWLEDGE_DIR = Path("knowledge_extracted")
OUTPUT_FILE = Path("memory-bank/gam_documentation_summary.md")


def extract_key_sections(text: str, filename: str) -> Dict:
    """Extract key information based on document type"""

    sections = {
        "filename": filename,
        "key_concepts": [],
        "commands": [],
        "api_endpoints": [],
        "configuration": [],
        "troubleshooting": [],
        "specifications": []
    }

    # Extract CLI commands (lines starting with common command patterns)
    command_patterns = [
        r'^(ghn|show|set|get|configure|enable|disable)\s+.*$',
        r'^#\s*(ghn|show|set|get).*$'
    ]

    for line in text.split('\n'):
        line = line.strip()
        for pattern in command_patterns:
            if re.match(pattern, line, re.IGNORECASE):
                sections["commands"].append(line)
                break

    # Extract API endpoints (URLs and paths)
    api_patterns = [
        r'(GET|POST|PUT|DELETE|PATCH)\s+(/[\w/\-{}]+)',
        r'(https?://[^\s]+)',
        r'(/api/[\w/\-]+)'
    ]

    for pattern in api_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        sections["api_endpoints"].extend(matches)

    # Extract IP addresses, VLANs, ports (specifications)
    spec_patterns = [
        r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})',  # IP addresses
        r'VLAN\s*[:=]?\s*(\d+)',  # VLANs
        r'Port\s*[:=]?\s*(\d+)',  # Ports
        r'Speed\s*[:=]?\s*([\d\w\s/]+)',  # Speeds
        r'(GAM-\d+-[MC])',  # Model numbers
    ]

    for pattern in spec_patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        sections["specifications"].extend(matches)

    # Remove duplicates
    for key in sections:
        if isinstance(sections[key], list):
            sections[key] = list(set(sections[key]))[:50]  # Limit to 50 unique items

    return sections


def analyze_json_file(json_path: Path) -> Dict:
    """Analyze a single extracted JSON file"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    metadata = data.get("metadata", {})
    chunks = data.get("chunks", [])

    # Combine all chunk text
    full_text = "\n".join([chunk.get("content", "") for chunk in chunks])

    # Extract key sections
    key_info = extract_key_sections(full_text, metadata.get("filename", ""))

    # Add metadata
    key_info["total_pages"] = metadata.get("total_pages", 0)
    key_info["size_mb"] = metadata.get("size_mb", 0)

    # Extract document purpose from first 500 characters
    preview = full_text[:500].replace('\n', ' ')
    key_info["preview"] = ' '.join(preview.split())

    return key_info


def create_markdown_summary(all_analyses: List[Dict]) -> str:
    """Create a markdown summary document"""

    md = "# GAM Documentation Knowledge Base\n\n"
    md += "Auto-generated summary of Positron GAM documentation\n\n"
    md += "---\n\n"

    # Group by document type
    doc_groups = {
        "API & Integration": [],
        "CLI & Commands": [],
        "Installation & Setup": [],
        "Configuration": [],
        "Troubleshooting": [],
        "Other": []
    }

    for analysis in all_analyses:
        filename = analysis["filename"]

        if "API" in filename or "Json" in filename:
            doc_groups["API & Integration"].append(analysis)
        elif "CLI" in filename or "command" in filename.lower():
            doc_groups["CLI & Commands"].append(analysis)
        elif "Install" in filename or "Activation" in filename or "quick start" in filename.lower():
            doc_groups["Installation & Setup"].append(analysis)
        elif "VLAN" in filename or "config" in filename.lower():
            doc_groups["Configuration"].append(analysis)
        elif "Troubleshoot" in filename:
            doc_groups["Troubleshooting"].append(analysis)
        else:
            doc_groups["Other"].append(analysis)

    # Generate markdown for each group
    for group_name, docs in doc_groups.items():
        if not docs:
            continue

        md += f"## {group_name}\n\n"

        for doc in docs:
            md += f"### {doc['filename']} ({doc['total_pages']} pages)\n\n"

            if doc.get('preview'):
                md += f"**Overview:** {doc['preview'][:200]}...\n\n"

            if doc.get('commands') and len(doc['commands']) > 0:
                md += f"**Commands Found:** {len(doc['commands'])} unique commands\n"
                md += "```\n"
                for cmd in doc['commands'][:10]:  # Show first 10
                    md += f"{cmd}\n"
                if len(doc['commands']) > 10:
                    md += f"... and {len(doc['commands']) - 10} more\n"
                md += "```\n\n"

            if doc.get('api_endpoints') and len(doc['api_endpoints']) > 0:
                md += f"**API Endpoints:** {len(doc['api_endpoints'])} found\n"
                md += "```\n"
                for endpoint in doc['api_endpoints'][:10]:
                    md += f"{endpoint}\n"
                if len(doc['api_endpoints']) > 10:
                    md += f"... and {len(doc['api_endpoints']) - 10} more\n"
                md += "```\n\n"

            if doc.get('specifications') and len(doc['specifications']) > 0:
                md += f"**Key Specifications:** {', '.join(str(s) for s in doc['specifications'][:15])}\n\n"

            md += "---\n\n"

    return md


def main():
    """Main analysis function"""

    json_files = sorted(KNOWLEDGE_DIR.glob("*.json"))
    json_files = [f for f in json_files if f.name != "_summary.json"]

    print(f"Analyzing {len(json_files)} extracted JSON files...\n")

    all_analyses = []

    for json_file in json_files:
        print(f"Analyzing: {json_file.name}")
        try:
            analysis = analyze_json_file(json_file)
            all_analyses.append(analysis)
            print(f"  ✓ Found {len(analysis.get('commands', []))} commands, "
                  f"{len(analysis.get('api_endpoints', []))} API endpoints")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")

    # Create markdown summary
    print(f"\nGenerating markdown summary...")
    markdown = create_markdown_summary(all_analyses)

    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(exist_ok=True)

    # Write output
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✓ Summary saved to: {OUTPUT_FILE}")
    print(f"  Total documents analyzed: {len(all_analyses)}")


if __name__ == "__main__":
    main()
