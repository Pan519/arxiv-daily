#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alan Global Copyright Protection Agreement (AGCPA v3.0)
版权所有 © 2024-2025 Alan. 保留所有权利。

根据 AGCPA v3.0 协议授权，除非获得 Alan 的书面授权，否则禁止任何形式的使用、复制或分发。
非商业个人使用需告知并注明来源。

官方协议链接: https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg
"""

"""
arXiv PDF链接到GCS路径转换器

这个脚本可以将arXiv的PDF链接转换为Google Cloud Storage (GCS)路径格式。
注意：
1. 生成的GCS链接格式是正确的，但并非所有文件都实际存在于GCS存储桶中
2. 根据研究，arXiv数据集在GCS上主要以tar.gz文件形式存储，而不是直接的PDF文件
3. 早期论文(如1994年)更有可能存在，而较新论文可能不存在
4. 如果需要访问PDF文件，建议直接从arxiv.org下载
"""

import re
import json
import os
import argparse
import sys
import urllib.request
import urllib.error
from urllib.request import urlopen
from urllib.error import HTTPError
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# 创建一个锁用于线程安全的日志写入
log_lock = threading.Lock()


def extract_paper_id(pdf_url):
    """
    从PDF链接中提取论文ID和版本
    
    Args:
        pdf_url (str): PDF链接
        
    Returns:
        tuple: (论文ID, 版本)
    """
    # 匹配 https://arxiv.org/pdf/2406.18629.pdf 格式的URL
    # 也匹配 https://arxiv.org/pdf/2406.18629v1.pdf 格式的URL
    # 还匹配 https://arxiv.org/pdf/9507001v2.pdf 格式的URL
    # 以及 https://arxiv.org/pdf/acc-phys/9507001v2.pdf 格式的URL
    # 以及 https://arxiv.org/pdf/2508.16526v1.pdf 格式的URL
    
    # 首先尝试匹配带点的格式 (如 2406.18629 或 2508.16526)
    match = re.search(r'/pdf/([0-9]+\.[0-9]+)(v[0-9]+)?\.pdf$', pdf_url)
    if match:
        paper_id = match.group(1)
        version = match.group(2) if match.group(2) else None
        return paper_id, version
    
    # 然后尝试匹配不带点的格式 (如 9507001)
    match = re.search(r'/pdf/([0-9]+)(v[0-9]+)?\.pdf$', pdf_url)
    if match:
        paper_id = match.group(1)
        # 对于不带点的格式，需要按年月+编号格式化
        # 前4位是年月，后面是编号
        version = match.group(2) if match.group(2) else None
        return paper_id, version
    
    # 处理带分类的格式 (如 acc-phys/9507001)
    match = re.search(r'/pdf/[^/]+/([0-9]+)(v[0-9]+)?\.pdf$', pdf_url)
    if match:
        paper_id = match.group(1)
        version = match.group(2) if match.group(2) else None
        return paper_id, version
    
    # 最后尝试匹配没有.pdf结尾但有版本号的格式
    match = re.search(r'/pdf/([0-9]+\.[0-9]+(?:v[0-9]+)?)$', pdf_url)
    if match:
        paper_id_with_version = match.group(1)
        if 'v' in paper_id_with_version:
            paper_id, version = paper_id_with_version.split('v', 1)
            version = f'v{version}'
        else:
            paper_id = paper_id_with_version
            version = None
        return paper_id, version
        
    raise ValueError("无效的arXiv PDF链接")


def get_category(paper_id, pdf_url=None):
    """
    获取论文分类信息，优先使用本地元数据文件
    
    Args:
        paper_id (str): 论文ID
        pdf_url (str): 原始PDF链接，用于提取分类信息
        
    Returns:
        str: 论文分类
    """
    # 首先尝试从本地元数据文件获取分类
    metadata_files = [
        os.path.join('metadata', 'arxiv-metadata-oai-snapshot-202508.json'),
        os.path.join('metadata', 'arxiv-metadata-oai-snapshot.json')
    ]
    
    for metadata_file in metadata_files:
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if paper_id in line:
                        data = json.loads(line)
                        # 返回第一个分类
                        return data['categories'].split()[0]
        except FileNotFoundError:
            continue
        except Exception:
            continue
    
    # 如果本地没有，则尝试从URL中提取分类
    if pdf_url:
        # 匹配类似 https://arxiv.org/pdf/acc-phys/9507001v2.pdf 的URL
        match = re.search(r'/pdf/([^/]+)/[0-9]+', pdf_url)
        if match and match.group(1) != paper_id:
            # 检查是否是有效的分类名（不包含点号）
            category = match.group(1)
            if '.' not in category:
                return category
    
    # 如果还获取不到，则尝试从arXiv API获取
    try:
        url = f"http://export.arxiv.org/api/query?id_list={paper_id}"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'arxiv-converter/1.0 (mailto:user@example.com)')
        response = urlopen(req, timeout=5)  # 减少超时设置到5秒
        content = response.read().decode('utf-8')
        
        # 简单解析XML，提取categories字段
        # 注意：实际项目中应使用XML解析器
        category_start = content.find('<category term="') + len('<category term="')
        if category_start >= len('<category term="'):
            category_end = content.find('"', category_start)
            return content[category_start:category_end]
    except Exception as e:
        log_message(f"警告: 无法从arXiv API获取分类信息 {paper_id}: {e}")
        pass
    
    # 默认返回一个常见分类
    return "cs.LG"  # 默认返回计算机科学-学习分类


def parse_year_month(paper_id):
    """
    从论文ID解析年份和月份
    
    Args:
        paper_id (str): 论文ID
        
    Returns:
        str: 年月字符串
    """
    # 处理带点的格式 (如 2406.18629 或 2508.16526)
    if '.' in paper_id:
        year_month = paper_id.split('.')[0][:4]
    # 处理不带点的格式 (如 9507001)
    else:
        year_month = paper_id[:4]
    
    # 确保年月是有效的数字格式
    if len(year_month) == 4 and year_month.isdigit():
        return year_month
    else:
        # 如果无法解析，返回默认值
        return "0000"


def get_gcs_path_prefix(paper_id):
    """
    根据论文ID确定GCS路径前缀
    
    Args:
        paper_id (str): 论文ID
        
    Returns:
        str: GCS路径前缀
    """
    # 根据实际测试和研究，路径结构主要基于年份：
    # - 2007年3月及之前: 使用分类目录（如cs.LG）
    # - 2007年4月及之后: 使用arxiv/arxiv/pdf目录
    year_month = parse_year_month(paper_id)
    try:
        year = int(year_month[:2])
        month = int(year_month[2:4])
        
        # 2007年之前的论文使用分类目录
        if year < 7:
            return None
        # 2025年及之后的论文使用arxiv目录
        elif year >= 25:
            return "arxiv"
        # 2007年4月及之后到2024年的论文使用分类目录
        else:
            return None
    except ValueError:
        # 默认使用分类目录
        return None


def convert_to_gcs_url(pdf_url):
    """
    将arXiv PDF链接转换为GCS路径
    
    Args:
        pdf_url (str): arXiv PDF链接
        
    Returns:
        str: GCS路径
    """
    # 提取论文ID和版本
    paper_id, version = extract_paper_id(pdf_url)
    
    # 解析年月
    year_month = parse_year_month(paper_id)
    
    # 如果没有版本号，需要从arXiv获取最新版本
    if not version:
        # 简化处理，默认使用v1，实际应用中应该查询最新版本
        version = "v1"
    
    # 获取分类信息（优先使用本地数据）
    category = get_category(paper_id, pdf_url)
    
    # 根据年月确定路径结构
    try:
        year = int(year_month[:2])  # 前两位表示年份（例如07表示2007年）
        month = int(year_month[2:4])  # 后两位表示月份
        
        # 2007年4月(0704)及之后使用arxiv/arxiv/pdf结构
        if year > 7 or (year == 7 and month >= 4):  
            gcs_url = f"https://storage.googleapis.com/arxiv-dataset/arxiv/arxiv/pdf/{year_month}/{paper_id}{version}.pdf"
        else:
            # 更早的论文使用分类目录
            gcs_url = f"https://storage.googleapis.com/arxiv-dataset/arxiv/{category}/pdf/{year_month}/{paper_id}{version}.pdf"
    except ValueError:
        # 如果解析年份失败，使用默认的分类路径结构
        gcs_url = f"https://storage.googleapis.com/arxiv-dataset/arxiv/{category}/pdf/{year_month}/{paper_id}{version}.pdf"
    
    # 确保所有字符都是小写
    gcs_url = gcs_url.lower()
    
    # 确保使用半角字符和正确的横杠
    gcs_url = gcs_url.replace('－', '-')  # 全角横杠替换为半角横杠
    gcs_url = gcs_url.replace('．', '.')  # 全角点替换为半角点
    
    # 清理可能的多余字符
    gcs_url = gcs_url.strip()
    
    return gcs_url


def log_message(message):
    """
    线程安全地写入日志信息
    
    Args:
        message (str): 日志信息
    """
    with log_lock:
        # 使用UTF-8-BOM编码写入日志文件，更好地支持中文
        try:
            # 使用a+模式确保文件存在，UTF-8-BOM with no BOM on append
            with open("conversion.log", "a+", encoding="utf-8-sig") as log_file:
                log_file.write(message + "\n")
        except Exception as e:
            # 如果UTF-8失败，尝试使用GBK
            try:
                with open("conversion.log", "a+", encoding="gbk") as log_file:
                    log_file.write(message + "\n")
            except Exception as e:
                # 最后尝试使用UTF-8无BOM
                with open("conversion.log", "a+", encoding="utf-8") as log_file:
                    log_file.write(message + "\n")


def process_url(url):
    """
    处理单个URL的转换
    
    Args:
        url (str): arXiv PDF链接
        
    Returns:
        tuple: (原始链接, GCS链接, 是否成功, 错误信息)
    """
    try:
        gcs_url = convert_to_gcs_url(url)
        # 减少日志写入频率，只记录转换结果而不每次都写入日志
        return (url, gcs_url, True, None)
    except Exception as e:
        error_msg = f"转换失败: {url} - {str(e)}"
        # 减少日志写入频率
        return (url, None, False, str(e))


def batch_convert(urls, max_workers=None):  # 默认不指定线程数
    """
    批量转换arXiv链接（多线程）
    
    Args:
        urls (list): arXiv PDF链接列表
        max_workers (int): 最大线程数（如果为None则自动调整）
        
    Returns:
        list: 转换结果列表
    """
    results = []
    total = len(urls)
    
    # 自动调整线程数（默认为URL数量的一半，但不超过20）
    if max_workers is None:
        max_workers = min(20, max(1, total // 2))
    
    log_message(f"总共需要处理 {total} 个链接，使用 {max_workers} 个线程")
    
    # 如果链接数量很少，直接顺序处理，避免线程开销
    if total <= 5:
        for i, url in enumerate(urls):
            result = process_url(url)
            results.append(result)
            if i % 10 == 0 or i == total - 1:
                log_message(f"进度: {i+1}/{total}")
        log_message(f"处理完成，共 {len(results)} 个链接")
        return results
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # 提交所有任务
        future_to_url = {executor.submit(process_url, url): url for url in urls}
        
        # 收集结果
        completed = 0
        for future in as_completed(future_to_url):
            try:
                result = future.result()
                results.append(result)
                completed += 1
                if completed % 10 == 0 or completed == total:
                    log_message(f"进度: {completed}/{total}")
            except Exception as e:
                url = future_to_url[future]
                error_msg = f"处理异常: {url} - {str(e)}"
                log_message(error_msg)
                results.append((url, None, False, str(e)))
    
    log_message(f"处理完成，共 {len(results)} 个链接")
    return results


def main():
    """
    主函数 - 命令行接口
    """
    parser = argparse.ArgumentParser(description='将arXiv PDF链接转换为GCS路径')
    parser.add_argument('urls', metavar='URL', type=str, nargs='*',
                        help='arXiv PDF链接')
    parser.add_argument('--file', '-f', type=str, 
                        help='包含arXiv链接的文件路径，每行一个链接')
    parser.add_argument('--output', '-o', type=str,
                        help='输出文件路径，将转换结果保存到文件')
    
    args = parser.parse_args()
    
    urls = []
    
    # 从命令行参数获取URL
    if args.urls:
        urls.extend(args.urls)
    
    # 从文件获取URL
    if args.file:
        try:
            # 尝试多种编码方式读取文件
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            file_urls = []
            
            for encoding in encodings:
                try:
                    with open(args.file, 'r', encoding=encoding) as f:
                        file_urls = [line.strip() for line in f if line.strip()]
                    log_message(f"使用 {encoding} 编码成功读取文件 {args.file}，共 {len(file_urls)} 个链接")
                    break
                except UnicodeDecodeError:
                    continue
            
            if not file_urls:
                raise Exception("无法使用常见编码读取文件")
                
            urls.extend(file_urls)
        except Exception as e:
            print(f"读取文件失败: {e}", file=sys.stderr)
            sys.exit(1)
    
    if not urls:
        # 如果没有提供URL，显示帮助信息和示例
        print("Arxiv PDF到GCS路径转换器", file=sys.stderr)
        print("=" * 50, file=sys.stderr)
        print("使用方法:", file=sys.stderr)
        print("  python arxiv_converter.py [URLs...]", file=sys.stderr)
        print("  python arxiv_converter.py --file links.txt", file=sys.stderr)
        print("  python arxiv_converter.py --file links.txt --output gcs_links.txt", file=sys.stderr)
        print("", file=sys.stderr)
        print("示例:", file=sys.stderr)
        print("  python arxiv_converter.py https://arxiv.org/pdf/2406.18629.pdf", file=sys.stderr)
        print("", file=sys.stderr)
        return
    
    log_message(f"总共需要处理 {len(urls)} 个链接")
    
    # 执行转换
    results = batch_convert(urls, max_workers=min(10, max(1, len(urls) // 2)))  # 动态调整线程数
    
    # 收集成功转换的链接
    gcs_urls = []
    success_count = 0
    for _, gcs_url, success, error in results:
        if success and gcs_url:
            gcs_urls.append(gcs_url)
            success_count += 1
        elif error:
            log_message(f"转换失败: {error}")
    
    # 输出结果
    if args.output:
        # 输出到文件
        try:
            with open(args.output, 'w', encoding='utf-8') as f:
                for gcs_url in gcs_urls:
                    f.write(gcs_url + '\n')
            log_message(f"转换结果已保存到文件: {args.output}")
        except Exception as e:
            print(f"保存文件失败: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # 输出到标准输出
        for gcs_url in gcs_urls:
            print(gcs_url)
    
    # 输出统计信息到日志
    log_message(f"转换完成: 成功 {success_count} 个，失败 {len(results) - success_count} 个")


if __name__ == "__main__":
    main()
    