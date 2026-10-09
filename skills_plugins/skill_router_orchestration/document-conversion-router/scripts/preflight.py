"""Read-only, route-specific dependency check. Does not install or download."""
from __future__ import annotations

import argparse
import importlib.metadata
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

from common import ConversionError, HINTS, chrome_path, mermaid_command, run, tool


def check(path="all", mermaid=False):
    required = {
        "pdf-md": {"docling", "pandoc"}, "docx-md": {"docling", "pandoc"},
        "md-docx": {"md2x", "pandoc"}, "md-pdf": {"md2x", "pandoc", "xelatex"},
        "pdf-docx": {"docling", "md2x", "pandoc"}, "docx-pdf": {"soffice"},
        "all": {"docling", "md2x", "pandoc", "xelatex"},
    }[path]
    if mermaid:
        required |= {"node", "mmdc"}
    result = {"python": {"version": sys.version.split()[0], "executable": sys.executable,
                         "ok": sys.version_info >= (3, 10)},
              "package_manager": {n: shutil.which(n) for n in ("uv", "pipx", "pip")},
              "route": path, "dependencies": {}, "models": {
                  "readiness": "未验证；离线样例转换成功才能确认所需模型齐备",
                  "explicit_directory": os.environ.get("ROUTER_MODELS"),
                  "cache": os.environ.get("HF_HOME", str(Path.home() / ".cache/huggingface"))}}
    missing = []
    for name in ("docling", "md2x", "pandoc", "node", "mmdc", "xelatex", "dot", "soffice"):
        cmd = mermaid_command(False) if name == "mmdc" else ([tool(name, False)] if tool(name, False) else None)
        status = {"required": name in required, "command": cmd, "available": bool(cmd)}
        if cmd:
            try:
                flag = "--help" if name in {"docling", "md2x"} else ("-V" if name == "dot" else "--version")
                output = run(cmd + [flag], timeout=90)
                status["probe_ok"] = True
                status["probe"] = output.strip()[:600]
                if name == "docling":
                    status["cli_style"] = "convert subcommand" if "convert-remote" in output else "legacy positional"
                    status["router_mode"] = "local Python API, remote services disabled"
            except ConversionError as e:
                status.update(probe_ok=False, error=str(e))
        else:
            status["installation_hint"] = HINTS.get(name, "可选依赖，无需安装")
        if name in required and (not cmd or status.get("probe_ok") is False):
            missing.append(name)
        result["dependencies"][name] = status
    packages = {}
    for name in ("docling", "md2x", "pypdf", "Pillow", "onnxruntime", "rapidocr"):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    result["packages"] = packages
    result["browser"] = {"detected": chrome_path(), "note": "未检测到时需已下载 Puppeteer 浏览器；预检不下载。"}
    for package in ("pypdf", "Pillow"):
        if packages[package] is None:
            missing.append(package)
    try:
        import torch
        result["gpu"] = {"cuda_available": torch.cuda.is_available(), "torch": torch.__version__,
                         "required": False, "mode": "默认 CPU；high 使用 Egret Medium 布局，不隐式启用 GPU/VLM"}
    except ImportError:
        result["gpu"] = {"cuda_available": None, "required": False}
    result["missing_required"] = missing
    result["ok"] = result["python"]["ok"] and not missing
    return result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--for", dest="route", default="all", choices=["all", "pdf-md", "docx-md", "md-docx", "md-pdf", "pdf-docx", "docx-pdf"])
    ap.add_argument("--mermaid", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    result = check(args.route, args.mermaid)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
