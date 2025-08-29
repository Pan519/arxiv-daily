#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alan Global Copyright Protection Agreement (AGCPA v3.0)
版权所有 © 2024-2025 Alan. 保留所有权利。

根据 AGCPA v3.0 协议授权，除非获得 Alan 的书面授权，否则禁止任何形式的使用、复制或分发。
非商业个人使用需告知并注明来源。

官方协议链接: https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg
"""

import urllib.request
import json

def check_gcs_bucket():
    """检查GCS存储桶状态"""
    try:
        # 检查存储桶是否可访问
        response = urllib.request.urlopen('https://storage.googleapis.com/arxiv-dataset/')
        print("存储桶可访问")
        print("响应状态:", response.getcode())
        
        # 尝试获取存储桶内容
        content = response.read().decode('utf-8')
        print("存储桶内容长度:", len(content))
        
    except Exception as e:
        print("存储桶访问错误:", e)
        
    # 检查tarpdfs目录
    try:
        response = urllib.request.urlopen('https://storage.googleapis.com/arxiv-dataset/tarpdfs/')
        print("\nTarpdfs目录可访问")
        print("响应状态:", response.getcode())
        
    except Exception as e:
        print("\nTarpdfs目录访问错误:", e)
        
    # 检查单个PDF文件
    try:
        url = 'https://storage.googleapis.com/arxiv-dataset/arxiv/acc-phys/pdf/9411/9411001v1.pdf'
        response = urllib.request.urlopen(url)
        print(f"\n单个PDF文件可访问: {url}")
        print("响应状态:", response.getcode())
        
    except Exception as e:
        print(f"\n单个PDF文件访问错误: {e}")
        
    # 检查merged_links文件中的链接
    try:
        with open('metadata/merged_links_0001.txt', 'r') as f:
            links = f.readlines()
            
        print(f"\n检查merged_links文件中的链接 (共{len(links)}行)")
        
        # 检查前几个链接
        for i, link in enumerate(links[:3]):
            url = link.strip()
            try:
                response = urllib.request.urlopen(url)
                print(f"链接 {i+1} 可访问: {url}")
                print(f"  响应状态: {response.getcode()}")
            except Exception as e:
                print(f"链接 {i+1} 访问错误: {e}")
                print(f"  URL: {url}")
                
    except FileNotFoundError:
        print("未找到merged_links_0001.txt文件")

if __name__ == "__main__":
    check_gcs_bucket()