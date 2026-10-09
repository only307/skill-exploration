"""Local PDF/DOCX/Markdown router. CLI output is one UTF-8 JSON object."""
from __future__ import annotations

import argparse
from collections import Counter
import copy
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import sys
import tempfile
import uuid
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

from common import ConversionError, ROOT, chrome_path, mermaid_command, run, tool

READER = "markdown-raw_tex-raw_html"
NS = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
      "a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
LOSS = "经 Markdown 重构属于有损转换：分页、字体、栏布局、公式和复杂对象可能变化；不保证 PDF 像素或语义无损往返。"
WORD_LOSS = "Word 的批注、修订、文本框、SmartArt、宏、嵌入对象和复杂分页可能丢失；已渲染流程图只能保留为图片，不能恢复原始 Mermaid。"


def detect(path: Path) -> str:
    if not path.is_file():
        raise ConversionError(f"输入文件不存在：{path}")
    with path.open("rb") as f:
        head = f.read(4096)
    if head.lstrip().startswith(b"%PDF-"):
        pdf_info(path)
        return "pdf"
    if head.startswith(b"PK"):
        try:
            with zipfile.ZipFile(path) as z:
                if z.testzip() is not None:
                    raise ConversionError("OOXML 压缩包损坏。")
                types = ET.fromstring(z.read("[Content_Types].xml"))
                if not any(x.get("ContentType") == "application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml" for x in types):
                    raise ConversionError("ZIP 不是普通 DOCX；宏文档和其他 Office 格式不在支持范围。")
                ET.fromstring(z.read("word/document.xml"))
                return "docx"
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
            raise ConversionError(f"不是有效 DOCX：{e}") from e
    try:
        text = path.read_text(encoding="utf-8-sig")
    except (UnicodeError, OSError) as e:
        raise ConversionError("不支持的文件签名或编码；Markdown 必须为 UTF-8。") from e
    if not text.strip() or any(ord(c) < 32 and c not in "\r\n\t" for c in text):
        raise ConversionError("输入为空或含二进制控制字符，无法识别为 Markdown。")
    if text.lstrip().startswith(("{\\rtf", "<!DOCTYPE", "<html", "<?xml")):
        raise ConversionError("检测到 RTF/HTML/XML；不属于支持的 Markdown 输入。")
    # Markdown has no magic signature. Content evidence is required for non-MD names.
    if path.suffix.lower() in {".md", ".markdown"} or re.search(r"(?m)^\s{0,3}(#{1,6}\s+|`{3,}|~{3,}|[-*+]\s+|\|.*\|)", text):
        return "md"
    raise ConversionError("无法凭内容确认 Markdown；纯文本无格式签名，请明确以 .md 文件提供。")


def route(kind: str, target: str, reflow: bool = False) -> list[str]:
    paths = {("pdf", "md"): ["docling"], ("docx", "md"): ["docling"],
             ("md", "docx"): ["md2x"], ("md", "pdf"): ["md2x"],
             ("pdf", "docx"): ["docling", "md2x"],
             ("docx", "pdf"): ["docling", "md2x"] if reflow else ["libreoffice"]}
    if (kind, target) not in paths:
        raise ConversionError(f"未支持的转换路径：{kind} → {target}")
    return paths[kind, target]


def pdf_info(path: Path) -> dict:
    try:
        from pypdf import PdfReader
    except ImportError as e:
        raise ConversionError("缺少 PDF 验证依赖 pypdf：在运行路由器的虚拟环境安装 pypdf。") from e
    try:
        reader = PdfReader(path, strict=True)
        if reader.is_encrypted:
            raise ConversionError("加密 PDF 需要先在本机解密。")
        if not reader.pages:
            raise ConversionError("PDF 无有效页面。")
        return {"pages": len(reader.pages), "text": "\n".join(p.extract_text() or "" for p in reader.pages)}
    except ConversionError:
        raise
    except Exception as e:
        raise ConversionError(f"PDF 验证失败：{e}") from e


def quality(text: str, expected: list[str]) -> None:
    if not text.strip():
        raise ConversionError("结果为空。")
    if text.count("\ufffd") > max(2, len(text) * 0.02):
        raise ConversionError("结果含大量乱码。")
    lines = [x.strip() for x in text.splitlines() if len(x.strip()) > 30]
    if len(lines) >= 12 and Counter(lines).most_common(1)[0][1] > len(lines) * 0.65:
        raise ConversionError("结果存在异常重复。")
    compact = re.sub(r"\s+", "", text).casefold()
    for snippet in expected:
        if re.sub(r"\s+", "", snippet).casefold() not in compact:
            raise ConversionError(f"结果缺少代表性文字：{snippet!r}")


def pandoc_ast(path: Path) -> dict:
    return json.loads(run([tool("pandoc"), str(path), "-f", READER, "-t", "json"]))


def write_ast(ast: dict, dest: Path) -> None:
    run([tool("pandoc"), "-f", "json", "-t", "markdown-raw_tex-raw_html", "--wrap=none", "-o", str(dest)],
        stdin=json.dumps(ast, ensure_ascii=False), cwd=dest.parent)


def walk(value):
    if isinstance(value, dict):
        yield value
        for v in value.values():
            yield from walk(v)
    elif isinstance(value, list):
        for v in value:
            yield from walk(v)


def normalize(md: Path, work: Path, warnings: list[str]) -> tuple[dict, list[Path]]:
    ast = pandoc_ast(md)
    if ast.get("meta"):
        warnings.append("输出管线忽略 YAML 元数据，避免其中的引擎选项或包含指令被执行；原文已保存。")
        ast["meta"] = {}
    assets = work / "assets"
    assets.mkdir(exist_ok=True)
    images = []
    for node in walk(ast["blocks"]):
        if node.get("t") not in {"Image", "Link"}:
            continue
        is_image = node["t"] == "Image"
        raw = node["c"][-1][0]
        url = urllib.parse.urlsplit(raw)
        local_uri = url.scheme == "file" and url.netloc in {"", "localhost"}
        local_absolute = Path(raw).is_absolute() and not raw.startswith(("\\\\", "//"))
        if (url.scheme and not local_uri and not local_absolute) or (url.netloc and not local_uri) or raw.startswith(("\\\\", "//")):
            if is_image:
                raise ConversionError(f"图片必须已在本机：拒绝远程/数据/绝对 URL {raw[:120]}")
            continue
        if not url.path:  # In-document anchor.
            continue
        src = Path(urllib.request.url2pathname(url.path)).resolve() if local_uri else (Path(raw).resolve() if local_absolute else (md.parent / urllib.parse.unquote(url.path)).resolve())
        if str(src).startswith(("\\\\", "//")):
            raise ConversionError("拒绝网络共享资源；请先将资源复制到本地。")
        if not src.is_file():
            if is_image:
                raise ConversionError(f"图片引用不存在：{raw}")
            warnings.append(f"相对链接目标不存在，保留原引用：{raw}")
            continue
        if src.suffix.lower() in {".svg", ".html", ".htm"} and is_image:
            raise ConversionError("SVG/HTML 图片请先离线转为 PNG；避免图像内的外部资源引用。")
        digest = hashlib.sha256(src.read_bytes()).hexdigest()[:20]
        dest = assets / (digest + src.suffix.lower())
        if not dest.exists():
            shutil.copy2(src, dest)
        node["c"][-1][0] = "assets/" + dest.name + ("#" + url.fragment if url.fragment else "")
        if is_image:
            images.append(dest)
    return ast, images


def render_mermaid(ast: dict, work: Path) -> tuple[dict, list[Path], list[str]]:
    rendered = copy.deepcopy(ast)
    images, codes = [], []
    for node in walk(rendered["blocks"]):
        if node.get("t") != "CodeBlock" or "mermaid" not in node["c"][0][1]:
            continue
        code = node["c"][1]
        if not code.strip():
            raise ConversionError("Mermaid 代码块为空。")
        if re.search(r"(?:https?|file|data):|<\s*(?:img|iframe|script)\b", code, re.I):
            raise ConversionError("离线 Mermaid 不允许 URL 或外部图像/脚本，请先改用本地图形元素。")
        number = len(images) + 1
        src = work / "assets" / f"mermaid-{number}.mmd"
        png = src.with_suffix(".png")
        src.write_text(code, encoding="utf-8")
        renderer = mermaid_command()
        help_text = run(renderer + ["--help"], timeout=30)
        size_args = ["--size", "1600"] if "--size" in help_text else ["-w", "1600"]
        args = renderer + ["-i", str(src), "-o", str(png), "-b", "white"] + size_args
        browser = chrome_path()
        if browser:
            config = work / "puppeteer.json"
            config.write_text(json.dumps({"executablePath": str(Path(browser).resolve())}), encoding="utf-8")
            args += ["-p", str(config)]
        run(args, cwd=work, timeout=180)
        if not png.is_file() or png.stat().st_size < 100:
            raise ConversionError(f"Mermaid {number} 未产生有效图像。")
        try:
            from PIL import Image, ImageStat
            with Image.open(png) as im:
                im.load()
                # A solid rectangle is not a usable diagram.
                if max(ImageStat.Stat(im.convert("RGB")).var) < 1:
                    raise ConversionError(f"Mermaid {number} 图像为空白。")
        except ImportError as e:
            raise ConversionError("验证 Mermaid 需要 Pillow：请在虚拟环境安装 Pillow。") from e
        node.clear()
        node.update(t="Para", c=[{"t": "Image", "c": [["", [], []],
                    [{"t": "Str", "c": f"Diagram-{number}"}], ["assets/" + png.name, ""]]}])
        images.append(png)
        codes.append(code)
    return rendered, images, codes


def inbound(source: Path, kind: str, work: Path, args, warnings: list[str]) -> Path:
    tool("docling")  # Actionable installation error, before spawning the adapter.
    scan = kind == "pdf" and not pdf_info(source)["text"].strip()
    attempts = [scan or args.ocr]
    if kind == "pdf" and not attempts[0]:
        attempts.append(True)  # Exactly one local full-page OCR fallback.
    failures = []
    for attempt, ocr in enumerate(attempts):
        dest = work / f"inbound-{attempt}"
        cmd = [sys.executable, str(ROOT / "scripts/docling_worker.py"), str(source), str(dest)]
        if ocr:
            cmd.append("--ocr")
        if args.quality == "high":
            cmd.append("--high")
        if args.models:
            cmd += ["--models", str(args.models.resolve())]
        try:
            run(cmd, cwd=work, timeout=args.timeout, offline=not args.allow_model_download)
            md = dest / "content.md"
            quality(md.read_text(encoding="utf-8"), args.expect)
            if attempt:
                warnings.append("标准解析未通过验证，已仅重试一次本地全页 OCR。")
            return md
        except (ConversionError, OSError) as e:
            failures.append(str(e))
    raise ConversionError("入站解析失败，已停止。\n" + "\n".join(failures))


def outbound(md: Path, dest: Path, args) -> None:
    exe = tool("md2x")
    help_text = run([exe, "--help"], timeout=30)
    prefix = [exe, "convert"] if re.search(r"\bconvert\b", help_text) and "site" in help_text else [exe]
    config = {"mermaid": {"on_failure": "error"}, "output": {"toc": False},
              "binaries": {"pandoc": tool("pandoc")},
              "advanced": {"no_clobber": True, "header_includes": [],
                           "pandoc_extra_args": ["--from=" + READER]}}
    if dest.suffix == ".pdf":
        config["binaries"]["xelatex"] = tool("xelatex")
        if args.cjk_font:
            config["fonts"] = {"cjk": args.cjk_font}
        elif re.search(r"[\u3400-\u9fff]", md.read_text(encoding="utf-8")):
            raise ConversionError("中文 PDF 请指定已安装字体，例如 --cjk-font 'Microsoft YaHei'，避免静默缺字。")
    cfg = md.parent / "router-md2x.json"  # JSON is a valid YAML subset.
    cfg.write_text(json.dumps(config), encoding="utf-8")
    try:
        run(prefix + [str(md), "-o", str(dest), "--config", str(cfg)], cwd=md.parent, timeout=args.timeout)
    except ConversionError as e:
        if "xeCJK.sty" in str(e) and "not found" in str(e):
            raise ConversionError("XeLaTeX 缺少中文支持包 xeCJK。请在所用用户级/便携 TeX 环境执行 tlmgr install xecjk（或用 MiKTeX Console 安装 xeCJK），准备齐备后再离线转换；路由器不会自动在线装包。") from e
        raise


def pixel_signature(image):
    rgb = image.convert("RGB")
    return rgb.size, hashlib.sha256(rgb.tobytes()).hexdigest()


def validate_output(path: Path, kind: str, expected: list[str], diagrams: list[Path],
                    codes: list[str], source_ast: dict | None, pictures: list[Path] | None = None) -> dict:
    if not path.is_file() or path.stat().st_size == 0:
        raise ConversionError("输出不存在或为空。")
    result = {"bytes": path.stat().st_size}
    if kind == "md":
        quality(path.read_text(encoding="utf-8"), expected)
        result["markdown_nonempty"] = True
        return result
    if kind == "docx":
        try:
            with zipfile.ZipFile(path) as z:
                if z.testzip():
                    raise ConversionError("输出 DOCX ZIP 损坏。")
                ET.fromstring(z.read("[Content_Types].xml"))
                root = ET.fromstring(z.read("word/document.xml"))
                text = " ".join(n.text or "" for n in root.findall(".//w:t", NS))
                quality(text, expected)
                relationship = ET.fromstring(z.read("word/_rels/document.xml.rels"))
                targets = {x.get("Id"): x.get("Target") for x in relationship if x.get("TargetMode") != "External"}
                embedded = []
                for blip in root.findall(".//a:blip", NS):
                    rid = blip.get("{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed")
                    if rid not in targets:
                        raise ConversionError("DOCX 图片没有有效关系。")
                    import posixpath
                    part = posixpath.normpath("word/" + targets[rid])
                    embedded.append(z.read(part))
                for image in diagrams + (pictures or []):
                    if image.read_bytes() not in embedded:
                        raise ConversionError(f"DOCX 中未找到要求保留的实际图像：{image.name}")
                if source_ast:
                    if any(n.get("t") == "Table" for n in walk(source_ast)) and not root.findall(".//w:tbl", NS):
                        raise ConversionError("原文表格未进入 DOCX。")
                    if any(n.get("t") == "Header" for n in walk(source_ast)) and not root.findall(".//w:pStyle", NS):
                        raise ConversionError("原文标题未形成 DOCX 段落样式。")
                result.update(valid_ooxml=True, embedded_images=len(embedded))
        except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
            raise ConversionError(f"DOCX 结构验证失败：{e}") from e
    else:
        info = pdf_info(path)
        text = info.pop("text")
        quality(text, expected)
        result.update(info)
        if diagrams or pictures:
            from PIL import Image
            from pypdf import PdfReader
            actual = {pixel_signature(img.image) for p in PdfReader(path).pages for img in p.images}
            for image in diagrams + (pictures or []):
                with Image.open(image) as im:
                    if pixel_signature(im) not in actual:
                        raise ConversionError(f"PDF 中未找到要求保留的图像像素内容：{image.name}")
            result["mermaid_pixel_matches"] = len(diagrams)
    for code in codes:
        if code.strip() in text:
            raise ConversionError("Mermaid 源码裸露在最终文档中。")
    result["mermaid_verified"] = len(diagrams)
    return result


def automatic_expected(ast: dict) -> list[str]:
    # A representative heading/paragraph, not syntax or picture labels.
    for block in ast["blocks"]:
        if block.get("t") in {"Header", "Para"}:
            words = [n["c"] for n in walk(block) if n.get("t") == "Str"]
            if words:
                return [" ".join(words)[:80]]
    return []


def convert(args) -> dict:
    source, output = args.input.resolve(), args.output.resolve()
    if source == output:
        raise ConversionError("不能覆盖输入文件。")
    if output.exists() and not args.overwrite:
        raise ConversionError(f"目标已存在，未覆盖：{output}；明确授权后可使用 --overwrite。")
    target = args.to or output.suffix.lower().lstrip(".")
    target = "md" if target == "markdown" else target
    if target not in {"md", "docx", "pdf"} or output.suffix.lower() not in ({".md", ".markdown"} if target == "md" else {"." + target}):
        raise ConversionError("目标格式或输出扩展名不一致；支持 .md/.docx/.pdf。")
    kind = detect(source)
    engines = route(kind, target, args.reflow)
    warnings = []
    if source.suffix.lower() not in {"." + kind, ".markdown" if kind == "md" else "." + kind}:
        warnings.append(f"扩展名与真实类型不一致；已按 {kind} 处理。")
    if kind in {"pdf", "docx"} and engines != ["libreoffice"]:
        warnings.append(LOSS)
    if kind == "pdf" and os.name == "nt":
        warnings.append("Windows 使用 Docling 的 PDFium 后端，避免原生解析器在中文安装路径下的资源读取问题。")
    if kind == "docx":
        warnings.append(WORD_LOSS)
    if engines == ["libreoffice"]:
        warnings.append("LibreOffice 与 Word 的字体替换和排版实现可能造成分页差异，请检查重要页面。")
    # Resolve all known dependencies before spending time on conversion.
    for name in engines:
        tool("soffice" if name == "libreoffice" else name)
    if engines != ["libreoffice"]:
        tool("pandoc")
    if "md2x" in engines and target == "pdf":
        tool("xelatex")
    output.parent.mkdir(parents=True, exist_ok=True)
    resource_name = output.stem + ".resources-" + uuid.uuid4().hex[:10]
    resources = output.parent / resource_name
    with tempfile.TemporaryDirectory(prefix=".router-", dir=output.parent) as tmp:
        work = Path(tmp)
        bundle = work / resource_name
        bundle.mkdir()
        staged_source = work / ("input." + kind)
        shutil.copy2(source, staged_source)
        staged_output = work / ("output." + target)
        diagrams, codes, ast, source_images = [], [], None, []
        if engines == ["libreoffice"]:
            profile = (work / "office-profile").as_uri()
            run([tool("soffice"), "-env:UserInstallation=" + profile, "--headless", "--convert-to", "pdf",
                 "--outdir", str(work), str(staged_source)], cwd=work, timeout=args.timeout)
            staged_output = work / "input.pdf"
            expected = args.expect
            if not expected:
                with zipfile.ZipFile(source) as z:
                    xml = ET.fromstring(z.read("word/document.xml"))
                    expected = [(n.text or "") for n in xml.findall(".//w:t", NS) if (n.text or "").strip()][:1]
        else:
            md = source if kind == "md" else inbound(staged_source, kind, work, args, warnings)
            shutil.copy2(md, bundle / "source.md")
            ast, source_images = normalize(md, bundle, warnings)
            write_ast(ast, bundle / "content.md")
            if kind == "pdf":
                pages = md.parent / "pages"
                if pages.is_dir():
                    shutil.copytree(pages, bundle / "assets/pages")
                    warnings.append("已在 Markdown 附录及资源包 assets/pages 保留整页图像，补充保存未识别为独立图片的图形；中转 DOCX 也会嵌入原页图像，体积可能增加。未重建 Mermaid 源码。")
            expected = args.expect or automatic_expected(ast)
            if target == "md":
                published_ast = copy.deepcopy(ast)
                for n in walk(published_ast):
                    if n.get("t") in {"Image", "Link"} and n["c"][-1][0].startswith("assets/"):
                        n["c"][-1][0] = resource_name + "/" + n["c"][-1][0]
                write_ast(published_ast, staged_output)
            else:
                render_ast, diagrams, codes = render_mermaid(ast, bundle)
                write_ast(render_ast, bundle / "rendered.md")
                outbound(bundle / "rendered.md", staged_output, args)
        verified = validate_output(staged_output, target, expected, diagrams, codes, ast, source_images)
        # Validate portable Markdown assets before any final publication.
        if ast:
            for node in walk(ast):
                if node.get("t") == "Image":
                    local = bundle / urllib.parse.unquote(urllib.parse.urlsplit(node["c"][-1][0]).path)
                    if not local.is_file():
                        raise ConversionError("资源规范化后出现失效图片引用。")
        versions = {}
        for package in ("docling", "md2x", "pypdf", "Pillow", "rapidocr", "onnxruntime"):
            try:
                versions[package] = importlib.metadata.version(package)
            except importlib.metadata.PackageNotFoundError:
                pass
        report = {"ok": True, "input": str(source), "detected": kind, "target": target,
                  "output": str(output), "resources": str(resources), "engines": engines,
                  "versions": versions, "validation": verified, "expected_text": expected,
                  "warnings": warnings, "offline": not args.allow_model_download, "quality": args.quality,
                  "mermaid_renderer": "Mermaid CLI via Node (shell=False)" if diagrams else None}
        for transient in ("router-md2x.json", "puppeteer.json"):
            (bundle / transient).unlink(missing_ok=True)
        (bundle / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        # Unique sidecar, then atomic no-clobber publication. Failed publication rolls it back.
        if resources.resolve().parent != output.parent.resolve() or bundle.resolve().parent != work.resolve():
            raise ConversionError("资源目录超出任务输出/暂存目录，停止发布。")
        shutil.move(str(bundle), str(resources))
        try:
            if args.overwrite:
                os.replace(staged_output, output)
            else:
                os.link(staged_output, output)  # Exclusive even if another process won the race.
        except OSError as e:
            shutil.rmtree(resources)
            raise ConversionError(f"发布失败，目标未覆盖（需支持硬链接的本地文件系统）：{e}") from e
        return report


def parser():
    ap = argparse.ArgumentParser(description="本地文档转换；输出 JSON，默认不联网、不覆盖。")
    ap.add_argument("input", type=Path)
    ap.add_argument("-o", "--output", type=Path, required=True)
    ap.add_argument("--to", choices=["md", "markdown", "docx", "pdf"])
    ap.add_argument("--expect", action="append", default=[], help="必须出现在结果中的代表性正文，可重复")
    ap.add_argument("--overwrite", action="store_true", help="仅在用户明确授权覆盖后使用")
    ap.add_argument("--reflow", action="store_true", help="明确要求内容重构时才将 DOCX→PDF 经 MD 中转")
    ap.add_argument("--ocr", action="store_true", help="PDF 首次即本地全页 OCR")
    ap.add_argument("--quality", choices=["standard", "high"], default="standard")
    ap.add_argument("--models", type=Path, default=os.environ.get("ROUTER_MODELS"), help="预先下载的 Docling 模型目录")
    ap.add_argument("--allow-model-download", action="store_true", help="首次预热允许下载公开开源模型，不上传文档")
    ap.add_argument("--cjk-font", help="XeLaTeX 中文字体名称")
    ap.add_argument("--timeout", type=int, default=900)
    return ap


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        result = convert(parser().parse_args())
    except (ConversionError, OSError, ValueError) as e:
        print(json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False))
        return 1
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
