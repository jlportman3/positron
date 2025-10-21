from pydantic_settings import BaseSettings
from typing import List, Optional
import os


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql://postgres:postgres@localhost:5432/positron_gam"
    
    # Redis
    redis_url: str = "redis://localhost:6379/0"
    
    # Application
    secret_key: str = "dev-secret-key-change-in-production"
    debug: bool = False
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    
    # SNMP Configuration
    default_snmp_community: str = "public"
    snmp_timeout: int = 10
    snmp_retries: int = 3
    
    # SSH Configuration
    ssh_timeout: int = 30
    ssh_connection_timeout: int = 10
    
    # Sonar Integration
    sonar_api_url: Optional[str] = None
    sonar_api_key: Optional[str] = None
    sonar_webhook_secret: Optional[str] = None
    
    # Splynx Integration
    splynx_api_url: Optional[str] = None
    splynx_api_key: Optional[str] = None
    splynx_api_secret: Optional[str] = None
    splynx_webhook_secret: Optional[str] = None
    
    # Monitoring
    monitoring_interval: int = 300  # 5 minutes
    health_check_interval: int = 60  # 1 minute
    
    # Email Alerts
    alert_email_enabled: bool = False
    alert_email_smtp_host: str = "smtp.gmail.com"
    alert_email_smtp_port: int = 587
    alert_email_username: Optional[str] = None
    alert_email_password: Optional[str] = None
    alert_email_from: Optional[str] = None
    alert_email_to: Optional[str] = None
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Celery
    celery_broker_url: Optional[str] = None
    celery_result_backend: Optional[str] = None
    
    # Security
    cors_origins: List[str] = ["http://localhost:3000"]
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # GAM Device Defaults
    default_management_vlan: int = 4093
    default_subscriber_vlan_start: int = 100
    default_subscriber_vlan_end: int = 4000
    default_bandwidth_plan_down: int = 100
    default_bandwidth_plan_up: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set Celery URLs to Redis URL if not specified
        if not self.celery_broker_url:
            self.celery_broker_url = self.redis_url
        if not self.celery_result_backend:
            self.celery_result_backend = self.redis_url


# Global settings instance
settings = Settings()
