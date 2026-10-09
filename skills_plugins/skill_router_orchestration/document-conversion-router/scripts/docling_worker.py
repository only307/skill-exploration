"""Isolated local Docling API adapter; no remote pipelines or uploaded files."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import socket


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("output", type=Path)
    ap.add_argument("--ocr", action="store_true")
    ap.add_argument("--high", action="store_true")
    ap.add_argument("--models", type=Path)
    args = ap.parse_args()
    if os.environ.get("HF_HUB_OFFLINE") == "1":
        def deny_network(*unused_args, **unused_kwargs):
            raise OSError("路由器离线模式：缺少本地模型时，请先显式预热下载。")
        socket.socket.connect = deny_network
        socket.create_connection = deny_network
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions, TableFormerMode, OcrMode, LayoutObjectDetectionOptions
    from docling_core.types.doc import ImageRefMode
    from docling.backend.pypdfium2_backend import PyPdfiumDocumentBackend
    opts = PdfPipelineOptions()
    opts.enable_remote_services = False
    opts.accelerator_options.device = "cpu"
    opts.do_ocr = args.ocr
    if args.ocr:
        opts.ocr_options = RapidOcrOptions(mode=OcrMode.FULL_PAGE, backend="onnxruntime")
    opts.generate_picture_images = True
    opts.generate_page_images = True
    opts.images_scale = 2.0
    if args.high:
        opts.table_structure_options.mode = TableFormerMode.ACCURATE
        opts.layout_options = LayoutObjectDetectionOptions.from_preset("layout_egret_medium")
    if args.models:
        opts.artifacts_path = args.models
    # docling-parse 7.22.2 cannot open its resources under a Chinese Windows path.
    # PDFium accepts Unicode paths while retaining Docling's layout/table pipeline.
    pdf_format = PdfFormatOption(pipeline_options=opts, backend=PyPdfiumDocumentBackend) if os.name == "nt" else PdfFormatOption(pipeline_options=opts)
    converter = DocumentConverter(allowed_formats=[InputFormat.PDF, InputFormat.DOCX],
                                  format_options={InputFormat.PDF: pdf_format})
    result = converter.convert(args.source, raises_on_error=True)
    args.output.mkdir(parents=True, exist_ok=True)
    result.document.save_as_markdown(args.output / "content.md", image_mode=ImageRefMode.REFERENCED)
    # Preserve full-page appearance too: vector diagrams may not be classified as pictures.
    page_dir = args.output / "pages"
    page_refs = []
    for number, page in result.document.pages.items():
        if page.image is not None:
            page_dir.mkdir(exist_ok=True)
            page.image.pil_image.save(page_dir / f"page-{number}.png")
            page_refs.append(f"![Original page {number}](pages/page-{number}.png)")
    if page_refs:
        # Embed page references so a subsequent DOCX preserves visual content too.
        with (args.output / "content.md").open("a", encoding="utf-8") as f:
            f.write("\n\n## Original page images (layout reference)\n\n" + "\n\n".join(page_refs) + "\n")


if __name__ == "__main__":
    main()
