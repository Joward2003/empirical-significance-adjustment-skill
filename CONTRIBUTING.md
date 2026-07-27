# Contributing

欢迎改进方法路由、审计脚本、文档和测试。

## 贡献原则

- 不提交以更小 p 值为唯一理由的模型、样本、聚类、控制或阈值选择。
- 新方法必须有唯一 `method_id`、适用前提、使用限制和完整报告字段。
- 新脚本必须保留既有 baseline 锁定、日志和报告审计链。
- 修改 Schema、注册表或报告模板时，同时更新测试和 README。
- 不把未核验的 PDF 标签写成可公开验证的文献来源。

## 提交前检查

```bash
python -m pip install -r requirements.txt
python scripts/test_repository_integrity.py
python -m unittest discover -s tests -v
git diff --check
```

请在 PR 中说明：问题、变更范围、验证命令和任何方法学限制。
