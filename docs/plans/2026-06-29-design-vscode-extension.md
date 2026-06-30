# uggo-lint VS Code 插件设计

**日期**: 2026-06-29

## 背景

`uggo-lint` 当前定位是 Go 仓库的 Git hook 与 `pre-commit` 辅助工具，主要在 commit 阶段执行检查。用户希望在 VS Code 开发过程中提前暴露问题，减少等到 commit 阶段才发现 lint 问题的反馈延迟。

## 目标

将 `uggo-lint` 扩展为可被 VS Code 实时调用的开发期检查工具，同时保留现有 CLI、Git hook、`pre-commit` 和 CI 使用方式。

## 非目标

- 不在第一版重写 `golangci-lint`、`goimports` 或 Go AST 分析能力。
- 不在第一版把所有 Python 规则迁移到 TypeScript。
- 不在保存文件时自动执行 `goimports -w` 或 `git add`，避免编辑器保存产生隐式修改和暂存行为。
- 不取代现有 commit 阶段检查；VS Code 插件只把反馈提前。

## 方案选择

### 方案 A：薄插件直接解析现有 CLI 文本输出

插件监听 VS Code 保存事件和命令面板命令，直接调用现有 `uggo-lint run`，再解析标准输出中的 finding 文本。

优点：
- 改动最小，最快可验证。
- Python CLI 逻辑完全复用。

缺点：
- 文本输出格式不是稳定 API，后续改文案会影响插件。
- 当前 `run` 依赖 staged files，不适合保存当前文件时检查未暂存内容。
- 很难准确映射行列信息到 VS Code Diagnostics。

### 方案 B：CLI 增加机器可读输出，VS Code 插件调用 CLI

CLI 增加 `check-file <path> --format json` 和 `run --format json`。插件调用 CLI 并消费 JSON，把结果转换为 VS Code Diagnostics。

优点：
- 复用 Python 规则和现有 Go 工具链编排。
- JSON 输出成为稳定集成契约，插件、CI、其他编辑器都能复用。
- 保存时可只检查当前文件，手动命令仍可运行完整 workspace 检查。

缺点：
- 需要先增强 CLI 输出模型。
- 第一版仍依赖本机安装 Python 包和外部 Go 工具。

### 方案 C：把规则重写为 TypeScript 插件逻辑

插件直接在 TypeScript 中实现规则扫描和 Diagnostics，不依赖 Python CLI。

优点：
- 编辑器体验可做到最轻量。
- 不要求用户额外安装 Python CLI 才能获得部分检查。

缺点：
- Python CLI 和插件规则会分叉，维护成本高。
- 会削弱现有项目作为单一规则来源的价值。
- 完整 workspace 检查仍要调用 `golangci-lint`。

## 推荐方案

采用方案 B：`uggo-lint` 保持 Python CLI 为核心规则来源，新增机器可读输出；VS Code 插件作为薄客户端，负责触发检查、展示问题和提供命令入口。

## 用户体验

### 保存时检查当前文件

当用户保存 `.go` 文件时，插件执行：

```bash
uggo-lint check-file path/to/file.go --format json
```

插件将 JSON findings 转换为 VS Code Diagnostics：
- `error` 映射为 Error
- `warning` 映射为 Warning
- 每条 finding 绑定文件、行、列、规则 ID 和消息

如果 `uggo-lint` 不存在或运行失败，插件只在输出面板和状态栏提示，不阻塞保存。

### 手动完整检查 workspace

命令面板提供 `Uggo Lint: Check Workspace`，执行：

```bash
uggo-lint run --format json --check-only
```

插件将完整结果写入 Problems 面板，并在输出面板显示原始运行摘要。完整检查不自动格式化、不自动暂存文件。

### Doctor 检查

命令面板提供 `Uggo Lint: Doctor`，执行：

```bash
uggo-lint doctor
```

用于检查 `go`、`golangci-lint`、`goimports` 和 `uggo-lint` 自身是否可用。

## CLI 设计

### Finding JSON 结构

CLI 输出稳定 JSON 对象：

```json
{
  "ok": false,
  "findings": [
    {
      "rule_id": "no-panic-outside-tests",
      "message": "Avoid panic outside tests.",
      "path": "internal/app/service.go",
      "line": 24,
      "column": 3,
      "severity": "error",
      "source": "uggo-lint"
    }
  ],
  "steps": [],
  "summary": "1 finding"
}
```

### `check-file`

`check-file` 对单个 `.go` 文件运行内置自定义规则，不调用 `goimports`、`git add` 或 staged file 逻辑。它适合保存时快速反馈。

### `run --format json`

`run --format json` 保留现有完整流程，但把自定义规则 findings 和外部命令失败包装为 JSON。第一版可以只把自定义规则映射为精确 Diagnostics；外部命令失败以 workspace 级诊断或输出面板摘要展示。

## VS Code 插件设计

### 插件目录

在仓库内新增 `vscode-extension/`，作为独立 Node/TypeScript package。这样可以保留 Python 包结构，同时让 VS Code 插件有自己的构建、测试和发布配置。

### 关键模块

- `vscode-extension/src/extension.ts`: 插件激活、命令注册、保存事件监听。
- `vscode-extension/src/runner.ts`: 调用 `uggo-lint` CLI，处理 cwd、超时、stdout/stderr。
- `vscode-extension/src/diagnostics.ts`: JSON findings 到 VS Code Diagnostics 的转换。
- `vscode-extension/src/config.ts`: 读取 VS Code 配置项。

### VS Code 配置项

- `uggoLint.executablePath`: 默认 `uggo-lint`。
- `uggoLint.checkOnSave`: 默认 `true`。
- `uggoLint.checkWorkspaceArgs`: 默认 `["run", "--format", "json", "--check-only"]`。
- `uggoLint.checkFileArgs`: 默认 `["check-file", "${file}", "--format", "json"]`。
- `uggoLint.timeoutMs`: 默认 `30000`。

### 命令

- `uggoLint.checkCurrentFile`: 检查当前打开的 Go 文件。
- `uggoLint.checkWorkspace`: 检查当前 workspace。
- `uggoLint.doctor`: 运行环境检查。
- `uggoLint.clearDiagnostics`: 清空插件产生的问题。

## 测试策略

### Python CLI 测试

新增或扩展 pytest：
- `check-file` 能对单文件输出 JSON。
- JSON finding 包含 path、line、column、severity、rule_id、message。
- `run --format json` 在自定义规则失败时返回可解析 JSON。
- 普通文本输出保持兼容。

### VS Code 插件测试

新增 TypeScript 单元测试：
- runner 能解析合法 JSON。
- runner 能处理 CLI 不存在、超时、非 JSON 输出。
- diagnostics 能正确映射 severity 和文件位置。
- config 能读取默认值。

第一版不强制引入复杂的 VS Code integration test；用 TypeScript 单元测试覆盖核心逻辑。

## 交付标准

- `uggo-lint check-file <file> --format json` 可用。
- `uggo-lint run --format json --check-only` 可用。
- VS Code 插件能在保存 `.go` 文件时显示内置规则问题。
- VS Code 插件能通过命令面板执行完整 workspace 检查。
- 插件 README 说明安装、配置和本地开发方式。
- 现有 CLI 文本行为和测试不回退。
