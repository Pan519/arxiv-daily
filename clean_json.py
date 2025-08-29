#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alan Global Copyright Protection Agreement (AGCPA v3.0)
版权所有 © 2024-2025 Alan. 保留所有权利。

根据 AGCPA v3.0 协议授权，除非获得 Alan 的书面授权，否则禁止任何形式的使用、复制或分发。
非商业个人使用需告知并注明来源。

官方协议链接: https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg
"""

import json
import os
from collections import OrderedDict

def clean_and_deduplicate_json():
    """
    清理和去重arxiv-metadata-oai-snapshot-202508.json文件
    """
    input_file = './metadata/arxiv-metadata-oai-snapshot-202508.json'
    backup_file = './metadata/arxiv-metadata-oai-snapshot-202508.json.bak'
    temp_file = './metadata/arxiv-metadata-oai-snapshot-202508.json.tmp'
    
    # 检查文件是否存在
    if not os.path.exists(input_file):
        print(f"文件 {input_file} 不存在")
        return
    
    # 创建备份
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(backup_file, 'w', encoding='utf-8') as f_out:
        f_out.write(f_in.read())
    
    print(f"已创建备份文件: {backup_file}")
    
    # 用于存储唯一记录的字典，以论文ID为键
    unique_records = OrderedDict()
    line_count = 0
    error_count = 0
    duplicate_count = 0
    
    # 读取并处理文件
    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:  # 跳过空行
                continue
                
            try:
                # 解析JSON行
                record = json.loads(line)
                line_count += 1
                
                # 获取论文ID
                paper_id = record.get('id')
                if not paper_id:
                    print(f"警告: 第{line_num}行缺少ID字段")
                    error_count += 1
                    continue
                
                # 检查是否已存在
                if paper_id in unique_records:
                    duplicate_count += 1
                    print(f"发现重复记录: {paper_id} (第{line_num}行)")
                else:
                    # 存储记录
                    unique_records[paper_id] = record
                    
            except json.JSONDecodeError as e:
                print(f"错误: 第{line_num}行JSON解析失败: {e}")
                error_count += 1
                continue
    
    # 写入清理后的数据到临时文件
    with open(temp_file, 'w', encoding='utf-8') as f:
        for record in unique_records.values():
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # 替换原文件
    os.replace(temp_file, input_file)
    
    print(f"处理完成:")
    print(f"  总行数: {line_count}")
    print(f"  唯一记录数: {len(unique_records)}")
    print(f"  重复记录数: {duplicate_count}")
    print(f"  错误行数: {error_count}")
    print(f"  文件已更新: {input_file}")

if __name__ == "__main__":
    clean_and_deduplicate_json()