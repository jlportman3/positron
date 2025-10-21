"""Splynx billing system integration"""
import httpx
import logging
from typing import List, Dict, Any, Optional
import hashlib

from ..config import settings

logger = logging.getLogger(__name__)


class SplynxClient:
    """Splynx API client"""

    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None
    ):
        self.api_url = api_url or settings.splynx_api_url
        self.api_key = api_key or settings.splynx_api_key
        self.api_secret = api_secret or settings.splynx_api_secret

    def _generate_signature(self, nonce: str) -> str:
        """Generate API signature"""
        message = nonce + self.api_key
        return hashlib.sha256((message + self.api_secret).encode()).hexdigest()

    async def _get_headers(self) -> Dict[str, str]:
        """Get request headers with signature"""
        import time
        nonce = str(int(time.time()))
        signature = self._generate_signature(nonce)

        return {
            "X-API-KEY": self.api_key,
            "X-API-SIGNATURE": signature,
            "X-API-NONCE": nonce,
            "Content-Type": "application/json"
        }

    async def test_connection(self) -> bool:
        """Test API connectivity"""
        try:
            headers = await self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/admin/info",
                    headers=headers,
                    timeout=10.0
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Splynx connection test failed: {e}")
            return False

    async def get_customers(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get customers from Splynx"""
        try:
            headers = await self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/admin/customers/customer",
                    headers=headers,
                    params={"limit": limit, "offset": offset},
                    timeout=30.0
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get customers: {response.status_code}")
                    return []

        except Exception as e:
            logger.error(f"Error fetching Splynx customers: {e}")
            return []

    async def get_customer(self, customer_id: str) -> Optional[Dict[str, Any]]:
        """Get specific customer"""
        try:
            headers = await self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/admin/customers/customer/{customer_id}",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
                return None

        except Exception as e:
            logger.error(f"Error fetching Splynx customer {customer_id}: {e}")
            return None

    async def get_customer_services(
        self,
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """Get customer services"""
        try:
            headers = await self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_url}/admin/customers/customer/{customer_id}/internet-services",
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    return response.json()
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
            headers = await self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.put(
                    f"{self.api_url}/admin/customers/customer/internet-service/{service_id}",
                    headers=headers,
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
            headers = await self._get_headers()
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.api_url}/admin/webhooks",
                    headers=headers,
                    json={
                        "url": webhook_url,
                        "events": events,
                        "secret": settings.splynx_webhook_secret
                    },
                    timeout=10.0
                )

                return response.status_code == 201

        except Exception as e:
            logger.error(f"Error creating webhook: {e}")
            return False
