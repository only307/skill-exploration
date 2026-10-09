# 测试材料入口

测试脚本、专用依赖和公开示例均在本目录。生成结果写入被 Git 忽略的 `artifacts/`，不随源码发布。

| 内容 | 位置 |
| --- | --- |
| 路由与失败保护测试 | `test_routing.py` |
| 真实引擎集成测试及动态样例生成 | `run_integration.py` |
| 测试专用依赖 | `requirements.txt`，引用上级锁定依赖 |
| 安装验收示例 | `fixtures/quickstart.md`、`fixtures/mermaid.md`、`fixtures/chinese.md` |
| 基线结果与未测范围 | [ACCEPTANCE.md](ACCEPTANCE.md) |

在 Skill 根目录运行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r tests\requirements.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -p test_routing.py -v
.\.venv\Scripts\python.exe tests\run_integration.py
```

首次下载模型时，集成测试可加 `--download`；之后省略并复测。每轮结果写入 `artifacts/run-随机编号/results.json`，同时保留测试文档与相邻资源。任何 FAIL 都需排查；SKIP 表示缺少依赖或未执行，不能算 PASS。CPU 模型首次启动可能较慢。

基线环境的原始输出仅保存在维护者本地；公开仓库提供验收摘要和可复现测试，不包含这些报告。不要将含本机绝对路径或用户文档的输出目录作为公开源码上传。
