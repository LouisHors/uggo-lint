# uggo-lint VS Code 插件实施计划

> **Execution note:** After this plan is approved, use `horspowers:executing-plans` or `horspowers:subagent-driven-development` to implement it task-by-task in the current host.

**日期**: 2026-06-29

## 目标

为 `uggo-lint` 增加机器可读 CLI 输出，并新增 VS Code 插件，让开发者能在保存 Go 文件时看到即时问题，也能通过命令面板运行完整 workspace 检查。

## 架构方案

保持 Python CLI 作为单一规则来源，先增加 `check-file` 和 `--format json` 输出契约。VS Code 插件放在 `vscode-extension/`，作为 TypeScript 薄客户端调用本机 `uggo-lint`，并把 JSON findings 映射到 VS Code Diagnostics。

## 技术栈

Python 3.11、argparse、pytest、TypeScript、VS Code Extension API、Node.js child_process、npm test。

---

### Task 1: 为自定义规则补齐位置信息

**Files:**
- Modify: `src/uggo_lint/rules.py`
- Test: `tests/test_rules.py`

**Step 1: Write the failing test**

在 `tests/test_rules.py` 中新增测试，使用包含 `panic("boom")` 的 Go 文件，断言返回的 finding 包含：
- `line == 4`
- `column > 0`
- `path` 指向测试文件
- `rule_id == "no-panic-outside-tests"`

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/test_rules.py -q`
Expected: FAIL，提示 `Finding` 没有 `line` 或 `column` 字段。

**Step 3: Add location fields**

在 `src/uggo_lint/rules.py` 中：
- 为 `Finding` dataclass 增加 `line: int = 1` 和 `column: int = 1`。
- 增加 helper，把 regex match 的字符偏移转换为 1-based line/column。
- 每条规则创建 finding 时传入检测位置。
- 找不到精确位置时回退到 `line=1`、`column=1`。

**Step 4: Run focused tests**

Run: `PYTHONPATH=src python -m pytest tests/test_rules.py -q`
Expected: PASS。

**Step 5: Run CLI regression tests**

Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_run.py -q`
Expected: PASS。

### Task 2: 增加 JSON 输出模型

**Files:**
- Create: `src/uggo_lint/output.py`
- Modify: `src/uggo_lint/cli.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_run.py`

**Step 1: Write failing JSON tests**

在 `tests/test_cli.py` 或 `tests/test_run.py` 中新增测试：
- 给定一个 `Finding`，JSON 输出包含 `ok`、`findings`、`steps`、`summary`。
- finding JSON 包含 `rule_id`、`message`、`path`、`line`、`column`、`severity`、`source`。
- 普通文本输出仍保持原有格式。

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_run.py -q`
Expected: FAIL，提示缺少 JSON formatter 或 CLI 参数。

**Step 3: Implement output helpers**

在 `src/uggo_lint/output.py` 中新增：
- `finding_to_dict(finding: Finding, repo_root: Path) -> dict[str, object]`
- `render_json_result(ok: bool, findings: list[Finding], repo_root: Path, steps: list[dict[str, object]] | None = None, summary: str = "") -> str`

**Step 4: Wire `--format` into parser**

在 `src/uggo_lint/cli.py` 中：
- 为 `run` 增加 `--format`，choices 为 `text` 和 `json`，默认 `text`。
- 保持现有文本输出路径不变。
- 当 `--format json` 时，只输出 JSON 到 stdout。

**Step 5: Run focused tests**

Run: `PYTHONPATH=src python -m pytest tests/test_cli.py tests/test_run.py -q`
Expected: PASS。

### Task 3: 增加 `check-file` 命令

**Files:**
- Modify: `src/uggo_lint/cli.py`
- Modify: `README.md`
- Test: `tests/test_cli.py`

**Step 1: Write failing command tests**

在 `tests/test_cli.py` 中新增测试：
- `uggo-lint check-file sample.go --format json` 对单文件输出 JSON。
- 有 error finding 时退出码为 `1`。
- 只有 warning finding 时退出码为 `0`。
- 文件不存在时退出码为 `1`，JSON 中包含错误摘要。

**Step 2: Run test to verify it fails**

Run: `PYTHONPATH=src python -m pytest tests/test_cli.py -q`
Expected: FAIL，提示 parser 不认识 `check-file`。

**Step 3: Implement command parser**

在 `src/uggo_lint/cli.py` 中：
- 新增 subparser `check-file`。
- 增加必填参数 `path`。
- 增加 `--format`，choices 为 `text` 和 `json`，默认 `text`。

**Step 4: Implement command handler**

在 `src/uggo_lint/cli.py` 中新增 `check_file_command(repo_root: Path, path: Path, output_format: str) -> int`：
- 校验文件存在。
- 校验后缀为 `.go`。
- 调用 `run_custom_rules(path)`。
- text 模式复用 `print_findings()`。
- json 模式调用 `render_json_result()`。
- 任意 `severity == "error"` 时返回 `1`，否则返回 `0`。

**Step 5: Update docs**

在 `README.md` 中新增 “Editor integration” 小节，说明：

```bash
uggo-lint check-file path/to/file.go --format json
uggo-lint run --format json --check-only
```

**Step 6: Run focused tests**

Run: `PYTHONPATH=src python -m pytest tests/test_cli.py -q`
Expected: PASS。

### Task 4: 搭建 VS Code 插件骨架

**Files:**
- Create: `vscode-extension/package.json`
- Create: `vscode-extension/tsconfig.json`
- Create: `vscode-extension/src/extension.ts`
- Create: `vscode-extension/src/config.ts`
- Create: `vscode-extension/README.md`

**Step 1: Create extension manifest**

在 `vscode-extension/package.json` 中定义：
- `name`: `uggo-lint-vscode`
- `displayName`: `uggo-lint`
- `engines.vscode`: `^1.90.0`
- activation event: `onLanguage:go`
- commands: `uggoLint.checkCurrentFile`、`uggoLint.checkWorkspace`、`uggoLint.doctor`、`uggoLint.clearDiagnostics`
- configuration: `uggoLint.executablePath`、`uggoLint.checkOnSave`、`uggoLint.timeoutMs`

**Step 2: Add TypeScript config**

在 `vscode-extension/tsconfig.json` 中设置 CommonJS 输出到 `out/`，源码目录为 `src/`，开启 `strict`。

**Step 3: Implement activation shell**

在 `vscode-extension/src/extension.ts` 中：
- 创建 `DiagnosticCollection`。
- 注册四个命令。
- 注册 `workspace.onDidSaveTextDocument`，仅在 `languageId === "go"` 且 `checkOnSave` 为 true 时触发。
- `deactivate()` 中 dispose collection。

**Step 4: Implement config reader**

在 `vscode-extension/src/config.ts` 中导出 `getUggoLintConfig()`，读取默认值：
- executablePath: `uggo-lint`
- checkOnSave: `true`
- timeoutMs: `30000`

**Step 5: Install dependencies**

Run: `cd vscode-extension && npm install`
Expected: 生成 `package-lock.json`。

**Step 6: Compile extension**

Run: `cd vscode-extension && npm run compile`
Expected: PASS，生成 `out/`。

### Task 5: 实现 CLI runner

**Files:**
- Create: `vscode-extension/src/runner.ts`
- Create: `vscode-extension/src/types.ts`
- Modify: `vscode-extension/src/extension.ts`
- Test: `vscode-extension/src/runner.test.ts`

**Step 1: Add tests for JSON parsing**

在 `vscode-extension/src/runner.test.ts` 中新增测试：
- 合法 JSON 输出解析为 `UggoLintResult`。
- CLI 退出码为 `1` 但 JSON 合法时仍返回 result。
- 非 JSON 输出抛出带 stderr/stdout 摘要的错误。

**Step 2: Run test to verify it fails**

Run: `cd vscode-extension && npm test`
Expected: FAIL，提示 runner 未实现。

**Step 3: Define result types**

在 `vscode-extension/src/types.ts` 中定义：
- `UggoLintSeverity = "error" | "warning"`
- `UggoLintFinding`
- `UggoLintResult`

**Step 4: Implement process runner**

在 `vscode-extension/src/runner.ts` 中：
- 使用 `child_process.spawn` 调用 CLI。
- 支持 cwd 和 timeout。
- 收集 stdout/stderr。
- JSON 合法时返回 result，即使 exit code 非 0。
- JSON 不合法或命令不存在时抛出明确错误。

**Step 5: Wire commands to runner**

在 `vscode-extension/src/extension.ts` 中：
- `checkCurrentFile` 调用 `check-file <file> --format json`。
- `checkWorkspace` 调用 `run --format json --check-only`。
- `doctor` 调用 `doctor` 并显示输出面板。

**Step 6: Run tests and compile**

Run: `cd vscode-extension && npm test && npm run compile`
Expected: PASS。

### Task 6: 映射 Diagnostics 与保存检查

**Files:**
- Create: `vscode-extension/src/diagnostics.ts`
- Modify: `vscode-extension/src/extension.ts`
- Test: `vscode-extension/src/diagnostics.test.ts`

**Step 1: Add diagnostics tests**

在 `vscode-extension/src/diagnostics.test.ts` 中新增测试：
- `severity: "error"` 映射到 `DiagnosticSeverity.Error`。
- `severity: "warning"` 映射到 `DiagnosticSeverity.Warning`。
- 1-based line/column 转为 VS Code 0-based range。
- source 设置为 `uggo-lint`，code 设置为 `rule_id`。

**Step 2: Run test to verify it fails**

Run: `cd vscode-extension && npm test`
Expected: FAIL，提示 diagnostics mapper 未实现。

**Step 3: Implement mapper**

在 `vscode-extension/src/diagnostics.ts` 中新增：
- `findingsToDiagnostics(findings: UggoLintFinding[]): Map<string, vscode.Diagnostic[]>`
- `findingToDiagnostic(finding: UggoLintFinding): vscode.Diagnostic`

**Step 4: Apply diagnostics in extension**

在 `vscode-extension/src/extension.ts` 中：
- 当前文件检查只更新当前文件的 diagnostics。
- workspace 检查按 finding path 分组更新 diagnostics。
- clear 命令调用 collection.clear()。

**Step 5: Verify save behavior manually**

Run: `cd vscode-extension && npm run compile`
Expected: PASS。

Manual check:
- 打开 Extension Development Host。
- 打开一个 Go 文件。
- 写入会触发 `no-panic-outside-tests` 的代码并保存。
- Problems 面板出现 `uggo-lint` 问题。

### Task 7: 更新文档与最终验证

**Files:**
- Modify: `README.md`
- Modify: `vscode-extension/README.md`
- Modify: `CHANGELOG.md`
- Test: full validation commands

**Step 1: Update root README**

在 `README.md` 中补充：
- VS Code 插件目录说明。
- CLI JSON 集成命令。
- 编辑器集成不替代 pre-commit/CI。

**Step 2: Update extension README**

在 `vscode-extension/README.md` 中补充：
- 本地开发步骤。
- 配置项说明。
- 命令面板命令。
- 常见问题：找不到 `uggo-lint`、找不到 Go 工具、保存时不检查。

**Step 3: Update changelog**

在 `CHANGELOG.md` 中新增未发布条目，说明 CLI JSON 输出、`check-file` 和 VS Code 插件。

**Step 4: Run Python tests**

Run: `PYTHONPATH=src python -m pytest -q`
Expected: PASS。

**Step 5: Run extension tests**

Run: `cd vscode-extension && npm test && npm run compile`
Expected: PASS。

**Step 6: Run smoke commands**

Run: `PYTHONPATH=src python -m uggo_lint check-file tests/fixtures/sample.go --format json`
Expected: 输出合法 JSON。如果仓库没有现成 Go fixture，则用临时目录创建一个包含触发规则的 `.go` 文件执行 smoke test。

**Step 7: Commit**

```bash
git add src/uggo_lint tests README.md CHANGELOG.md vscode-extension docs/plans docs/active
git commit -m "feat: add vscode extension integration plan"
```
