# 安装与验收：Windows / PowerShell

[返回项目入口](README.md) · [AI 能力要求](AGENT_REQUIREMENTS.md) · [上游来源与版权](THIRD_PARTY_NOTICES.md) · [MIT LICENSE](LICENSE)

本教程以 **Windows 64 位 + PowerShell + Python 3.11** 为验收环境。源码不附带运行环境，使用前需要完成依赖安装。锁定依赖针对 Windows Python 3.11，其他系统或 Python 大版本未按本教程验收。

**按需要走到对应步骤：**普通 MD→DOCX：0～4；有 Mermaid：再做 5；输出 PDF：再做 6；PDF 入站/OCR：做 7；让 Codex 自动发现：8；完整复测：9；上游源码：10。只转换 MD→DOCX 时不必先下载 OCR 模型或安装 TeX、LibreOffice。

每一步都按“操作、合格证据、不合格处理”判断。不要把 AI 说“已完成”、目录存在或文件扩展名正确当成成功。终端中只粘贴代码框内的指令，不粘贴 `PS C:\...>` 等提示符。

## 0. 确认 AI 具备必要能力

AI 至少需要：**本机文件读取、指定目录写入、真实终端执行、输出结果校验**。安装阶段还要能联网下载依赖。详细确认请求和可执行指令见 [AGENT_REQUIREMENTS.md](AGENT_REQUIREMENTS.md)。

**合格证据：**AI 实际读到 SKILL 的名称，写入并读回 `router-capability-ok`，给出真实 Python 版本与退出码；校验时能展示报告并打开或提取输出。

**不合格处理：**为 AI 打开此项目并启用本机终端和目录访问；不支持这些能力的聊天工具需要你自己执行下面的指令。只读到上传附件不等于拥有本机文件访问。没有预览能力时，由你打开输出核对视觉效果。

## 1. 取得源码并确认目录

### 已有本地源码

在文件资源管理器中打开项目目录，地址栏输入 `powershell` 后回车；或者打开 Windows 终端的 PowerShell 标签并执行：

```powershell
$routerSource = Read-Host '输入 document-conversion-router 源码目录的完整路径'
Set-Location -LiteralPath $routerSource
Get-Location
Test-Path -LiteralPath .\SKILL.md
Test-Path -LiteralPath .\scripts\convert.py
Test-Path -LiteralPath .\requirements.lock.txt
```

**合格证据：**当前位置是 `document-conversion-router` 源码目录，三个检查都是 `True`。

**不合格处理：**不能找到目录时，把第一条路径改成你电脑上的真实解压位置；检查下载是否多套一层 `仓库名-main`。不要在外层目录直接运行后续安装。

### 从 GitHub 下载本项目

打开 [only307/skill-exploration](https://github.com/only307/skill-exploration)，点击 `Code` → `Download ZIP` → 解压 → 进入 `skills_plugins/skill_router_orchestration/document-conversion-router`。ZIP 方式不需要安装 Git。下载得到的是源码，不包含 `.venv`、模型或 TeX。

也可以从 [Git 官方](https://git-scm.com/downloads/win)准备 Git，然后执行：

```powershell
git clone https://github.com/only307/skill-exploration.git
$LASTEXITCODE
Set-Location -LiteralPath .\skill-exploration\skills_plugins\skill_router_orchestration\document-conversion-router
```

**合格证据：**clone 退出码 0；进入 Skill 子目录后，前述三个文件检查均为 `True`。后续命令都在这个子目录执行。

**不合格处理：**`git` 不存在时用 ZIP；404 时确认仓库地址、权限和是否已发布；网络失败先修复网络。不要把上游 Docling 或 MD2X 地址当成本项目下载地址。上游源码下载另见第 10 步。

## 2. 确认 Python 并建立项目环境

```powershell
py -3.11 --version
$LASTEXITCODE
```

**合格证据：**显示 Python 3.11.x，退出码 0。本机原始验收使用 3.11.9；这不表示必须采用旧补丁版本。新机器可用受支持的 Python 3.11 构建，安装后按本教程重新验收。

**不合格处理：**从 [Python 官方 Windows 下载](https://www.python.org/downloads/windows/)准备 Python 3.11 的 64 位运行时，重新打开终端。避免使用缺常规 pip/venv 的 embeddable ZIP。只有 Python 3.12/3.13 等版本时，不要直接假设这份锁定清单已经兼容；为本项目另备 3.11。没有 `py` 但确有 3.11 时用该解释器完整路径：`& '实际路径\python.exe' --version`，后面建环境命令也使用这个解释器。

先检查是否已有环境：

```powershell
Test-Path -LiteralPath .\.venv\Scripts\python.exe
```

只有结果为 `False` 时创建；已有时直接检查，避免覆盖其他环境：

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -c "import sys; print(sys.version); print(sys.executable); print(sys.prefix != sys.base_prefix)"
```

**合格证据：**3.11.x，解释器位于本项目 `.venv\Scripts\python.exe`，最后一行 `True`。

**不合格处理：**若已有环境版本不对，先退出占用它的程序，把旧 `.venv` 在本项目内改名备份，再建新环境；不要删除不明目录。`venv` 或 `pip` 缺失时修复 Python 安装。本教程直接调用解释器，**不需要运行 Activate.ps1 或修改执行策略**。

## 3. 安装锁定依赖并预检

使用项目解释器安装；下载量可能较大，请预留空间并等待真实完成：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.lock.txt
$LASTEXITCODE
.\.venv\Scripts\python.exe -m pip check
$LASTEXITCODE
.\.venv\Scripts\python.exe -c "from importlib.metadata import version; print('docling',version('docling')); print('md2x',version('md2x')); print('rapidocr',version('rapidocr'))"
.\.venv\Scripts\python.exe scripts\preflight.py --for md-docx
$LASTEXITCODE
```

**合格证据：**安装和 `pip check` 退出码 0；显示 Docling 2.135.0、MD2X 0.1.0、RapidOCR 3.9.2；预检 JSON `ok: true`、`missing_required: []`，退出码 0。pypandoc_binary 已提供本地 Pandoc，无需另装全局版本。

**不合格处理：**

| 现象 | 处理 |
| --- | --- |
| `No module named pip` | 用当前环境执行 `python.exe -m ensurepip --upgrade`，再安装 |
| 下载超时 / 证书失败 | 检查网络、代理、系统时间或组织证书；修复后重跑。不要通过关闭证书验证掩盖问题 |
| `No matching distribution` | 确认 Windows 64 位、Python 3.11；其他平台需重新解析依赖并重测 |
| 空间不足 / 安装中断 | 释放磁盘空间后重跑；有部分目录不能算完成 |
| `pip check` 报冲突 | 检查是否用了系统 Python或升级过单包；新建干净项目环境按锁定清单安装 |
| 缺 Pandoc / MD2X / Docling | 按缺项确认 `.venv` 安装及路径；不要在另一个 Python 环境补包 |
| 缺 RapidOCR 的接口 | 恢复锁定的 3.9.2，不能盲目升级到 3.10 |

已有 `uv` 时可以用 `uv pip install --python .venv\Scripts\python.exe -r requirements.lock.txt`；本教程不要求先安装 uv。只用 MD→DOCX 时全路线预检可能报告 TeX/LibreOffice 缺失，使用对应路线即可。

## 4. 首个真实转换：Markdown → Word

建立验收输出目录并调用随项目提供的原创样例：

```powershell
New-Item -ItemType Directory -Force -Path .\tests\artifacts\quickstart | Out-Null
.\.venv\Scripts\python.exe scripts\convert.py tests\fixtures\quickstart.md -o tests\artifacts\quickstart\quickstart.docx --expect 'Router Quickstart' --expect 'router_quickstart_42'
$LASTEXITCODE
Test-Path -LiteralPath .\tests\artifacts\quickstart\quickstart.docx
```

**合格证据：**退出码 0，JSON `ok: true`，文件存在；在 Word 或 LibreOffice 打开，看到标题、正文、两列表格及代码文字，没有损坏提示。终端报告中的 `resources` 指向相邻资源目录，内有 `report.json` 和可移植 `content.md`。

**不合格处理：**按 JSON `error` 修复；已经有同名文件时换 `quickstart-2.docx` 重跑。默认不覆盖是正常保护行为。只有确认要替换自己旧输出时才显式加 `--overwrite`，不得对源文件使用。主文件打不开或缺正文时，即使存在文件也不能算合格。

所有教程的验收输出都在 `tests/artifacts`；你日常转换自己的文档时，可以把输出放到自己指定的文档目录。

## 5. 有 Mermaid 图表时准备 Node 与本地浏览器

没有 Mermaid 的文档可跳过本步骤。

```powershell
node --version
npm.cmd --version
```

**合格证据：**都返回版本，退出码 0。Mermaid CLI 固定 12.0.0；本机 Node v26.4.0 已测。Node 版本需满足该包声明的要求，可用 `npm.cmd view @mermaid-js/mermaid-cli@12.0.0 engines` 查看，不把任何未来 Node 版本自动当作兼容。

**不合格处理：**从 [Node 官方下载](https://nodejs.org/en/download)准备兼容版本。便携 ZIP 解压至 `.tools\node`（确保该目录直接含 node.exe、npm.cmd），仅在当前终端加路径：

```powershell
$routerNodeDir = (Resolve-Path -LiteralPath .\.tools\node).Path
$env:PATH = $routerNodeDir + ';' + $env:PATH
$env:ROUTER_NODE = Join-Path $routerNodeDir 'node.exe'
node --version
npm.cmd --version
```

然后安装图表程序。使用已有本地 Edge/Chrome，安装阶段不自动下载另一个浏览器：

```powershell
npm.cmd install --prefix .tools\mermaid --ignore-scripts @mermaid-js/mermaid-cli@12.0.0
$LASTEXITCODE
node .tools\mermaid\node_modules\@mermaid-js\mermaid-cli\src\cli.js --version
.\.venv\Scripts\python.exe scripts\preflight.py --for md-docx --mermaid
.\.venv\Scripts\python.exe scripts\convert.py tests\fixtures\mermaid.md -o tests\artifacts\quickstart\mermaid.docx --expect 'Router Mermaid'
$LASTEXITCODE
```

**合格证据：**npm 退出码 0；CLI 版本 12.0.0；预检通过并有可用本地浏览器；转换 `ok: true`；打开 Word 看见 Start→Check→Done 流程图。报告应检查实际嵌入的图像，而不是只把 mermaid 代码块保留成文字。

**不合格处理：**没有浏览器时从浏览器官方来源安装 Edge/Chrome，或按 [Puppeteer 官方浏览器安装说明](https://pptr.dev/guides/installation)单独准备，再把 `ROUTER_CHROME` 指向真实浏览器 exe。Mermaid CLI 路径特殊时设置 `ROUTER_MMDC_JS` 为 `src\cli.js`，不要指定 mmdc.cmd。图表语法错误就修复源码后复测；远程图标、远程图片在本路由不支持，不允许把渲染失败当作成功。

## 6. 输出 PDF 时准备 XeLaTeX 与中文支持

只输出 DOCX 可跳过。安装阶段需要网络；本路由转换时不会自动补齐 TeX 包。

### 已有可用 XeLaTeX

预检先确认本项目可发现它：

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py --for md-pdf
```

本机已测的便携 TinyTeX 在当前用户缓存 `.cache\document-router-tools\TinyTeX`，路由器会自动发现；其他位置设 `ROUTER_XELATEX` 为真实 xelatex.exe 路径。环境变量仅在当前终端有效。

### 尚未准备：便携 TinyTeX 示例

以下下载本次验收对应的固定发行版。[官方发行页](https://github.com/rstudio/tinytex-releases/releases/tag/v2026.10)可核对来源。先确认 `.tools\TinyTeX` **不存在**再解压；已有时不要用下面步骤覆盖它：

```powershell
New-Item -ItemType Directory -Force -Path .\.tools | Out-Null
Test-Path -LiteralPath .\.tools\TinyTeX
Invoke-WebRequest -Uri 'https://github.com/rstudio/tinytex-releases/releases/download/v2026.10/TinyTeX-v2026.10.zip' -OutFile .\.tools\TinyTeX-v2026.10.zip
Expand-Archive -LiteralPath .\.tools\TinyTeX-v2026.10.zip -DestinationPath .\.tools
Test-Path -LiteralPath .\.tools\TinyTeX\bin\windows\xelatex.exe
$env:ROUTER_XELATEX = (Resolve-Path -LiteralPath .\.tools\TinyTeX\bin\windows\xelatex.exe).Path
& $env:ROUTER_XELATEX --version
```

**合格证据：**真实下载完成；最后文件检查 `True`；版本能输出；`--for md-pdf` 预检 `ok: true`。也可使用 [MiKTeX 官方用户级安装](https://miktex.org/download)，提前安装所需包并关闭转换时在线自动安装。

**不合格处理：**ZIP 下载失败先检查网络；展开目录多一层时找真实 `bin\windows\xelatex.exe` 并设置变量。过旧 TeX 发行版的仓库可能不匹配，先更新所选发行版/基础工具，不能忽略版本错误。

中文正文还需要 xeCJK 和可用中文字体。TinyTeX 包准备示例：

```powershell
$routerTexBin = Split-Path -Parent $env:ROUTER_XELATEX
& (Join-Path $routerTexBin 'tlmgr.bat') update --self
$LASTEXITCODE
& (Join-Path $routerTexBin 'tlmgr.bat') install xecjk
$LASTEXITCODE
& (Join-Path $routerTexBin 'kpsewhich.exe') xeCJK.sty
.\.venv\Scripts\python.exe scripts\convert.py tests\fixtures\chinese.md -o tests\artifacts\quickstart\chinese.pdf --cjk-font 'Microsoft YaHei' --expect '中文转换验收' --expect '本地中文正文'
$LASTEXITCODE
```

**合格证据：**包准备命令退出码 0；`kpsewhich` 找到 xeCJK.sty；PDF 转换 `ok: true`；打开可看见中文标题/表格，复制正文能得到正确中文，没有方框乱码。

**不合格处理：**缺 `xeCJK.sty` 时在所选 TeX 环境安装；MiKTeX 用 Console 包管理界面。镜像失败可以在安装阶段改用可信 CTAN 镜像，如 `tlmgr.bat --repository https://mirrors.tuna.tsinghua.edu.cn/CTAN/systems/texlive/tlnet install xecjk`；更新镜像与发行版仍须兼容。字体找不到时选此电脑确实安装的中文字体并修改 `--cjk-font`，不要下载和分发未知授权字体。其他 `.sty` 缺失按日志在选定 TeX 环境补包，然后离线重跑。每次复测换新的输出文件名。

有 Mermaid 的 PDF 再测试：

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py --for md-pdf --mermaid
.\.venv\Scripts\python.exe scripts\convert.py tests\fixtures\mermaid.md -o tests\artifacts\quickstart\mermaid.pdf --expect 'Router Mermaid'
```

**合格证据：**有效 PDF 至少 1 页，标题可提取，流程图真实显示；报告验证其图像像素。失败先分清 TeX 包、字体、浏览器或 Mermaid 错误，分别按本步/第 5 步修复。

## 7. PDF 入站、OCR 与离线预热

准备一份你有权处理的 PDF，选一段确定存在的正文作为 `--expect`。用文件资源管理器复制文件到 `tests/artifacts/quickstart/input.pdf`，不要拿复杂论文作为首次安装是否成功的唯一判断。

```powershell
.\.venv\Scripts\python.exe scripts\preflight.py --for pdf-md
.\.venv\Scripts\python.exe scripts\convert.py tests\artifacts\quickstart\input.pdf -o tests\artifacts\quickstart\warmup.md --allow-model-download --expect '请替换成PDF里确实存在的正文'
$LASTEXITCODE
```

**合格证据：**预检通过；真实模型下载与转换成功，正文、图像引用和表格符合该样例。预检不会证明模型已齐备。

**不合格处理：**`--expect` 示例文字必须先替换，否则理应失败。缺模型、网络下载失败时修复网络并预热；内存不足时关闭占内存应用、使用标准 CPU 模式；超时可在确认程序确实工作后增加 `--timeout 1800`。阅读顺序/表格不对属于内容质量问题，不算安装已经解决它。

扫描件另用 `scan.pdf` 预热 OCR；本机已测英文扫描，中文 OCR 还需对你的实际样例验收：

```powershell
.\.venv\Scripts\python.exe scripts\convert.py tests\artifacts\quickstart\scan.pdf -o tests\artifacts\quickstart\ocr-warmup.md --ocr --allow-model-download --expect '请替换成扫描件正文'
```

预热后同一路线**省略下载开关**并换输出名：

```powershell
.\.venv\Scripts\python.exe scripts\convert.py tests\artifacts\quickstart\input.pdf -o tests\artifacts\quickstart\offline.md --expect '请替换成PDF正文'
.\.venv\Scripts\python.exe scripts\convert.py tests\artifacts\quickstart\scan.pdf -o tests\artifacts\quickstart\ocr-offline.md --ocr --expect '请替换成扫描件正文'
```

**合格证据：**不带下载开关也成功，文字与资源核对通过。报告的 `offline: true` 表示未启用模型下载，并非对所有外部程序的网络审计；可断开网络复测，确认该环境的离线可用性。高质量 `--quality high` 使用另一个布局模型，需要独立预热和同模式离线复测。

**不合格处理：**缺哪个模型就仅对相应路线预热；不要把缺缓存的失败改成隐式云端转换。提取仍为空/乱码/缺正文时检查扫描质量、OCR 语言和期望文字；程序有限次尝试，不无限重试，也不把原页截图当作文本提取成功。

## 8. 让 Codex 发现 Skill（可选）

截至 2026-10-09，官方文档列出个人位置 `~/.agents/skills`、仓库位置 `.agents/skills`，支持链接目录；更新未出现时重启。旧安装可能同时使用其他位置，应以你宿主的实际发现列表为准。[OpenAI 官方技能文档](https://learn.chatgpt.com/docs/build-skills)

本项目根目录只是源码目录，不保证被宿主自动发现。安装已验收后，可建立个人目录链接，仍使用原项目的 `.venv` 和 `.tools`，不复制巨大的运行时：

```powershell
$routerSource = (Get-Location).Path
$routerSkillParent = Join-Path $env:USERPROFILE '.agents\skills'
New-Item -ItemType Directory -Force -Path $routerSkillParent | Out-Null
$routerSkillLink = Join-Path $routerSkillParent 'document-conversion-router'
Test-Path -LiteralPath $routerSkillLink
```

只有最后为 `False` 时创建 Windows 目录联接：

```powershell
New-Item -ItemType Junction -Path $routerSkillLink -Target $routerSource
Get-Content -LiteralPath (Join-Path $routerSkillLink 'SKILL.md') -TotalCount 4
```

**合格证据：**链接读取到正确 name；在新会话的技能列表里看到“文档格式转换路由”；能显式选取或请求读取该 Skill，并真实调用原项目解释器转换样例。CLI/IDE 可使用 `$document-conversion-router`；其他界面以实际技能选择器为准。

**不合格处理：**同名目录已存在时先检查指向，不覆盖、不复制套娃；链接不支持或没权限时使用宿主支持的安装器，并确保实际执行环境能找到依赖。未识别先重启并核查当前技能目录、重复名称和禁用配置。仅复制 `SKILL.md` 会缺脚本与引用。原项目移动后链接会失效，需要更新链接。能力与终端测试不通过时先回到第 0 步。

不想安装到个人目录时，直接告诉 AI：“读取这个目录的 SKILL.md，使用它转换文档”；这能验证工作流，但不等于安装完成。

## 9. 完整测试与交付验收

安装测试依赖并执行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r tests\requirements.txt
$LASTEXITCODE
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_routing.py -v
$LASTEXITCODE
.\.venv\Scripts\python.exe tests\run_integration.py
$LASTEXITCODE
```

新机器模型没预热时，集成命令先加 `--download`，之后再省略重跑。每轮输出在 `tests/artifacts/run-随机编号/results.json`，测试样例也在该轮目录，不散落到根目录。

**合格证据：**22 项单元测试通过；真实集成没有 FAIL；每个 SKIP 单独说明依赖或未测原因。当前机正常基线为 11 PASS / 1 SKIP（LibreOffice 路线未测试），不能宣称全部路线验收。缺其他依赖的新机器可能有更多 SKIP，需要安装并补测对应路线。

**不合格处理：**保留失败的 `results.json` 与原文档，按 case 定位；修复后新轮次复测，不手改历史 PASS。测试脚本退出码 0 也可能存在 SKIP，务必读汇总。

直接 DOCX→PDF 需要 [LibreOffice 官方下载](https://www.libreoffice.org/download/)，将 `ROUTER_SOFFICE` 指向实际 `program\soffice.exe`，预检 `--for docx-pdf` 后对真实样例验收。没有它就说明该路线未测试。用户明确接受内容重构时才用 `--reflow`，并说明格式损失。

最终可用性检查：主文件能打开；代表性文字正确；表格/图片/流程图看得见；资源路径完整；源文件未改变。分享 Markdown 要带相邻资源目录，或分享资源包中的 `content.md` 和整个 `assets`；不要只分享保留原始引用的 `source.md`。异常或损失见 [测试验收报告](tests/ACCEPTANCE.md)。

## 10. 可选：下载上游最新源码或移植代码

**官方入口：[Docling](https://github.com/docling-project/docling) · [MD2X](https://github.com/ChaoticQubit/MD2X)**。源码可直接下载和按 MIT 条款复制、修改、分发；保留 [独立版权声明](THIRD_PARTY_NOTICES.md)和下载版本原有许可。上游代码与模型、工具依赖的授权范围不同。

不用 Git：下载 [Docling main ZIP](https://github.com/docling-project/docling/archive/refs/heads/main.zip) 和 [MD2X main ZIP](https://github.com/ChaoticQubit/MD2X/archive/refs/heads/main.zip)，解压到 `.tools/upstream` 供本机研究。这样不会把上游测试、模型和开发文件散落进本项目根目录，也不会自动替换当前环境。

有 Git：在项目根目录执行，目标目录必须尚不存在；已有副本时不要再次 clone 到里面：

```powershell
New-Item -ItemType Directory -Force -Path .\.tools\upstream | Out-Null
git clone --depth 1 https://github.com/docling-project/docling.git .tools/upstream/docling
$LASTEXITCODE
git clone --depth 1 https://github.com/ChaoticQubit/MD2X.git .tools/upstream/md2x
$LASTEXITCODE
git -C .tools/upstream/docling rev-parse HEAD
git -C .tools/upstream/md2x rev-parse HEAD
Get-Content -LiteralPath .\.tools\upstream\docling\LICENSE
Get-Content -LiteralPath .\.tools\upstream\md2x\LICENSE
```

**合格证据：**两次 clone 退出码 0；有两个完整 commit；两个 LICENSE 分别保留原始持有人；没有用路由作者名字替换。main 会变化，记录你实际下载的 commit。许可核查快照见版权文件。

**不合格处理：**Git 不存在就用 ZIP；网络失败修复后用新目录重试；缺 LICENSE、来源不明或许可已改变时先重新核查，不沿用“上一次是 MIT”的结论。clone 成功不是运行兼容验收。

若希望把选定上游代码提交到你的仓库：在清楚标识的 `vendor/docling` / `vendor/md2x` 保存实际选用的源码与原 LICENSE / NOTICE，不提交其 `.git`、下载模型、虚拟环境和生成文件；更新本声明，记录来源 URL、commit、复制范围和改动。上游自带测试应保持其必要结构，路由项目自己的测试与生成文件仍全部归 `tests`。当前发布的路由源码通过独立安装调用上游引擎，不包含上游源码副本。

使用源码替换依赖前先建独立试验环境，按上游说明安装所需版本；检查 `md2x --help` 和 Docling API 变化；再跑本项目所有相关测试，确认模型许可与输出质量，才更新 requirements / 锁定清单 / 来源表 / CHANGELOG。不要只执行 `pip install -U` 然后保留旧测试结论。当前 PyPI MD2X 与 main 语法不同，RapidOCR 版本也有已知兼容边界。

## 通用排错索引

| 提示 | 判断与下一步 |
| --- | --- |
| 找不到文件 | 核对实际位置，给含空格路径加引号，使用 `-LiteralPath` 读取 |
| `ok: false` | 读完整 error，修复对应依赖/输入，再换输出名重试 |
| 文件已存在 | 更换输出文件名；确实允许覆盖旧结果才加 `--overwrite` |
| 必须指定中文字体 | 使用本机已安装字体，加 `--cjk-font` 并补 xeCJK |
| 远程图片被拒绝 | 合法下载为本地 PNG 后修改引用；不在转换时自动联网取图 |
| 资源文件缺失 | 主文档与相邻资源目录一起移动，或用可移植 content.md |
| 发布失败 / 硬链接 | 使用支持硬链接的本地 NTFS 输出位置；不要静默改成覆盖源文件 |
| 结果有损 | 对照原文检查结构；必要时保留源文件或用直接 Office 导出，不声称无损 |
| `SKIP` | 表示没测到，需要准备该路线依赖再验收 |

进一步配置见 [入站细节](references/inbound.md) / [出站细节](references/outbound.md)。所有测试材料入口见 [tests/README.md](tests/README.md)。
