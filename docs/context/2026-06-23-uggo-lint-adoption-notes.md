# uggo-lint 采纳说明

## 目标

帮助团队以最小迁移成本把 `uggo-lint` 接入已有 Go 仓库，并尽量复用已经存在的 `golangci-lint`、`goimports` 和 `pre-commit` 资产。

## 推荐接入顺序

1. 先执行 `uggo-lint doctor`，确认基础依赖完整
2. 根据仓库现状选择 `hook_backend`
3. 本地先跑 `uggo-lint run`
4. 再把相同入口接到 CI

## 与现有 golangci-lint 仓库的兼容策略

- 如果仓库已经有 `.golangci.yml`，保留原有配置，让 `uggo-lint` 只负责触发与少量补充规则
- 如果仓库已经在用 `pre-commit`，优先使用 `uggo-lint print-precommit-config`
- 如果仓库没有统一 hook 方案，可以先用 `uggo-lint install-hooks`

## 常见失败场景

### 1. 本地缺工具

表现：
- `uggo-lint doctor` 报缺少 `goimports` 或 `golangci-lint`

排查：
- 先确认命令是否在 `PATH`
- 再确认 CI 与本地是否使用了相同版本

### 2. CI 通过，本地不通过

表现：
- 本地 `run` 触发格式化，但 CI 只做检查

排查：
- 明确本地是否启用 `check_only`
- 保证 README 和仓库配置使用相同约定

### 3. 仓库已存在 pre-commit 配置

表现：
- `install-hooks` 提示使用 pre-commit 路径

排查：
- 这是预期行为
- 使用 `print-precommit-config` 或 `.pre-commit-hooks.yaml` 接入即可
