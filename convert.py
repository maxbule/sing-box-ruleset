#!/usr/bin/env python3
"""
Clash 规则转换脚本
将 Clash 规则转换为 sing-box 格式
"""

import yaml
import json
import os
import requests

FIELD_MAP = {
    'DOMAIN': 'domain', 'DOMAIN-SUFFIX': 'domain_suffix',
    'DOMAIN-KEYWORD': 'domain_keyword', 'IP-CIDR': 'ip_cidr',
    'IP-CIDR6': 'ip_cidr', 'GEOIP': 'geoip'
}

def download_and_convert():
    if not os.path.exists('json_rules'): os.makedirs('json_rules')
    
    with open('sources.txt', 'r') as f:
        links = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    for link in links:
        name = link.split('/')[-1].replace('.yaml', '').replace('.yml', '')
        print(f"Processing {name}...")
        try:
            resp = requests.get(link, timeout=10)
            data = yaml.safe_load(resp.text)
            
            # 兼容 Clash Provider 的 payload 格式
            clash_rules = data.get('payload', []) if isinstance(data, dict) else data
            
            sb_json = {"version": 1, "rules": []}
            temp_rules = {}

            for line in clash_rules:
                parts = line.split(',')
                if len(parts) < 2: continue
                sb_type = FIELD_MAP.get(parts[0].strip().upper())
                if sb_type:
                    temp_rules.setdefault(sb_type, []).append(parts[1].strip())

            for k, v in temp_rules.items():
                sb_json["rules"].append({k: list(set(v))}) # 去重

            with open(f'json_rules/{name}.json', 'w') as out_f:
                json.dump(sb_json, out_f, indent=2)
        except Exception as e:
            print(f"Error processing {link}: {e}")

if __name__ == "__main__":
    download_and_convert()