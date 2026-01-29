"""
Device announcement endpoint.

This is the endpoint GAM devices call to register themselves.
PUT /device/announcement/request with Basic Auth (device:device)
"""
import logging
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, verify_device_auth
from app.models import Device, Alarm
from app.schemas.device import DeviceAnnouncement

logger = logging.getLogger(__name__)

router = APIRouter()


@router.put("/device/announcement/request")
async def device_announcement(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: bool = Depends(verify_device_auth),
):
    # Log raw body for debugging
    body = await request.body()
    logger.info(f"Raw announcement body: {body.decode('utf-8', errors='ignore')[:2000]}")

    # Parse JSON manually for more flexibility
    import json
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid JSON: {e}")

    # Build a case-insensitive lookup from raw data
    ci_data = {k.lower(): v for k, v in data.items()}

    def ci_get(*keys, default=None):
        for k in keys:
            if k.lower() in ci_data:
                val = ci_data[k.lower()]
                return str(val) if val is not None else default
        return default

    def ci_int(*keys, default=0):
        for k in keys:
            if k.lower() in ci_data:
                try:
                    return int(ci_data[k.lower()])
                except (TypeError, ValueError):
                    pass
        return default

    def ci_bool(*keys, default=False):
        for k in keys:
            if k.lower() in ci_data:
                val = ci_data[k.lower()]
                if isinstance(val, bool):
                    return val
                return str(val).lower() in ('true', '1', 'yes')
        return default

    announcement = DeviceAnnouncement(
        SerialNumber=ci_get('SerialNumber', 'SN', default=''),
        MACAddress=ci_get('MACAddress', 'MAC'),
        Name=ci_get('Name', 'hostname'),
        Vendor=ci_get('Vendor', 'Manufacturer'),
        ProductClass=ci_get('ProductClass', 'Model'),
        HardwareVersion=ci_get('HardwareVersion', 'HWVersion'),
        Compatible=ci_get('Compatible'),
        UNIPorts=ci_get('UNIPorts', 'Ports'),
        CLEICode=ci_get('CLEICode'),
        IPAddress=ci_get('IPAddress'),
        FQDN=ci_get('FQDN'),
        Proto=ci_get('Proto', 'protocol', default='http'),
        Port=ci_get('Port', default='80'),
        SoftwareVersion=ci_get('SoftwareVersion', 'FWVersion', 'Version'),
        SoftwareRevision=ci_get('SoftwareRevision'),
        SoftwareBuildDate=ci_get('SoftwareBuildDate'),
        Firmware=ci_get('Firmware'),
        FirmwareEncryptionKeyID=ci_get('FirmwareEncryptionKeyID'),
        SoftwareUpgradeStatus=ci_get('SoftwareUpgradeStatus'),
        SwapSoftwareVersion=ci_get('SwapSoftwareVersion'),
        SwapSoftwareRevision=ci_get('SwapSoftwareRevision'),
        SwapSoftwareBuildDate=ci_get('SwapSoftwareBuildDate'),
        AnnouncementPeriod=ci_get('AnnouncementPeriod'),
        AnnouncementURL=ci_get('AnnouncementURL'),
        UserName=ci_get('UserName', 'Username'),
        Password=ci_get('Password'),
        UserNameLevel0=ci_get('UserNameLevel0'),
        PasswordLevel0=ci_get('PasswordLevel0'),
        UserNameLevel1=ci_get('UserNameLevel1'),
        PasswordLevel1=ci_get('PasswordLevel1'),
        UserNameLevel2=ci_get('UserNameLevel2'),
        PasswordLevel2=ci_get('PasswordLevel2'),
        UserNameLevel3=ci_get('UserNameLevel3'),
        PasswordLevel3=ci_get('PasswordLevel3'),
        UserNameLevel4=ci_get('UserNameLevel4'),
        PasswordLevel4=ci_get('PasswordLevel4'),
        UserNameLevel5=ci_get('UserNameLevel5'),
        PasswordLevel5=ci_get('PasswordLevel5'),
        UserNameLevel6=ci_get('UserNameLevel6'),
        PasswordLevel6=ci_get('PasswordLevel6'),
        UserNameLevel7=ci_get('UserNameLevel7'),
        PasswordLevel7=ci_get('PasswordLevel7'),
        UserNameLevel8=ci_get('UserNameLevel8'),
        PasswordLevel8=ci_get('PasswordLevel8'),
        UserNameLevel9=ci_get('UserNameLevel9'),
        PasswordLevel9=ci_get('PasswordLevel9'),
        UserNameLevel10=ci_get('UserNameLevel10'),
        PasswordLevel10=ci_get('PasswordLevel10'),
        UserNameLevel11=ci_get('UserNameLevel11'),
        PasswordLevel11=ci_get('PasswordLevel11'),
        UserNameLevel12=ci_get('UserNameLevel12'),
        PasswordLevel12=ci_get('PasswordLevel12'),
        UserNameLevel13=ci_get('UserNameLevel13'),
        PasswordLevel13=ci_get('PasswordLevel13'),
        UserNameLevel14=ci_get('UserNameLevel14'),
        PasswordLevel14=ci_get('PasswordLevel14'),
        UserNameLevel15=ci_get('UserNameLevel15'),
        PasswordLevel15=ci_get('PasswordLevel15'),
        RemotePortTunnel=ci_int('RemotePortTunnel'),
        RemotePortTunnelIndex=ci_int('RemotePortTunnelIndex'),
        Virtual=ci_bool('Virtual'),
        Uptime=ci_int('Uptime', default=None),
        Location=ci_get('Location'),
        Contact=ci_get('Contact'),
    )

    logger.info(f"Parsed announcement: serial={announcement.SerialNumber}")
    """Handle device announcement from GAM devices.

    Devices call this endpoint periodically to announce themselves.
    If the device doesn't exist, it's created. If it exists, it's updated.
    """
    serial_number = announcement.SerialNumber

    if not serial_number:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="SerialNumber is required",
        )

    # Get client IP from request
    client_ip = announcement.IPAddress
    if not client_ip and request.client:
        client_ip = request.client.host

    logger.info(f"Device announcement from {serial_number} ({client_ip})")

    # Find existing device by serial number
    result = await db.execute(
        select(Device).where(Device.serial_number == serial_number)
    )
    device = result.scalar_one_or_none()

    now = datetime.utcnow()

    if device:
        # Update existing device
        device.mac_address = announcement.MACAddress or device.mac_address
        device.name = announcement.Name or device.name
        device.vendor = announcement.Vendor or device.vendor
        device.product_class = announcement.ProductClass or device.product_class
        device.hardware_version = announcement.HardwareVersion or device.hardware_version
        device.compatible = announcement.Compatible or device.compatible
        device.uni_ports = announcement.UNIPorts or device.uni_ports
        device.clei_code = announcement.CLEICode or device.clei_code

        # Network - always update IP
        device.ip_address = client_ip
        device.fqdn = announcement.FQDN or device.fqdn
        device.proto = announcement.Proto or device.proto
        device.port = announcement.Port or device.port

        # Software
        device.software_version = announcement.SoftwareVersion or device.software_version
        device.software_revision = announcement.SoftwareRevision or device.software_revision
        device.software_build_date = announcement.SoftwareBuildDate or device.software_build_date
        device.firmware = announcement.Firmware or device.firmware
        device.firmware_encryption_key_id = announcement.FirmwareEncryptionKeyID or device.firmware_encryption_key_id
        device.software_upgrade_status = announcement.SoftwareUpgradeStatus or device.software_upgrade_status

        # Swap partition
        device.swap_software_version = announcement.SwapSoftwareVersion or device.swap_software_version
        device.swap_software_revision = announcement.SwapSoftwareRevision or device.swap_software_revision
        device.swap_software_build_date = announcement.SwapSoftwareBuildDate or device.swap_software_build_date

        # Announcement settings
        device.announcement_period = announcement.AnnouncementPeriod or device.announcement_period
        device.announcement_url = announcement.AnnouncementURL or device.announcement_url

        # Credentials - update all levels
        device.user_name = announcement.UserName or device.user_name
        device.password = announcement.Password or device.password
        device.user_name_level0 = announcement.UserNameLevel0 or device.user_name_level0
        device.password_level0 = announcement.PasswordLevel0 or device.password_level0
        device.user_name_level1 = announcement.UserNameLevel1 or device.user_name_level1
        device.password_level1 = announcement.PasswordLevel1 or device.password_level1
        device.user_name_level2 = announcement.UserNameLevel2 or device.user_name_level2
        device.password_level2 = announcement.PasswordLevel2 or device.password_level2
        device.user_name_level3 = announcement.UserNameLevel3 or device.user_name_level3
        device.password_level3 = announcement.PasswordLevel3 or device.password_level3
        device.user_name_level4 = announcement.UserNameLevel4 or device.user_name_level4
        device.password_level4 = announcement.PasswordLevel4 or device.password_level4
        device.user_name_level5 = announcement.UserNameLevel5 or device.user_name_level5
        device.password_level5 = announcement.PasswordLevel5 or device.password_level5
        device.user_name_level6 = announcement.UserNameLevel6 or device.user_name_level6
        device.password_level6 = announcement.PasswordLevel6 or device.password_level6
        device.user_name_level7 = announcement.UserNameLevel7 or device.user_name_level7
        device.password_level7 = announcement.PasswordLevel7 or device.password_level7
        device.user_name_level8 = announcement.UserNameLevel8 or device.user_name_level8
        device.password_level8 = announcement.PasswordLevel8 or device.password_level8
        device.user_name_level9 = announcement.UserNameLevel9 or device.user_name_level9
        device.password_level9 = announcement.PasswordLevel9 or device.password_level9
        device.user_name_level10 = announcement.UserNameLevel10 or device.user_name_level10
        device.password_level10 = announcement.PasswordLevel10 or device.password_level10
        device.user_name_level11 = announcement.UserNameLevel11 or device.user_name_level11
        device.password_level11 = announcement.PasswordLevel11 or device.password_level11
        device.user_name_level12 = announcement.UserNameLevel12 or device.user_name_level12
        device.password_level12 = announcement.PasswordLevel12 or device.password_level12
        device.user_name_level13 = announcement.UserNameLevel13 or device.user_name_level13
        device.password_level13 = announcement.PasswordLevel13 or device.password_level13
        device.user_name_level14 = announcement.UserNameLevel14 or device.user_name_level14
        device.password_level14 = announcement.PasswordLevel14 or device.password_level14
        device.user_name_level15 = announcement.UserNameLevel15 or device.user_name_level15
        device.password_level15 = announcement.PasswordLevel15 or device.password_level15

        # SSH Tunnel
        if announcement.RemotePortTunnel:
            device.remote_port_tunnel = announcement.RemotePortTunnel
        if announcement.RemotePortTunnelIndex:
            device.remote_port_tunnel_index = announcement.RemotePortTunnelIndex

        # Status
        device.is_virtual = announcement.Virtual
        if announcement.Uptime is not None:
            device.uptime = announcement.Uptime
        device.location = announcement.Location or device.location
        device.contact = announcement.Contact or device.contact

        # Timestamps
        device.last_announcement = now
        device.last_seen = now
        device.is_online = True

        logger.info(f"Updated device {serial_number}")

    else:
        # Create new device
        device = Device(
            serial_number=serial_number,
            mac_address=announcement.MACAddress,
            name=announcement.Name,
            vendor=announcement.Vendor,
            product_class=announcement.ProductClass,
            hardware_version=announcement.HardwareVersion,
            compatible=announcement.Compatible,
            uni_ports=announcement.UNIPorts,
            clei_code=announcement.CLEICode,

            ip_address=client_ip,
            fqdn=announcement.FQDN,
            proto=announcement.Proto or "https",
            port=announcement.Port or "443",

            software_version=announcement.SoftwareVersion,
            software_revision=announcement.SoftwareRevision,
            software_build_date=announcement.SoftwareBuildDate,
            firmware=announcement.Firmware,
            firmware_encryption_key_id=announcement.FirmwareEncryptionKeyID,
            software_upgrade_status=announcement.SoftwareUpgradeStatus,

            swap_software_version=announcement.SwapSoftwareVersion,
            swap_software_revision=announcement.SwapSoftwareRevision,
            swap_software_build_date=announcement.SwapSoftwareBuildDate,

            announcement_period=announcement.AnnouncementPeriod,
            announcement_url=announcement.AnnouncementURL,

            user_name=announcement.UserName,
            password=announcement.Password,
            user_name_level0=announcement.UserNameLevel0,
            password_level0=announcement.PasswordLevel0,
            user_name_level1=announcement.UserNameLevel1,
            password_level1=announcement.PasswordLevel1,
            user_name_level2=announcement.UserNameLevel2,
            password_level2=announcement.PasswordLevel2,
            user_name_level3=announcement.UserNameLevel3,
            password_level3=announcement.PasswordLevel3,
            user_name_level4=announcement.UserNameLevel4,
            password_level4=announcement.PasswordLevel4,
            user_name_level5=announcement.UserNameLevel5,
            password_level5=announcement.PasswordLevel5,
            user_name_level6=announcement.UserNameLevel6,
            password_level6=announcement.PasswordLevel6,
            user_name_level7=announcement.UserNameLevel7,
            password_level7=announcement.PasswordLevel7,
            user_name_level8=announcement.UserNameLevel8,
            password_level8=announcement.PasswordLevel8,
            user_name_level9=announcement.UserNameLevel9,
            password_level9=announcement.PasswordLevel9,
            user_name_level10=announcement.UserNameLevel10,
            password_level10=announcement.PasswordLevel10,
            user_name_level11=announcement.UserNameLevel11,
            password_level11=announcement.PasswordLevel11,
            user_name_level12=announcement.UserNameLevel12,
            password_level12=announcement.PasswordLevel12,
            user_name_level13=announcement.UserNameLevel13,
            password_level13=announcement.PasswordLevel13,
            user_name_level14=announcement.UserNameLevel14,
            password_level14=announcement.PasswordLevel14,
            user_name_level15=announcement.UserNameLevel15,
            password_level15=announcement.PasswordLevel15,

            remote_port_tunnel=announcement.RemotePortTunnel,
            remote_port_tunnel_index=announcement.RemotePortTunnelIndex,

            is_virtual=announcement.Virtual,
            uptime=announcement.Uptime,
            location=announcement.Location,
            contact=announcement.Contact,

            last_announcement=now,
            last_seen=now,
            is_online=True,
        )
        db.add(device)
        logger.info(f"Created new device {serial_number}")

    await db.commit()
    await db.refresh(device)

    # Process active alarms from announcement
    active_alarms_data = data.get("activeAlarms", [])
    if active_alarms_data and isinstance(active_alarms_data, list):
        await process_active_alarms(db, device, active_alarms_data)

    # Return success - devices expect 200 OK
    return {"status": "ok", "serial_number": serial_number}


async def process_active_alarms(
    db: AsyncSession,
    device: Device,
    active_alarms_data: list,
):
    """Process active alarms from device announcement.

    This function:
    1. Creates new alarms for any not seen before
    2. Updates existing alarms
    3. Closes alarms that are no longer in the active list
    """
    now = datetime.utcnow()
    received_gam_ids = set()

    for alarm_data in active_alarms_data:
        if not isinstance(alarm_data, dict):
            continue

        # Extract alarm fields (case-insensitive lookup)
        def get_val(d, *keys):
            for k in keys:
                if k in d:
                    return d[k]
                # Case-insensitive lookup
                for dk in d:
                    if dk.lower() == k.lower():
                        return d[dk]
            return None

        gam_id = get_val(alarm_data, "gamId", "GamId", "id", "Id")
        if not gam_id:
            # Generate a unique ID based on condition type and interface
            cond_type = get_val(alarm_data, "condType", "CondType", "conditionType", "type") or "Unknown"
            if_descr = get_val(alarm_data, "ifDescr", "IfDescr", "interface") or ""
            gam_id = f"{cond_type}_{if_descr}_{device.serial_number}"

        received_gam_ids.add(str(gam_id))

        # Check if alarm already exists
        result = await db.execute(
            select(Alarm).where(
                Alarm.device_id == device.id,
                Alarm.gam_id == str(gam_id),
                Alarm.closing_date == None
            )
        )
        existing_alarm = result.scalar_one_or_none()

        # Extract alarm data
        cond_type = get_val(alarm_data, "condType", "CondType", "conditionType", "type") or "Unknown"
        severity = get_val(alarm_data, "severity", "Severity") or "NA"
        serv_aff = get_val(alarm_data, "servAff", "ServAff", "serviceAffecting")
        if_index = get_val(alarm_data, "ifIndex", "IfIndex")
        if_descr = get_val(alarm_data, "ifDescr", "IfDescr", "interface")
        details = get_val(alarm_data, "details", "Details", "description")
        occur_time = get_val(alarm_data, "occurTime", "OccurTime", "occurredAt", "time")

        # Software fault info
        sw_fault_file = get_val(alarm_data, "swFaultFileName", "SwFaultFileName")
        sw_fault_line = get_val(alarm_data, "swFltLine", "SwFltLine")
        sw_fault_module = get_val(alarm_data, "swFltModuleId", "SwFltModuleId")
        hw_fault_id = get_val(alarm_data, "hwFltId", "HwFltId")

        if existing_alarm:
            # Update existing alarm
            existing_alarm.severity = severity
            existing_alarm.serv_aff = serv_aff
            existing_alarm.details = details
            existing_alarm.updated_at = now
            logger.debug(f"Updated alarm {gam_id} for device {device.serial_number}")
        else:
            # Create new alarm
            new_alarm = Alarm(
                device_id=device.id,
                gam_id=str(gam_id),
                if_index=str(if_index) if if_index else None,
                if_descr=str(if_descr) if if_descr else None,
                cond_type=cond_type,
                severity=severity,
                serv_aff=serv_aff,
                details=details,
                occur_time=str(occur_time) if occur_time else None,
                sw_fault_file_name=str(sw_fault_file) if sw_fault_file else None,
                sw_fault_line=str(sw_fault_line) if sw_fault_line else None,
                sw_fault_module_id=str(sw_fault_module) if sw_fault_module else None,
                hw_fault_id=str(hw_fault_id) if hw_fault_id else None,
                is_manual=False,
                occurred_at=now,
            )
            db.add(new_alarm)
            logger.info(f"New alarm {gam_id}: {cond_type} ({severity}) for device {device.serial_number}")

    # Close alarms that are no longer active
    # Get all active alarms for this device
    result = await db.execute(
        select(Alarm).where(
            Alarm.device_id == device.id,
            Alarm.closing_date == None,
            Alarm.is_manual == False  # Don't auto-close manually created alarms
        )
    )
    current_alarms = result.scalars().all()

    for alarm in current_alarms:
        if alarm.gam_id and alarm.gam_id not in received_gam_ids:
            # This alarm is no longer in the active list - close it
            alarm.closing_date = now
            logger.info(f"Closed alarm {alarm.gam_id}: {alarm.cond_type} for device {device.serial_number}")

    await db.commit()
