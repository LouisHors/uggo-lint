# 实施 uggo-lint VS Code 插件集成

## 任务描述

按设计文档和实施计划，为 `uggo-lint` 增加机器可读 CLI 输出与 VS Code 插件集成，使开发者能在保存 Go 文件时获得即时诊断，也能手动运行完整 workspace 检查。

## 相关文档

- 设计文档: [../plans/2026-06-29-design-vscode-extension.md](../plans/2026-06-29-design-vscode-extension.md)
- 计划文档: [../plans/2026-06-29-vscode-extension.md](../plans/2026-06-29-vscode-extension.md)

## 实施计划

1. Task 1: 为自定义规则补齐位置信息
2. Task 2: 增加 JSON 输出模型
3. Task 3: 增加 `check-file` 命令
4. Task 4: 搭建 VS Code 插件骨架
5. Task 5: 实现 CLI runner
6. Task 6: 映射 Diagnostics 与保存检查
7. Task 7: 更新文档与最终验证

## 验收标准

- `uggo-lint check-file <file> --format json` 可输出可解析 JSON。
- `uggo-lint run --format json --check-only` 可输出可解析 JSON。
- VS Code 插件能在保存 `.go` 文件时写入 Problems 诊断。
- VS Code 插件能通过命令面板运行当前文件检查、workspace 检查、doctor 和清空诊断。
- Python 测试和 VS Code 插件测试均通过。
- README、插件 README 和 CHANGELOG 说明新能力与使用方式。

## 进展记录

- 2026-06-29: 已完成 CLI JSON 输出、check-file 命令与 VS Code 插件骨架。
- 2026-06-29: 已通过 Python 全量测试与 VS Code 插件单测。
- 2026-06-29: 已确认 workspace 支持 `--all` 全量检查路径，满足保存时诊断与手动完整检查目标。
