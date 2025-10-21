"""Sonar billing system integration"""
import httpx
import logging
from typing import List, Dict, Any, Optional

from ..config import settings

logger = logging.getLogger(__name__)


class SonarClient:
    """Sonar API client"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None
    ):
        self.api_url = api_url or settings.sonar_api_url
        self.api_key = api_key or settings.sonar_api_key
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/auth/test",
                    headers=self.headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Sonar connection test failed: {e}")
            return False

    async def get_customers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get customers from Sonar"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/customers",
                    headers=self.headers,
                    params={"limit": limit, "offset": offset},
                    timeout=30.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                else:
                    logger.error(f"Failed to get customers: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching Sonar customers: {e}")
            return []

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get specific customer"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/customers/{customer_id}",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            logger.error(f"Error fetching Sonar customer {customer_id}: {e}")
            return None

    async def get_customer_services(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """Get customer services"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/customers/{customer_id}/services",
                    headers=self.headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    data = response.json()
                    return data.get("data", [])
                return []

        except Exception as e:
            logger.error(f"Error fetching services for customer {customer_id}: {e}")
            return []

    async def update_service_status(
        self,
        service_id: str,
        status: str
    ) -> bool:
        """Update service status"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.patch(
                    f"{self.api_url}/services/{service_id}",
                    headers=self.headers,
                    json={"status": status},
                    timeout=10.0
                )

                return response.status_code == 200

        except Exception as e:
            logger.error(f"Error updating service status: {e}")
            return False

    async def create_webhook(
        self,
        webhook_url: str,
        events: List[str]
    ) -> bool:
        """Create webhook subscription"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/webhooks",
                    headers=self.headers,
                    json={
                        "url": webhook_url,
                        "events": events,
                        "secret": settings.sonar_webhook_secret
                    },
                    timeout=10.0
                )

                return response.status_code == 201

        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return False
