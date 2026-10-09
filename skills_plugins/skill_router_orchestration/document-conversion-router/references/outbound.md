# 输出、Mermaid 与依赖预检

首次安装与逐步失败处理见根目录 [安装说明](../INSTALL_BEGINNER.md)，本文补充工具路径和输出约定。

保留 MD2X 0.1.0（MIT），实际写出依赖成熟 Pandoc。MD2X 上游社区规模小、PyPI 与 main 功能不同，本项目锁定已实测版本，不把其 site/AI 功能带入默认转换。Pandoc 本身不渲染 Mermaid。

MD2X 的默认 `keep_source` 不满足严格验收；本路由使用 Pandoc AST 识别 Mermaid（含不同 fence 形式），通过本地 Mermaid CLI 渲染，再交 MD2X 写出。这样也避开上游临时文件默认编码和 Windows `.cmd` 调用问题。强制失败策略，保留 `.mmd` 和含源码的 `content.md`，不给 Graphviz 做未经验证的近似转换。

## 安装与指定路径

在 Skill 根目录执行，均为项目隔离安装：

```powershell
uv pip install --python .venv\Scripts\python.exe pypandoc_binary
npm.cmd install --prefix .tools\mermaid --ignore-scripts @mermaid-js/mermaid-cli@12.0.0
.\.venv\Scripts\python.exe scripts\preflight.py --for md-docx --mermaid
```

Node 已有即可；缺失时从 [Node 官方下载](https://nodejs.org/en/download)选择 Windows ZIP，不要求全局安装。Mermaid CLI 12 改用 `--size`；脚本根据实际 `--help` 检测，旧版使用 `-w`。新版 npm 可能禁止 Puppeteer 安装脚本；可直接使用已有 Edge/Chrome（本机已验证），或按 [Puppeteer 官方说明](https://pptr.dev/guides/installation)显式下载浏览器。路由器优先检测本地 Edge/Chrome，也支持 `ROUTER_CHROME`。禁止图表里的远程 URL、外部图像/脚本；不传远程图标包选项。

PDF 需要 XeLaTeX 和完整所需 LaTeX 包，可选择 [MiKTeX 用户级安装](https://miktex.org/download)或 [TinyTeX 便携发行版](https://github.com/rstudio/tinytex-releases/releases)。本机实测使用用户缓存中的 TinyTeX v2026.10，不修改系统 PATH/注册表。MiKTeX 需提前补齐包并关闭转换时自动在线安装；本路由不自动安装缺包。

中文正文还需要 `xeCJK` 包。本机已在便携 TinyTeX 中补齐并实测中文 PDF；新机器缺包时，先在所选 TeX 环境手动执行 `tlmgr install xecjk`（或 MiKTeX Console 安装 xeCJK），再离线转换。默认镜像不可访问时可指定受信任的 CTAN 镜像；这是安装阶段，不在路由器内自动发生。

```powershell
$env:ROUTER_XELATEX = Join-Path $env:USERPROFILE '.cache\document-router-tools\TinyTeX\bin\windows\xelatex.exe'
.\.venv\Scripts\python.exe scripts\preflight.py --for md-pdf --mermaid
.\.venv\Scripts\python.exe scripts\convert.py "流程 图.md" -o "结果.pdf" --expect "标题"
# 中文正文必须指定已安装 CJK 字体，并核查提取文字。
.\.venv\Scripts\python.exe scripts\convert.py "中文.md" -o "中文.pdf" --cjk-font "Microsoft YaHei" --expect "中文标题"
```

路由器会自动发现当前用户 `.cache/document-router-tools/TinyTeX/bin/windows/xelatex.exe` 或项目 `.tools/TinyTeX/bin/windows/xelatex.exe`，因此本机无需修改系统 PATH；其他安装位置可用上面的环境变量指定。环境变量仅当前进程会话有效，不写入全局设置。可选 `ROUTER_DOCLING`、`ROUTER_MD2X`、`ROUTER_PANDOC`、`ROUTER_XELATEX`、`ROUTER_NODE`、`ROUTER_SOFFICE` 指定程序文件；`ROUTER_MMDC_JS` 指 Mermaid CLI `src/cli.js`，通过 Node 参数数组启动，不执行 `.cmd/.bat/.ps1`。显式指定的程序不存在时失败，不悄悄换程序。Docling 必须安装在运行路由器的同一 Python 环境中。

Graphviz `dot` 只在预检报告为可选项；不是本项目必需依赖，也不会用简化渲染冒充完整 Mermaid。

## 直接 DOCX→PDF

优先 [LibreOffice](https://www.libreoffice.org/download/) headless 导出，设置 `ROUTER_SOFFICE` 指向 `soffice.exe`。每次独立用户配置目录，避免影响打开的办公会话。缺失时停止提示，不自动改走有损 MD；用户明确需要内容重构才加 `--reflow`。不需要付费 Microsoft Office。字体替换仍可能改变分页。

## 验证与输出约定

- 主输出原子发布，默认不覆盖；资源目录带独立任务 ID，避免并发污染。无覆盖模式需要支持硬链接的本地文件系统（本次 NTFS）；不支持时明确失败，不降级为覆盖写入。
- `content.md` 是可移植版本，使用相对 `assets/` 路径，保留原 Markdown 的 Mermaid 语义源码；`source.md` 是原始 Markdown 字节快照，引用可能仍指原位置，应分享 `content.md`。
- 最终 MD 引用相邻资源目录；DOCX 是有效 OOXML，检查正文、标题/表格结构和实际嵌入关系；PDF 页数须大于零且可提取代表性文字。Mermaid DOCX 检查对应 PNG 字节，PDF 检查对应图像 RGB 像素，不只计数。
- Markdown 中本地图片须存在，拒绝网络共享和远程图片；SVG/HTML 图片先离线转 PNG。现有本地附件链接复制进 assets，不存在的链接警告。YAML 元数据不作为引擎参数执行，原文快照保留；raw HTML/TeX 作为文字，不执行其排版代码。
- `--expect` 可多次指定正文；不指定时自动抽取首个可用标题/段落。自动验证不是视觉质量保证，复杂多栏、合并单元格、公式、脚注、批注与分页仍需核查。
- 不需要 MCP 连接、账号或 API Key。本项目没有远程模式；不要将 `docling convert-remote`、MD2X `[ai]` 或 living-site 接入默认路由。
