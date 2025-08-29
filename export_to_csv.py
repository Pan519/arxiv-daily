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
import csv
import os
import logging
from typing import List, Dict, Any

# 配置日志
logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.INFO
)

def json_to_csv(input_file: str, output_dir: str, records_per_file: int = 500):
    """
    将JSON元数据文件转换为CSV格式，每个文件包含指定数量的记录
    
    Args:
        input_file: 输入的JSON文件路径
        output_dir: 输出CSV文件的目录
        records_per_file: 每个CSV文件包含的记录数，默认为500
    """
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 定义CSV字段，确保字段顺序一致
    csv_fields = [
        'id', 'authors', 'title', 'comments', 'journal-ref', 'doi',
        'categories', 'abstract', 'update_date', 'authors_parsed',
        'primary_category', 'publish_time', 'entry_id'
        # 注意：links字段可能包含多个URL，处理时需要特殊处理
    ]
    
    file_counter = 0
    record_counter = 0
    csv_file = None
    csv_writer = None
    
    logging.info(f"开始处理文件: {input_file}")
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                    
                try:
                    # 解析JSON行
                    data = json.loads(line)
                    
                    # 每达到指定记录数就创建新文件
                    if record_counter % records_per_file == 0:
                        if csv_file:
                            csv_file.close()
                        
                        file_counter += 1
                        output_file = os.path.join(output_dir, f'arxiv-metadata-{file_counter:03d}.csv')
                        csv_file = open(output_file, 'w', newline='', encoding='utf-8')
                        csv_writer = csv.DictWriter(csv_file, fieldnames=csv_fields)
                        csv_writer.writeheader()
                        logging.info(f"创建新文件: {output_file}")
                    
                    # 处理特殊字段
                    processed_data = {}
                    for field in csv_fields:
                        if field in data:
                            value = data[field]
                            # 处理列表类型字段
                            if isinstance(value, list):
                                if field == 'categories':
                                    # 类别列表用分号分隔
                                    processed_data[field] = ';'.join(value)
                                elif field == 'authors_parsed':
                                    # 作者解析列表用特殊格式
                                    authors_str = '|'.join([f"{author[0]},{author[1]},{author[2]}" for author in value])
                                    processed_data[field] = authors_str
                                else:
                                    processed_data[field] = str(value)
                            # 处理None值
                            elif value is None:
                                processed_data[field] = ''
                            else:
                                processed_data[field] = str(value)
                        else:
                            processed_data[field] = ''
                    
                    # 写入CSV
                    csv_writer.writerow(processed_data)
                    record_counter += 1
                    
                    if record_counter % 1000 == 0:
                        logging.info(f"已处理 {record_counter} 条记录")
                        
                except json.JSONDecodeError as e:
                    logging.warning(f"第{line_num}行JSON解析错误: {e}")
                    continue
                except Exception as e:
                    logging.error(f"处理第{line_num}行时出错: {e}")
                    continue
        
        # 关闭最后的文件
        if csv_file:
            csv_file.close()
            
        logging.info(f"处理完成，总共转换了 {record_counter} 条记录到 {file_counter} 个CSV文件中")
        
    except Exception as e:
        logging.error(f"处理文件时出错: {e}")
        raise

def main():
    """
    主函数
    """
    # 输入文件路径
    input_file = './metadata/arxiv-metadata-oai-snapshot-202508.json'
    
    # 输出目录
    output_dir = './metadata/csv'
    
    # 每个CSV文件的记录数
    records_per_file = 500
    
    # 检查输入文件是否存在
    if not os.path.exists(input_file):
        logging.error(f"输入文件不存在: {input_file}")
        return
    
    logging.info("开始将JSON元数据转换为CSV格式...")
    json_to_csv(input_file, output_dir, records_per_file)
    logging.info("转换完成!")

if __name__ == "__main__":
    main()
    