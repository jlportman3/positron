"""
Dashboard API endpoints.
"""
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from app.api.deps import get_db, get_current_user
from app.models import User, Device, Endpoint, Subscriber, Alarm, AuditLog, Bandwidth
from pydantic import BaseModel
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


class DashboardStats(BaseModel):
    """Complete dashboard statistics."""
    # Device stats
    total_devices: int
    online_devices: int
    offline_devices: int
    device_online_rate: float

    # Endpoint stats
    total_endpoints: int
    connected_endpoints: int
    disconnected_endpoints: int
    endpoint_connection_rate: float
    # Detailed endpoint statuses (for pie chart)
    endpoints_ok: int
    endpoints_offline: int
    endpoints_mj_tca: int
    endpoints_mn_tca: int
    endpoints_not_configured: int

    # Subscriber stats
    total_subscribers: int

    # Bandwidth stats
    total_bandwidth_profiles: int

    # Alarm counts
    alarm_critical: int
    alarm_major: int
    alarm_minor: int
    alarm_normal: int
    alarm_total: int
    recent_critical: int  # Critical alarms in last 24h

    # Baseline stats
    baseline_devices: int
    non_baseline_devices: int

    # Recent activity
    activity_today: int
    activity_this_week: int


class RecentAlarm(BaseModel):
    """Recent alarm for dashboard."""
    id: str
    severity: str
    name: str
    device_name: Optional[str]
    raised_at: datetime


class RecentActivity(BaseModel):
    """Recent activity for dashboard."""
    id: str
    username: str
    action: str
    entity_type: str
    entity_name: Optional[str]
    created_at: datetime


class DistributionItem(BaseModel):
    """Distribution item for charts."""
    name: str
    count: int


class DashboardData(BaseModel):
    """Complete dashboard data."""
    stats: DashboardStats
    recent_alarms: List[RecentAlarm]
    recent_activity: List[RecentActivity]
    bandwidth_distribution: List[DistributionItem]
    version_distribution: List[DistributionItem]


@router.get("", response_model=DashboardData)
async def get_dashboard_data(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get all dashboard data in a single request."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=7)

    # Device stats
    devices_result = await db.execute(select(Device))
    devices = devices_result.scalars().all()
    total_devices = len(devices)
    online_devices = len([d for d in devices if d.is_online])
    offline_devices = total_devices - online_devices
    device_online_rate = (online_devices / total_devices * 100) if total_devices > 0 else 0

    # Endpoint stats
    endpoints_result = await db.execute(select(Endpoint))
    endpoints = endpoints_result.scalars().all()
    total_endpoints = len(endpoints)
    connected_endpoints = len([e for e in endpoints if e.alive])
    disconnected_endpoints = total_endpoints - connected_endpoints
    endpoint_connection_rate = (connected_endpoints / total_endpoints * 100) if total_endpoints > 0 else 0

    # Detailed endpoint status breakdown
    endpoints_ok = 0
    endpoints_offline = 0
    endpoints_mj_tca = 0
    endpoints_mn_tca = 0
    endpoints_not_configured = 0
    for e in endpoints:
        if not e.alive:
            endpoints_offline += 1
        elif e.tca_status == 'MJ':
            endpoints_mj_tca += 1
        elif e.tca_status == 'MN':
            endpoints_mn_tca += 1
        elif not e.conf_user_name:
            endpoints_not_configured += 1
        else:
            endpoints_ok += 1

    # Subscriber stats
    subscriber_count = await db.execute(select(func.count(Subscriber.id)))
    total_subscribers = subscriber_count.scalar() or 0

    # Bandwidth stats
    bandwidth_count = await db.execute(
        select(func.count(Bandwidth.id)).where(Bandwidth.deleted == False)
    )
    total_bandwidth_profiles = bandwidth_count.scalar() or 0

    # Alarm counts
    alarm_critical = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.closing_date == None,
            Alarm.severity == 'CR'
        )
    )
    alarm_major = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.closing_date == None,
            Alarm.severity == 'MJ'
        )
    )
    alarm_minor = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.closing_date == None,
            Alarm.severity == 'MN'
        )
    )
    alarm_normal = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.closing_date == None,
            Alarm.severity == 'NA'
        )
    )

    cr = alarm_critical.scalar() or 0
    mj = alarm_major.scalar() or 0
    mn = alarm_minor.scalar() or 0
    na = alarm_normal.scalar() or 0

    # Recent critical alarms (last 24h)
    yesterday = now - timedelta(hours=24)
    recent_critical_result = await db.execute(
        select(func.count(Alarm.id)).where(
            Alarm.severity == 'CR',
            Alarm.occurred_at >= yesterday
        )
    )
    recent_cr = recent_critical_result.scalar() or 0

    # Baseline stats - for now, all online devices are considered baseline
    # TODO: Add actual baseline tracking when config sync is implemented
    baseline_devices = online_devices
    non_baseline_devices = 0

    # Activity counts
    activity_today_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= today_start)
    )
    activity_this_week_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.created_at >= week_start)
    )

    # Recent alarms
    recent_alarms_result = await db.execute(
        select(Alarm)
        .where(Alarm.closing_date == None)
        .order_by(desc(Alarm.occurred_at))
        .limit(5)
    )
    recent_alarms_list = recent_alarms_result.scalars().all()

    # Get device names for alarms
    device_ids = [a.device_id for a in recent_alarms_list if a.device_id]
    device_name_map = {}
    if device_ids:
        devices_for_alarms = await db.execute(
            select(Device).where(Device.id.in_(device_ids))
        )
        for d in devices_for_alarms.scalars().all():
            device_name_map[str(d.id)] = d.name or d.serial_number

    # Recent activity
    recent_activity_result = await db.execute(
        select(AuditLog)
        .order_by(desc(AuditLog.created_at))
        .limit(10)
    )
    recent_activity_list = recent_activity_result.scalars().all()

    # Bandwidth distribution - count subscribers per bandwidth profile name
    # bw_profile_id=0 or empty name means "Default BW Profile"
    bandwidth_dist_result = await db.execute(
        select(
            Subscriber.bw_profile_id,
            Subscriber.bw_profile_name,
            func.count(Subscriber.id).label('count')
        )
        .group_by(Subscriber.bw_profile_id, Subscriber.bw_profile_name)
        .order_by(desc('count'))
    )
    bandwidth_distribution = []
    for row in bandwidth_dist_result.all():
        name = row.bw_profile_name.strip() if row.bw_profile_name else ''
        if not name or row.bw_profile_id == 0:
            name = 'Default BW Profile'
        bandwidth_distribution.append(DistributionItem(name=name, count=row.count or 0))

    # Software version distribution - count devices per software version
    version_dist_result = await db.execute(
        select(
            Device.software_version,
            func.count(Device.id).label('count')
        )
        .where(Device.software_version != None)
        .group_by(Device.software_version)
        .order_by(desc('count'))
    )
    version_distribution = [
        DistributionItem(name=row.software_version or 'Unknown', count=row.count or 0)
        for row in version_dist_result.all()
    ]
    # If no versions, show empty
    if not version_distribution:
        version_distribution = []

    return DashboardData(
        stats=DashboardStats(
            total_devices=total_devices,
            online_devices=online_devices,
            offline_devices=offline_devices,
            device_online_rate=round(device_online_rate, 1),
            total_endpoints=total_endpoints,
            connected_endpoints=connected_endpoints,
            disconnected_endpoints=disconnected_endpoints,
            endpoint_connection_rate=round(endpoint_connection_rate, 1),
            endpoints_ok=endpoints_ok,
            endpoints_offline=endpoints_offline,
            endpoints_mj_tca=endpoints_mj_tca,
            endpoints_mn_tca=endpoints_mn_tca,
            endpoints_not_configured=endpoints_not_configured,
            total_subscribers=total_subscribers,
            total_bandwidth_profiles=total_bandwidth_profiles,
            alarm_critical=cr,
            alarm_major=mj,
            alarm_minor=mn,
            alarm_normal=na,
            alarm_total=cr + mj + mn + na,
            recent_critical=recent_cr,
            baseline_devices=baseline_devices,
            non_baseline_devices=non_baseline_devices,
            activity_today=activity_today_result.scalar() or 0,
            activity_this_week=activity_this_week_result.scalar() or 0,
        ),
        recent_alarms=[
            RecentAlarm(
                id=str(a.id),
                severity=a.severity,
                name=a.cond_type,
                device_name=device_name_map.get(str(a.device_id)),
                raised_at=a.occurred_at,
            )
            for a in recent_alarms_list
        ],
        recent_activity=[
            RecentActivity(
                id=str(a.id),
                username=a.username,
                action=a.action,
                entity_type=a.entity_type,
                entity_name=a.entity_name,
                created_at=a.created_at,
            )
            for a in recent_activity_list
        ],
        bandwidth_distribution=bandwidth_distribution,
        version_distribution=version_distribution,
    )
