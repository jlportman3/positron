"""
Splynx API Client with Basic authentication.

This client makes outbound API calls to Splynx for:
- Inventory lookup by MAC address
- Customer information retrieval
- Customer notes creation
- Ticket creation
- Administrator listing

Authentication: Basic Auth with API key as username and API secret as password.
"""
import base64
import logging
from typing import Optional, List, Any
from dataclasses import dataclass
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


@dataclass
class SplynxInventoryItem:
    """Splynx inventory item."""
    id: int
    name: str
    mac: Optional[str] = None
    serial_number: Optional[str] = None
    customer_id: Optional[int] = None
    customer_name: Optional[str] = None
    status: Optional[str] = None
    item_type: Optional[str] = None
    vendor: Optional[str] = None
    model: Optional[str] = None


@dataclass
class SplynxCustomer:
    """Splynx customer."""
    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    street_1: Optional[str] = None
    city: Optional[str] = None
    zip_code: Optional[str] = None
    geo_lat: Optional[float] = None
    geo_lon: Optional[float] = None
    billing_type: Optional[str] = None
    partner_id: Optional[int] = None


@dataclass
class SplynxService:
    """Splynx internet service."""
    id: int
    customer_id: int
    description: Optional[str] = None
    status: Optional[str] = None
    tariff_id: Optional[int] = None
    tariff_name: Optional[str] = None
    login: Optional[str] = None
    ip_address: Optional[str] = None
    download_speed: Optional[int] = None
    upload_speed: Optional[int] = None


@dataclass
class SplynxAdmin:
    """Splynx administrator."""
    id: int
    name: str
    email: Optional[str] = None
    role_id: Optional[int] = None
    role_name: Optional[str] = None


@dataclass
class SplynxTicket:
    """Splynx ticket."""
    id: int
    subject: str
    customer_id: Optional[int] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class SplynxApiError(Exception):
    """Splynx API error."""
    def __init__(self, message: str, status_code: int = 0, response_body: str = ""):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_body = response_body


class SplynxClient:
    """
    Async client for Splynx API with Basic authentication.

    Authentication uses Basic Auth:
    Authorization: Basic base64(api_key:api_secret)
    """

    def __init__(self, base_url: str, api_key: str, api_secret: str, timeout: float = 30.0):
        """
        Initialize Splynx client.

        Args:
            base_url: Splynx instance URL (e.g., https://splynx.alamobb.net)
            api_key: API key from Splynx
            api_secret: API secret from Splynx
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    def _generate_auth_header(self) -> str:
        """Generate the Basic authorization header."""
        credentials = f"{self.api_key}:{self.api_secret}"
        encoded = base64.b64encode(credentials.encode('utf-8')).decode('utf-8')
        return f"Basic {encoded}"

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self.timeout)
        return self._client

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict] = None,
        json: Optional[dict] = None,
    ) -> Any:
        """Make an authenticated API request."""
        client = await self._get_client()
        url = f"{self.base_url}{endpoint}"
        headers = {
            "Authorization": self._generate_auth_header(),
            "Content-Type": "application/json",
        }

        logger.debug(f"Splynx API request: {method} {url}")

        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json,
            )

            if response.status_code >= 400:
                logger.error(f"Splynx API error: {response.status_code} - {response.text[:500]}")
                raise SplynxApiError(
                    f"Splynx API error: {response.status_code}",
                    status_code=response.status_code,
                    response_body=response.text[:1000]
                )

            return response.json()

        except httpx.TimeoutException:
            raise SplynxApiError("Request timed out", status_code=0)
        except httpx.RequestError as e:
            raise SplynxApiError(f"Request failed: {str(e)}", status_code=0)

    # =========================================================================
    # Test Connection
    # =========================================================================

    async def test_connection(self) -> dict:
        """
        Test the connection to Splynx API.

        Returns dict with success status and message.
        """
        try:
            # Try to fetch a single customer to verify auth works
            result = await self._request(
                "GET",
                "/api/2.0/admin/customers/customer",
                params={"limit": 1}
            )
            return {
                "status": "success",
                "message": "Successfully connected to Splynx API"
            }
        except SplynxApiError as e:
            return {
                "status": "error",
                "error": e.message,
                "status_code": e.status_code,
                "detail": e.response_body[:200] if e.response_body else None
            }

    # =========================================================================
    # Inventory Operations
    # =========================================================================

    async def search_inventory_by_mac(self, mac_address: str) -> Optional[SplynxInventoryItem]:
        """
        Search Splynx inventory by MAC address.

        Args:
            mac_address: MAC address to search for (any format)

        Returns:
            SplynxInventoryItem if found, None otherwise
        """
        # Normalize MAC to uppercase with colons
        mac_clean = mac_address.upper().replace("-", ":").replace(".", "")
        if len(mac_clean) == 12:
            mac_clean = ":".join([mac_clean[i:i+2] for i in range(0, 12, 2)])

        logger.info(f"Searching Splynx inventory for MAC: {mac_clean}")

        try:
            # Splynx stores MAC addresses in the 'barcode' field, not 'mac'
            result = await self._request(
                "GET",
                "/api/2.0/admin/inventory/items",
                params={"main_attributes[barcode]": mac_clean}
            )

            if result and len(result) > 0:
                item = result[0]
                item_name = await self._resolve_item_name(item)
                return SplynxInventoryItem(
                    id=item.get("id"),
                    name=item_name,
                    mac=item.get("barcode"),  # MAC is in barcode field
                    serial_number=item.get("serial_number"),
                    customer_id=item.get("customer_id"),
                    customer_name=item.get("customer_name"),
                    status=item.get("status"),
                    item_type=item.get("item_type"),
                    vendor=item.get("vendor"),
                    model=item.get("model"),
                )

            # Try without colons
            mac_no_colons = mac_address.upper().replace(":", "").replace("-", "").replace(".", "")
            result = await self._request(
                "GET",
                "/api/2.0/admin/inventory/items",
                params={"main_attributes[barcode]": mac_no_colons}
            )

            if result and len(result) > 0:
                item = result[0]
                item_name = await self._resolve_item_name(item)
                return SplynxInventoryItem(
                    id=item.get("id"),
                    name=item_name,
                    mac=item.get("barcode"),  # MAC is in barcode field
                    serial_number=item.get("serial_number"),
                    customer_id=item.get("customer_id"),
                    customer_name=item.get("customer_name"),
                    status=item.get("status"),
                    item_type=item.get("item_type"),
                    vendor=item.get("vendor"),
                    model=item.get("model"),
                )

            logger.info(f"No inventory item found for MAC: {mac_address}")
            return None

        except SplynxApiError as e:
            logger.error(f"Error searching inventory: {e.message}")
            raise

    async def get_all_inventory_with_customers(self) -> List[SplynxInventoryItem]:
        """
        Get all inventory items that are assigned to customers.

        Used for reconciliation.
        """
        items = []
        page = 1
        page_size = 100

        while True:
            result = await self._request(
                "GET",
                "/api/2.0/admin/inventory/items",
                params={
                    "main_attributes[customer_id][>]": 0,  # Only items with customer
                    "limit": page_size,
                    "page": page
                }
            )

            if not result:
                break

            for item in result:
                item_name = await self._resolve_item_name(item)
                items.append(SplynxInventoryItem(
                    id=item.get("id"),
                    name=item_name,
                    mac=item.get("barcode"),  # MAC is in barcode field
                    serial_number=item.get("serial_number"),
                    customer_id=item.get("customer_id"),
                    customer_name=item.get("customer_name"),
                    status=item.get("status"),
                    item_type=item.get("item_type"),
                    vendor=item.get("vendor"),
                    model=item.get("model"),
                ))

            if len(result) < page_size:
                break

            page += 1

        logger.info(f"Retrieved {len(items)} inventory items with customer assignments")
        return items

    async def get_product(self, product_id: int) -> Optional[dict]:
        """
        Get inventory product details by ID.

        Returns raw product dict with name, vendor_id, etc.
        """
        try:
            return await self._request(
                "GET",
                f"/api/2.0/admin/inventory/products/{product_id}"
            )
        except SplynxApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching product {product_id}: {e.message}")
            return None

    async def _resolve_item_name(self, item: dict) -> str:
        """Resolve inventory item name from product_id, falling back to mark field."""
        product_id = item.get("product_id")
        if product_id:
            product = await self.get_product(product_id)
            if product and product.get("name"):
                return product["name"]
        # Fallback: use mark only if it's not a condition keyword
        mark = item.get("mark", "")
        if mark and mark.lower() not in ("used", "new", "broken", "reserved"):
            return mark
        return item.get("name", "")

    # =========================================================================
    # Customer Operations
    # =========================================================================

    async def get_customer(self, customer_id: int) -> Optional[SplynxCustomer]:
        """
        Get customer details by ID.

        Args:
            customer_id: Splynx customer ID

        Returns:
            SplynxCustomer if found
        """
        logger.info(f"Getting Splynx customer: {customer_id}")

        try:
            result = await self._request(
                "GET",
                f"/api/2.0/admin/customers/customer/{customer_id}"
            )

            if result:
                return SplynxCustomer(
                    id=result.get("id"),
                    name=result.get("name", ""),
                    email=result.get("email"),
                    phone=result.get("phone"),
                    status=result.get("status"),
                    street_1=result.get("street_1"),
                    city=result.get("city"),
                    zip_code=result.get("zip_code"),
                    geo_lat=result.get("geo_lat"),
                    geo_lon=result.get("geo_lon"),
                    billing_type=result.get("billing_type"),
                    partner_id=result.get("partner_id"),
                )

            return None

        except SplynxApiError as e:
            if e.status_code == 404:
                return None
            raise

    async def get_tariff(self, tariff_id: int) -> Optional[dict]:
        """
        Get internet tariff details by ID.

        Returns raw tariff dict with speed_download, speed_upload (in kbps), title, etc.
        """
        try:
            return await self._request(
                "GET",
                f"/api/2.0/admin/tariffs/internet/{tariff_id}"
            )
        except SplynxApiError as e:
            if e.status_code == 404:
                return None
            logger.error(f"Error fetching tariff {tariff_id}: {e.message}")
            return None

    async def get_customer_services(self, customer_id: int) -> List[SplynxService]:
        """
        Get internet services for a customer.

        Speed info is on the tariff, not the service itself, so we fetch
        the tariff for each service to get download/upload speeds.

        Args:
            customer_id: Splynx customer ID

        Returns:
            List of SplynxService
        """
        logger.info(f"Getting services for customer: {customer_id}")

        try:
            result = await self._request(
                "GET",
                f"/api/2.0/admin/customers/customer/{customer_id}/internet-services"
            )

            services = []
            if result:
                for svc in result:
                    tariff_id = svc.get("tariff_id")
                    tariff_name = svc.get("description") or ""
                    download_speed = 0
                    upload_speed = 0

                    # Fetch tariff to get speed and name
                    if tariff_id:
                        tariff = await self.get_tariff(tariff_id)
                        if tariff:
                            tariff_name = tariff.get("title") or tariff.get("service_name") or tariff_name
                            # Splynx tariff speeds are in kbps, convert to Mbps
                            dl_kbps = tariff.get("speed_download") or 0
                            ul_kbps = tariff.get("speed_upload") or 0
                            download_speed = round(int(dl_kbps) / 1000) if dl_kbps else 0
                            upload_speed = round(int(ul_kbps) / 1000) if ul_kbps else 0

                    services.append(SplynxService(
                        id=svc.get("id"),
                        customer_id=svc.get("customer_id"),
                        description=svc.get("description"),
                        status=svc.get("status"),
                        tariff_id=tariff_id,
                        tariff_name=tariff_name,
                        login=svc.get("login"),
                        ip_address=svc.get("ipv4"),
                        download_speed=download_speed,
                        upload_speed=upload_speed,
                    ))

            return services

        except SplynxApiError as e:
            if e.status_code == 404:
                return []
            raise

    # =========================================================================
    # Customer Notes
    # =========================================================================

    async def add_customer_note(self, customer_id: int, note: str, author: str = "GAM System") -> bool:
        """
        Add a note to a customer record.

        Args:
            customer_id: Splynx customer ID
            note: Note text to add
            author: Author name for the note

        Returns:
            True if successful
        """
        logger.info(f"Adding note to customer {customer_id}")

        try:
            await self._request(
                "POST",
                "/api/2.0/admin/customers/customer-notes",
                json={
                    "customer_id": customer_id,
                    "comment": note,
                    "date_time": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                }
            )
            logger.info(f"Successfully added note to customer {customer_id}")
            return True

        except SplynxApiError as e:
            logger.error(f"Failed to add note to customer {customer_id}: {e.message}")
            raise

    # =========================================================================
    # Tickets
    # =========================================================================

    async def create_ticket(
        self,
        subject: str,
        message: str = "",
        customer_id: Optional[int] = None,
        assigned_to: Optional[int] = None,
        priority: str = "medium",
        ticket_type: str = "task",
        due_date: Optional[str] = None,
    ) -> SplynxTicket:
        """
        Create a ticket/task in Splynx.

        Splynx requires two steps: create ticket, then add message body
        via the ticket-messages endpoint.

        Args:
            subject: Ticket subject
            message: Ticket body/message (added as first message)
            customer_id: Customer ID to link ticket to
            assigned_to: Admin ID to assign ticket to
            priority: low, medium, high
            ticket_type: ticket, task, internal
            due_date: Due date in YYYY-MM-DD format

        Returns:
            Created SplynxTicket
        """
        logger.info(f"Creating Splynx ticket: {subject}")

        payload = {
            "subject": subject,
            "priority": priority,
        }

        if customer_id:
            payload["customer_id"] = customer_id

        if assigned_to:
            payload["assigned_to"] = assigned_to

        if due_date:
            payload["due_date"] = due_date

        try:
            result = await self._request(
                "POST",
                "/api/2.0/admin/support/tickets",
                json=payload
            )

            ticket_id = result.get("id")
            logger.info(f"Created ticket ID: {ticket_id}")

            # Add message body as a ticket message
            if message and ticket_id:
                try:
                    await self._request(
                        "POST",
                        "/api/2.0/admin/support/ticket-messages",
                        json={
                            "ticket_id": ticket_id,
                            "message": message,
                            "type": "admin",
                        }
                    )
                    logger.info(f"Added message to ticket {ticket_id}")
                except SplynxApiError as e:
                    logger.warning(f"Ticket {ticket_id} created but message failed: {e.message}")

            return SplynxTicket(
                id=ticket_id,
                subject=subject,
                customer_id=customer_id,
                status=result.get("status"),
                priority=priority,
            )

        except SplynxApiError as e:
            logger.error(f"Failed to create ticket: {e.message}")
            raise

    # =========================================================================
    # Administrators
    # =========================================================================

    async def get_administrators(self) -> List[SplynxAdmin]:
        """
        Get list of Splynx administrators.

        Used to populate assignee dropdown in settings.
        """
        logger.info("Getting Splynx administrators")

        try:
            result = await self._request(
                "GET",
                "/api/2.0/admin/administration/administrators"
            )

            admins = []
            if result:
                for admin in result:
                    admins.append(SplynxAdmin(
                        id=admin.get("id"),
                        name=admin.get("name", ""),
                        email=admin.get("email"),
                        role_id=admin.get("role_id"),
                        role_name=admin.get("role"),
                    ))

            logger.info(f"Retrieved {len(admins)} administrators")
            return admins

        except SplynxApiError as e:
            logger.error(f"Failed to get administrators: {e.message}")
            raise


# =========================================================================
# Factory Function
# =========================================================================

async def create_splynx_client_from_settings(db) -> Optional[SplynxClient]:
    """
    Create a SplynxClient using settings from the database.

    Args:
        db: AsyncSession database connection

    Returns:
        SplynxClient if configured, None otherwise
    """
    from sqlalchemy import select
    from app.models import Setting

    # Get settings
    api_url_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_api_url")
    )
    api_url = api_url_result.scalar_one_or_none()

    api_key_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_api_key")
    )
    api_key = api_key_result.scalar_one_or_none()

    api_secret_result = await db.execute(
        select(Setting).where(Setting.key == "splynx_api_secret")
    )
    api_secret = api_secret_result.scalar_one_or_none()

    if not api_url or not api_url.value:
        logger.warning("Splynx API URL not configured")
        return None

    if not api_key or not api_key.value:
        logger.warning("Splynx API key not configured")
        return None

    if not api_secret or not api_secret.value:
        logger.warning("Splynx API secret not configured")
        return None

    return SplynxClient(
        base_url=api_url.value,
        api_key=api_key.value,
        api_secret=api_secret.value,
    )
