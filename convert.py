#!/usr/bin/env python3
"""
Clash 规则转换脚本
将 Clash 规则转换为 sing-box 格式
支持本地文件路径和远程链接
"""

import yaml
import json
import os
import requests
from pathlib import Path

FIELD_MAP = {
    'DOMAIN': 'domain', 'DOMAIN-SUFFIX': 'domain_suffix',
    'DOMAIN-KEYWORD': 'domain_keyword', 'IP-CIDR': 'ip_cidr',
    'IP-CIDR6': 'ip_cidr', 'GEOIP': 'geoip'
}

def load_rule_content(source):
    """
    加载规则内容，支持本地文件路径和远程 URL
    
    Args:
        source: 本地路径 (./path/to/file.yaml) 或远程 URL (https://...)
    
    Returns:
        (content: str, source_type: str) 或 (None, None)
    """
    # 检查是否为本地路径
    if source.startswith('./') or source.startswith('../') or not source.startswith('http'):
        local_path = Path(source)
        if local_path.exists():
            try:
                with open(local_path, 'r', encoding='utf-8') as f:
                    return f.read(), 'local'
            except Exception as e:
                print(f"  ✗ Error reading local file {source}: {e}")
                return None, None
        else:
            print(f"  ✗ Local file not found: {source}")
            return None, None
    
    # 处理远程 URL
    try:
        resp = requests.get(source, timeout=10)
        resp.raise_for_status()
        return resp.text, 'remote'
    except Exception as e:
        print(f"  ✗ Error fetching {source}: {e}")
        return None, None


def convert_rules(content, name):
    """
    将 Clash 规则内容转换为 sing-box JSON 格式
    
    Args:
        content: YAML 规则内容
        name: 规则名称
    
    Returns:
        dict 或 None
    """
    try:
        data = yaml.safe_load(content)
        
        # 兼容 Clash Provider 的 payload 格式
        clash_rules = data.get('payload', []) if isinstance(data, dict) else data
        
        if not clash_rules:
            print(f"  ⚠ No rules found in {name}")
            return None
        
        sb_json = {"version": 1, "rules": []}
        temp_rules = {}

        for line in clash_rules:
            parts = line.split(',')
            if len(parts) < 2: 
                continue
            sb_type = FIELD_MAP.get(parts[0].strip().upper())
            if sb_type:
                temp_rules.setdefault(sb_type, []).append(parts[1].strip())

        for k, v in temp_rules.items():
            sb_json["rules"].append({k: list(set(v))})  # 去重

        return sb_json
    except Exception as e:
        print(f"  ✗ Error parsing {name}: {e}")
        return None


def download_and_convert():
    """主转换函数"""
    if not os.path.exists('json_rules'): 
        os.makedirs('json_rules')
    
    with open('sources.txt', 'r', encoding='utf-8') as f:
        sources = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    if not sources:
        print("No sources found in sources.txt")
        return

    success_count = 0
    for source in sources:
        # 提取名称
        name = source.split('/')[-1].replace('.yaml', '').replace('.yml', '')
        print(f"Processing {name}...", end=' ')
        
        # 加载规则内容
        content, source_type = load_rule_content(source)
        if not content:
            print()
            continue
        
        # 转换规则
        sb_json = convert_rules(content, name)
        if not sb_json:
            print()
            continue
        
        # 保存为 JSON
        try:
            output_path = f'json_rules/{name}.json'
            with open(output_path, 'w', encoding='utf-8') as out_f:
                json.dump(sb_json, out_f, indent=2, ensure_ascii=False)
            
            rule_count = sum(len(v) for rule in sb_json['rules'] for v in rule.values())
            print(f"✓ ({rule_count} rules, {source_type})")
            success_count += 1
        except Exception as e:
            print(f"✗ Error saving {name}: {e}")
    
    print(f"\n✓ Successfully processed {success_count}/{len(sources)} sources")

if __name__ == "__main__":
    download_and_convert()