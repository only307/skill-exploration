# 基线验收摘要

验收日期：2026-10-09（Asia/Shanghai）；Windows 64 位，Python 3.11.9。引擎为 Docling 2.135.0、MD2X 0.1.0，依赖以 `requirements.lock.txt` 为准。

本文记录基线环境的结果，不代表其他系统、依赖升级后或复杂文档都具有相同质量，也不代表已在第二台全新电脑完成从零安装。

实际兼容处理包括中文 Windows 路径下使用 Docling PDFium 后端、固定 RapidOCR 3.9.2，以及通过 Node 参数数组调用 Mermaid CLI 12。这些处理位于路由代码，不修改上游源码。

## 真实验收

2026-10-09 的基线离线集成结果为 **11 PASS / 1 SKIP / 0 FAIL**，包含 7 条真实转换和 4 项保护检查。目录整理后的复测结果一致。原始 JSON、转换文件和图片仅保存在维护者本地的 `tests/artifacts/`，不随源码发布；公开仓库可按 [测试入口](README.md)重跑。

| 测试 | 结果与证据 |
| --- | --- |
| 简单 PDF→MD | PASS，标题/正文非空且含指定文字；资源与原页图像存在 |
| 简单 DOCX→MD | PASS，指定正文、标题、表格及有效图片引用 |
| 标题/表格/图片/代码 MD→DOCX | PASS，有效 OOXML、Heading1、表格、代码正文、1 张嵌入图片 |
| Mermaid MD→PDF | PASS，1 页、可提取指定正文、图像 RGB 像素匹配；源码不裸露 |
| Mermaid MD→DOCX | PASS，2 张嵌入图片（原图与流程图），Mermaid PNG 字节匹配 |
| 扫描 PDF→MD | PASS，本地 ONNX CPU OCR；无文字层样例中识别到指定英文正文 |
| PDF→DOCX | PASS，正确中转路由、有损警告、嵌入原页图像以保留图形 |
| 中文、空格、`&` 文件名 | PASS，贯穿上述输入与输出路径 |
| 目标已存在 | PASS，返回错误且原字节不变 |
| 缺少依赖 | PASS，真实 CLI 强制不存在的 MD2X 路径，返回中文安装提示，无输出 |
| 非法 Mermaid | PASS，真实渲染错误使任务失败，未交付文档 |
| 源文件完整性 | PASS，全部输入 SHA-256 不变 |
| DOCX→PDF 直接导出 | **未测试 / SKIP**：本机没有 LibreOffice，未悄悄改走 Markdown |

另已通过：22 项单元测试；Skill Creator `quick_validate.py`（`Skill is valid!`）；脚本编译检查；Egret Medium 高质量 CPU 模式及离线复测；将 Markdown 和资源包移至另一个临时目录后，图片引用仍有效。

中文正文 PDF 额外测试：首次因缺少 `xeCJK.sty` 失败；补齐用户缓存中的便携 TeX 包后，使用 Microsoft YaHei **离线复测通过**：有效 1 页、中文标题及正文均可提取，输出现位于 `tests/artifacts/中文正文测试.pdf`。本次没有修改系统 TeX 安装或全局 PATH。中文扫描 OCR、多栏论文、复杂合并表格与公式未做真实质量基准，不声称已经验收。

## 复现

在 Skill 根目录执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r tests\requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_routing.py -v
.\.venv\Scripts\python.exe tests\run_integration.py
```

完整安装与模型预热见 [安装说明](../INSTALL_BEGINNER.md)。每轮结果写入新的 `tests/artifacts/run-随机编号/results.json`；失败与跳过原因需要逐项核对。

## 损失边界与未测范围

- 直接 DOCX→PDF 因基线环境缺少 LibreOffice 未验收；不把通过 Markdown 的有损重构当作该路线通过。
- 中文扫描 OCR、多栏论文、复杂合并表格及公式未做真实质量基准。自动内容和图像核验不代替复杂文档的视觉与语义核对。
- PDF 不保证版面或语义无损往返。原页图像附录有助于保留图形，但可能重复页面视觉内容并增加体积。
- Word 批注、修订、文本框、SmartArt、嵌入对象及复杂分页可能丢失；宏文档拒绝。PDF/DOCX 中的流程图不能恢复原始 Mermaid 源码。
- 新机器须准备所需模型、浏览器、TeX 包和字体。中文 PDF 使用该机已安装的 CJK 字体；当前测试结果不授予字体或模型的额外分发权利。

原创内容采用 [MIT LICENSE](../LICENSE)，上游版权和许可独立保留在 [第三方声明](../THIRD_PARTY_NOTICES.md)。
