"""SSH client for GAM device configuration"""
import paramiko
import logging
from typing import Optional, Dict, List
from ..config import settings

logger = logging.getLogger(__name__)


class SSHClient:
    """SSH client for GAM device configuration"""

    def __init__(
        self,
        ip_address: str,
        username: str,
        password: Optional[str] = None,
        private_key: Optional[str] = None,
        timeout: Optional[int] = None
    ):
        self.ip_address = ip_address
        self.username = username
        self.password = password
        self.private_key = private_key
        self.timeout = timeout or settings.ssh_connection_timeout
        self.client: Optional[paramiko.SSHClient] = None

    async def connect(self) -> bool:
        """Establish SSH connection"""
        try:
            self.client = paramiko.SSHClient()
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            connect_kwargs = {
                'hostname': self.ip_address,
                'username': self.username,
                'timeout': self.timeout,
                'look_for_keys': False,
                'allow_agent': False
            }

            if self.password:
                connect_kwargs['password'] = self.password
            elif self.private_key:
                # Load private key from string
                from io import StringIO
                key_file = StringIO(self.private_key)
                pkey = paramiko.RSAKey.from_private_key(key_file)
                connect_kwargs['pkey'] = pkey
            else:
                logger.error("No authentication method provided")
                return False

            self.client.connect(**connect_kwargs)
            logger.info(f"SSH connected to {self.ip_address}")
            return True

        except Exception as e:
            logger.error(f"SSH connection error to {self.ip_address}: {e}")
            return False

    async def disconnect(self):
        """Close SSH connection"""
        if self.client:
            self.client.close()
            logger.info(f"SSH disconnected from {self.ip_address}")

    async def execute(self, command: str) -> Dict[str, any]:
        """Execute command and return output using interactive shell"""
        if not self.client:
            logger.error("SSH client not connected")
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Not connected',
                'exit_code': -1
            }

        try:
            import time

            # Invoke an interactive shell
            channel = self.client.invoke_shell()
            channel.settimeout(settings.ssh_timeout)

            # Wait for initial prompt (# or >)
            time.sleep(1)
            if channel.recv_ready():
                channel.recv(65535)  # Clear any initial output

            # Disable paging first
            channel.send('terminal length 0\n')
            time.sleep(0.5)
            if channel.recv_ready():
                channel.recv(65535)  # Clear the response

            # Send actual command with newline
            channel.send(command + '\n')
            time.sleep(1)  # Initial wait for command to start

            # Collect output
            output = ""
            max_wait = settings.ssh_timeout
            start_time = time.time()
            no_data_count = 0

            while time.time() - start_time < max_wait:
                if channel.recv_ready():
                    chunk = channel.recv(65535).decode('utf-8', errors='ignore')
                    output += chunk
                    no_data_count = 0  # Reset counter when we get data

                    # Check if we got a prompt back (command finished)
                    # Look for prompt at start of line after the command output
                    lines = output.split('\n')
                    last_line = lines[-1].strip() if lines else ""
                    # Check if last line is just a prompt
                    if last_line and (last_line == '#' or last_line == '>' or last_line.endswith('# ') or last_line.endswith('> ')):
                        break
                else:
                    time.sleep(0.5)
                    no_data_count += 1
                    # If no data for 5 consecutive checks (2.5 seconds), assume command done
                    if no_data_count >= 5:
                        break

            channel.close()

            # Remove the command echo and prompt from output
            lines = output.split('\n')
            # Skip first line (command echo) and last line (prompt)
            clean_output = '\n'.join(lines[1:-1]) if len(lines) > 2 else output

            # Log the raw and cleaned output for debugging
            logger.info(f"Raw output from '{command}': {repr(output[:500])}")  # First 500 chars
            logger.info(f"Cleaned output: {repr(clean_output.strip()[:500])}")

            return {
                'success': True,
                'stdout': clean_output.strip(),
                'stderr': '',
                'exit_code': 0
            }

        except Exception as e:
            logger.error(f"SSH command execution error: {e}")
            return {
                'success': False,
                'stdout': '',
                'stderr': str(e),
                'exit_code': -1
            }

    async def execute_commands(self, commands: List[str]) -> List[Dict[str, any]]:
        """Execute multiple commands"""
        results = []
        for command in commands:
            result = await self.execute(command)
            results.append(result)
            if not result['success']:
                logger.warning(f"Command failed: {command}")
                break
        return results

    async def configure_port(
        self,
        port_number: int,
        vlan_id: int,
        bandwidth_down: int,
        bandwidth_up: int,
        mimo_enabled: bool = False
    ) -> bool:
        """Configure GAM port for subscriber"""
        try:
            commands = [
                f"configure terminal",
                f"interface ghn0/{port_number}",
                f"vlan {vlan_id}",
                f"bandwidth downstream {bandwidth_down}",
                f"bandwidth upstream {bandwidth_up}",
            ]

            if mimo_enabled:
                commands.append("mimo enable")
            else:
                commands.append("mimo disable")

            commands.extend([
                "no shutdown",
                "exit",
                "write memory"
            ])

            results = await self.execute_commands(commands)

            # Check if all commands succeeded
            return all(r['success'] for r in results)

        except Exception as e:
            logger.error(f"Port configuration error: {e}")
            return False

    async def disable_port(self, port_number: int) -> bool:
        """Disable GAM port"""
        try:
            commands = [
                "configure terminal",
                f"interface ghn0/{port_number}",
                "shutdown",
                "exit",
                "write memory"
            ]

            results = await self.execute_commands(commands)
            return all(r['success'] for r in results)

        except Exception as e:
            logger.error(f"Port disable error: {e}")
            return False

    async def enable_port(self, port_number: int) -> bool:
        """Enable GAM port"""
        try:
            commands = [
                "configure terminal",
                f"interface ghn0/{port_number}",
                "no shutdown",
                "exit",
                "write memory"
            ]

            results = await self.execute_commands(commands)
            return all(r['success'] for r in results)

        except Exception as e:
            logger.error(f"Port enable error: {e}")
            return False

    async def get_port_config(self, port_number: int) -> Optional[Dict[str, any]]:
        """Get port configuration"""
        try:
            command = f"show interface ghn0/{port_number}"
            result = await self.execute(command)

            if result['success']:
                # Parse output (this will depend on actual GAM CLI format)
                return {
                    'raw_output': result['stdout'],
                    'port_number': port_number
                }
            return None

        except Exception as e:
            logger.error(f"Get port config error: {e}")
            return None

    async def test_connection(self) -> bool:
        """Test SSH connectivity"""
        connected = await self.connect()
        if connected:
            result = await self.execute("show version")
            await self.disconnect()
            return result['success']
        return False

    async def get_ghn_endpoints(self) -> Optional[List[Dict[str, any]]]:
        """
        Get all discovered G.hn endpoints from the device.
        Executes 'show ghn discover all' and parses the output.

        Returns list of endpoints with:
        - mac_address: endpoint MAC address
        - port: physical port number
        - status: connection status
        """
        try:
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect for endpoint query")
                return None

            result = await self.execute("show ghn discover all")
            await self.disconnect()

            if not result['success']:
                logger.error(f"show ghn discover all failed: {result['stderr']}")
                return None

            # Parse the output
            endpoints = self._parse_ghn_discover_output(result['stdout'])
            logger.info(f"Retrieved {len(endpoints)} G.hn endpoints from {self.ip_address}")
            return endpoints

        except Exception as e:
            logger.error(f"Error getting G.hn endpoints: {e}")
            return None

    async def get_ghn_subscribers(self) -> Optional[List[Dict[str, any]]]:
        """
        Get all configured subscribers from the device running-config.
        Executes 'show running-config' and parses subscriber lines.

        Returns list of subscribers with:
        - id: subscriber ID
        - name: subscriber name
        - vlan_id: VLAN ID
        - endpoint_id: associated endpoint ID
        - bw_profile: bandwidth profile
        """
        try:
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect for subscriber query")
                return None

            result = await self.execute("show running-config")
            await self.disconnect()

            if not result['success']:
                logger.error(f"show running-config failed: {result['stderr']}")
                return None

            # Parse the output
            subscribers = self._parse_ghn_subscriber_from_config(result['stdout'])
            logger.info(f"Retrieved {len(subscribers)} G.hn subscribers from {self.ip_address}")
            return subscribers

        except Exception as e:
            logger.error(f"Error getting G.hn subscribers: {e}")
            return None

    async def get_ghn_port_status(self) -> Optional[List[Dict[str, any]]]:
        """
        Get status of all G.hn ports.
        Executes 'show ghn port' and parses the output.

        Returns list of ports with:
        - port_number: port number
        - status: operational status
        - link_state: link up/down
        """
        try:
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect for port status query")
                return None

            result = await self.execute("show ghn port")
            await self.disconnect()

            if not result['success']:
                logger.error(f"show ghn port failed: {result['stderr']}")
                return None

            # Parse the output
            ports = self._parse_ghn_port_output(result['stdout'])
            logger.info(f"Retrieved status for {len(ports)} G.hn ports from {self.ip_address}")
            return ports

        except Exception as e:
            logger.error(f"Error getting G.hn port status: {e}")
            return None

    async def get_running_config(self) -> Optional[str]:
        """
        Get the running configuration from the device.
        Executes 'show running-config' and returns the full output.
        """
        try:
            connected = await self.connect()
            if not connected:
                logger.error("Failed to connect for config retrieval")
                return None

            result = await self.execute("show running-config")
            await self.disconnect()

            if result['success']:
                return result['stdout']
            else:
                logger.error(f"show running-config failed: {result['stderr']}")
                return None

        except Exception as e:
            logger.error(f"Error getting running config: {e}")
            return None

    def _parse_ghn_discover_output(self, output: str) -> List[Dict[str, any]]:
        """
        Parse output from 'show ghn discover all' command.

        Expected format:
        Port  MACAddress         Configured  IsUP
        -----------------------------------------
         4    00:0E:D8:1C:95:08  yes         no
        """
        endpoints = []

        try:
            lines = output.strip().split('\n')

            # Skip header lines (first 2 lines: header + separator)
            data_start = 0
            for i, line in enumerate(lines):
                if '---' in line or '---------' in line:
                    data_start = i + 1
                    break

            # Parse data lines
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!') or line.startswith('%'):
                    continue

                # Try to parse tabular format: Port MAC Configured IsUP
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        # Format: Port MACAddress Configured IsUP
                        endpoint = {
                            'port': int(parts[0]),
                            'mac_address': parts[1],
                            'configured': parts[2] if len(parts) > 2 else 'unknown',
                            'is_up': parts[3] if len(parts) > 3 else 'unknown'
                        }
                        endpoints.append(endpoint)
                        logger.info(f"Parsed endpoint: port={endpoint['port']}, mac={endpoint['mac_address']}, configured={endpoint['configured']}, is_up={endpoint['is_up']}")
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse discover line: {line} - {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing discover output: {e}")

        return endpoints

    def _parse_ghn_endpoint_output(self, output: str) -> List[Dict[str, any]]:
        """
        Parse output from 'show ghn endpoint' command.

        Expected format from running-config:
        ghn endpoint 1 name "Positron_1C9508" mac-address 00:0e:d8:1c:95:08 port 4

        CLI output format (assumed, to be verified):
        Endpoint ID   Name              MAC Address        Port
        -----------   ----              -----------        ----
        1             Positron_1C9508   00:0e:d8:1c:95:08  4
        """
        endpoints = []

        try:
            lines = output.strip().split('\n')

            # Skip header lines (first 2-3 lines typically)
            data_start = 0
            for i, line in enumerate(lines):
                if '---' in line or 'Endpoint ID' in line:
                    data_start = i + 1
                    if i > 0 and '---' in line:
                        break

            # Parse data lines
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue

                # Try to parse tabular format
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        endpoint = {
                            'id': int(parts[0]),
                            'name': parts[1].strip('"'),
                            'mac_address': parts[2],
                            'port': int(parts[3])
                        }
                        endpoints.append(endpoint)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse endpoint line: {line} - {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing endpoint output: {e}")

        return endpoints

    def _parse_ghn_subscriber_from_config(self, output: str) -> List[Dict[str, any]]:
        """
        Parse subscriber configuration from running-config.

        Expected format:
        ghn subscriber 1 name "test" vid 100 endpoint 1 bw-profile unthrottled poe disable
        """
        subscribers = []

        try:
            lines = output.strip().split('\n')

            for line in lines:
                line = line.strip()
                if not line.startswith('ghn subscriber'):
                    continue

                # Parse: ghn subscriber <id> name "<name>" vid <vlan> endpoint <ep_id> bw-profile <profile> ...
                parts = line.split()
                try:
                    subscriber_id_idx = 2  # Position after "ghn subscriber"
                    subscriber = {
                        'id': int(parts[subscriber_id_idx])
                    }

                    # Extract name (quoted string)
                    if 'name' in parts:
                        name_idx = parts.index('name') + 1
                        name = parts[name_idx].strip('"')
                        subscriber['name'] = name

                    # Extract vid (VLAN ID)
                    if 'vid' in parts:
                        vid_idx = parts.index('vid') + 1
                        subscriber['vlan_id'] = int(parts[vid_idx])

                    # Extract endpoint
                    if 'endpoint' in parts:
                        ep_idx = parts.index('endpoint') + 1
                        subscriber['endpoint_id'] = int(parts[ep_idx])

                    # Extract bw-profile
                    if 'bw-profile' in parts:
                        bw_idx = parts.index('bw-profile') + 1
                        subscriber['bw_profile'] = parts[bw_idx]

                    subscribers.append(subscriber)
                except (ValueError, IndexError) as e:
                    logger.warning(f"Failed to parse subscriber config line: {line} - {e}")
                    continue

        except Exception as e:
            logger.error(f"Error parsing subscriber config: {e}")

        return subscribers

    def _parse_ghn_subscriber_output(self, output: str) -> List[Dict[str, any]]:
        """
        Parse output from 'show ghn subscriber' command.

        Expected format from running-config:
        ghn subscriber 1 name "test" vid 100 endpoint 1 bw-profile unthrottled poe disable

        CLI output format (assumed, to be verified):
        Subscriber ID  Name    VLAN  Endpoint  BW Profile
        -------------  ----    ----  --------  ----------
        1              test    100   1         unthrottled
        """
        subscribers = []

        try:
            lines = output.strip().split('\n')

            # Skip header lines
            data_start = 0
            for i, line in enumerate(lines):
                if '---' in line or 'Subscriber ID' in line:
                    data_start = i + 1
                    if i > 0 and '---' in line:
                        break

            # Parse data lines
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue

                # Try to parse tabular format
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        subscriber = {
                            'id': int(parts[0]),
                            'name': parts[1].strip('"'),
                            'vlan_id': int(parts[2]),
                            'endpoint_id': int(parts[3]),
                            'bw_profile': parts[4] if len(parts) > 4 else None
                        }
                        subscribers.append(subscriber)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse subscriber line: {line} - {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing subscriber output: {e}")

        return subscribers

    def _parse_ghn_port_output(self, output: str) -> List[Dict[str, any]]:
        """
        Parse output from 'show ghn port' command.

        CLI output format (assumed, to be verified):
        Port  Status      Link
        ----  ------      ----
        1     enabled     down
        2     enabled     down
        3     enabled     down
        4     enabled     up
        """
        ports = []

        try:
            lines = output.strip().split('\n')

            # Skip header lines
            data_start = 0
            for i, line in enumerate(lines):
                if '---' in line or 'Port' in line:
                    data_start = i + 1
                    if i > 0 and '---' in line:
                        break

            # Parse data lines
            for line in lines[data_start:]:
                line = line.strip()
                if not line or line.startswith('#') or line.startswith('!'):
                    continue

                # Try to parse tabular format
                parts = line.split()
                if len(parts) >= 2:
                    try:
                        port = {
                            'port_number': int(parts[0]),
                            'status': parts[1] if len(parts) > 1 else 'unknown',
                            'link_state': parts[2] if len(parts) > 2 else 'unknown'
                        }
                        ports.append(port)
                    except (ValueError, IndexError) as e:
                        logger.warning(f"Failed to parse port line: {line} - {e}")
                        continue

        except Exception as e:
            logger.error(f"Error parsing port output: {e}")

        return ports
