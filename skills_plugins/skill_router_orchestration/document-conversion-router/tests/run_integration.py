"""Real engine acceptance tests. Missing engines are SKIP, never PASS.

Run with the project venv; --download permits model warm-up. All output is ignored.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from common import tool, mermaid_command
from convert import pdf_info, detect, pandoc_ast, walk


def fixtures(root):
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from docx import Document
    assets = root / "原始 图片"
    assets.mkdir()
    image = Image.new("RGB", (240, 100), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((10, 10, 230, 90), fill="#2563eb")
    draw.text((30, 40), "ROUTER IMAGE", fill="white")
    image.save(assets / "示例 图.png")
    md = root / "中文 空格 & source.md"
    md.write_text('''# Router Acceptance

Representative body text for routing validation.

| Item | Value |
| --- | --- |
| Alpha | 42 |

![Sample](<原始 图片/示例 图.png>)

```python
print("router_code_42")
```
''', encoding="utf-8")
    mermaid = root / "流程 图 source.md"
    mermaid.write_text(md.read_text(encoding="utf-8") + '''
```mermaid
flowchart LR
  A[Start] --> B{Check}
  B --> C[Done]
```
''', encoding="utf-8")
    pdf = root / "简单 中文 空格.pdf"
    c = canvas.Canvas(str(pdf))
    c.setFont("Helvetica-Bold", 20)
    c.drawString(60, 770, "Router PDF Title")
    c.setFont("Helvetica", 12)
    c.drawString(60, 730, "Representative PDF body text for acceptance.")
    c.drawImage(str(assets / "示例 图.png"), 60, 600, width=240, height=100)
    c.save()
    docx = root / "简单 中文 空格.docx"
    doc = Document()
    doc.add_heading("Router Word Title", 0)
    doc.add_paragraph("Representative Word body text for acceptance.")
    table = doc.add_table(rows=2, cols=2)
    table.cell(0, 0).text, table.cell(0, 1).text = "Item", "Value"
    table.cell(1, 0).text, table.cell(1, 1).text = "Alpha", "42"
    doc.add_picture(str(assets / "示例 图.png"))
    doc.save(docx)
    scan = root / "扫描 中文 空格.pdf"
    page = Image.new("RGB", (1400, 1800), "white")
    d = ImageDraw.Draw(page)
    font = ImageFont.truetype("C:/Windows/Fonts/arial.ttf", 48) if os.name == "nt" else ImageFont.load_default(size=48)
    d.text((100, 150), "Router Scan Title", font=font, fill="black")
    d.text((100, 260), "Scanned document body text.", font=font, fill="black")
    c = canvas.Canvas(str(scan), pagesize=(700, 900))
    c.drawImage(ImageReader(page), 0, 0, width=700, height=900)
    c.save()
    return md, mermaid, pdf, docx, scan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", action="store_true")
    args = ap.parse_args()
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    root = ROOT / "tests" / "artifacts" / ("run-" + uuid.uuid4().hex[:8])
    root.mkdir(parents=True)
    md, mermaid, pdf, docx, scan = fixtures(root)
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in (md, mermaid, pdf, docx, scan)}
    cases = [("simple_pdf_to_md", pdf, "md", ["docling", "pandoc"], "Representative PDF body"),
             ("simple_docx_to_md", docx, "md", ["docling", "pandoc"], "Representative Word body"),
             ("rich_md_to_docx", md, "docx", ["md2x", "pandoc"], "router_code_42"),
             ("mermaid_md_to_pdf", mermaid, "pdf", ["md2x", "pandoc", "xelatex", "mmdc"], "Representative body"),
             ("mermaid_md_to_docx", mermaid, "docx", ["md2x", "pandoc", "mmdc"], "Representative body"),
             ("scanned_pdf_to_md", scan, "md", ["docling", "pandoc"], "Scanned document body text"),
             ("pdf_to_docx_lossy", pdf, "docx", ["docling", "md2x", "pandoc"], "Representative PDF body"),
             ("docx_to_pdf_direct", docx, "pdf", ["soffice"], "Representative Word body")]
    results = []
    for name, src, ext, deps, expected in cases:
        dest = root / (name + " 中文 输出." + ext)
        missing = [x for x in deps if not (mermaid_command(False) if x == "mmdc" else tool(x, False))]
        if missing:
            row = {"case": name, "status": "SKIP", "reason": "未测试，缺少依赖：" + ", ".join(missing)}
        else:
            command = [sys.executable, str(ROOT / "scripts/convert.py"), str(src), "-o", str(dest), "--expect", expected]
            if args.download:
                command.append("--allow-model-download")
            p = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
            try:
                report = json.loads(p.stdout)
            except ValueError:
                report = {"error": p.stdout[-5000:] + p.stderr[-5000:]}
            row = {"case": name, "status": "PASS" if p.returncode == 0 and report.get("ok") else "FAIL", "report": report}
            if row["status"] == "PASS":
                try:
                    assert detect(dest) == ext
                    if ext == "md":
                        text = dest.read_text(encoding="utf-8")
                        assert expected.casefold() in text.casefold()
                        for n in walk(pandoc_ast(dest)):
                            if n.get("t") == "Image":
                                assert (dest.parent / urllib.parse.unquote(n["c"][-1][0])).is_file()
                    if ext == "docx":
                        with zipfile.ZipFile(dest) as z:
                            xml = z.read("word/document.xml").decode()
                            if src in {md, mermaid}:
                                assert "router_code_42" in xml and "w:tbl" in xml and "Heading1" in xml
                                assert len([x for x in z.namelist() if x.startswith("word/media/")]) >= (2 if src == mermaid else 1)
                            assert "flowchart LR" not in xml
                    if "mermaid" in name:
                        assert report["validation"]["mermaid_verified"] == 1
                        bundle = Path(report["resources"])
                        assert "flowchart LR" in (bundle / "content.md").read_text(encoding="utf-8")
                        assert "flowchart LR" in (bundle / "assets/mermaid-1.mmd").read_text(encoding="utf-8")
                    if name == "pdf_to_docx_lossy":
                        assert any("有损" in x for x in report["warnings"])
                except Exception as e:
                    row.update(status="FAIL", reason="独立验收断言失败：" + repr(e))
        results.append(row)
        print(json.dumps({"case": name, "status": row["status"], "error": row.get("reason") or row.get("report", {}).get("error")}, ensure_ascii=False), flush=True)
    # Real no-clobber check needs no conversion dependencies.
    existing = root / "已有 文件.docx"
    existing.write_bytes(b"DO NOT OVERWRITE")
    p = subprocess.run([sys.executable, str(ROOT / "scripts/convert.py"), str(md), "-o", str(existing)], capture_output=True, text=True, encoding="utf-8")
    results.append({"case": "no_silent_overwrite", "status": "PASS" if p.returncode != 0 and existing.read_bytes() == b"DO NOT OVERWRITE" else "FAIL"})
    env = os.environ.copy()
    env["ROUTER_MD2X"] = str(root / "missing-engine.exe")
    p = subprocess.run([sys.executable, str(ROOT / "scripts/convert.py"), str(md), "-o", str(root / "missing.docx")], env=env, capture_output=True, text=True, encoding="utf-8")
    missing_report = json.loads(p.stdout)
    results.append({"case": "missing_dependency_cli", "status": "PASS" if p.returncode != 0 and "缺少依赖 md2x" in missing_report.get("error", "") and not (root / "missing.docx").exists() else "FAIL"})
    if tool("md2x", False) and tool("pandoc", False) and mermaid_command(False):
        bad = root / "invalid mermaid.md"
        bad.write_text('# Invalid diagram\n\n```mermaid\nflowchart LR\n A[unclosed\n```\n', encoding="utf-8")
        failed_output = root / "invalid-mermaid.docx"
        p = subprocess.run([sys.executable, str(ROOT / "scripts/convert.py"), str(bad), "-o", str(failed_output)], capture_output=True, text=True, encoding="utf-8", timeout=180)
        results.append({"case": "mermaid_failure_is_fatal", "status": "PASS" if p.returncode != 0 and not failed_output.exists() else "FAIL"})
    results.append({"case": "source_integrity", "status": "PASS" if all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in hashes.items()) else "FAIL"})
    report_path = root / "results.json"
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(report_path), flush=True)
    return int(any(r["status"] == "FAIL" for r in results))


if __name__ == "__main__":
    raise SystemExit(main())
