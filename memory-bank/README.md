# Memory Bank - GAM Documentation Knowledge Base

This directory contains extracted and processed knowledge from Positron GAM technical documentation.

## Contents

### 1. `gam_knowledge_for_development.md` ⭐ **START HERE**
**Most Important** - Comprehensive development reference covering:
- Device models and specifications (11 GAM models documented)
- Default network settings and VLAN configuration
- Management interfaces (JSON-RPC API, CLI, SNMP)
- Subscriber provisioning workflows
- IPTV/multicast configuration
- Security considerations
- Integration requirements for management system
- Development priorities and next steps

**Use this as your primary reference when building features.**

### 2. `gam_technical_reference.md`
Technical deep-dive with extracted details:
- 150+ CLI commands organized by category
- JSON-RPC API methods and examples
- Installation requirements and default settings
- Device model specifications table

### 3. `gam_documentation_summary.md`
Quick reference summary of all 12 PDF documents:
- Document organization by category
- Page counts and content previews
- Quick command/API endpoint counts per document

## Source Documentation

All knowledge extracted from 12 PDF files in `../docs/`:

| Document | Pages | Category | Key Content |
|----------|-------|----------|-------------|
| GAM CLI guide | 139 | Reference | Complete CLI command reference |
| GAM-Installation and Activation Guide | 90 | Setup | Installation procedures, default config |
| GAM Json API | 66 | Integration | JSON-RPC API documentation |
| GAM quick start guide | 36 | Getting Started | Overview, quick setup |
| GAM IGMP snooping guide | 10 | Configuration | IPTV multicast setup |
| GAM Software upgrade procedure | 10 | Maintenance | Firmware upgrade steps |
| GAM VLAN configuration guide | 8 | Configuration | VLAN best practices |
| GAM Basic Troubleshooting Guide | 9 | Support | Common issues and fixes |
| Others (6 documents) | 18 | Various | Coax mixing, power, SFP adapters, etc. |

**Total:** 388 pages of documentation processed

## Processing Scripts

Located in project root:

- `process_pdfs.py` - Extracts text from PDFs into JSON chunks
- `analyze_pdfs.py` - Creates initial summary from extracted JSON
- `extract_detailed_knowledge.py` - Performs detailed analysis and creates technical reference

## Extracted Data

Raw extracted data in `../knowledge_extracted/` (12 JSON files):
- Each JSON contains document metadata, chunked content
- Chunks are 10 pages each for easier processing
- Total extracted: ~388 pages of text content

## Usage for Development

### When implementing new features:

1. **Start with** `gam_knowledge_for_development.md` - Sections 1-10 cover most common scenarios

2. **For specific CLI commands** → See `gam_technical_reference.md` CLI Command Reference section

3. **For API integration** → See `gam_technical_reference.md` JSON-RPC API Reference section

4. **For exact command syntax** → Reference the raw extracted JSON in `../knowledge_extracted/PAS_-_GAM_CLI_guide.json`

### Quick Lookups

**Default Settings:**
- Management IP: 192.168.1.1
- Management VLAN: 4093
- SNMP Community: public (default)
- JSON-RPC Port: 8080

**Key VLANs:**
- 1: Default untagged
- 100-4000: Subscriber VLANs (recommended range)
- 4093: Management VLAN
- 4094: Reserved/internal

**Model Naming:**
- M-series: Copper (Cat3/5) - 1 subscriber per port
- C-series: Coax (RG59/RG6) - up to 16 subscribers per port
- Numbers: 4, 8, 12, 24 = port count

## Next Steps

To continue knowledge extraction:

1. **API Method Discovery** - Test JSON-RPC API against live GAM to discover additional methods beyond the one documented
2. **SNMP MIB Analysis** - Request Positron MIB files or perform OID walk to document available SNMP OIDs
3. **Web UI Exploration** - Document web interface capabilities not covered in CLI/API docs
4. **Vendor Support** - Contact Positron for additional technical documentation (SNMP MIBs, advanced API docs)

## Regenerating Knowledge Base

If documentation is updated:

```bash
# Activate virtual environment
source .venv/bin/activate

# Re-extract from PDFs
python3 process_pdfs.py

# Re-analyze and create summaries
python3 analyze_pdfs.py

# Re-create technical reference
python3 extract_detailed_knowledge.py
```

---

**Last Updated:** 2025-10-21
**Documentation Version:** Based on PDFs dated 2020-2025
**Status:** Initial extraction complete, ready for development use
