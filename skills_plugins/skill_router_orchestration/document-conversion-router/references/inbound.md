# 入站解析与安装

首次安装请先读根目录 [安装说明](../INSTALL_BEGINNER.md)，本文补充后端选择、模型与兼容性细节。

PDF / DOCX 入站使用 Docling 的本地 Python API，版本以锁定依赖为准。模型与工具的来源和许可见 [sources.md](sources.md)；验证范围见 [测试验收摘要](../tests/ACCEPTANCE.md)。

## 项目级安装（PowerShell，在 Skill 根目录）

```powershell
uv venv --python 3.11 .venv
uv pip install --python .venv\Scripts\python.exe -r requirements.lock.txt
.\.venv\Scripts\python.exe scripts\preflight.py --for pdf-md
```

Python 最低 3.10，本次 3.11.9；锁定清单验收目标是 Windows Python 3.11。`uv` 已有时使用；没有 uv 可用 `py -3.11 -m venv .venv`，然后用该环境的 `python -m pip install -r requirements.lock.txt`。其他平台须另行解析并复测。不要执行系统级安装。路由器主体只使用标准库；PDF 验证需要 pypdf，图像核验需要 Pillow。外部引擎自身依赖不因此成为标准库。

Docling 锁定 2.135.0，RapidOCR 锁定 3.9.2（3.10.0 已移除 Docling 所需接口）。`requirements.lock.txt` 记录本次 Windows/Python 3.11 解析的传递依赖；其他 Python/平台须重新解析并重测。主依赖声明为 requirements.txt。本机 `docling --help` 已确认 `convert` 子命令。路由器采用 Python API，因此不依赖新旧 CLI 参数差异。若手工调用 CLI，先运行本机 `docling --help` / `docling convert --help`，不要机械照抄旧命令。

## 首次预热与离线

```powershell
.\.venv\Scripts\python.exe scripts\convert.py "简单.pdf" -o "预热.md" --allow-model-download --expect "已知正文"
.\.venv\Scripts\python.exe scripts\convert.py "扫描.pdf" -o "OCR预热.md" --ocr --allow-model-download --expect "已知正文"
# 之后省略下载开关，验证同一管线能离线运行。
.\.venv\Scripts\python.exe scripts\convert.py "简单.pdf" -o "离线结果.md" --expect "已知正文"
```

预热只下载公开模型，文档在本机处理，不需要账号或 API Key。模型默认使用引擎缓存；`--models` 可指定 `docling-tools models download` 预先准备的目录。不同 OCR 语言/后端的权重需要分别预热。默认离线在 Docling 子进程关闭 Hugging Face 网络并阻止 socket 连接；缺模型则失败。预检不会把“缓存目录存在”冒充“模型齐备”。

Windows 默认选 Docling 自带 `PyPdfiumDocumentBackend`：本机 docling-parse 7.22.2 在含中文的安装目录无法读取 glyph 资源；PDFium 仍使用 Docling 的本地布局与表格管线。普通数字 PDF 不 OCR，无文字层启用 RapidOCR/ONNX CPU；混合扫描可显式 `--ocr`。默认 Heron 布局，表格为 Accurate；`--quality high` 改用本地 Egret Medium 布局及 Accurate 表格，需额外模型预热。本实现不提供未经验证的 GPU/VLM 管线；需要此类增强时报告设备/模型要求，不能静默云端降级。

标准输出为空、乱码、异常重复或缺指定正文时，数字 PDF 最多再试一次全页 OCR；扫描已启用 OCR 时不重复同一尝试。模型、依赖缺失仍会按此上限停止。DOCX 不尝试无意义 OCR。

提取图片写入相邻资源目录 `assets`；PDF 还保存 `assets/pages` 整页图像，并在 Markdown 附录引用。这样 PDF→DOCX 中转也会嵌入原页图像，补充保存未识别为独立图片的图形，但增加体积与页面重复。整页图像不表示 Markdown 的阅读顺序或表格一定正确。PDF/DOCX 渲染图不恢复 Mermaid 源码。
