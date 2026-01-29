"""
Export API endpoints for CSV downloads.
"""
import csv
import io
from datetime import datetime
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.api.deps import get_db, get_current_user
from app.models import User, Device, Endpoint, Subscriber, Alarm, Bandwidth, Group, AuditLog

router = APIRouter()


def make_csv_response(data: list, headers: list, filename: str) -> Response:
    """Create a CSV response from data."""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(data)
    content = output.getvalue()

    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
        },
    )


@router.get("/devices")
async def export_devices(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export all devices to CSV."""
    result = await db.execute(select(Device).order_by(Device.name, Device.serial_number))
    devices = result.scalars().all()

    headers = [
        "Serial Number", "Name", "IP Address", "Status", "Product Class",
        "Software Version", "Hardware Version", "Uptime", "Last Seen",
        "MAC Address", "Location", "Contact"
    ]

    data = []
    for d in devices:
        data.append([
            d.serial_number,
            d.name or "",
            d.ip_address or "",
            "Online" if d.is_online else "Offline",
            d.product_class or "",
            d.software_version or "",
            d.hardware_version or "",
            d.uptime or "",
            d.last_seen.isoformat() if d.last_seen else "",
            d.mac_address or "",
            d.location or "",
            d.contact or "",
        ])

    filename = f"devices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/endpoints")
async def export_endpoints(
    device_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export endpoints to CSV."""
    query = select(Endpoint)
    if device_id:
        query = query.where(Endpoint.device_id == device_id)
    query = query.order_by(Endpoint.conf_endpoint_name, Endpoint.mac_address)

    result = await db.execute(query)
    endpoints = result.scalars().all()

    headers = [
        "MAC Address", "Name", "Status", "State", "Model", "Port",
        "RX PHY Rate", "TX PHY Rate", "Wire Length (ft)", "Subscriber",
        "Bandwidth Profile", "Firmware Version", "Device ID"
    ]

    data = []
    for e in endpoints:
        data.append([
            e.mac_address or "",
            e.conf_endpoint_name or "",
            "Connected" if e.alive else "Disconnected",
            e.state or "",
            e.model_string or e.model_type or "",
            e.detected_port_if_index or e.conf_port_if_index or "",
            e.rx_phy_rate or "",
            e.tx_phy_rate or "",
            e.wire_length_feet or "",
            e.conf_user_name or "",
            e.conf_bw_profile_name or "",
            e.fw_version or "",
            str(e.device_id) if e.device_id else "",
        ])

    filename = f"endpoints_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/subscribers")
async def export_subscribers(
    device_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export subscribers to CSV matching Virtuoso format."""
    query = select(Subscriber, Device.name.label("device_name"), Device.ip_address.label("device_ip")).outerjoin(
        Device, Subscriber.device_id == Device.id
    )
    if device_id:
        query = query.where(Subscriber.device_id == device_id)
    query = query.order_by(Subscriber.name)

    result = await db.execute(query)
    rows = result.all()

    headers = [
        "Name", "Description", "UID", "Endpoint Name", "Endpoint MAC",
        "Bandwidth Profile", "Port 1 VLAN", "Port 1 Tagged",
        "Allowed Tagged VLANs (Port 1)", "Port 2 VLAN", "Port 2 Tagged",
        "Allowed Tagged VLANs (Port 2)", "Remapped VLAN",
        "Double Tags", "Trunk Mode", "PoE Mode",
        "NNI Interface", "System Name", "GAM IP Address"
    ]

    data = []
    for s, device_name, device_ip in rows:
        data.append([
            s.name or "",
            s.description or "",
            s.uid or "",
            s.endpoint_name or "",
            s.endpoint_mac_address or "",
            s.bw_profile_name or "",
            s.port1_vlan_id or "",
            "Yes" if s.vlan_is_tagged else "No",
            s.allowed_tagged_vlan or "",
            s.port2_vlan_id or "",
            "Yes" if s.vlan_is_tagged2 else "No",
            s.allowed_tagged_vlan2 or "",
            s.remapped_vlan_id or "",
            "Yes" if s.double_tags else "No",
            "Yes" if s.trunk_mode else "No",
            s.poe_mode_ctrl or "",
            s.nni_if_index or "",
            device_name or "",
            device_ip or "",
        ])

    filename = f"subscribers_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/alarms")
async def export_alarms(
    device_id: Optional[UUID] = None,
    active_only: bool = True,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export alarms to CSV."""
    query = select(Alarm)
    if device_id:
        query = query.where(Alarm.device_id == device_id)
    if active_only:
        query = query.where(Alarm.closing_date == None)
    query = query.order_by(Alarm.occurred_at.desc())

    result = await db.execute(query)
    alarms = result.scalars().all()

    headers = [
        "Severity", "Condition", "Interface", "Details", "Service Affecting",
        "Occurred At", "Acknowledged By", "Acknowledged At", "Closed At", "Device ID"
    ]

    data = []
    for a in alarms:
        data.append([
            a.severity or "",
            a.cond_type or "",
            a.if_descr or "",
            a.details or "",
            "Yes" if a.serv_aff == "Y" else "No",
            a.occurred_at.isoformat() if a.occurred_at else "",
            a.acknowledged_by or "",
            a.acknowledged_at.isoformat() if a.acknowledged_at else "",
            a.closing_date.isoformat() if a.closing_date else "",
            str(a.device_id) if a.device_id else "",
        ])

    filename = f"alarms_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/bandwidths")
async def export_bandwidths(
    device_id: Optional[UUID] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export bandwidth profiles to CSV."""
    query = select(Bandwidth).where(Bandwidth.deleted == False)
    if device_id:
        query = query.where(Bandwidth.device_id == device_id)
    query = query.order_by(Bandwidth.name)

    result = await db.execute(query)
    bandwidths = result.scalars().all()

    headers = [
        "Name", "UID", "Downstream (kbps)", "Upstream (kbps)",
        "Description", "Synced", "Device ID"
    ]

    data = []
    for b in bandwidths:
        data.append([
            b.name or "",
            b.uid or "",
            b.ds_bw or 0,
            b.us_bw or 0,
            b.description or "",
            "Yes" if b.sync else "No",
            str(b.device_id) if b.device_id else "",
        ])

    filename = f"bandwidths_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/groups")
async def export_groups(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export groups to CSV."""
    result = await db.execute(select(Group).order_by(Group.name))
    groups = result.scalars().all()

    headers = [
        "Name", "Description", "Parent ID", "Created At", "Created By"
    ]

    data = []
    for g in groups:
        data.append([
            g.name or "",
            g.description or "",
            str(g.parent_id) if g.parent_id else "",
            g.created_at.isoformat() if g.created_at else "",
            g.created_by or "",
        ])

    filename = f"groups_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/users")
async def export_users(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export users to CSV."""
    result = await db.execute(select(User).order_by(User.username))
    users = result.scalars().all()

    headers = [
        "Username", "Email", "Enabled", "Privilege Level",
        "Session Timeout", "Last Login", "Created At"
    ]

    data = []
    for u in users:
        data.append([
            u.username or "",
            u.email or "",
            "Yes" if u.enabled else "No",
            u.privilege_level or 0,
            u.session_timeout or "",
            u.last_login.isoformat() if u.last_login else "",
            u.created_at.isoformat() if u.created_at else "",
        ])

    filename = f"users_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)


@router.get("/audit-logs")
async def export_audit_logs(
    username: Optional[str] = None,
    action: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Export audit logs to CSV."""
    query = select(AuditLog)
    if username:
        query = query.where(AuditLog.username == username)
    if action:
        query = query.where(AuditLog.action == action)
    query = query.order_by(AuditLog.created_at.desc())

    result = await db.execute(query)
    logs = result.scalars().all()

    headers = [
        "Timestamp", "Username", "IP Address", "Action", "Entity Type",
        "Entity ID", "Entity Name", "Description", "Status"
    ]

    data = []
    for log in logs:
        data.append([
            log.created_at.isoformat() if log.created_at else "",
            log.username or "",
            log.ip_address or "",
            log.action or "",
            log.entity_type or "",
            log.entity_id or "",
            log.entity_name or "",
            log.description or "",
            log.status or "",
        ])

    filename = f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return make_csv_response(data, headers, filename)
