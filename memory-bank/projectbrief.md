# Project Brief: Positron GAM Management System

## Core Requirements

Build an open-source, self-hosted management system for Positron GAM (G.hn Access Multiplexer) equipment that replaces VIRTUOSO's paid management features and integrates with Sonar and Splynx billing systems.

## Problem Statement

Positron charges separately for VIRTUOSO Domain Controller which provides:
- Zero-touch provisioning
- Centralized device management  
- OSS/BSS integration
- Subscriber workflow automation

The user wants to avoid these costs while managing 11-50 GAM units in a medium-scale ISP deployment.

## Solution Goals

1. **Replace VIRTUOSO**: Create open-source alternative to paid management platform
2. **Billing Integration**: Two-way sync with both Sonar and Splynx (equally important)
3. **Subscriber Management**: Complete subscriber lifecycle management
4. **Automated Provisioning**: Zero-touch subscriber service provisioning
5. **Centralized Monitoring**: Real-time device health and performance monitoring

## Scope and Scale

- **Device Count**: 11-50 GAM units (medium deployment)
- **Deployment**: New deployment (not yet in production) - greenfield opportunity
- **Multi-tenant**: Not initially required, but planned for future
- **Priority Features**: 
  1. Sonar/Splynx integration
  2. Subscriber management
  3. Provisioning automation

## Success Criteria

- Manage 11-50 GAM devices from single interface
- Seamless integration with both Sonar and Splynx billing systems
- Automated subscriber provisioning and service management
- Cost savings by avoiding VIRTUOSO licensing
- Easy deployment and updates via Docker containers

## Constraints

- Must avoid conflicts with existing Docker applications on server
- User has GAM hardware available for testing
- Both Sonar and Splynx integration equally important
- Docker deployment preferred for easy updates
