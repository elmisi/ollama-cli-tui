"""Async wrapper for Ollama CLI commands."""

import asyncio
import codecs
import html
import json
import logging
import re
import shutil
import time
import urllib.request
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ANSI escape sequence pattern for stripping terminal control codes
ANSI_ESCAPE_PATTERN = re.compile(r'\x1b\[[0-9;]*[a-zA-Z]|\x1b\].*?\x07|\x1b[PX^_].*?\x1b\\')

# Cache configuration
CACHE_DIR = Path.home() / ".cache" / "ollama-tui"
CACHE_TTL = 24 * 60 * 60  # 24 hours in seconds


@dataclass
class RemoteModel:
    """Represents a model available on Ollama registry."""

    name: str
    sizes: str  # Parameter sizes like "7b, 13b, 70b"
    description: str  # Short description of the model


@dataclass
class ModelTag:
    """Represents a specific tag/version of a model."""

    tag: str  # Full tag like "llama3.1:8b"
    size: str  # Download size like "4.9GB"


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
    until: str


def flush_cache() -> None:
    """Delete all cached data."""
    if CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        logger.info(f"Cache flushed: {CACHE_DIR}")


def _get_cache(cache_file: Path) -> dict | None:
    """Get cached data if valid (within TTL)."""
    if not cache_file.exists():
        return None
    try:
        data = json.loads(cache_file.read_text())
        if time.time() - data.get("timestamp", 0) < CACHE_TTL:
            logger.info(f"Cache hit: {cache_file.name}")
            return data
        logger.info(f"Cache expired: {cache_file.name}")
    except (json.JSONDecodeError, KeyError):
        logger.warning(f"Invalid cache file: {cache_file}")
    return None


def _set_cache(cache_file: Path, data: dict) -> None:
    """Save data to cache with timestamp."""
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    data["timestamp"] = time.time()
    cache_file.write_text(json.dumps(data))
    logger.info(f"Cache saved: {cache_file.name}")


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
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        buffer = ""
        # Use incremental decoder to handle multi-byte UTF-8 chars split across chunks
        decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        while True:
            chunk = await proc.stdout.read(256)
            if not chunk:
                # Flush any remaining bytes from decoder
                buffer += decoder.decode(b'', final=True)
                break
            buffer += decoder.decode(chunk)
            # Split by carriage return or newline
            while "\r" in buffer or "\n" in buffer:
                # Find the earliest separator
                r_pos = buffer.find("\r")
                n_pos = buffer.find("\n")
                if r_pos == -1:
                    pos = n_pos
                elif n_pos == -1:
                    pos = r_pos
                else:
                    pos = min(r_pos, n_pos)
                line = buffer[:pos].strip()
                buffer = buffer[pos + 1:]
                if line:
                    # Strip ANSI escape sequences from output
                    clean_line = ANSI_ESCAPE_PATTERN.sub('', line)
                    if clean_line:
                        yield clean_line
        # Yield any remaining content
        if buffer.strip():
            clean_buffer = ANSI_ESCAPE_PATTERN.sub('', buffer.strip())
            if clean_buffer:
                yield clean_buffer
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
        """Fetch available models from Ollama library via scraping (cached 24h)."""
        cache_file = CACHE_DIR / "models.json"

        # Check cache first
        cached = _get_cache(cache_file)
        if cached and "models" in cached:
            return [RemoteModel(**m) for m in cached["models"]]

        # Fetch from network
        loop = asyncio.get_event_loop()
        try:
            def fetch():
                req = urllib.request.Request(
                    "https://ollama.com/library",
                    headers={"User-Agent": "ollama-tui/0.1"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode()

            page_content = await loop.run_in_executor(None, fetch)

            # Split by model links and parse each block
            models = []
            model_blocks = re.split(r'<a href="/library/', page_content)[1:]

            for block in model_blocks:
                # Extract name
                name_match = re.match(r'([^"]+)', block)
                if not name_match:
                    continue
                name = name_match.group(1)
                if not name or name.startswith("?"):
                    continue

                # Extract sizes (parameter counts like 7b, 70b)
                sizes = re.findall(r'x-test-size[^>]*>([^<]+)</span>', block)
                sizes_str = ", ".join(sizes) if sizes else "-"

                # Extract description (decode HTML entities)
                desc_match = re.search(r'text-neutral-800 text-md">([^<]+)</p>', block)
                description = html.unescape(desc_match.group(1).strip()) if desc_match else ""

                models.append(RemoteModel(name=name, sizes=sizes_str, description=description))

            logger.info(f"Fetched {len(models)} remote models from library")

            # Save to cache
            _set_cache(cache_file, {"models": [asdict(m) for m in models]})

            return models
        except Exception as e:
            logger.error(f"Failed to fetch remote models: {e}")
            return []

    async def fetch_model_tags(self, model_name: str) -> list[ModelTag]:
        """Fetch available tags/versions for a model with their sizes (cached 24h)."""
        cache_file = CACHE_DIR / "tags" / f"{model_name}.json"

        # Check cache first
        cached = _get_cache(cache_file)
        if cached and "tags" in cached:
            return [ModelTag(**t) for t in cached["tags"]]

        # Fetch from network
        loop = asyncio.get_event_loop()
        try:
            def fetch():
                req = urllib.request.Request(
                    f"https://ollama.com/library/{model_name}/tags",
                    headers={"User-Agent": "ollama-tui/0.1"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    return resp.read().decode()

            page_content = await loop.run_in_executor(None, fetch)

            tags = []
            # Find all tag entries: input with value and following size
            # Pattern: <input class="command hidden" value="model:tag" /> ... <p class="col-span-2 text-neutral-500 text-[13px]">SIZE</p>
            blocks = re.split(r'<input class="command hidden" value="', page_content)[1:]

            for block in blocks:
                # Extract tag name
                tag_match = re.match(r'([^"]+)"', block)
                if not tag_match:
                    continue
                tag = tag_match.group(1)

                # Extract size
                size_match = re.search(r'col-span-2 text-neutral-500 text-\[13px\]">([^<]+)</p>', block)
                size = size_match.group(1).strip() if size_match else "-"

                tags.append(ModelTag(tag=tag, size=size))

            logger.info(f"Fetched {len(tags)} tags for {model_name}")

            # Save to cache
            _set_cache(cache_file, {"tags": [asdict(t) for t in tags]})

            return tags
        except Exception as e:
            logger.error(f"Failed to fetch tags for {model_name}: {e}")
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
        # Pattern: NAME | ID | SIZE | PROCESSOR | UNTIL
        # Example: qwen2.5:7b    845dbda0ea48    4.7 GB    100% GPU    4 minutes from now
        pattern = re.compile(
            r"^(\S+)\s+(\w+)\s+(\d+\.?\d*\s*[KMGT]?B)\s+(\d+%\s*\w+)\s+(.+?)\s*$"
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
                        until=match.group(5).strip(),
                    )
                )
            else:
                logger.debug(f"Failed to parse ps line: {line!r}")

        logger.info(f"Parsed {len(models)} running models")
        return models
