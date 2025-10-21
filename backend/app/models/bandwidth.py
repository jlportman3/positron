from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..database import Base
import uuid


class BandwidthPlan(Base):
    __tablename__ = "bandwidth_plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    
    # Bandwidth limits in Mbps
    downstream_mbps = Column(Integer, nullable=False)
    upstream_mbps = Column(Integer, nullable=False)
    
    # Plan configuration
    is_default = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Rate limiting configuration
    burst_downstream_mbps = Column(Integer, nullable=True)  # Burst allowance
    burst_upstream_mbps = Column(Integer, nullable=True)
    priority = Column(Integer, default=0, nullable=False)  # QoS priority (0-7)
    
    # Usage limits (optional)
    monthly_data_limit_gb = Column(Integer, nullable=True)  # Monthly data cap
    daily_data_limit_gb = Column(Integer, nullable=True)   # Daily data cap
    
    # Pricing information (for integration with billing systems)
    monthly_price = Column(Integer, nullable=True)  # Price in cents
    setup_fee = Column(Integer, nullable=True)      # Setup fee in cents
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    subscribers = relationship("Subscriber", back_populates="bandwidth_plan")

    def __repr__(self):
        return f"<BandwidthPlan(name='{self.name}', down={self.downstream_mbps}, up={self.upstream_mbps})>"

    @property
    def subscriber_count(self):
        """Get count of subscribers using this plan"""
        return len([s for s in self.subscribers if s.status == "active"])

    @property
    def speed_description(self):
        """Get human-readable speed description"""
        if self.downstream_mbps == self.upstream_mbps:
            return f"{self.downstream_mbps} Mbps"
        else:
            return f"{self.downstream_mbps}/{self.upstream_mbps} Mbps"

    @property
    def has_data_limits(self):
        """Check if plan has data usage limits"""
        return self.monthly_data_limit_gb is not None or self.daily_data_limit_gb is not None

    @property
    def monthly_price_dollars(self):
        """Get monthly price in dollars"""
        return self.monthly_price / 100 if self.monthly_price else 0

    @property
    def setup_fee_dollars(self):
        """Get setup fee in dollars"""
        return self.setup_fee / 100 if self.setup_fee else 0

    def is_suitable_for_port_type(self, port_type):
        """Check if bandwidth plan is suitable for given port type"""
        # COAX ports support up to 800 Mbps, above that should be "unthrottled"
        if port_type == "coax" and max(self.downstream_mbps, self.upstream_mbps) > 800:
            return False
        
        # MIMO/SISO ports support up to 1000 Mbps
        if port_type in ["mimo", "siso"] and max(self.downstream_mbps, self.upstream_mbps) > 1000:
            return False
            
        return True

    def get_rate_limit_config(self):
        """Get rate limiting configuration for GAM device"""
        config = {
            "downstream_mbps": self.downstream_mbps,
            "upstream_mbps": self.upstream_mbps,
            "priority": self.priority
        }
        
        if self.burst_downstream_mbps:
            config["burst_downstream_mbps"] = self.burst_downstream_mbps
        if self.burst_upstream_mbps:
            config["burst_upstream_mbps"] = self.burst_upstream_mbps
            
        return config

    @classmethod
    def get_default_plan(cls, session):
        """Get the default bandwidth plan"""
        return session.query(cls).filter(cls.is_default == True, cls.is_active == True).first()

    @classmethod
    def create_default_plans(cls, session):
        """Create default bandwidth plans"""
        default_plans = [
            {
                "name": "Basic 100/100",
                "description": "Basic symmetric 100 Mbps plan",
                "downstream_mbps": 100,
                "upstream_mbps": 100,
                "is_default": True,
                "monthly_price": 5000,  # $50.00
            },
            {
                "name": "Standard 250/250", 
                "description": "Standard symmetric 250 Mbps plan",
                "downstream_mbps": 250,
                "upstream_mbps": 250,
                "monthly_price": 7500,  # $75.00
            },
            {
                "name": "Premium 500/500",
                "description": "Premium symmetric 500 Mbps plan", 
                "downstream_mbps": 500,
                "upstream_mbps": 500,
                "monthly_price": 10000,  # $100.00
            },
            {
                "name": "Gigabit 1000/1000",
                "description": "Gigabit symmetric plan",
                "downstream_mbps": 1000,
                "upstream_mbps": 1000,
                "monthly_price": 15000,  # $150.00
            }
        ]
        
        for plan_data in default_plans:
            existing = session.query(cls).filter(cls.name == plan_data["name"]).first()
            if not existing:
                plan = cls(**plan_data)
                session.add(plan)
        
        session.commit()
