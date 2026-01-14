# SSH Login Credentials Support - Implementation Complete

## Summary

Successfully added SSH login credential storage to GAM devices to enable CLI-based device management and accurate CPE discovery.

## Database Changes

### New Columns Added to `gam_devices` Table

| Column Name | Type | Nullable | Default | Description |
|------------|------|----------|---------|-------------|
| `ssh_username` | VARCHAR(100) | Yes | NULL | SSH username for CLI access |
| `ssh_password` | VARCHAR(255) | Yes | NULL | SSH password (should be encrypted in production) |
| `ssh_port` | INTEGER | No | 22 | SSH port number |

**Note**: The existing `ssh_credentials` JSONB column remains for backward compatibility.

### Migration Applied

**File**: `backend/alembic/versions/20251021_1754_6031547f8dde_add_ssh_login_fields_to_gam_devices.py`

**Changes**:
- Added `ssh_username` column (nullable)
- Added `ssh_password` column (nullable)
- Added `ssh_port` column (not null, default 22)

## Model Updates

### GAMDevice Model ([backend/app/models/gam.py](backend/app/models/gam.py#L49-L55))

```python
# Connection settings
snmp_community = Column(String(100), nullable=False, default="public")
ssh_credentials = Column(JSONB, nullable=True)  # Store encrypted credentials (legacy)
ssh_username = Column(String(100), nullable=True)  # SSH username for CLI access
ssh_password = Column(String(255), nullable=True)  # SSH password (should be encrypted in production)
ssh_port = Column(Integer, nullable=False, default=22)  # SSH port
management_vlan = Column(Integer, nullable=False, default=4093)
```

## API Schema Updates

### GAMDeviceCreate Schema

Added SSH fields for device creation:
```python
class GAMDeviceCreate(BaseModel):
    name: str
    ip_address: str
    model: str
    snmp_community: Optional[str] = None
    ssh_username: Optional[str] = None  # NEW
    ssh_password: Optional[str] = None  # NEW
    ssh_port: Optional[int] = 22        # NEW
    location: Optional[str] = None
    management_vlan: Optional[int] = None
```

### GAMDeviceUpdate Schema

Added SSH fields for device updates:
```python
class GAMDeviceUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    status: Optional[DeviceStatus] = None
    snmp_community: Optional[str] = None
    ssh_username: Optional[str] = None  # NEW
    ssh_password: Optional[str] = None  # NEW
    ssh_port: Optional[int] = None      # NEW
```

### GAMDeviceResponse Schema

Added SSH username and port to response (password excluded for security):
```python
class GAMDeviceResponse(BaseModel):
    id: UUID
    name: str
    ip_address: str
    model: str
    status: DeviceStatus
    location: Optional[str]
    firmware_version: Optional[str]
    uptime: Optional[int]
    cpu_usage: Optional[int]
    memory_usage: Optional[int]
    ssh_username: Optional[str]  # NEW - visible in API response
    ssh_port: Optional[int]      # NEW - visible in API response
```

**Security Note**: The `ssh_password` field is deliberately excluded from the response schema to prevent credential leakage.

## Service Layer Updates

### GAMManager.create_device() Method

Updated to accept and store SSH credentials:
```python
async def create_device(
    self,
    name: str,
    ip_address: str,
    model: str,
    snmp_community: Optional[str] = None,
    ssh_credentials: Optional[Dict] = None,
    ssh_username: Optional[str] = None,    # NEW
    ssh_password: Optional[str] = None,    # NEW
    ssh_port: Optional[int] = None,        # NEW
    location: Optional[str] = None,
    management_vlan: Optional[int] = None,
    mac_address: Optional[str] = None,
    firmware_version: Optional[str] = None,
    serial_number: Optional[str] = None
) -> GAMDevice
```

## Current Device Configuration

The existing GAM device has been updated with SSH credentials:

```
Device: GAM-10.0.99.61 (10.0.99.61)
SSH Username: admin
SSH Port: 22
SSH Password: (stored in database, not shown)
```

## Security Considerations

### Current Implementation (Development)

⚠️ **IMPORTANT**: The current implementation stores SSH passwords in **plain text** in the database. This is acceptable for development/testing but **NOT suitable for production**.

### Production Recommendations

1. **Encrypt Passwords**: Use a proper encryption library (e.g., `cryptography` in Python)
   ```python
   from cryptography.fernet import Fernet

   # Generate encryption key (store securely, e.g., environment variable)
   key = Fernet.generate_key()
   cipher = Fernet(key)

   # Encrypt password before storing
   encrypted_password = cipher.encrypt(password.encode())

   # Decrypt when needed
   decrypted_password = cipher.decrypt(encrypted_password).decode()
   ```

2. **Use SSH Keys Instead**: Prefer SSH key-based authentication over passwords
   - Store public key on GAM devices
   - Store private key securely (encrypted, restricted permissions)
   - More secure and eliminates password storage

3. **Secrets Management**: Use dedicated secrets management solutions
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault
   - Environment variables with restricted access

4. **Access Control**: Implement role-based access control (RBAC)
   - Only authorized users can view/edit device credentials
   - Audit logging for credential access

## Next Steps

### 1. Implement SSH CLI Integration

Create methods in SSHClient to execute commands and parse output:

```python
# backend/app/utils/ssh_client.py

async def execute_command(self, command: str) -> str:
    """Execute SSH command and return output"""
    pass

async def get_ghn_endpoints(self) -> List[Dict]:
    """Execute 'show ghn endpoint' and parse results"""
    output = await self.execute_command("show ghn endpoint")
    return self._parse_ghn_endpoint_output(output)

async def get_ghn_subscribers(self) -> List[Dict]:
    """Execute 'show ghn subscriber' and parse results"""
    output = await self.execute_command("show ghn subscriber")
    return self._parse_ghn_subscriber_output(output)
```

### 2. Update CPE Discovery Endpoint

Modify the `/devices/{device_id}/discovered-cpe` endpoint to use SSH instead of SNMP:

```python
@router.get("/devices/{device_id}/discovered-cpe")
async def get_discovered_cpe_via_cli(device_id: UUID, db: AsyncSession):
    device = await manager.get_device(device_id)

    # Use SSH CLI instead of SNMP
    ssh_client = SSHClient(
        ip_address=device.ip_address,
        username=device.ssh_username,
        password=device.ssh_password,
        port=device.ssh_port
    )

    # Get endpoints from device
    endpoints = await ssh_client.get_ghn_endpoints()

    # Compare against database
    # ... (same logic as before)
```

### 3. Create CLI Output Parsers

Parse Positron CLI command outputs:

```python
def _parse_ghn_endpoint_output(self, output: str) -> List[Dict]:
    """
    Parse 'show ghn endpoint' output

    Expected format:
    Endpoint ID   Name              MAC Address        Port
    -----------   ----              -----------        ----
    1             Positron_1C9508   00:0e:d8:1c:95:08  4
    """
    endpoints = []
    # Parse logic here
    return endpoints
```

### 4. Add Frontend SSH Credential Input

Update the "Add GAM Device" form to include SSH credentials:
- SSH Username field
- SSH Password field (masked input)
- SSH Port field (default 22)

### 5. Test SSH Connection

Create a test endpoint to verify SSH credentials:

```python
@router.post("/devices/{device_id}/test-ssh")
async def test_ssh_connection(device_id: UUID):
    """Test SSH connectivity and credentials"""
    device = await manager.get_device(device_id)

    ssh_client = SSHClient(
        ip_address=device.ip_address,
        username=device.ssh_username,
        password=device.ssh_password,
        port=device.ssh_port
    )

    try:
        result = await ssh_client.execute_command("show version")
        return {"success": True, "message": "SSH connection successful"}
    except Exception as e:
        return {"success": False, "error": str(e)}
```

## Testing

### Database Verification

```sql
-- Check SSH fields are populated
SELECT name, ip_address, ssh_username, ssh_port
FROM gam_devices;

-- Result:
-- name             | ip_address  | ssh_username | ssh_port
-- GAM-10.0.99.61   | 10.0.99.61  | admin        | 22
```

### API Verification

```bash
# GET device - SSH username visible, password hidden
curl http://10.0.60.38:8003/api/v1/gam/devices | jq

# Response includes:
{
  "ssh_username": "admin",
  "ssh_port": 22
  # ssh_password NOT included for security
}
```

## Files Modified

1. **backend/app/models/gam.py** - Added SSH credential columns to GAMDevice model
2. **backend/app/api/v1/gam.py** - Updated API schemas to include SSH fields
3. **backend/app/services/gam_manager.py** - Updated create_device() to accept SSH credentials
4. **backend/alembic/versions/20251021_1754_6031547f8dde_add_ssh_login_fields_to_gam_devices.py** - Database migration

## Conclusion

✅ **Database schema updated** with SSH login fields
✅ **API schemas updated** to accept/return SSH credentials (password excluded from responses)
✅ **GAM manager service** updated to handle SSH credentials
✅ **Existing device configured** with SSH username and port

**Next**: Implement SSH CLI command execution to enable accurate CPE discovery using `show ghn endpoint` command.
