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
        """Execute command and return output"""
        if not self.client:
            logger.error("SSH client not connected")
            return {
                'success': False,
                'stdout': '',
                'stderr': 'Not connected',
                'exit_code': -1
            }

        try:
            stdin, stdout, stderr = self.client.exec_command(command, timeout=settings.ssh_timeout)
            exit_code = stdout.channel.recv_exit_status()

            return {
                'success': exit_code == 0,
                'stdout': stdout.read().decode('utf-8'),
                'stderr': stderr.read().decode('utf-8'),
                'exit_code': exit_code
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
