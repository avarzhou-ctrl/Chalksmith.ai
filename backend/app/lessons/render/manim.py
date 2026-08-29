import asyncio
import ast
import os
import re
import signal
from pathlib import Path
from urllib.parse import urlparse

import httpx
from google.auth.transport.requests import Request
from google.oauth2 import id_token

from backend.app.lessons.render.base import (
    ArtifactLimitError,
    GeneratedCodeError,
    InfrastructureRenderError,
    PolicyViolationError,
    RenderedAsset,
)


class LocalManimRenderer:
    def __init__(self, timeout_seconds: int, max_render_bytes: int) -> None:
        self.timeout_seconds = timeout_seconds
        self.max_render_bytes = max_render_bytes

    async def render(self, code: str, workdir: Path) -> RenderedAsset:
        validate_manim_code(code)
        source = workdir / "lesson.py"
        source.write_text(code, encoding="utf-8")
        log_path = workdir / "manim.log"
        with log_path.open("wb") as log_file:
            try:
                process = await asyncio.create_subprocess_exec(
                    "manim",
                    "-ql",
                    "--disable_caching",
                    "--media_dir",
                    str(workdir / "media"),
                    str(source),
                    "GeneratedScene",
                    cwd=workdir,
                    env={
                        "PATH": os.environ.get("PATH", "/usr/local/bin:/usr/bin:/bin"),
                        "HOME": str(workdir),
                        "TMPDIR": str(workdir),
                        "LANG": "C.UTF-8",
                    },
                    stdout=log_file,
                    stderr=asyncio.subprocess.STDOUT,
                    start_new_session=True,
                )
            except OSError as error:
                raise InfrastructureRenderError("The Manim executable is unavailable.") from error
            try:
                await asyncio.wait_for(process.wait(), timeout=self.timeout_seconds)
            except asyncio.CancelledError:
                await _terminate_process_group(process)
                raise
            except TimeoutError as error:
                await _terminate_process_group(process)
                raise ArtifactLimitError("Manim rendering timed out.") from error
        if process.returncode != 0:
            diagnostic = _clean_diagnostic(_read_log_tail(log_path))
            raise GeneratedCodeError(diagnostic)
        videos = list((workdir / "media").rglob("*.mp4"))
        if not videos:
            raise InfrastructureRenderError("Manim completed without producing an MP4 file.")
        if videos[0].stat().st_size > self.max_render_bytes:
            raise ArtifactLimitError("The rendered video exceeds the output size limit.")
        return RenderedAsset(path=videos[0], content_type="video/mp4", extension="mp4")


class RemoteManimRenderer:
    def __init__(
        self,
        url: str,
        timeout_seconds: int,
        max_render_bytes: int,
        *,
        authenticate: bool = True,
    ) -> None:
        self.url = url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self.max_render_bytes = max_render_bytes
        self.authenticate = authenticate

    async def render(self, code: str, workdir: Path) -> RenderedAsset:
        headers: dict[str, str] = {}
        try:
            if self.authenticate:
                token = await asyncio.to_thread(id_token.fetch_id_token, Request(), self.url)
                headers["Authorization"] = f"Bearer {token}"
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.post(
                    f"{self.url}/internal/render/manim",
                    json={"code": code},
                    headers=headers,
                )
        except Exception as error:
            raise InfrastructureRenderError("The remote Manim renderer is unavailable.") from error
        if response.status_code == 422:
            raise GeneratedCodeError(response.text[-4000:])
        if response.status_code in {413, 504}:
            raise ArtifactLimitError(response.text[-4000:])
        if response.status_code != 200:
            raise InfrastructureRenderError(
                f"The remote Manim renderer returned HTTP {response.status_code}."
            )
        if len(response.content) > self.max_render_bytes:
            raise ArtifactLimitError("The rendered video exceeds the output size limit.")
        output = workdir / "lesson.mp4"
        output.write_bytes(response.content)
        return RenderedAsset(path=output, content_type="video/mp4", extension="mp4")


class UnavailableManimRenderer:
    async def render(self, _code: str, _workdir: Path) -> RenderedAsset:
        raise InfrastructureRenderError("The isolated Manim renderer is not configured.")


def is_local_renderer_url(url: str) -> bool:
    return urlparse(url).hostname in {"localhost", "127.0.0.1", "::1"}


async def _terminate_process_group(process: asyncio.subprocess.Process) -> None:
    if process.returncode is not None:
        return
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    await process.wait()


def _read_log_tail(path: Path, limit: int = 16_000) -> str:
    with path.open("rb") as log_file:
        log_file.seek(0, os.SEEK_END)
        size = log_file.tell()
        log_file.seek(max(0, size - limit))
        return log_file.read().decode("utf-8", errors="replace")


def _clean_diagnostic(output: str) -> str:
    cleaned = re.sub(r"\x1b\[[0-9;]*m", "", output)
    return cleaned[-4000:] or "Manim rendering failed."


def validate_manim_code(code: str) -> None:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        raise GeneratedCodeError(
            f"Generated Manim code has invalid syntax: {error.msg}."
        ) from error

    allowed_imports = {"manim", "math", "numpy", "random"}
    forbidden_calls = {
        "breakpoint",
        "classmethod",
        "compile",
        "delattr",
        "dir",
        "eval",
        "exec",
        "getattr",
        "globals",
        "help",
        "input",
        "locals",
        "memoryview",
        "open",
        "property",
        "setattr",
        "staticmethod",
        "type",
        "vars",
        "__import__",
    }
    forbidden_attributes = {
        "DataSource",
        "fromfile",
        "genfromtxt",
        "load",
        "load_library",
        "loadtxt",
        "memmap",
        "popen",
        "save",
        "savetxt",
        "system",
        "tofile",
    }
    forbidden_objects = {"Code", "ImageMobject", "SVGMobject"}
    has_scene = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [alias.name for alias in node.names] if isinstance(node, ast.Import) else [node.module or ""]
            if any(name.split(".", 1)[0] not in allowed_imports for name in names):
                raise PolicyViolationError("Generated Manim code imports a blocked module.")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_calls:
            raise PolicyViolationError(
                f"Generated Manim code calls blocked function {node.func.id}."
            )
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in forbidden_objects:
            raise PolicyViolationError(
                f"Generated Manim code uses blocked object {node.func.id}."
            )
        if isinstance(node, ast.Name) and (
            node.id.startswith("__") or node.id in forbidden_calls
        ):
            raise PolicyViolationError("Generated Manim code uses blocked runtime internals.")
        if isinstance(node, ast.Attribute) and (
            node.attr.startswith("_")
            or node.attr in forbidden_attributes
            or node.attr in forbidden_objects
        ):
            raise PolicyViolationError("Generated Manim code uses blocked runtime introspection.")
        if isinstance(node, ast.ClassDef) and node.name == "GeneratedScene":
            has_scene = True
    if not has_scene:
        raise GeneratedCodeError("Generated Manim code must define GeneratedScene.")
