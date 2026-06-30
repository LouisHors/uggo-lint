# 发布 uggo-lint VS Code 插件

## 任务描述

把当前 `vscode-extension/` 目录推进为可打包、可安装、可发布到 VS Code Marketplace 的正式扩展，并完成发布后的验证和文档收尾。

## 相关文档

- 设计文档: [../plans/2026-06-29-design-vscode-extension.md](../plans/2026-06-29-design-vscode-extension.md)
- 计划文档: [../plans/2026-06-29-vscode-extension-publishing.md](../plans/2026-06-29-vscode-extension-publishing.md)

## 实施计划

1. Task 1: 补齐发布元数据
2. Task 2: 验证可安装产物
3. Task 3: 建立发布流程
4. Task 4: 发布后验证与收尾

## 验收标准

- `vsce package` 能生成可安装的 `.vsix`。
- 扩展元数据满足 Marketplace 发布要求。
- 可在干净环境安装并激活扩展。
- 发布流程（手动或 CI）有明确命令和说明。
- `README.md`、`vscode-extension/README.md` 和 `CHANGELOG.md` 说明发布方式。

## 进展记录

- 2026-06-29: 已开始整理发布计划，待执行。
- 2026-06-29: 已完成 Marketplace 元数据、.vscodeignore、发布脚本与 GitHub Actions 工作流。
- 2026-06-29: 已成功执行 `npm test` 与 `npm run vscode:package`，生成 `.vsix`。
- 2026-06-29: 本机缺少 `code` 命令，无法在 CLI 中完成安装验证。
