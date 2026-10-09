# 变更记录

记录本路由项目的变化，不代表 Docling 或 MD2X 上游发布日志。

## 2026-10-09 — 文档与目录整理

- 增加 Skill 目录项目入口、AI 能力要求、安装说明和本变更记录，保留根目录 `SKILL.md`。
- 原创内容采用 MIT，版权署名为 `2026 only307`；仓库根目录与 Skill 目录保留相同许可证。独立第三方声明保留 Docling / MD2X 原始版权和完整 MIT 文本。
- 将 `references/acceptance.md` 移至 `tests/ACCEPTANCE.md`；将根目录测试依赖移至 `tests/requirements.txt`；将 `test-output` 整体移至 `tests/artifacts`。保留历史结果，没有删除样例或原测试输出。
- 修正测试输出路径、测试依赖相对引用、文档链接与 Git 忽略路径；所有新增测试样例和复测证据统一在 `tests`。
- 提供上游 main 源码下载与许可保留规范，运行依赖仍锁定已测发布版。
- 更新集合仓库下载地址与 Skill 子目录路径；删除许可证教学文件和临时目录整理报告，合并有效验收摘要，移除个人路径和未采用工具的选型笔记。

## 2026-10-09 — 首次实现与验收

- 建立 PDF / DOCX / Markdown 路由；默认 Docling 2.135.0、MD2X 0.1.0，固定兼容 RapidOCR 3.9.2。
- 增加离线模型调用、限次 OCR、Markdown 资源整理、Mermaid 本地渲染、输出内容核验及原子交付。
- 修复中文 Windows 路径下 PDF 后端与 Mermaid CLI 12 参数兼容问题。
- 22 项单元测试通过；离线集成 11 PASS / 1 SKIP；直接 DOCX→PDF 缺 LibreOffice 未验收。详见测试目录。
