import asyncio
import docker
import os
import tempfile
import uuid
from typing import Dict, Optional, List
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class DockerSandbox:
    """
    Docker-based sandbox for safe command execution
    """

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.container: Optional[docker.models.containers.Container] = None
        self.client = docker.from_env()
        self.container_name = f"cli-quest-{session_id}"
        self.working_dir = "/workspace"

    async def initialize(self):
        """Initialize the sandbox container"""
        try:
            # Create a simple Ubuntu container with basic CLI tools
            self.container = self.client.containers.run(
                "ubuntu:22.04",
                name=self.container_name,
                command="/bin/bash",
                stdin_open=True,
                tty=True,
                detach=True,
                working_dir=self.working_dir,
                mem_limit="128m",  # Limit memory usage
                cpu_quota=50000,   # Limit CPU usage (50% of one core)
                network_disabled=True,  # Disable network access for security
                remove=True,  # Auto-remove when stopped
                volumes={
                    # Create a temporary volume for the workspace
                    f"cli-quest-{self.session_id}": {
                        "bind": self.working_dir,
                        "mode": "rw"
                    }
                }
            )

            # Install basic tools in the container
            await self._setup_container()

            logger.info(f"Sandbox container initialized: {self.container_name}")

        except Exception as e:
            logger.error(f"Failed to initialize sandbox: {e}")
            raise

    async def _setup_container(self):
        """Set up the container with basic tools and files"""
        setup_commands = [
            "apt-get update -qq",
            "apt-get install -y -qq curl wget nano vim less tree file",
            "mkdir -p /workspace/challenges",
            "echo 'Welcome to CLI Quest!' > /workspace/README.txt",
            "echo 'Use ls to see available files and directories.' >> /workspace/README.txt"
        ]

        for cmd in setup_commands:
            try:
                result = self.container.exec_run(cmd, workdir=self.working_dir)
                if result.exit_code != 0:
                    logger.warning(f"Setup command failed: {cmd} - {result.output.decode()}")
            except Exception as e:
                logger.warning(f"Error running setup command '{cmd}': {e}")

    async def execute_command(self, command: str) -> str:
        """
        Execute a command in the sandbox

        Args:
            command: Command to execute

        Returns:
            Command output
        """
        if not self.container:
            raise RuntimeError("Sandbox not initialized")

        try:
            # Security: Basic command filtering
            if self._is_dangerous_command(command):
                return "Error: Command not allowed for security reasons"

            # Execute the command
            result = self.container.exec_run(
                f"/bin/bash -c '{command}'",
                workdir=self.working_dir,
                tty=True
            )

            output = result.output.decode('utf-8', errors='replace')

            # Add exit code info if command failed
            if result.exit_code != 0:
                output += f"\n[Exit code: {result.exit_code}]"

            return output

        except Exception as e:
            logger.error(f"Command execution error: {e}")
            return f"Error executing command: {str(e)}"

    def _is_dangerous_command(self, command: str) -> bool:
        """
        Check if a command is potentially dangerous

        Args:
            command: Command to check

        Returns:
            True if command should be blocked
        """
        dangerous_patterns = [
            "rm -rf /",
            ":(){ :|:& };:",  # Fork bomb
            "dd if=/dev/zero",
            "mkfs",
            "fdisk",
            "mount",
            "umount",
            "sudo",
            "su ",
            "passwd",
            "useradd",
            "userdel",
            "chmod 777 /",
            "chown root",
            "> /dev/",
            "curl http",
            "wget http",
            "nc -l",
            "netcat -l"
        ]

        command_lower = command.lower().strip()

        for pattern in dangerous_patterns:
            if pattern in command_lower:
                return True

        return False

    async def resize_terminal(self, cols: int, rows: int):
        """
        Resize the terminal

        Args:
            cols: Number of columns
            rows: Number of rows
        """
        if self.container:
            try:
                self.container.resize(height=rows, width=cols)
            except Exception as e:
                logger.warning(f"Failed to resize terminal: {e}")

    async def setup_challenge(self, challenge_files: Dict[str, str]):
        """
        Set up files for a specific challenge

        Args:
            challenge_files: Dictionary of filename -> content
        """
        if not self.container:
            raise RuntimeError("Sandbox not initialized")

        for filename, content in challenge_files.items():
            try:
                # Create file in container
                self.container.exec_run(
                    f"bash -c 'cat > {filename}'",
                    stdin=True,
                    workdir=self.working_dir
                )

                # Write content to file
                self.container.exec_run(
                    f"bash -c 'echo {repr(content)} > {filename}'",
                    workdir=self.working_dir
                )

            except Exception as e:
                logger.error(f"Failed to create challenge file {filename}: {e}")

    async def cleanup(self):
        """Clean up the sandbox container"""
        if self.container:
            try:
                self.container.stop(timeout=5)
                logger.info(f"Sandbox container stopped: {self.container_name}")
            except Exception as e:
                logger.error(f"Error stopping container: {e}")
                try:
                    self.container.kill()
                except Exception as kill_error:
                    logger.error(f"Error killing container: {kill_error}")

            self.container = None