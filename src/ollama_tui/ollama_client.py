"""Async wrapper for Ollama CLI commands."""

import asyncio
import json
import logging
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class RemoteModel:
    """Represents a model available on Ollama registry."""

    name: str
    size: str
    modified: str


@dataclass
class Model:
    """Represents a local Ollama model."""

    name: str
    id: str
    size: str
    modified: str


@dataclass
class RunningModel:
    """Represents a running Ollama model."""

    name: str
    id: str
    size: str
    processor: str
    context: str
    until: str


class OllamaClient:
    """Async wrapper for Ollama CLI commands."""

    async def check_available(self) -> bool:
        """Check if ollama CLI is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                "ollama",
                "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.wait()
            return proc.returncode == 0
        except FileNotFoundError:
            return False

    async def list_models(self) -> list[Model]:
        """Get list of local models from 'ollama list'."""
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "list",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return self._parse_list_output(stdout.decode())

    async def list_running(self) -> list[RunningModel]:
        """Get list of running models from 'ollama ps'."""
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "ps",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, _ = await proc.communicate()
        return self._parse_ps_output(stdout.decode())

    async def pull_model(self, model_name: str):
        """Pull a model, yielding progress lines."""
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "pull",
            model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        async for line in proc.stdout:
            yield line.decode().strip()
        await proc.wait()

    async def delete_model(self, model_name: str) -> tuple[bool, str]:
        """Delete a model with 'ollama rm'."""
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "rm",
            model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        success = proc.returncode == 0
        message = stdout.decode() if success else stderr.decode()
        return success, message.strip()

    async def stop_model(self, model_name: str) -> tuple[bool, str]:
        """Stop a running model with 'ollama stop'."""
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "stop",
            model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        success = proc.returncode == 0
        message = stdout.decode() if success else stderr.decode()
        return success, message.strip()

    async def show_model(self, model_name: str) -> str:
        """Get model details with 'ollama show'."""
        proc = await asyncio.create_subprocess_exec(
            "ollama",
            "show",
            model_name,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode == 0:
            return stdout.decode()
        return f"Error: {stderr.decode()}"

    async def search_models(self) -> list[RemoteModel]:
        """Fetch available models from Ollama library via scraping."""
        loop = asyncio.get_event_loop()
        try:
            def fetch():
                req = urllib.request.Request(
                    "https://ollama.com/library",
                    headers={"User-Agent": "ollama-tui/0.1"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode()

            html = await loop.run_in_executor(None, fetch)

            # Extract model names from href="/library/modelname"
            pattern = re.compile(r'href="/library/([^"]+)"')
            model_names = sorted(set(pattern.findall(html)))

            models = [
                RemoteModel(name=name, size="", modified="")
                for name in model_names
                if name and not name.startswith("?")  # Filter out query params
            ]

            logger.info(f"Fetched {len(models)} remote models from library")
            return models
        except Exception as e:
            logger.error(f"Failed to fetch remote models: {e}")
            return []

    def _format_size(self, size_bytes: int) -> str:
        """Format bytes to human readable size."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def _parse_list_output(self, output: str) -> list[Model]:
        """Parse columnar output from ollama list."""
        lines = output.strip().split("\n")
        if len(lines) < 2:
            logger.debug(f"No models found, lines: {lines}")
            return []

        models = []
        # Pattern: NAME (no spaces) | ID (hex) | SIZE (num + unit) | MODIFIED (rest)
        # Example: qwen2.5:7b    845dbda0ea48    4.7 GB    5 hours ago
        pattern = re.compile(r"^(\S+)\s+(\w+)\s+(\d+\.?\d*\s*[KMGT]?B)\s+(.+?)\s*$")

        for line in lines[1:]:
            match = pattern.match(line)
            if match:
                models.append(
                    Model(
                        name=match.group(1),
                        id=match.group(2),
                        size=match.group(3),
                        modified=match.group(4).strip(),
                    )
                )
            else:
                logger.debug(f"Failed to parse line: {line!r}")

        logger.info(f"Parsed {len(models)} models")
        return models

    def _parse_ps_output(self, output: str) -> list[RunningModel]:
        """Parse columnar output from ollama ps."""
        lines = output.strip().split("\n")
        if len(lines) < 2:
            logger.debug("No running models")
            return []

        models = []
        # Pattern: NAME | ID | SIZE | PROCESSOR | CONTEXT | UNTIL
        # Example: qwen2.5:7b    845dbda0ea48    4.7 GB    100% GPU    1234    4 minutes from now
        pattern = re.compile(
            r"^(\S+)\s+(\w+)\s+(\d+\.?\d*\s*[KMGT]?B)\s+(\d+%\s*\w+)\s+(\d+)\s+(.+?)\s*$"
        )

        for line in lines[1:]:
            match = pattern.match(line)
            if match:
                models.append(
                    RunningModel(
                        name=match.group(1),
                        id=match.group(2),
                        size=match.group(3),
                        processor=match.group(4),
                        context=match.group(5),
                        until=match.group(6).strip(),
                    )
                )
            else:
                logger.debug(f"Failed to parse ps line: {line!r}")

        logger.info(f"Parsed {len(models)} running models")
        return models
