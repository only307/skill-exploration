# 第三方来源、版权与 MIT 许可声明

**这份文件保留本 Skill 调用的两个上游引擎的来源、版权和许可。** 本 Skill 原创内容采用 [MIT LICENSE](LICENSE)，与仓库根目录 [LICENSE](../../../LICENSE) 一致，署名为 `2026 only307`。该声明仅适用于维护者有权许可的原创内容，不替代上游许可证，也不改变上游版权归属。

**显眼的上游入口：[Docling 官方仓库](https://github.com/docling-project/docling) · [MD2X 官方仓库](https://github.com/ChaoticQubit/MD2X)**

本项目的入站解析使用 Docling，Markdown 出站使用 MD2X。当前实现调用独立安装的 Python API / CLI，未将这两个项目的源码内嵌进可提交的路由代码。下面保留上游完整 MIT 文本，方便使用者溯源，以及后续按许可移植源码时保留版权。项目维护者的授权不能代替上游许可。

## 1. Docling

- 产品与源码：[docling-project/docling](https://github.com/docling-project/docling)
- 最新源码下载：[main ZIP](https://github.com/docling-project/docling/archive/refs/heads/main.zip)
- 实际调用的发布版：2.135.0；完整依赖见 requirements.lock.txt。
- 版权持有人：**The Docling Contributors**（按上游原文保留，没有改成路由维护者）。
- 许可：MIT；[随上游更新的 LICENSE](https://github.com/docling-project/docling/blob/main/LICENSE)。
- 许可核查：2026-10-09；main 快照 `b2a59b9fa1a31ae6584d4dd18cd0c2bb3ca285b6`；[可追溯许可原文](https://github.com/docling-project/docling/blob/b2a59b9fa1a31ae6584d4dd18cd0c2bb3ca285b6/LICENSE)。这是来源审查快照，运行环境仍为上面的已测发布版。

完整原文：

```text
MIT License

Copyright The Docling Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 2. MD2X

- 产品与源码：[ChaoticQubit/MD2X](https://github.com/ChaoticQubit/MD2X)
- 最新源码下载：[main ZIP](https://github.com/ChaoticQubit/MD2X/archive/refs/heads/main.zip)
- 实际调用的发布版：0.1.0；PyPI 和 main 的 CLI 可能不同。
- 版权持有人：**ChaoticQubit**；保留上游年份 2026。
- 许可：MIT；[随上游更新的 LICENSE](https://github.com/ChaoticQubit/MD2X/blob/main/LICENSE)。
- 许可核查：2026-10-09；main 快照 `d94038d4e9e964368faa12ad1f191f0c0b746e06`；[可追溯许可原文](https://github.com/ChaoticQubit/MD2X/blob/d94038d4e9e964368faa12ad1f191f0c0b746e06/LICENSE)。

完整原文：

```text
MIT License

Copyright (c) 2026 ChaoticQubit

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## 3. 复制、修改和移植时怎样保留

MIT 允许使用、复制、修改、合并、分发、再许可和销售。分发上游软件的副本或实质部分时，须保留其版权与许可声明；上面的完整原文包含免责声明。来源跳转链接帮助溯源，不能代替这些文本。[MIT 官方文本](https://opensource.org/license/mit)

下载或复制最新源码时，保留下载版本自带的 LICENSE，以及实际涉及的 NOTICE / 第三方许可；本声明是两个主项目的声明，不能覆盖整个上游依赖树。复制的代码放在清楚标识的来源目录，记录 commit、复制范围和本地修改，保留文件原有许可头。本仓库 LICENSE 不会把上游版权改成维护者版权。操作与验收见 [安装说明](INSTALL_BEGINNER.md#10-可选下载上游最新源码或移植代码)。

## 4. 其他依赖和模型不是统一 MIT

Pandoc 是 GPL-2.0-or-later；RapidOCR 与部分布局/OCR 模型涉及 Apache-2.0；实际采用的 TableFormer v2.3.0 模型卡标记 CDLA-Permissive-2.0。TeX、字体、浏览器、PDF 后端和间接依赖分别有自己的许可。此文件不声称“所有代码和权重都属于 MIT”。完整来源表见 [references/sources.md](references/sources.md)，含本次使用的模型快照。

本仓库不打包模型、浏览器、TeX 或 Pandoc 二进制。若以后打包分发这些组件，需要同时保留对应声明并履行该组件的分发条件。用户输入文档的版权和输出内容权利也不由本仓库 LICENSE 重新授予。
