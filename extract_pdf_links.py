#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Alan Global Copyright Protection Agreement (AGCPA v3.0)
版权所有 © 2024-2025 Alan. 保留所有权利。

根据 AGCPA v3.0 协议授权，除非获得 Alan 的书面授权，否则禁止任何形式的使用、复制或分发。
非商业个人使用需告知并注明来源。

官方协议链接: https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg
"""

# @Time    : 2025/8/28
# @Author  : 
# @Version : v1.0
# @Function: 提取arxiv-metadata-oai-snapshot文件中的PDF下载链接
# @Usage   : python extract_pdf_links.py [--file FILE] [--output OUTPUT]

import os
import re
import json
import logging
import argparse
from typing import List, Dict

# 设置日志级别和格式
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S'
)

def extract_pdf_links_from_file(file_path: str, output_path: str = None) -> List[str]:
    """
    从指定的元数据文件中提取PDF下载链接
    
    Args:
        file_path: 元数据文件路径
        output_path: 输出文件路径（可选）
        
    Returns:
        List of PDF links
    """
    pdf_links = []
    
    logging.info(f"开始从文件 {file_path} 提取PDF链接")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            line_count = 0
            for line in f:
                line_count += 1
                if line.strip():
                    try:
                        data = json.loads(line)
                        # 从id字段构造PDF链接
                        if 'id' in data:
                            paper_id = data['id']
                            # 构造PDF链接: https://arxiv.org/pdf/{paper_id}.pdf
                            pdf_link = f"https://arxiv.org/pdf/{paper_id}.pdf"
                            pdf_links.append(pdf_link)
                            
                            # 记录前几个链接用于调试
                            if len(pdf_links) <= 5:
                                logging.debug(f"提取到链接: {pdf_link}")
                                
                    except json.JSONDecodeError as e:
                        logging.warning(f"第{line_count}行JSON解析错误: {e}")
                        continue
        
        logging.info(f"从文件 {file_path} 中提取到 {len(pdf_links)} 个PDF链接")
        
        # 如果指定了输出路径，则将链接写入文件
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                for link in pdf_links:
                    f.write(link + '\n')
            logging.info(f"PDF链接已保存到: {output_path}")
        
        return pdf_links
        
    except Exception as e:
        logging.error(f"读取文件 {file_path} 时出错: {e}", exc_info=True)
        raise

def find_metadata_files(metadata_dir: str = './metadata') -> List[str]:
    """
    查找metadata目录下的所有arxiv-metadata-oai-snapshot文件
    
    Args:
        metadata_dir: 元数据目录路径
        
    Returns:
        List of file paths
    """
    files = []
    
    if not os.path.exists(metadata_dir):
        logging.warning(f"元数据目录 {metadata_dir} 不存在")
        return files
    
    # 使用正则表达式匹配文件名
    pattern = r'arxiv-metadata-oai-snapshot(-\d{6})?\.json$'
    
    for filename in os.listdir(metadata_dir):
        if re.search(pattern, filename):
            file_path = os.path.join(metadata_dir, filename)
            files.append(file_path)
            logging.debug(f"发现元数据文件: {file_path}")
    
    logging.info(f"找到 {len(files)} 个元数据文件")
    return files

def main():
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='提取arxiv-metadata-oai-snapshot文件中的PDF下载链接')
    parser.add_argument('--file', type=str, help='指定要处理的元数据文件路径')
    parser.add_argument('--output', type=str, help='输出文件路径')
    parser.add_argument('--metadata_dir', type=str, default='./metadata', help='元数据目录路径')
    
    args = parser.parse_args()
    
    # 如果指定了特定文件，则只处理该文件
    if args.file:
        if os.path.exists(args.file):
            extract_pdf_links_from_file(args.file, args.output)
        else:
            logging.error(f"指定的文件 {args.file} 不存在")
            return
    else:
        # 查找并处理所有元数据文件
        files = find_metadata_files(args.metadata_dir)
        if not files:
            logging.warning("未找到任何元数据文件")
            return
        
        all_links = []
        for file_path in files:
            links = extract_pdf_links_from_file(file_path)
            all_links.extend(links)
        
        # 去重
        unique_links = list(set(all_links))
        logging.info(f"总共提取到 {len(unique_links)} 个唯一的PDF链接")
        
        # 如果指定了输出路径，则将所有链接写入文件
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                for link in sorted(unique_links):  # 排序以便于查看
                    f.write(link + '\n')
            logging.info(f"所有PDF链接已保存到: {args.output}")

if __name__ == "__main__":
    main()