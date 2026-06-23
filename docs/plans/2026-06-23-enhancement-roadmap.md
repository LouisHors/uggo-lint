# uggo-lint 强化路线图实施计划

> **Execution note:** After this plan is approved, use `horspowers:executing-plans` or `horspowers:subagent-driven-development` to implement it task-by-task in the current host.

**日期**: 2026-06-23

## 目标

将 `uggo-lint` 从“可用的本地 lint 小工具”强化为“可配置、可复用、可在团队仓库稳定落地”的 Go 代码质量工具，覆盖本地 pre-commit、CI 检查、规则扩展与标准化分发。

## 架构方案

保持当前 Python CLI + 现有 Go 工具链复用的混合架构，不重写底层 lint 能力，而是在 `src/uggo_lint` 上继续增强配置解析、运行模式、hook 集成和规则模块。文档、测试和分发元数据同步补齐，使仓库既适合个人使用，也能被其他项目直接接入。

## 技术栈

Python 3.11、argparse、PyYAML、pytest、Git hooks、pre-commit、golangci-lint、goimports。

---

### Task 1: 建立配置驱动骨架

**Files:**
- Modify: `src/uggo_lint/config.py`
- Modify: `src/uggo_lint/cli.py`
- Modify: `examples/uggo-lint-config.example.yaml`
- Modify: `README.md`
- Test: `tests/test_config.py`
- Test: `tests/test_cli.py`

**Step 1: 先补失败测试，固定配置预期**

在 `tests/test_config.py` 中新增以下场景：
- 能读取 `strict` / `default` 模式
- 能读取 `ignore_paths`、`ignore_rules`、`check_only`
- 配置缺失时仍回退默认值

**Step 2: 运行配置测试，确认当前实现不满足新需求**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_config.py -q`
Expected: FAIL，提示新字段不存在或默认值不匹配

**Step 3: 扩展配置模型**

在 `src/uggo_lint/config.py` 中：
- 为 `UggoLintConfig` 增加 `mode`、`check_only`、`ignore_paths`、`ignore_rules`、`hook_backend` 等字段
- 将 `load_config()` 改为集中处理默认值、列表类型和布尔值
- 让 `strict` 模式自动映射更严格的默认规则集合，但允许局部覆盖

**Step 4: 将 CLI 接入新配置字段**

在 `src/uggo_lint/cli.py` 中让 `run`、`install-hooks`、`doctor` 读取统一配置对象，而不是只消费 `only_staged` 与 `required_tools`。

**Step 5: 更新示例配置和 README**

- 在 `examples/uggo-lint-config.example.yaml` 中给出最小配置与严格模式示例
- 在 `README.md` 中补充“项目如何通过 `.uggo-lint.yaml` 调整行为”的说明

**Step 6: 重新运行配置与 CLI 测试**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_config.py tests/test_cli.py -q`
Expected: PASS

**Step 7: Commit**

`git add src/uggo_lint/config.py src/uggo_lint/cli.py examples/uggo-lint-config.example.yaml README.md tests/test_config.py tests/test_cli.py && git commit -m "feat: add configurable lint modes"`

### Task 2: 强化 Hook 与 CI 运行体验

**Files:**
- Modify: `src/uggo_lint/cli.py`
- Modify: `src/uggo_lint/git_tools.py`
- Modify: `README.md`
- Create: `.pre-commit-hooks.yaml`
- Test: `tests/test_precommit.py`
- Test: `tests/test_git_tools.py`

**Step 1: 先写失败测试，固定 hook 安装行为**

在 `tests/test_precommit.py` 和 `tests/test_git_tools.py` 中新增场景：
- 能输出标准 pre-commit 仓库元数据
- 能区分原生 `.git/hooks/pre-commit` 与 `pre-commit` 框架安装建议
- `check-only` 模式不会触发 `goimports -w`

**Step 2: 运行目标测试，确认现有行为不足**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_precommit.py tests/test_git_tools.py -q`
Expected: FAIL

**Step 3: 扩展 hook 元数据能力**

- 在仓库根新增 `.pre-commit-hooks.yaml`，声明 `uggo-lint` hook
- 保持 `print-precommit-config` 兼容本地 `repo: local` 用法
- 在 `src/uggo_lint/git_tools.py` 中增加 pre-commit 检测辅助函数

**Step 4: 扩展 CLI 选项与安装逻辑**

在 `src/uggo_lint/cli.py` 中：
- 为 `run` 增加 `--check-only`
- 为 `install-hooks` 增加后端选择或自动检测逻辑
- 输出明确的接入提示，告诉用户当前应使用哪种方式

**Step 5: 更新 README 接入文档**

补充三种接入方式：
- 直接执行 `uggo-lint install-hooks`
- 复制 `print-precommit-config` 输出到现有配置
- 通过 `.pre-commit-hooks.yaml` 作为独立仓库引用

**Step 6: 重新运行 hook 相关测试**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_precommit.py tests/test_git_tools.py tests/test_cli.py -q`
Expected: PASS

**Step 7: Commit**

`git add .pre-commit-hooks.yaml src/uggo_lint/cli.py src/uggo_lint/git_tools.py README.md tests/test_precommit.py tests/test_git_tools.py tests/test_cli.py && git commit -m "feat: improve hook and pre-commit integration"`

### Task 3: 优化增量 lint 执行精度与输出

**Files:**
- Modify: `src/uggo_lint/cli.py`
- Modify: `src/uggo_lint/git_tools.py`
- Modify: `src/uggo_lint/runtime.py`
- Test: `tests/test_run.py`
- Test: `tests/test_runtime.py`

**Step 1: 先写失败测试，固定运行计划行为**

在 `tests/test_run.py` 中新增场景：
- staged 文件属于多个 package 时能聚合出稳定命令
- `check-only` 模式跳过格式化与 re-stage
- 失败输出包含步骤名、命令、退出码和 stderr 分类

**Step 2: 运行增量执行测试，确认当前实现未覆盖**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_run.py tests/test_runtime.py -q`
Expected: FAIL

**Step 3: 重构运行计划模型**

在 `src/uggo_lint/cli.py` 中：
- 将 `RunPlan` 扩展为包含格式化步骤、lint 目标、是否跳过 re-stage 等结构
- 让计划生成基于 staged Go 文件所属目录，构造更聚焦的 `golangci-lint` 目标
- 保留“无 staged Go 文件直接跳过”的轻量体验

**Step 4: 补齐子进程输出分组**

在 `run_process()` 一侧收集 stdout/stderr，并在失败时输出：
- 当前阶段（format/restage/lint/custom-rules）
- 命令行
- 退出码
- 关键错误内容

**Step 5: 用小步测试验证行为**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_run.py -q`
Expected: PASS

**Step 6: 运行完整核心测试**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_run.py tests/test_runtime.py tests/test_git_tools.py -q`
Expected: PASS

**Step 7: Commit**

`git add src/uggo_lint/cli.py src/uggo_lint/git_tools.py src/uggo_lint/runtime.py tests/test_run.py tests/test_runtime.py tests/test_git_tools.py && git commit -m "feat: improve incremental lint execution"`

### Task 4: 扩充 Uber Go Guide 规则集

**Files:**
- Modify: `src/uggo_lint/rules.py`
- Modify: `README.md`
- Test: `tests/test_rules.py`

**Step 1: 先写失败测试，定义低误报规则边界**

在 `tests/test_rules.py` 中新增场景：
- 检查 `context.Context` 是否位于参数列表首位
- 检查错误字符串是否避免首字母大写和尾部标点
- 检查 receiver 命名在同文件内是否明显不一致
- 确保不会误报测试文件与合法例外

**Step 2: 运行规则测试，确认当前只覆盖 3 条规则**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_rules.py -q`
Expected: FAIL

**Step 3: 分层组织规则实现**

在 `src/uggo_lint/rules.py` 中：
- 将每条规则拆成独立检测函数
- 抽一个统一的 rule registry，便于按配置启停
- 保持文件级文本扫描实现，优先低复杂度与可维护性

**Step 4: 增加规则文档说明**

在 `README.md` 中补充每条内置规则的目的、误报边界和适用场景，让团队知道什么时候应该修复，什么时候可以通过配置豁免。

**Step 5: 重新运行规则测试**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest tests/test_rules.py -q`
Expected: PASS

**Step 6: Commit**

`git add src/uggo_lint/rules.py README.md tests/test_rules.py && git commit -m "feat: extend uber-go-inspired rules"`

### Task 5: 完善团队复用与 CI 落地材料

**Files:**
- Modify: `README.md`
- Create: `examples/github-actions-go.yml`
- Create: `docs/context/2026-06-23-uggo-lint-adoption-notes.md`
- Test: 手工验证文档命令示例

**Step 1: 先整理团队接入目标**

将 README 中新增一节，明确说明以下问题：
- 适合什么类型的 Go 仓库
- 本地开发者需要安装哪些工具
- CI 中如何避免“本地过、CI 不过”

**Step 2: 增加可复制的 CI 示例**

新增 `examples/github-actions-go.yml`，包含：
- Python 环境准备
- `uggo-lint` 安装方式
- `uggo-lint doctor`
- `uggo-lint run --check-only` 或等价模式

**Step 3: 增加一份采纳说明上下文文档**

在 `docs/context/2026-06-23-uggo-lint-adoption-notes.md` 中记录：
- 推荐接入顺序
- 对已有 `golangci-lint` 仓库的兼容策略
- 常见失败场景与排查路径

**Step 4: 校对 README 中的命令示例**

手工执行并确认以下命令至少能给出合理输出：
- `PYTHONPATH=src python -m uggo_lint doctor`
- `PYTHONPATH=src python -m uggo_lint print-precommit-config`
- `PYTHONPATH=src python -m uggo_lint run --check-only`（完成实现后）

**Step 5: Commit**

`git add README.md examples/github-actions-go.yml docs/context/2026-06-23-uggo-lint-adoption-notes.md && git commit -m "docs: add ci and adoption guidance"`

### Task 6: 打磨发布与安装链路

**Files:**
- Modify: `pyproject.toml`
- Modify: `setup.py`
- Modify: `README.md`
- Create: `CHANGELOG.md`
- Create: `.github/workflows/release-check.yml`（如果仓库决定内置 GitHub Actions）
- Test: `tests/test_cli.py`、安装验证命令

**Step 1: 先明确发布目标**

将发布目标限定为“开发者可本地安装、可用 `pipx` 分发、版本元数据一致”，先不引入复杂包发布自动化。

**Step 2: 补充分发元数据**

在 `pyproject.toml` 中补充：
- 关键词、项目 URL、可选依赖或开发依赖说明
- 更明确的 build-system 声明（如果决定补齐）
- 与 README 一致的安装说明

**Step 3: 增加变更记录机制**

新增 `CHANGELOG.md`，初始化 `0.1.0` 和后续强化版本的记录格式。

**Step 4: 验证安装流程**

在本地通过以下命令完成一次安装链路验证：
- `python -m pip install -e .` 或文档中确定的替代命令
- `uggo-lint doctor`
- `uggo-lint --help` 或等效入口验证

**Step 5: 如仓库需要，增加发布检查工作流**

如果决定在 GitHub 上托管自动检查，则新增轻量 `.github/workflows/release-check.yml`，只验证安装和基础命令，不提前做 PyPI 发布。

**Step 6: Commit**

`git add pyproject.toml setup.py README.md CHANGELOG.md .github/workflows/release-check.yml && git commit -m "build: improve packaging and release flow"`

## 跨任务收尾

**Step 1: 运行完整回归测试**

Run: `PYTHONPATH=src /Users/ugreen/hors/my-code-wiki/.venv/bin/python -m pytest -q`
Expected: PASS

**Step 2: 运行核心命令验证**

Run:
- `PYTHONPATH=src python -m uggo_lint doctor`
- `PYTHONPATH=src python -m uggo_lint print-precommit-config`
- `PYTHONPATH=src python -m uggo_lint run`

Expected:
- doctor 输出依赖检查结果
- pre-commit 配置可直接复制使用
- run 在无 staged Go 文件时给出可理解提示

**Step 3: 更新任务文档进展**

将活跃任务文档状态从“待开始”更新为与实际执行阶段一致；如果完成全部强化，再归档任务文档。

**Step 4: 最终提交建议**

按任务分阶段提交，避免把 6 个方向压成单个大提交。推荐每个 Task 独立提交，最后再用一个 docs/build 收尾提交。
