# 文档格式转换路由 Skill

把 PDF、Word（DOCX）和 Markdown 交给本地转换工具，并检查正文、图片和 Mermaid 图表是否实际进入输出。适合能读取本地文件、执行终端指令的 AI 助手，也可以直接在终端使用。

**从这里开始：[安装说明](INSTALL_BEGINNER.md) · [AI 能力要求](AGENT_REQUIREMENTS.md) · [上游来源与版权声明](THIRD_PARTY_NOTICES.md) · [MIT LICENSE](LICENSE)**

**两个主引擎：[Docling 官方源码与下载](https://github.com/docling-project/docling) · [MD2X 官方源码与下载](https://github.com/ChaoticQubit/MD2X)**。两个项目均按各自 MIT 许可使用，完整原始版权和许可文本已保留在上面的独立声明中。

## 能做什么

| 输入 → 输出 | 默认工具 | 使用边界 |
| --- | --- | --- |
| PDF → Markdown | Docling | 本地布局、表格、OCR；首次需要下载模型 |
| DOCX → Markdown | Docling | 提取内容与图片；复杂 Word 特性可能丢失 |
| Markdown → DOCX / PDF | MD2X + Pandoc | Mermaid 先经本地 Mermaid CLI 渲染；PDF 另需 XeLaTeX |
| PDF → DOCX | Docling → MD2X | 有损内容重构，保留原页图像附录 |
| DOCX → PDF | LibreOffice | 直接导出；基线环境缺少 LibreOffice，该路线未验收。明确加 `--reflow` 才走有损重构 |

默认保护源文件，拒绝静默覆盖。结果含主文件与相邻资源目录，资源目录保留图片、可移植 Markdown 和转换报告。扫描件 OCR、复杂多栏、合并表格、公式及分页都需要人工核对，不能承诺版面无损。

转换引擎无需 API Key、账号或云端调用；AI 助手本身的订阅费用不属于转换引擎费用。首次准备依赖、模型和 TeX 包需要网络，模型预热后默认离线转换。

## 源码下载

**项目仓库：**[only307/skill-exploration](https://github.com/only307/skill-exploration)。本 Skill 位于 `skills_plugins/skill_router_orchestration/document-conversion-router`。

在仓库网页点击 `Code` → `Download ZIP`，解压后进入上述子目录；也可使用 Git：

```powershell
git clone https://github.com/only307/skill-exploration.git
Set-Location -LiteralPath .\skill-exploration\skills_plugins\skill_router_orchestration\document-conversion-router
```

该子目录应同时含 `SKILL.md`、`scripts` 和 `requirements.lock.txt`。已有源码时直接进入该目录，按 [安装说明第 1 步](INSTALL_BEGINNER.md#1-取得源码并确认目录)继续。源码不包含虚拟环境、模型或工具二进制。

**上游最新源码：**[Docling main ZIP](https://github.com/docling-project/docling/archive/refs/heads/main.zip) / [MD2X main ZIP](https://github.com/ChaoticQubit/MD2X/archive/refs/heads/main.zip)。克隆、记录版本、移植与许可保留步骤见 [安装说明第 10 步](INSTALL_BEGINNER.md#10-可选下载上游最新源码或移植代码)。

当前程序调用独立安装的引擎，没有内嵌两套上游源码。本仓库维护自己的路由、验证与资源整理代码。允许按上游许可复制或修改代码，但最新 main 不等于已测发布版，不能直接替换后沿用原测试结论。

## 已安装环境的快速使用

下面是 Windows PowerShell 指令，在本 Skill 根目录（含 `SKILL.md` 的目录）执行；首次安装请先读完整教程。

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py --for md-docx
.\.venv\Scripts\python.exe scripts\convert.py "你的文档.md" -o "转换结果.docx" --expect "应出现的正文"
```

Mermaid 加装 Node、Mermaid CLI 与浏览器；中文 PDF 还需中文字体和 xeCJK：

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py --for md-pdf --mermaid
.\.venv\Scripts\python.exe scripts\convert.py "中文流程图.md" -o "中文流程图.pdf" --cjk-font "Microsoft YaHei" --expect "中文标题"
```

成功要求：退出码为 0、报告 `ok: true`、主文件实际存在、能打开且正文/表格/图片/图表符合预期。报告通过也要核对真实内容。失败处理和每步验收见教程。

## Skill 目录导览

| 文件或目录 | 作用 |
| --- | --- |
| `README.md` | 项目说明、下载、重要入口 |
| `INSTALL_BEGINNER.md` | 从 AI 能力确认到真实转换的逐步安装与排错 |
| `AGENT_REQUIREMENTS.md` | AI 所需能力、证据格式与交付标准 |
| `THIRD_PARTY_NOTICES.md` | Docling / MD2X 原始 MIT 版权声明和来源 |
| `LICENSE` | 本 Skill 原创内容的 MIT 许可证，与仓库根目录许可证一致 |
| `CHANGELOG.md` | 本项目变更记录 |
| `SKILL.md` / `agents` | AI 工作流与界面信息 |
| `scripts` | 实际转换与预检代码 |
| `references` | 入站/出站细节和主要依赖的来源与许可 |
| `requirements.txt` / `requirements.lock.txt` | 直接依赖 / Windows Python 3.11 锁定依赖 |
| `tests` | 测试脚本、测试依赖、示例和验收摘要；生成结果仅保存在本地 |

`.venv`、`.tools` 是本机依赖目录，`tests/artifacts` 是测试输出，均被 Git 忽略，不随源码发布。分享 Markdown 时连同相邻资源文件夹一起分享。

## 测试状态与许可证范围

2026-10-09 的 Windows Python 3.11 基线已通过 22 项单元测试，离线集成为 **11 PASS / 1 SKIP**；直接 DOCX→PDF 因缺 LibreOffice 跳过。另已测中文正文 PDF 和高质量 CPU 入站。验收摘要、重跑方法与未测范围见 [tests/ACCEPTANCE.md](tests/ACCEPTANCE.md) 和 [tests/README.md](tests/README.md)。原始测试输出仅保存在维护者本地，不随源码发布。

本 Skill 的原创代码、指令、文档和测试采用 [MIT](LICENSE)，版权署名为 `Copyright (c) 2026 only307`；与仓库根目录 [LICENSE](../../../LICENSE) 一致。保留目录内许可证，便于单独分发这个 Skill。

Docling、MD2X 的版权和许可属于各自上游，完整原文见 [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)。Pandoc、模型权重、TeX、字体和浏览器分别适用自己的许可，不因本仓库 MIT 声明改变。依赖详情见 [references/sources.md](references/sources.md)。
