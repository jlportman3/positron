#!/usr/bin/env python3
"""
Extract detailed, structured knowledge from GAM documentation
Focuses on API endpoints, CLI commands, SNMP OIDs, and configuration details
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Set

KNOWLEDGE_DIR = Path("knowledge_extracted")
OUTPUT_DIR = Path("memory-bank")


def extract_api_details(json_path: Path) -> Dict:
    """Extract detailed API information from JSON API guide"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    full_text = "\n".join([chunk.get("content", "") for chunk in chunks])

    api_info = {
        "endpoints": [],
        "methods": [],
        "authentication": [],
        "examples": []
    }

    # Extract JSON-RPC method calls
    # Pattern: {"method": "something", ...}
    method_pattern = r'"method"\s*:\s*"([^"]+)"'
    methods = re.findall(method_pattern, full_text)
    api_info["methods"] = list(set(methods))

    # Extract authentication info
    if "username" in full_text.lower() or "password" in full_text.lower():
        auth_section = []
        for line in full_text.split('\n'):
            if 'username' in line.lower() or 'password' in line.lower() or 'auth' in line.lower():
                auth_section.append(line.strip())
        api_info["authentication"] = auth_section[:20]

    # Extract code examples (JSON blocks)
    json_blocks = re.findall(r'\{[^{}]*"method"[^{}]*\}', full_text, re.DOTALL)
    api_info["examples"] = json_blocks[:10]

    return api_info


def extract_cli_commands(json_path: Path) -> Dict:
    """Extract CLI command structure from CLI guide"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    full_text = "\n".join([chunk.get("content", "") for chunk in chunks])

    cli_info = {
        "show_commands": set(),
        "set_commands": set(),
        "configure_commands": set(),
        "ghn_commands": set(),
        "vlan_commands": set(),
        "network_commands": set()
    }

    lines = full_text.split('\n')
    for line in lines:
        line = line.strip()

        # Show commands
        if line.startswith('show '):
            cli_info["show_commands"].add(line[:100])

        # Set commands
        if line.startswith('set '):
            cli_info["set_commands"].add(line[:100])

        # Configure commands
        if line.startswith('configure ') or 'configure' in line.lower():
            cli_info["configure_commands"].add(line[:100])

        # G.hn specific
        if 'ghn' in line.lower() or 'g.hn' in line.lower():
            cli_info["ghn_commands"].add(line[:100])

        # VLAN commands
        if 'vlan' in line.lower():
            cli_info["vlan_commands"].add(line[:100])

        # Network commands
        if any(keyword in line.lower() for keyword in ['ip', 'ipv6', 'dhcp', 'dns', 'gateway']):
            cli_info["network_commands"].add(line[:100])

    # Convert sets to sorted lists and limit
    for key in cli_info:
        cli_info[key] = sorted(list(cli_info[key]))[:30]

    return cli_info


def extract_installation_info(json_path: Path) -> Dict:
    """Extract installation and configuration details"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    full_text = "\n".join([chunk.get("content", "") for chunk in chunks])

    install_info = {
        "default_settings": {},
        "ip_addresses": set(),
        "vlans": set(),
        "ports": set(),
        "requirements": []
    }

    # Extract default IP addresses
    ip_pattern = r'(?:default|management).*?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
    ips = re.findall(ip_pattern, full_text, re.IGNORECASE)
    install_info["ip_addresses"] = list(set(ips))

    # Extract VLAN information
    vlan_pattern = r'VLAN\s*(?:ID)?[:\s]*(\d+)'
    vlans = re.findall(vlan_pattern, full_text, re.IGNORECASE)
    install_info["vlans"] = list(set(vlans))

    # Extract port numbers
    port_pattern = r'Port[:\s]*(\d+)'
    ports = re.findall(port_pattern, full_text, re.IGNORECASE)
    install_info["ports"] = list(set(ports))

    # Extract requirements
    for line in full_text.split('\n'):
        if any(keyword in line.lower() for keyword in ['require', 'prerequisite', 'must', 'need']):
            if len(line.strip()) > 20 and len(line.strip()) < 200:
                install_info["requirements"].append(line.strip())

    install_info["requirements"] = install_info["requirements"][:20]

    return install_info


def extract_model_specifications(json_path: Path) -> Dict:
    """Extract GAM model specifications"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    chunks = data.get("chunks", [])
    full_text = "\n".join([chunk.get("content", "") for chunk in chunks])

    specs = {
        "models": {},
        "port_counts": {},
        "technologies": set(),
        "distances": []
    }

    # Extract model numbers
    model_pattern = r'GAM-(\d+)-([MC]X?R?X?)'
    models = re.findall(model_pattern, full_text)

    for port_count, tech in models:
        model_name = f"GAM-{port_count}-{tech}"
        if model_name not in specs["models"]:
            specs["models"][model_name] = {
                "ports": port_count,
                "technology": "Copper" if tech.startswith('M') else "Coax"
            }

    # Extract distance specifications
    distance_pattern = r'(\d+)\s*(?:meters|feet|m|ft)'
    distances = re.findall(distance_pattern, full_text, re.IGNORECASE)
    specs["distances"] = list(set(distances))

    # Extract technologies
    tech_keywords = ['G.hn', 'MIMO', 'SISO', 'QAM', 'IPTV', 'IGMP']
    for keyword in tech_keywords:
        if keyword.lower() in full_text.lower():
            specs["technologies"].add(keyword)

    specs["technologies"] = list(specs["technologies"])

    return specs


def create_detailed_markdown(all_details: Dict) -> str:
    """Create detailed markdown knowledge base"""

    md = "# GAM Technical Knowledge Base\n\n"
    md += "Detailed technical reference extracted from Positron GAM documentation\n\n"
    md += "---\n\n"

    # API Details
    if "api" in all_details:
        api = all_details["api"]
        md += "## JSON-RPC API Reference\n\n"

        if api.get("methods"):
            md += "### Available Methods\n\n"
            md += "```\n"
            for method in sorted(api["methods"])[:50]:
                md += f"{method}\n"
            md += "```\n\n"

        if api.get("examples"):
            md += "### Example API Calls\n\n"
            md += "```json\n"
            for example in api["examples"][:5]:
                md += f"{example}\n\n"
            md += "```\n\n"

    # CLI Commands
    if "cli" in all_details:
        cli = all_details["cli"]
        md += "## CLI Command Reference\n\n"

        for cmd_type, commands in cli.items():
            if commands and len(commands) > 0:
                md += f"### {cmd_type.replace('_', ' ').title()}\n\n"
                md += "```\n"
                for cmd in commands[:20]:
                    md += f"{cmd}\n"
                md += "```\n\n"

    # Installation Details
    if "installation" in all_details:
        install = all_details["installation"]
        md += "## Installation & Configuration\n\n"

        if install.get("ip_addresses"):
            md += "### Default IP Addresses\n\n"
            for ip in install["ip_addresses"][:10]:
                md += f"- {ip}\n"
            md += "\n"

        if install.get("vlans"):
            md += "### VLANs Referenced\n\n"
            for vlan in sorted(install["vlans"])[:20]:
                md += f"- VLAN {vlan}\n"
            md += "\n"

        if install.get("requirements"):
            md += "### Requirements\n\n"
            for req in install["requirements"][:15]:
                md += f"- {req}\n"
            md += "\n"

    # Model Specifications
    if "specifications" in all_details:
        specs = all_details["specifications"]
        md += "## GAM Device Models\n\n"

        if specs.get("models"):
            md += "### Supported Models\n\n"
            md += "| Model | Ports | Technology |\n"
            md += "|-------|-------|------------|\n"
            for model, details in sorted(specs["models"].items()):
                md += f"| {model} | {details['ports']} | {details['technology']} |\n"
            md += "\n"

        if specs.get("technologies"):
            md += "### Technologies\n\n"
            for tech in specs["technologies"]:
                md += f"- {tech}\n"
            md += "\n"

        if specs.get("distances"):
            md += "### Distance Specifications\n\n"
            md += f"Common distances mentioned: {', '.join(sorted(set(specs['distances']))[:15])}\n\n"

    return md


def main():
    """Main extraction function"""

    all_details = {}

    # Extract API details
    api_file = KNOWLEDGE_DIR / "PAS_-_GAM_Json_API.json"
    if api_file.exists():
        print("Extracting API details...")
        all_details["api"] = extract_api_details(api_file)
        print(f"  ✓ Found {len(all_details['api']['methods'])} API methods")

    # Extract CLI details
    cli_file = KNOWLEDGE_DIR / "PAS_-_GAM_CLI_guide.json"
    if cli_file.exists():
        print("Extracting CLI commands...")
        all_details["cli"] = extract_cli_commands(cli_file)
        total_commands = sum(len(v) for v in all_details["cli"].values())
        print(f"  ✓ Found {total_commands} CLI commands")

    # Extract installation details
    install_file = KNOWLEDGE_DIR / "PAS_-_GAM-Installation_and_Activation_Guide-180-0186-001-R03.json"
    if install_file.exists():
        print("Extracting installation details...")
        all_details["installation"] = extract_installation_info(install_file)
        print(f"  ✓ Found {len(all_details['installation']['ip_addresses'])} IPs, "
              f"{len(all_details['installation']['vlans'])} VLANs")

    # Extract model specifications
    quickstart_file = KNOWLEDGE_DIR / "PAS_-_GAM_quick_start_guide.json"
    if quickstart_file.exists():
        print("Extracting model specifications...")
        all_details["specifications"] = extract_model_specifications(quickstart_file)
        print(f"  ✓ Found {len(all_details['specifications']['models'])} device models")

    # Create detailed markdown
    print("\nGenerating detailed knowledge base...")
    markdown = create_detailed_markdown(all_details)

    output_file = OUTPUT_DIR / "gam_technical_reference.md"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(markdown)

    print(f"✓ Detailed reference saved to: {output_file}")


if __name__ == "__main__":
    main()
