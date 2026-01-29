# Alamo GAM -- Field Installation Procedure

This document provides step-by-step instructions for deploying the Alamo GAM system at a customer site and provisioning subscribers. Follow each step in order.

**What is Alamo GAM?** An open-source replacement for the Positron VIRTUOSO Domain Controller. It manages Positron GAM (G.hn Access Multiplexer) devices -- coax models (GAM-4-C, GAM-8-C, GAM-12-C, GAM-24-C) and MIMO copper models (GAM-4-M, GAM-8-M, GAM-12-M, GAM-24-M).

---

## Step 1: Configure Splynx FIRST

Before touching the GAM system, all subscriber records must exist in Splynx. The Alamo GAM controller pulls customer and service data from Splynx, so nothing will work if the billing side is not set up.

### 1.1 Create the Customer Account

1. Log into Splynx.
2. Navigate to **Customers > Add**.
3. Fill in the customer name, address, and contact information.
4. Save the account.

### 1.2 Set Up the Internet Service/Plan

1. Open the customer account.
2. Go to **Services > Internet > Add**.
3. Select the appropriate internet plan (e.g., 100 Mbps, 250 Mbps).
4. Set the start date and confirm billing details.
5. Save the service. Note the plan name -- you will need a matching bandwidth profile in Alamo GAM later.

### 1.3 Add the Endpoint Inventory Item

1. Navigate to **Inventory > Items > Add**.
2. Set the item type to the appropriate CPE/ONT model.
3. Enter the **MAC address** of the customer's endpoint device (printed on the device label). This MAC address is how Alamo GAM matches endpoints to Splynx records.
4. Save the inventory item.

### 1.4 Associate Inventory with the Customer Service

1. Open the customer's internet service.
2. Link the inventory item (CPE/ONT) to the service.
3. Verify the association is saved. The MAC address, customer, and plan should all be linked together in Splynx.

---

## Step 2: Deploy Alamo GAM

### 2.1 Requirements

- Linux server (Ubuntu 22.04+ recommended)
- Docker Engine 24+ and Docker Compose v2+
- Network connectivity to the GAM devices (layer 2 or routed)
- Ports available: **3005** (web UI), **8005** (backend API), **2223** (SSH tunnels)

### 2.2 Clone and Configure

```bash
git clone https://github.com/joeportman/positron.git /opt/alamogam
cd /opt/alamogam
```

Copy and edit the environment file:

```bash
cp backend/.env.example backend/.env
```

Edit `backend/.env` and set at minimum:

| Variable | Description | Example |
|----------|-------------|---------|
| `SECRET_KEY` | Random string, 32+ characters | `openssl rand -hex 32` |
| `DEBUG` | Set to `false` for production | `false` |
| `DEVICE_USERNAME` | Credentials GAM devices use to announce | `device` |
| `DEVICE_PASSWORD` | Credentials GAM devices use to announce | `device` |
| `BASE_URL` | Public URL of this server for device announcements | `http://192.168.1.100:8005` |

In `docker-compose.yml`, update `BASE_URL` under the backend environment to match the IP or hostname that GAM devices can reach.

### 2.3 Start the System

```bash
cd /opt/alamogam
docker compose up -d
```

Verify all four containers are running:

```bash
docker compose ps
```

Expected output:

```
alamogam_postgres   running (healthy)
alamogam_redis      running (healthy)
alamogam_backend    running
alamogam_frontend   running
```

### 2.4 Access the Web Interface

Open a browser and navigate to:

```
http://<server-ip>:3005
```

Default credentials:

| Field | Value |
|-------|-------|
| Username | `admin` |
| Password | `Senator+1234` |

**Change the default password immediately** after first login.

---

## Step 3: Initial System Configuration

After logging in, navigate to the **Settings** page to configure integrations.

### 3.1 General Settings

Go to **Settings > General** and configure:

- **Backup quantity** -- how many configuration backups to retain per device
- **Active thresholds** -- time before a device is considered offline (e.g., 5 minutes with no heartbeat)

### 3.2 Splynx Integration

Go to **Settings > Splynx** and enter:

| Field | Value |
|-------|-------|
| API URL | Your Splynx instance URL (e.g., `https://splynx.example.com/api/2.0`) |
| API Key | Splynx API key |
| API Secret | Splynx API secret |

Test the connection before saving. If the test fails, verify the API key has the required permissions in Splynx (read access to customers, services, and inventory).

### 3.3 SMTP (Email Alerts)

Go to **Settings > SMTP** and configure if you want email notifications for device alarms:

| Field | Example |
|-------|---------|
| SMTP Host | `smtp.gmail.com` |
| SMTP Port | `587` |
| Username | `alerts@example.com` |
| Password | App password |
| From Email | `alerts@example.com` |

### 3.4 RADIUS (If Applicable)

If your deployment uses RADIUS authentication, configure the RADIUS server settings under **Settings > RADIUS**.

---

## Step 4: GAM Device Onboarding

### 4.1 Physical Connection

1. Connect the GAM device's uplink port to the network switch with connectivity to the Alamo GAM server.
2. Power on the GAM device.
3. Ensure the GAM device has an IP address (DHCP or static) that can reach the Alamo GAM backend on port 8005.

### 4.2 Configure the GAM Announcement URL

Each GAM device must be told where to send its announcements. Using the GAM's local management interface (or CLI), set the announcement/discovery URL to:

```
http://<alamogam-server-ip>:8005
```

The device will send a `PUT /device/announcement/request` to the Alamo GAM backend with its identity information (serial number, model, MAC address, firmware version).

The device authenticates using Basic Auth with the `DEVICE_USERNAME` and `DEVICE_PASSWORD` configured in Step 2.2.

### 4.3 Verify Device Registration

1. Open the Alamo GAM web UI.
2. Navigate to the **Devices** page.
3. The GAM device should appear within 1-2 minutes of powering on.
4. Verify the model, serial number, and firmware version are correct.

### 4.4 Sync Device Data

After the device appears:

1. Click on the device to open its detail page.
2. Click **Sync** to pull the full configuration (ports, endpoints, subscribers) from the device.
3. Wait for the sync to complete. This may take 30-60 seconds depending on the number of connected endpoints.

---

## Step 5: Bandwidth Profile Setup

Bandwidth profiles define the speed tiers available on the GAM devices. These must match the plans configured in Splynx.

### 5.1 Create Profiles

1. Navigate to **Bandwidth Profiles**.
2. Click **Add Profile**.
3. Enter the profile name to match the Splynx plan name (e.g., "100Mbps", "250Mbps").
4. Set the downstream and upstream rates.
5. Save.

Repeat for each speed tier.

### 5.2 Push Profiles to Devices

1. Select the bandwidth profiles to deploy.
2. Click **Push to Device** and select the target GAM device(s).
3. Confirm the push. The profiles are sent to the GAM via JSON-RPC.

---

## Step 6: Subscriber Provisioning

### 6.1 Identify Unprovisioned Endpoints

1. Navigate to the **Endpoints** page.
2. After a GAM device syncs, all connected endpoints (CPE/ONT devices) appear here.
3. Unprovisioned endpoints are listed without a subscriber association.

### 6.2 Look Up the Endpoint in Splynx

1. Click on an unprovisioned endpoint.
2. The system will look up the endpoint's MAC address in Splynx.
3. If the MAC was added in Step 1.3, the matching customer and service are returned.

### 6.3 Create the Subscriber

1. From the lookup result, click **Create Subscriber**.
2. Configure the following:
   - **VLAN** -- the VLAN ID for this subscriber's traffic
   - **Bandwidth Profile** -- select the profile matching the customer's plan
   - **Endpoint association** -- should be pre-filled from the lookup
3. Save the subscriber.

### 6.4 Push Subscriber to Device

1. Click **Push to Device** to send the subscriber configuration to the GAM.
2. The system sends the VLAN assignment, bandwidth profile, and endpoint binding to the device via JSON-RPC.
3. Wait for confirmation that the push succeeded.

---

## Step 7: Verification

### 7.1 Endpoint Status

- Navigate to **Endpoints** and verify the provisioned endpoint shows as **Active**.
- Confirm the correct VLAN and bandwidth profile are displayed.

### 7.2 Bandwidth Verification

- From the endpoint detail page, confirm the downstream and upstream rates match the customer's plan.
- Run a speed test from the customer's device to validate throughput.

### 7.3 Customer Connectivity

- Have the customer browse the internet and confirm connectivity.
- Verify DHCP is assigning an IP from the correct pool for the subscriber's VLAN.

### 7.4 Dashboard Check

- Return to the **Dashboard** page.
- Verify no alarms are raised for the GAM device or the new subscriber.
- Confirm the device shows the correct number of active endpoints.

---

## Troubleshooting

### Device Not Appearing in Alamo GAM

| Check | How |
|-------|-----|
| Announcement URL correct? | Verify the GAM is configured to announce to `http://<server-ip>:8005` |
| Network connectivity? | From the GAM network, `curl http://<server-ip>:8005/health` should return a response |
| Firewall? | Ensure port 8005 (TCP) is open between the GAM and the server |
| Credentials? | The GAM must use the same `DEVICE_USERNAME`/`DEVICE_PASSWORD` as configured in the backend |
| Containers running? | Run `docker compose ps` and confirm the backend is healthy |

### Subscriber Push Failing

| Check | How |
|-------|-----|
| Device reachable via JSON-RPC? | The backend must be able to reach the GAM device's management IP on port 80/443 |
| Device credentials? | Verify the RPC credentials configured in Alamo GAM match the GAM device |
| Profile exists on device? | Ensure the bandwidth profile was pushed to the device before the subscriber |
| Check backend logs | `docker compose logs backend --tail 50` |

### Splynx Lookup Failing

| Check | How |
|-------|-----|
| API credentials valid? | Re-test the Splynx connection in **Settings > Splynx** |
| MAC address format? | Ensure the MAC in Splynx matches exactly (same format, no extra characters) |
| Inventory linked to service? | The inventory item must be associated with the customer's active service in Splynx |

### Viewing Logs

```bash
# All services
docker compose logs --tail 100

# Backend only
docker compose logs backend --tail 100 -f

# Database
docker compose logs postgres --tail 50
```

### Restarting Services

```bash
# Restart everything
docker compose restart

# Restart just the backend
docker compose restart backend
```

---

## Port Reference

| Port | Service | Purpose |
|------|---------|---------|
| 3005 | Frontend | Web UI |
| 8005 | Backend | API and device announcements |
| 2223 | Backend | SSH reverse tunnels from devices |
| 5437 | PostgreSQL | Database (internal, not needed externally) |
| 6381 | Redis | Cache (internal, not needed externally) |

---

## Quick Reference Card

```
1. Splynx: Customer > Service > Inventory (MAC) > Link
2. Deploy: git clone, docker compose up -d
3. Configure: Settings > Splynx credentials
4. Onboard: Set GAM announcement URL > device auto-registers
5. Profiles: Create bandwidth profiles > push to device
6. Provision: Endpoints page > Splynx lookup > create subscriber > push
7. Verify: Endpoint active, speed test, dashboard clear
```
