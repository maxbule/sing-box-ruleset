# 本地规则源配置指南

## 概述

本项目支持两种方式获取 Clash 规则：
1. **远程链接方式**（当前）：直接从 GitHub 原始文件链接下载
2. **本地文件方式**（推荐）：从本地 ios_rule_script 仓库读取

## 方案一：使用 Git 子模块（推荐）

### 步骤 1：添加子模块
```bash
cd /workspaces/sing-box-ruleset
git submodule add https://github.com/maxbule/ios_rule_script.git ios_rules
git commit -m "Add ios_rule_script as submodule"
```

### 步骤 2：修改 sources.txt
将 sources.txt 中的远程链接改为本地路径。例如：

**修改前：**
```txt
https://raw.githubusercontent.com/maxbule/ios_rule_script/master/rule/Clash/Netflix/Netflix_Classical.yaml
https://raw.githubusercontent.com/maxbule/ios_rule_script/master/rule/Clash/Spotify/Spotify.yaml
```

**修改后：**
```txt
./ios_rules/rule/Clash/Netflix/Netflix_Classical.yaml
./ios_rules/rule/Clash/Spotify/Spotify.yaml
```

### 步骤 3：自动更新规则

**手动更新：**
```bash
# 更新 ios_rule_script 子模块
git submodule update --remote

# 重新生成 JSON 文件
python convert.py
```

**GitHub Actions 自动更新：**
见下一节

## 方案二：使用本地克隆的 ios_rule_script

如果你已经有本地的 ios_rule_script 仓库：

### 在 sources.txt 中使用相对路径：
```txt
../ios_rule_script/rule/Clash/Netflix/Netflix_Classical.yaml
../ios_rule_script/rule/Clash/Spotify/Spotify.yaml
```

## GitHub Actions 自动化

### 场景 1：当 ios_rule_script 更新时自动生成规则

创建 `.github/workflows/update-on-submodule-change.yml`：

```yaml
name: Update Rules on Submodule Change

on:
  workflow_dispatch:  # 手动触发
  schedule:
    - cron: '0 12 * * *'  # 每天 UTC 12 点运行

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout with submodules
        uses: actions/checkout@v3
        with:
          submodules: 'recursive'
          fetch-depth: 0

      - name: Update submodules
        run: |
          git submodule update --remote --merge
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Generate rules
        run: python convert.py

      - name: Commit and push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add -A
          if git diff --quiet && git diff --staged --quiet; then
            echo "No changes detected"
          else
            git commit -m "Auto: Update rules from submodule"
            git push
          fi
```

### 场景 2：监听 ios_rule_script 仓库的更新

使用 GitHub Actions 的 repository_dispatch 或定时检查：

```yaml
name: Check ios_rule_script Updates

on:
  schedule:
    - cron: '0 */6 * * *'  # 每 6 小时检查一次
  workflow_dispatch:

jobs:
  check-and-update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          submodules: 'recursive'

      - name: Check for updates
        run: |
          git fetch origin
          git submodule update --remote --depth 1
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Generate rules
        run: python convert.py

      - name: Create Pull Request
        uses: peter-evans/create-pull-request@v5
        with:
          commit-message: 'chore: Auto update rules'
          title: 'chore: Auto update rules from ios_rule_script'
          body: 'This PR updates the rules based on the latest ios_rule_script changes.'
          branch: auto/update-rules
```

## convert.py 功能说明

改进后的 `convert.py` 支持：

1. **本地文件读取**
   ```python
   # 支持的路径格式
   ./ios_rules/rule/Clash/Netflix/Netflix_Classical.yaml
   ../ios_rule_script/rule/Clash/Spotify/Spotify.yaml
   /absolute/path/to/rule.yaml
   ```

2. **远程 URL 下载**
   ```python
   https://raw.githubusercontent.com/maxbule/ios_rule_script/master/rule/Clash/...
   ```

3. **错误处理**
   - 自动跳过不存在的文件
   - 详细的错误日志
   - 规则计数统计

4. **输出格式**
   ```
   Processing Netflix_Classical... ✓ (158 rules, local)
   Processing Spotify... ✓ (241 rules, remote)
   ✓ Successfully processed 52/52 sources
   ```

## 推荐配置

### 最佳实践：使用子模块 + GitHub Actions

1. **初始化**
   ```bash
   git submodule add https://github.com/maxbule/ios_rule_script.git ios_rules
   ```

2. **修改 sources.txt**
   - 将所有链接改为 `./ios_rules/rule/Clash/...` 格式

3. **部署 GitHub Actions**
   - 使用上面的定时更新工作流
   - 设置合适的运行频率（如每天或每 6 小时）

4. **本地测试**
   ```bash
   git submodule update --remote
   python convert.py
   ```

## 故障排查

### 问题 1：找不到本地文件
```
✗ Local file not found: ./ios_rules/rule/Clash/Netflix/Netflix_Classical.yaml
```

**解决方案**：
- 检查路径是否正确
- 运行 `git submodule update --init --recursive`
- 验证文件确实存在

### 问题 2：子模块未更新
```bash
# 强制更新到最新版本
git submodule update --remote --merge

# 初始化未初始化的子模块
git submodule update --init --recursive
```

### 问题 3：权限问题
如果使用 HTTPS URL，GitHub Actions 可能需要 token。在仓库设置中配置：
- Settings → Secrets → 添加 `GH_TOKEN`

## 总结

| 方案 | 优点 | 缺点 |
|------|------|------|
| 远程链接 | 简单，无需配置 | 依赖网络，更新延迟 |
| 本地子模块 | 完全自动化，版本控制 | 需要初始配置 |
| 本地克隆 | 灵活 | 需要手动管理 |

**推荐使用子模块方案** - 结合 GitHub Actions，可以实现完全自动化的规则更新流程。
