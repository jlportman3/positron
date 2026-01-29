# Alamo GAM Bug Reports

**Date:** 2026-01-29
**Tester:** Baron (manual UI testing)
**Build:** Current Docker deployment (port 3005/8005)

---

## Bug 1: Subscriber Export Format Incomplete
**Severity:** Medium
**Page:** Subscribers > Export
**Description:** Subscriber CSV export only includes 10 columns. Virtuoso exports 17+ fields including Port 2 VLAN, remapped VLAN, double tags, system name, GAM IP address, and NNI interface index.
**Expected:** Export should match Virtuoso format with all subscriber configuration fields.
**Status:** Open

## Bug 2: Bandwidth Plans — Global vs Per-Device (Question)
**Severity:** Info
**Page:** Bandwidths
**Description:** Question: are bandwidth plans global across all GAMs in Virtuoso?
**Answer:** Per-device in Virtuoso, but syncable across devices. Our implementation already matches this behavior.
**Status:** No change needed

## Bug 3: Bandwidth Export Returns More Plans Than Displayed
**Severity:** High
**Page:** Bandwidths > Export
**Description:** Exporting bandwidth plans returns more entries than what is displayed on the page. The export includes soft-deleted profiles that are filtered out of the list view. Additionally, export format may not match Virtuoso output (missing Systems list, downstream/upstream should be in Mbps).
**Expected:** Export should only include non-deleted profiles and match Virtuoso column format.
**Status:** Open

## Bug 4: Bandwidth Delete Button Greyed Out for Synced Plans
**Severity:** Medium
**Page:** Bandwidths
**Description:** After adding and syncing a bandwidth plan, the trash can (delete) icon is greyed out/disabled. Delete should only be disabled for Default plans and plans that have active subscribers assigned.
**Expected:** Delete enabled for user-created plans without subscribers, disabled for Default plans and plans with assigned subscribers.
**Status:** Open

## Bug 5: GAM Detail Page — Blank Firmware and Swap Version
**Severity:** Medium
**Page:** Device Detail (e.g., /devices/{id})
**Description:** Firmware and Swap Version fields are blank on the GAM detail page. Virtuoso displays both the active firmware version and the alternate/swap version from the device's dual firmware partitions.
**Expected:** Show software_version and swap_software_version populated from device sync.
**Status:** Open

## Bug 6: Endpoints Page — Many Blank Columns
**Severity:** Medium
**Page:** Endpoints (all columns enabled)
**Description:** When enabling all columns on the endpoints page, many columns show blank values: Description, ASY (hardware version), Revision, Serial, Configured Port, State, Ethernet Port 1/2, Max Bandwidth, Uptime, Groups.
**Expected:** Columns should display data from endpoint sync. Fields requiring detailed sync should show "—" rather than blank.
**Status:** Open

## Bug 7: Unprovisioned Endpoint — No Provision Mechanism
**Severity:** High
**Page:** Endpoint Detail (e.g., /endpoints/{id})
**Description:** When viewing an unprovisioned endpoint, there is no immediate mechanism to provision it. Suggestion: auto-fetch Splynx information, and if a customer and plan exist, display a "Provision" button to create the subscriber directly from the endpoint detail page.
**Expected:** Endpoint detail should show Splynx data (if available) and offer one-click provisioning. If no Splynx match, offer manual provision form.
**Status:** Open (Enhancement)

## Bug 8: Groups Page Not Displaying Groups
**Severity:** High
**Page:** Groups
**Description:** Previously added group(s) are not being displayed on the groups page despite having been created successfully.
**Expected:** All created groups should appear in the groups tree/list view.
**Status:** Open

## Bug 9: Timezone/NTP Update Fails
**Severity:** High
**Page:** Timezones & NTP
**Description:** Cannot set GAM timezone or NTP settings. Error: "Failed to update timezone settings. Check device connectivity."
**Expected:** Should successfully update timezone and NTP configuration on GAM devices via JSON-RPC.
**Status:** Open

## Bug 10: Firmware Versions Page — Blank Columns
**Severity:** Medium
**Page:** Firmware
**Description:** Firmware versions page shows many blank cells in the Model, Current Version, and Alternate Version columns.
**Expected:** Device firmware status should show product_class (Model), software_version (Current), and swap_software_version (Alternate) from device sync data.
**Status:** Open

## Bug 11: Firmware Operations Safety Concerns
**Severity:** Critical (Safety)
**Page:** Firmware
**Description:** Concern that firmware operations could brick a device. Need to review Virtuoso's firmware upgrade safeguards and implement matching protections.
**Virtuoso Safeguards Identified:**
1. Validate firmware matches device model (productClass)
2. Check device is reachable before upgrade
3. `noSwap` flag prevents auto-activation
4. "Download Only" mode available
5. Dual firmware partitions — rollback via swap activation
6. 45-second timeout on upload operations
7. Status tracking via software_upgrade_status field
**Status:** Documentation only — safeguards to be implemented with firmware upgrade feature

## Bug 12: Firmware Upload — "Field Required" Error
**Severity:** High
**Page:** Firmware > Upload
**Description:** When selecting all required firmware files (.mfip, .xml, .sha256, .sign) and clicking Upload, the error "Field required" appears. Previous fix (changing is_default from bool to str Form parameter) did not resolve the issue.
**Expected:** Firmware upload should succeed with selected files.
**Status:** Open

## Bug 13: Alamo GAM Application Upgrades
**Severity:** Info (Design Decision)
**Page:** System Info
**Description:** Uploading new application versions via the UI is not the desired approach. Instead, the system should contact an upgrade repository for application updates. This is about the Alamo GAM management application itself, NOT device firmware.
**Expected:** Repository-based upgrade method to be designed and implemented separately.
**Status:** Deferred — separate design needed

## Bug 14: License Tab — Missing Component Licenses
**Severity:** Low
**Page:** System Info > License tab
**Description:** License tab only shows a single license. Virtuoso displays all open-source component licenses (GPL, LGPL, Apache, MIT, BSD, etc.) for every dependency.
**Expected:** Show a table of all OSS components with their respective licenses, versions, and URLs.
**Status:** Open

## Bug 15: Certificates — Missing Features
**Severity:** Medium (Enhancement)
**Page:** System Info > Certificates tab
**Description:** Certificates management needs enhancement:
- System config should have a hostname field for public DNS name
- If public DNS exists, enable automatic Let's Encrypt certificate provisioning
- Support for nginx proxy or Netbird address for hosts on private (bogon) networks
- Netbird should be configurable with a setup key
**Expected:** Full certificate lifecycle management with auto-provisioning options.
**Status:** Deferred — separate plan needed (too large for bug fix round)

## Bug 16: Logs Page Too Sparse
**Severity:** Medium
**Page:** Logs
**Description:** The logs page is woefully terse, showing only hardcoded sample log entries. No real system log data is displayed. Virtuoso shows detailed logs including user actions, device communications (JSON-RPC calls/responses), system events, with level/source/date filtering and search.
**Expected:** Real log data with filtering by level, source, date range, and search capability.
**Status:** Open

## Bug 17: Users Page — Blank Device and RADIUS Columns
**Severity:** Low
**Page:** Users
**Description:** The Device and RADIUS columns on the Users page are blank for all users. Questions: (1) Are these columns appropriate for Alamo GAM users? (2) Can/should we push user accounts to GAM devices?
**Note:** Virtuoso stores 16 credential sets per device (one per privilege level) and pushes user credentials to GAMs.
**Status:** Open (columns display fix); User push to GAMs deferred

## Bug 18: Settings Terms & Conditions — No Default Boilerplate
**Severity:** Low
**Page:** Settings > Terms and Conditions
**Description:** The Terms and Conditions field is empty with no way to quickly populate it. Should offer an industry-standard boilerplate that can be loaded with one click when the field is empty.
**Expected:** "Load Default Template" button that populates with standard ISP/network management T&C (acceptable use, data privacy, session monitoring, password policy, unauthorized access, service availability, limitation of liability).
**Status:** Open

## Bug 19: User Timezone — Not a Dropdown
**Severity:** Low
**Page:** Users (create/edit dialog), Settings > Users
**Description:** Timezone field is a free-text input instead of a dropdown of valid IANA timezones.
**Expected:** Dropdown with valid IANA timezones, US timezones prioritized at top.
**Status:** Open

## Bug 20: Privilege Settings — All Hardcoded to Level 5
**Severity:** Medium
**Page:** Settings > Privileges
**Description:** The privilege/permissions configuration page appears to have all permissions hardcoded to level 5. Virtuoso has a detailed permission matrix with 8 sections (Monitoring, Services, Devices, Automation, Versions, Admin, Settings, Sessions) where each permission can be set to any level 1-15.
**Expected:** Per-feature privilege levels stored in database, configurable via dropdowns (1-15).
**Status:** Open

## Bug 21: SMTP Settings — Missing Auth Toggle and Test Function
**Severity:** Medium
**Page:** Settings > SMTP Server
**Description:** Three issues:
1. No checkbox to indicate whether authentication is required
2. Auth fields (username/password) always shown even when auth is not needed
3. No test function to verify SMTP configuration
**Expected:** (1) "Requires Authentication" checkbox, (2) hide auth fields when unchecked, (3) "Send Test Email" button with recipient input.
**Status:** Open

---

## Summary

| # | Bug | Severity | Status |
|---|-----|----------|--------|
| 1 | Subscriber export incomplete | Medium | Open |
| 2 | Bandwidth global vs per-device | Info | No change needed |
| 3 | Bandwidth export includes deleted | High | Open |
| 4 | Bandwidth delete greyed out | Medium | Open |
| 5 | Device detail blank firmware | Medium | Open |
| 6 | Endpoints blank columns | Medium | Open |
| 7 | No endpoint provision mechanism | High | Open (Enhancement) |
| 8 | Groups not displayed | High | Open |
| 9 | Timezone/NTP update fails | High | Open |
| 10 | Firmware page blank columns | Medium | Open |
| 11 | Firmware safety concerns | Critical | Documentation only |
| 12 | Firmware upload field required | High | Open |
| 13 | App upgrades via repository | Info | Deferred |
| 14 | Missing OSS licenses | Low | Open |
| 15 | Certificates features | Medium | Deferred |
| 16 | Logs page too sparse | Medium | Open |
| 17 | Users blank columns | Low | Open |
| 18 | Terms no boilerplate | Low | Open |
| 19 | Timezone not dropdown | Low | Open |
| 20 | Privileges hardcoded to 5 | Medium | Open |
| 21 | SMTP no auth toggle/test | Medium | Open |

**Total:** 21 items — 17 actionable, 4 deferred/no-change
**High/Critical:** 5 (Bugs 3, 7, 8, 9, 12 + safety documentation for 11)
