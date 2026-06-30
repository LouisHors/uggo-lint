# uggo-lint VS Code 插件发布实施计划

> **Execution note:** After this plan is approved, use `horspowers:subagent-driven-development` or `horspowers:executing-plans` to implement it task-by-task in the current host.

**日期**: 2026-06-29

## 目标

把现有 `vscode-extension/` 从本地可运行的插件骨架，推进为可打包、可安装、可发布到 VS Code Marketplace 的正式扩展。

## 架构方案

保留当前 Python CLI 作为检查引擎，VS Code 扩展继续作为薄客户端。发布阶段只补齐 Marketplace 所需的扩展元数据、打包忽略规则、版本管理和发布命令，不重写运行时逻辑。

## 技术栈

VS Code Extension API、`@vscode/vsce`、Node.js、TypeScript、npm、Visual Studio Marketplace。

---

### Task 1: 补齐发布元数据

**Files:**
- Modify: `vscode-extension/package.json`
- Create: `vscode-extension/.vscodeignore`
- Create: `vscode-extension/CHANGELOG.md`
- Create: `vscode-extension/LICENSE`
- Modify: `vscode-extension/README.md`

**Step 1: Write the failing release metadata check**

在发布相关文件中补齐 Marketplace 需要的字段和排除规则，先用人工检查清单确认当前缺失项：
- `repository`
- `bugs`
- `homepage`
- `icon`
- `.vscodeignore`
- 扩展根目录内的 `CHANGELOG.md`
- 扩展根目录内的 `LICENSE`

**Step 2: Run the current packaging command to expose missing metadata**

Run:
```bash
cd vscode-extension
npm run compile
npx @vscode/vsce package
```
Expected: 如果 metadata 不完整，`vsce` 会提示缺失字段、忽略规则或打包问题。

**Step 3: Add publish-ready metadata**

在 `vscode-extension/package.json` 中补齐：
- `repository` 指向仓库地址
- `bugs` 指向 issue 页
- `homepage` 指向项目主页或 README
- `icon` 指向扩展图标（如 `images/icon.png`；若暂不加入图标，则明确保留默认样式并在发布前复核）
- `publisher` 保持与 Marketplace 账号一致

在 `vscode-extension/.vscodeignore` 中排除：
- `src/**`
- `*.ts`
- `*.map`
- `**/*.test.*`
- `node_modules/**`（如无运行时依赖则全部排除）
- 本地开发文件和临时文件

**Step 4: Add Marketplace-facing documentation files**

在 `vscode-extension/CHANGELOG.md` 中写入首个发布条目。
在 `vscode-extension/README.md` 中补齐安装、配置、命令和本地开发说明。
如需要，补充 `vscode-extension/LICENSE`，确保打包目录内可直接发布。

**Step 5: Re-run packaging**

Run:
```bash
cd vscode-extension
npm run compile
npx @vscode/vsce package
```
Expected: 生成 `.vsix` 文件且无 metadata 错误。

### Task 2: 验证可安装产物

**Files:**
- No new source files expected
- Test: `vscode-extension/*.vsix`

**Step 1: Install the packaged VSIX in a clean profile**

Run:
```bash
code --install-extension vscode-extension/uggo-lint-vscode-0.1.1.vsix --force
```
Expected: VS Code 安装成功，无扩展清单错误。

**Step 2: Smoke test activation**

在 VS Code Extension Development Host 或本机 VS Code 中：
- 打开一个 Go 文件
- 触发 `Uggo Lint: Check Current File`
- 触发 `Uggo Lint: Check Workspace`
- 确认 Output 面板和 Problems 面板均正常工作

**Step 3: Verify release versioning**

检查 `vscode-extension/package.json` 的版本号是否符合首次发布语义，并确认与后续发布策略一致（例如首次正式版 `0.1.0`）。

### Task 3: 建立发布流程

**Files:**
- Modify: `vscode-extension/package.json`
- Create: `.github/workflows/publish-vscode-extension.yml`
- Modify: `README.md`
- Modify: `vscode-extension/README.md`

**Step 1: Decide the publishing path**

优先采用官方推荐的安全自动化发布方式：
- 首选：Microsoft Entra ID + workload identity federation / managed identity
- 备用：`vsce login` + Personal Access Token

**Step 2: Add release scripts**

在 `vscode-extension/package.json` 中新增脚本：
- `vscode:package`
- `vscode:publish`
- `vscode:prepublish`

**Step 3: Add CI publishing workflow**

创建 GitHub Actions 工作流，完成以下动作：
- checkout
- setup Node.js
- install dependencies
- compile extension
- package 或 publish
- 仅在 tag / release / 手动触发时执行发布

**Step 4: Document the workflow**

在 `README.md` 与 `vscode-extension/README.md` 中写明：
- 如何本地打包
- 如何本地安装 `.vsix`
- 如何进行正式发布
- 如何进行预发布（如后续启用）

### Task 4: 发布后验证与收尾

**Files:**
- Modify: `CHANGELOG.md`
- Modify: `vscode-extension/CHANGELOG.md`
- Modify: `docs/active/2026-06-29-task-publish-vscode-extension.md`

**Step 1: Verify Marketplace listing inputs**

检查以下信息是否齐备：
- publisher id
- extension name
- repository link
- README 渲染效果
- LICENSE
- icon（如果添加）

**Step 2: Publish a release or pre-release**

Run one of:
```bash
cd vscode-extension
npx @vscode/vsce publish
```
或
```bash
cd vscode-extension
npx @vscode/vsce publish --pre-release
```
Expected: Marketplace 返回成功并生成可安装条目。

**Step 3: Validate install and update behavior**

在干净的 VS Code 环境中：
- 安装 Marketplace 版本
- 确认扩展激活正常
- 运行命令面板命令
- 确认 Problems 面板和保存检查正常

**Step 4: Update changelog and task tracking**

把本次发布版本写入 `CHANGELOG.md` 与 `vscode-extension/CHANGELOG.md`，并在活跃任务文档中记录发布完成状态。
