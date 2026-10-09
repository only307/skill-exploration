"""Original, standard-library process and dependency helpers."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]


class ConversionError(Exception):
    pass


HINTS = {
    "docling": 'uv pip install --python .venv\\Scripts\\python.exe "docling==2.135.0"',
    "md2x": 'uv pip install --python .venv\\Scripts\\python.exe "md2x==0.1.0"',
    "pandoc": 'uv pip install --python .venv\\Scripts\\python.exe pypandoc_binary',
    "xelatex": '安装用户级 MiKTeX：https://miktex.org/download；补齐 LaTeX 包后设置 ROUTER_XELATEX。',
    "node": '从 https://nodejs.org/en/download 下载 Windows ZIP，设置 ROUTER_NODE 为 node.exe。',
    "mmdc": 'npm install --prefix .tools\\mermaid @mermaid-js/mermaid-cli@12.0.0；设置 ROUTER_MMDC_JS 为该包 src\\cli.js。',
    "soffice": '安装 LibreOffice：https://www.libreoffice.org/download/；设置 ROUTER_SOFFICE 为 soffice.exe。',
}


def tool(name: str, required: bool = True) -> str | None:
    override = os.environ.get("ROUTER_" + name.upper())
    candidates = [override] if override else [str(Path(sys.executable).parent / (name + (".exe" if os.name == "nt" else "")))]
    found = shutil.which(name) if not override else None
    if found:
        candidates.append(found)
    if name == "xelatex" and not override:
        candidates += [str(Path.home() / ".cache/document-router-tools/TinyTeX/bin/windows/xelatex.exe"),
                       str(ROOT / ".tools/TinyTeX/bin/windows/xelatex.exe")]
    if name == "pandoc" and not override:
        # pypandoc_binary's private installation, without invoking a downloader.
        import importlib.util
        spec = importlib.util.find_spec("pypandoc")
        if spec and spec.origin:
            candidates.append(str(Path(spec.origin).parent / "files" / ("pandoc.exe" if os.name == "nt" else "pandoc")))
    for value in candidates:
        if value and Path(value).is_file():
            p = Path(value).resolve()
            if p.suffix.lower() in {".cmd", ".bat", ".ps1"}:
                continue  # Never pass document paths through a command interpreter.
            return str(p)
    if required:
        raise ConversionError(f"缺少依赖 {name}。{HINTS.get(name, '请安装并加入 PATH 或设置 ROUTER_' + name.upper())}")
    return None


def mermaid_command(required: bool = True) -> list[str] | None:
    js = os.environ.get("ROUTER_MMDC_JS")
    if not js:
        local = ROOT / ".tools/mermaid/node_modules/@mermaid-js/mermaid-cli/src/cli.js"
        if local.is_file():
            js = str(local)
    if not js:
        shim = shutil.which("mmdc")
        if shim:
            candidate = Path(shim).parent / "node_modules/@mermaid-js/mermaid-cli/src/cli.js"
            if candidate.is_file():
                js = str(candidate)
    if js and Path(js).is_file():
        node = tool("node", required=required)
        return [node, str(Path(js).resolve())] if node else None
    executable = tool("mmdc", required=False)
    if executable:
        return [executable]
    if required:
        raise ConversionError("缺少 Mermaid CLI。" + HINTS["mmdc"])
    return None


def chrome_path() -> str | None:
    candidates = [os.environ.get("ROUTER_CHROME")]
    if os.name == "nt":
        for base in (os.environ.get("PROGRAMFILES"), os.environ.get("PROGRAMFILES(X86)"), os.environ.get("LOCALAPPDATA")):
            if base:
                candidates += [str(Path(base) / "Microsoft/Edge/Application/msedge.exe"),
                               str(Path(base) / "Google/Chrome/Application/chrome.exe")]
    return next((str(Path(p).resolve()) for p in candidates if p and Path(p).is_file()), None)


def run(args: list[str], cwd: Path | None = None, timeout: int = 600,
        stdin: str | None = None, offline: bool = True) -> str:
    env = os.environ.copy()
    env.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", NO_COLOR="1", TERM="dumb")
    if offline:
        env.update(HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", HF_HUB_DISABLE_TELEMETRY="1")
    try:
        p = subprocess.run(args, cwd=cwd, env=env, input=stdin, capture_output=True,
                           text=True, encoding="utf-8", errors="replace", shell=False, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise ConversionError(f"程序启动失败或超时：{Path(args[0]).name}：{e}") from e
    if p.returncode:
        raise ConversionError(f"{Path(args[0]).name} 退出码 {p.returncode}：\n{(p.stderr or p.stdout)[-5000:]}")
    return p.stdout
