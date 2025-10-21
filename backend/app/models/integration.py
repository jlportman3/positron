from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from ..database import Base
import uuid
import enum


class SystemType(str, enum.Enum):
    SONAR = "sonar"
    SPLYNX = "splynx"


class JobType(str, enum.Enum):
    CUSTOMER_SYNC = "customer_sync"
    SERVICE_SYNC = "service_sync"
    BILLING_SYNC = "billing_sync"
    WEBHOOK_PROCESS = "webhook_process"
    FULL_SYNC = "full_sync"


class JobStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExternalSystem(Base):
    __tablename__ = "external_systems"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    type = Column(Enum(SystemType), nullable=False)
    
    # Connection settings
    api_url = Column(String(500), nullable=False)
    api_key = Column(String(500), nullable=False)  # Should be encrypted
    api_secret = Column(String(500), nullable=True)  # For systems requiring secret
    webhook_secret = Column(String(500), nullable=True)  # For webhook validation
    
    # Configuration
    enabled = Column(Boolean, default=True, nullable=False)
    sync_interval = Column(Integer, default=3600, nullable=False)  # Seconds
    auto_sync = Column(Boolean, default=True, nullable=False)
    
    # Sync settings
    sync_customers = Column(Boolean, default=True, nullable=False)
    sync_services = Column(Boolean, default=True, nullable=False)
    sync_billing = Column(Boolean, default=False, nullable=False)
    
    # Field mappings (JSON configuration)
    field_mappings = Column(JSONB, nullable=True)
    sync_filters = Column(JSONB, nullable=True)  # Filters for what to sync
    
    # Status tracking
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_successful_sync = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    total_syncs = Column(Integer, default=0, nullable=False)
    failed_syncs = Column(Integer, default=0, nullable=False)
    
    # Rate limiting
    rate_limit_requests = Column(Integer, default=100, nullable=False)  # Requests per minute
    rate_limit_window = Column(Integer, default=60, nullable=False)  # Window in seconds
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ExternalSystem(name='{self.name}', type='{self.type}', enabled={self.enabled})>"

    @property
    def is_healthy(self):
        """Check if system is healthy based on recent sync success"""
        if not self.enabled:
            return False
        
        if not self.last_sync:
            return False
            
        # Consider healthy if last sync was successful and within 2x sync interval
        if self.last_successful_sync:
            import datetime
            threshold = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=self.sync_interval * 2)
            return self.last_successful_sync > threshold
            
        return False

    @property
    def success_rate(self):
        """Calculate sync success rate"""
        if self.total_syncs == 0:
            return 0
        return ((self.total_syncs - self.failed_syncs) / self.total_syncs) * 100

    def get_default_field_mappings(self):
        """Get default field mappings based on system type"""
        if self.type == SystemType.SONAR:
            return {
                "customer_id": "id",
                "customer_name": "name", 
                "customer_email": "email",
                "service_address": "service_address",
                "service_plan": "internet_service.plan_name",
                "bandwidth_down": "internet_service.download_speed",
                "bandwidth_up": "internet_service.upload_speed",
                "status": "status"
            }
        elif self.type == SystemType.SPLYNX:
            return {
                "customer_id": "id",
                "customer_name": "name",
                "customer_email": "email", 
                "service_address": "full_address",
                "service_plan": "tariff_name",
                "bandwidth_down": "tariff.speed_download",
                "bandwidth_up": "tariff.speed_upload",
                "status": "status"
            }
        return {}

    def update_sync_status(self, success=True, error_message=None):
        """Update sync status after sync attempt"""
        import datetime
        now = datetime.datetime.now(datetime.timezone.utc)
        
        self.last_sync = now
        self.total_syncs += 1
        
        if success:
            self.last_successful_sync = now
            self.last_error = None
        else:
            self.failed_syncs += 1
            self.last_error = error_message


class SyncJob(Base):
    __tablename__ = "sync_jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    system_id = Column(UUID(as_uuid=True), nullable=False)  # Reference to ExternalSystem
    job_type = Column(Enum(JobType), nullable=False)
    status = Column(Enum(JobStatus), default=JobStatus.PENDING, nullable=False)
    
    # Job details
    parameters = Column(JSONB, nullable=True)  # Job-specific parameters
    result = Column(JSONB, nullable=True)      # Job result data
    error_message = Column(Text, nullable=True)
    
    # Progress tracking
    records_total = Column(Integer, default=0, nullable=False)
    records_processed = Column(Integer, default=0, nullable=False)
    records_successful = Column(Integer, default=0, nullable=False)
    records_failed = Column(Integer, default=0, nullable=False)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Retry logic
    retry_count = Column(Integer, default=0, nullable=False)
    max_retries = Column(Integer, default=3, nullable=False)
    next_retry_at = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SyncJob(type='{self.job_type}', status='{self.status}', progress={self.progress_percentage}%)>"

    @property
    def progress_percentage(self):
        """Calculate job progress percentage"""
        if self.records_total == 0:
            return 0
        return (self.records_processed / self.records_total) * 100

    @property
    def success_rate(self):
        """Calculate success rate for processed records"""
        if self.records_processed == 0:
            return 0
        return (self.records_successful / self.records_processed) * 100

    @property
    def duration_seconds(self):
        """Get job duration in seconds"""
        if not self.started_at:
            return 0
        
        end_time = self.completed_at or func.now()
        return (end_time - self.started_at).total_seconds()

    @property
    def can_retry(self):
        """Check if job can be retried"""
        return (self.status == JobStatus.FAILED and 
                self.retry_count < self.max_retries)

    def start_job(self):
        """Mark job as started"""
        import datetime
        self.status = JobStatus.RUNNING
        self.started_at = datetime.datetime.now(datetime.timezone.utc)

    def complete_job(self, success=True, error_message=None, result=None):
        """Mark job as completed"""
        import datetime
        self.completed_at = datetime.datetime.now(datetime.timezone.utc)
        
        if success:
            self.status = JobStatus.COMPLETED
        else:
            self.status = JobStatus.FAILED
            self.error_message = error_message
            
        if result:
            self.result = result

    def update_progress(self, processed=None, successful=None, failed=None):
        """Update job progress"""
        if processed is not None:
            self.records_processed = processed
        if successful is not None:
            self.records_successful = successful
        if failed is not None:
            self.records_failed = failed

    def schedule_retry(self, delay_minutes=5):
        """Schedule job for retry"""
        import datetime
        self.retry_count += 1
        self.status = JobStatus.PENDING
        self.next_retry_at = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=delay_minutes)
