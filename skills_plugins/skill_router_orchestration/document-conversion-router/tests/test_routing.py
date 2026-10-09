"""Fast routing and failure-path checks; no downloaded models required."""
from pathlib import Path
import json
import os
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import convert as router
import common


class RoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def text(self, name="中文 空格.md", content="# Heading\n\nBody text."):
        p = self.root / name
        p.write_text(content, encoding="utf-8")
        return p

    def test_routing_matrix(self):
        for a, b, expected in [("pdf", "md", ["docling"]), ("docx", "md", ["docling"]),
                                ("md", "docx", ["md2x"]), ("md", "pdf", ["md2x"]),
                                ("pdf", "docx", ["docling", "md2x"]),
                                ("docx", "pdf", ["libreoffice"])]:
            with self.subTest(a=a, b=b):
                self.assertEqual(router.route(a, b), expected)
        self.assertEqual(router.route("docx", "pdf", True), ["docling", "md2x"])

    def test_unsupported_route(self):
        with self.assertRaises(common.ConversionError):
            router.route("xlsx", "pdf")

    def test_content_over_extension(self):
        self.assertEqual(router.detect(self.text("伪装.pdf")), "md")

    def test_utf8_plain_markdown(self):
        self.assertEqual(router.detect(self.text(content="普通正文，无格式。")), "md")

    def test_binary_rejected(self):
        p = self.root / "fake.md"
        p.write_bytes(b"\x00\xff\x10")
        with self.assertRaises(common.ConversionError):
            router.detect(p)

    def test_empty_rejected(self):
        with self.assertRaises(common.ConversionError):
            router.detect(self.text(content=""))

    def test_arbitrary_zip_rejected(self):
        p = self.root / "fake.docx"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("random.txt", "hello")
        with self.assertRaises(common.ConversionError):
            router.detect(p)

    def test_macro_docx_rejected(self):
        p = self.root / "macro.docx"
        with zipfile.ZipFile(p, "w") as z:
            z.writestr("[Content_Types].xml", '<Types><Override ContentType="application/vnd.ms-word.document.macroEnabled.main+xml"/></Types>')
            z.writestr("word/document.xml", "<document/>")
        with self.assertRaises(common.ConversionError):
            router.detect(p)

    def test_html_rejected(self):
        with self.assertRaises(common.ConversionError):
            router.detect(self.text(content="<!DOCTYPE html><html>Hi</html>"))

    def test_quality_expected_text(self):
        with self.assertRaisesRegex(common.ConversionError, "代表性文字"):
            router.quality("Present text", ["Missing text"])

    def test_quality_garbled(self):
        with self.assertRaisesRegex(common.ConversionError, "乱码"):
            router.quality("\ufffd" * 10 + "text", [])

    def test_quality_repeated(self):
        with self.assertRaisesRegex(common.ConversionError, "重复"):
            router.quality(("repeated line containing more than thirty characters\n" * 20), [])

    def test_output_no_clobber_before_dependencies(self):
        src = self.text()
        dest = self.root / "exists.docx"
        dest.write_bytes(b"original")
        args = router.parser().parse_args([str(src), "-o", str(dest)])
        with self.assertRaisesRegex(common.ConversionError, "目标已存在"):
            router.convert(args)
        self.assertEqual(dest.read_bytes(), b"original")

    def test_source_never_overwritten(self):
        src = self.text()
        args = router.parser().parse_args([str(src), "-o", str(src), "--overwrite"])
        with self.assertRaisesRegex(common.ConversionError, "输入文件"):
            router.convert(args)

    def test_missing_dependency_actionable(self):
        with patch.dict(os.environ, {"PATH": "", "ROUTER_DOCLING": "Z:/nonexistent/docling.exe"}), patch.object(sys, "executable", "Z:/missing/python.exe"):
            with self.assertRaisesRegex(common.ConversionError, "uv pip install"):
                common.tool("docling")

    def test_process_uses_array_and_no_shell(self):
        class Done:
            returncode, stdout, stderr = 0, "ok", ""
        args = ["engine.exe", "中文 空格 & name.md"]
        with patch("common.subprocess.run", return_value=Done()) as proc:
            self.assertEqual(common.run(args), "ok")
            self.assertEqual(proc.call_args.args[0], args)
            self.assertIs(proc.call_args.kwargs["shell"], False)

    def test_explicit_tool_override_does_not_silently_fall_back(self):
        sibling = self.root / ("md2x.exe" if os.name == "nt" else "md2x")
        sibling.write_bytes(b"present")
        with patch.dict(os.environ, {"ROUTER_MD2X": str(self.root / "missing.exe")}), patch.object(sys, "executable", str(self.root / "python.exe")), patch("common.shutil.which", return_value=str(sibling)):
            with self.assertRaisesRegex(common.ConversionError, "缺少依赖 md2x"):
                common.tool("md2x")

    def test_timeout_actionable(self):
        import subprocess
        with patch("common.subprocess.run", side_effect=subprocess.TimeoutExpired(["engine"], 1)):
            with self.assertRaisesRegex(common.ConversionError, "超时"):
                common.run(["engine"])

    def test_remote_image_rejected_without_fetch(self):
        ast = {"blocks": [{"t": "Image", "c": [["", [], []], [], ["https://example.com/image.png", ""]]}]}
        with patch("convert.pandoc_ast", return_value=ast):
            with self.assertRaisesRegex(common.ConversionError, "拒绝远程"):
                router.normalize(self.text(), self.root, [])

    def test_missing_image_rejected(self):
        ast = {"blocks": [{"t": "Image", "c": [["", [], []], [], ["missing.png", ""]]}]}
        with patch("convert.pandoc_ast", return_value=ast):
            with self.assertRaisesRegex(common.ConversionError, "图片引用不存在"):
                router.normalize(self.text(), self.root, [])

    def test_inbound_at_most_one_fallback(self):
        args = router.parser().parse_args(["in.pdf", "-o", "out.md"])
        with patch("convert.tool", return_value="docling.exe"), patch("convert.pdf_info", return_value={"text": "born digital"}), patch("convert.run", side_effect=common.ConversionError("failed")) as proc:
            with self.assertRaisesRegex(common.ConversionError, "已停止"):
                router.inbound(self.root / "input.pdf", "pdf", self.root, args, [])
            self.assertEqual(proc.call_count, 2)
            self.assertIn("--ocr", proc.call_args.args[0])

    def test_scan_no_infinite_retry(self):
        args = router.parser().parse_args(["in.pdf", "-o", "out.md"])
        with patch("convert.tool", return_value="docling.exe"), patch("convert.pdf_info", return_value={"text": ""}), patch("convert.run", side_effect=common.ConversionError("failed")) as proc:
            with self.assertRaises(common.ConversionError):
                router.inbound(self.root / "input.pdf", "pdf", self.root, args, [])
            self.assertEqual(proc.call_count, 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
