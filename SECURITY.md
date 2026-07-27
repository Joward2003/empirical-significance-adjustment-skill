# Security and Integrity Policy

请不要在公开 issue 中上传原始数据、受限研究材料、身份信息或密钥。

本项目的 JSONL 哈希链可检测运行记录在写入后的常规编辑、删除或重排；它不是数字签名，
也不能阻止拥有全部本地文件写权限的一方重写 snapshot、日志和哈希。若需要更强保证，
请将 `baseline_snapshot.json`、两份 JSONL 日志和最终报告的 SHA-256 提交到受保护的 Git
远端、机构存档或签名时间戳服务。

若发现脚本可绕过 baseline 锁定、Schema 校验或 p 值决策限制，请私下联系维护者，并提供
最小可复现步骤；在修复发布前请避免公开利用细节。
