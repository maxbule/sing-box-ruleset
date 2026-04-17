#!/bin/bash
# 快速设置脚本 - 配置本地 ios_rule_script 规则源

set -e

echo "=== Sing-box Ruleset Local Configuration ==="
echo ""
echo "This script helps you set up ios_rule_script as a Git submodule"
echo ""

# 检查是否已有子模块
if [ -d "ios_rules" ]; then
    echo "✓ ios_rules directory already exists"
    read -p "Do you want to update it? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cd ios_rules
        git pull origin master
        cd ..
        echo "✓ Updated ios_rules submodule"
    fi
else
    echo "Adding ios_rule_script as submodule..."
    git submodule add https://github.com/maxbule/ios_rule_script.git ios_rules
    git commit -m "Add ios_rule_script as submodule"
    echo "✓ Added ios_rules submodule"
fi

echo ""
echo "Generating rules list from ios_rule_script..."

# 生成 sources.txt 中的本地路径
echo "# Automatically generated from ios_rule_script" > sources-local.txt
echo "# Generated at: $(date)" >> sources-local.txt
echo "" >> sources-local.txt

# 查找所有 YAML 文件并生成本地路径
for file in ios_rules/rule/Clash/**/*.yaml; do
    if [ -f "$file" ]; then
        echo "./$file" >> sources-local.txt
    fi
done

RULE_COUNT=$(grep "^\./" sources-local.txt | wc -l)
echo "✓ Generated sources-local.txt with $RULE_COUNT rules"

echo ""
echo "Next steps:"
echo "1. Review sources-local.txt"
echo "2. To use local rules: cp sources-local.txt sources.txt"
echo "3. Run: python convert.py"
echo "4. To auto-update in future: git submodule update --remote && python convert.py"
