# AI 助手能力与验收要求

本 Skill 是本地工具工作流。只会回答问题、不能操作本机文件和终端的聊天窗口，无法独立完成安装与转换。用户也可以自己执行 [安装教程](INSTALL_BEGINNER.md)，不依赖 AI 自动执行。

## 安装前确认能力

| 能力 | 怎样证明 | 合格 | 不合格处理 |
| --- | --- | --- | --- |
| 读取本机文件 | 读取当前项目 `SKILL.md` 的 name 和第一条流程 | 引用真实内容和路径 | 给 AI 打开项目/授予目录访问，或自己操作 |
| 写入本机文件 | 在 `tests/artifacts/capability` 写入小文件并读回 | 内容一致，路径在指定目录内 | 检查项目写入权限；不能写则停止自动安装 |
| 执行终端 | 执行 `Get-Location` 与 Python 版本检查 | 展示真实输出和退出码 | 使用带本地终端的 AI 工具，或由用户执行 |
| 下载依赖 | 安装阶段访问官方 GitHub、PyPI、npm、模型/TeX 来源 | 有真实安装日志，无需文档上传 | 解决代理/证书/网络；也可先离线准备包和模型 |
| 校验文档 | 运行本仓库验证，并打开或提取实际输出 | 能核对代表性文字、图片、表格与 Mermaid | 无预览工具时让用户打开并核对，不声称视觉验收通过 |

不要求 GPU、MCP、转换 API Key 或 Microsoft Office。AI 服务可能有自己的账号或费用。AI 的联网能力用于研究与安装，不能据此把文档上传远程转换服务。

## 可直接交给 AI 的能力确认请求

> 请先验证你是否能读取这个项目的 SKILL.md、在 tests/artifacts/capability 内创建并读回测试文件、执行 PowerShell 并报告真实 Python 版本与退出码。给出实际证据。尚未确认终端和文件能力时，不要声称安装完成。确认后按 INSTALL_BEGINNER.md 安装，只将安装依赖放入 .venv / .tools，测试文件放入 tests，保留全部上游版权声明。

## 能力确认指令

在项目根目录执行：

```powershell
Get-Location
Get-Content -LiteralPath .\SKILL.md -TotalCount 8
New-Item -ItemType Directory -Force -Path .\tests\artifacts\capability | Out-Null
'router-capability-ok' | Set-Content -LiteralPath .\tests\artifacts\capability\probe.txt -Encoding utf8
Get-Content -LiteralPath .\tests\artifacts\capability\probe.txt
py -3.11 --version
$LASTEXITCODE
```

合格：位置正确；真实读到 name `document-conversion-router`；文件读回 `router-capability-ok`；Python 显示 3.11.x、退出码 0。缺 `py` 时按教程安装 Python 或指定真实 `python.exe`。AI 仅复述此示例输出不算证据。

## 安装和转换执行规则

1. 先识别输入真实格式和目标格式，再读需要的入站/出站引用，运行该路线预检。不要用 `--for all` 的可选路线缺项阻止只转换 Markdown 的用户。
2. 使用项目 `.venv` 的 Python，不混用系统环境。显式工具路径无效时修复路径，不隐藏失败。
3. 初次模型下载须使用 `--allow-model-download`；下载完成后对同一路线不带此参数复测。模型目录存在不证明离线齐备。
4. 调用程序用参数数组；文档内容不当作终端指令执行。保存原文件，不静默覆盖，不任意访问远程图片。
5. Mermaid 渲染失败就报告失败；不能把裸 Mermaid 代码当成图表交付。不能用结构不等价的简化图冒充成功。
6. PDF→DOCX 是有损重构，DOCX→PDF 直接导出缺 LibreOffice 时报告缺项；加 `--reflow` 必须符合用户内容重构需求。
7. 升级或移植源码时记录来源、完整 commit、许可和修改；复测后才更新支持状态。

## 每项结果的验收范式

记录 **操作 → 证据 → 结论 → 失败处理**：

```text
操作：MD→DOCX，输入 tests/fixtures/quickstart.md
证据：退出码 0；JSON ok=true；正文含 Router Quickstart；DOCX 能打开；表格显示两列
结论：本样例通过；没有据此证明复杂 Word 分页正确
失败处理：保留报告与原文件，按 missing_required/error 修复，再输出至新文件名复测
```

PASS 表示真实执行并满足该项标准；FAIL 表示执行未满足标准；SKIP 表示未运行或依赖缺失，不能算 PASS。交付时给出主文件、资源目录、报告、转换路线、未测范围和重要损失；复杂视觉项目需要用户或具备预览能力的 AI 核对。

## 让宿主发现 Skill

不自动复制整个 `.venv` 或 `.tools` 到 Skill 目录。先按安装教程在原项目验证，再建立宿主支持的指向项目的目录链接。Codex 的本地技能位置、链接方式和识别验收见 [安装教程第 8 步](INSTALL_BEGINNER.md#8-让-codex-发现-skill可选)。其他 AI 宿主请使用其实际支持的技能目录；没有 Skill 加载功能时可明确请求 AI 读取本项目 `SKILL.md` 后执行脚本。
