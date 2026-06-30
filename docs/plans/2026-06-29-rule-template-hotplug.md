# uggo-lint 规则模板热插拔实施计划

> **Execution note:** After this plan is approved, use `horspowers:subagent-driven-development` or `horspowers:executing-plans` to implement it task-by-task in the current host.

**日期**: 2026-06-29

## 目标

让 `uggo-lint` 支持按配置加载不同的规则模板包，使团队可以在不改动核心代码的情况下切换、增删和复用一组规则定义。

## 架构方案

保持内置规则作为默认规则来源，再增加声明式模板规则层。模板规则由本地 YAML 文件或目录加载，运行时按配置合并到规则注册表中；每次执行 CLI 时重新加载，不引入常驻守护进程或文件监听。

## 技术栈

Python 3.11、PyYAML、pytest、dataclasses、glob/pathlib、CLI 配置加载。

---

### Task 1: 定义模板规则格式

**Files:**
- Create: `src/uggo_lint/rule_templates.py`
- Modify: `src/uggo_lint/config.py`
- Modify: `README.md`
- Create: `examples/uggo-lint-template.example.yaml`
- Test: `tests/test_config.py`

**Step 1: Write the failing config tests**

在 `tests/test_config.py` 中新增测试，验证能够读取：
- `rule_templates` 列表
- 单个模板文件路径
- 模板目录路径
- 关闭模板加载时的默认行为

**Step 2: Run the test to confirm the field is missing**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_config.py -q
```
Expected: FAIL，提示配置模型还没有模板字段。

**Step 3: Add template config fields**

在 `src/uggo_lint/config.py` 中新增：
- `rule_templates: list[str]`
- `enabled_rule_sets: list[str]`（可选，用于显式启用内置或模板规则集）

在 `src/uggo_lint/rule_templates.py` 中定义模板文件格式：
- `id`
- `message`
- `severity`
- `match` 条件（例如 `path_glob`、`contains`、`regex`）
- 可选的 `line_hint` 或 `column_hint`

**Step 4: Re-run the config tests**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_config.py -q
```
Expected: PASS。

### Task 2: 实现模板加载器

**Files:**
- Create: `src/uggo_lint/rule_registry.py`
- Create: `src/uggo_lint/rule_templates.py`
- Modify: `src/uggo_lint/cli.py`
- Test: `tests/test_rule_templates.py`

**Step 1: Write failing loader tests**

在 `tests/test_rule_templates.py` 中新增测试，覆盖：
- 单个 YAML 模板文件加载成功
- 目录中的多个模板文件合并加载
- 非法模板文件给出可读错误
- 同一个规则 id 重复时拒绝或按确定性策略处理

**Step 2: Run tests to expose current lack of loader**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_rule_templates.py -q
```
Expected: FAIL。

**Step 3: Implement template parsing and registry**

在 `src/uggo_lint/rule_templates.py` 中实现：
- 读取 YAML
- 规范化模板结构
- 生成 `Finding` 或可执行规则对象

在 `src/uggo_lint/rule_registry.py` 中实现：
- 汇总内置规则
- 汇总模板规则
- 去重和冲突处理

**Step 4: Re-run the loader tests**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_rule_templates.py -q
```
Expected: PASS。

### Task 3: 接入 CLI 执行路径

**Files:**
- Modify: `src/uggo_lint/cli.py`
- Modify: `src/uggo_lint/output.py`
- Test: `tests/test_cli.py`
- Test: `tests/test_run.py`

**Step 1: Write failing integration tests**

新增测试，验证：
- `check-file` 会同时跑内置规则和模板规则
- `run --format json --all` 会输出模板规则命中
- 模板规则的 `rule_id`、`message`、`severity` 会透出到 JSON

**Step 2: Run tests to confirm integration gap**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_cli.py tests/test_run.py -q
```
Expected: FAIL。

**Step 3: Wire registry into command execution**

在 `src/uggo_lint/cli.py` 中改为从 rule registry 获取所有规则，并在 `run_command` / `check_file_command` 里统一执行。

**Step 4: Re-run the integration tests**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_cli.py tests/test_run.py -q
```
Expected: PASS。

### Task 4: 文档与示例模板

**Files:**
- Modify: `README.md`
- Create: `examples/uggo-lint-template.example.yaml`
- Modify: `CHANGELOG.md`

**Step 1: Describe the template model**

在 `README.md` 中增加一节，说明：
- 哪些规则适合做模板
- 模板文件怎么放
- 如何按项目切换模板集
- 模板规则与内置规则的关系

**Step 2: Add example template packs**

在 `examples/uggo-lint-template.example.yaml` 中提供最小可运行示例，覆盖：
- `path_glob`
- `contains`
- `severity`
- `message`

**Step 3: Update changelog**

在 `CHANGELOG.md` 中补充规则模板支持说明。

### Task 5: 最终验证与边界检查

**Files:**
- Test: full Python suite

**Step 1: Run the full Python test suite**

Run:
```bash
PYTHONPATH=src .venv/bin/python -m pytest -q
```
Expected: 全量通过。

**Step 2: Verify template override boundaries**

手工检查以下约束是否成立：
- 模板规则不破坏内置规则输出
- 模板加载失败时给出清晰错误
- 默认配置下不额外启用模板规则

**Step 3: Commit**

```bash
git add src/uggo_lint tests README.md CHANGELOG.md examples/uggo-lint-template.example.yaml docs/plans
git commit -m "feat: add rule template hot-plug plan"
```
