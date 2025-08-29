#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Alan Global Copyright Protection Agreement (AGCPA v3.0)
版权所有 © 2024-2025 Alan. 保留所有权利。

根据 AGCPA v3.0 协议授权，除非获得 Alan 的书面授权，否则禁止任何形式的使用、复制或分发。
非商业个人使用需告知并注明来源。

官方协议链接: https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg
"""

import os
import re
import json
import logging
import argparse
import datetime
from typing import List, Dict, Set

# 配置详细的日志
logging.basicConfig(
    format='[%(asctime)s %(levelname)s] %(message)s',
    datefmt='%m/%d/%Y %H:%M:%S',
    level=logging.DEBUG,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('arxiv_query.log', encoding='utf-8')
    ]
)

base_url = "https://arxiv.paperswithcode.com/api/v0/papers/"
arxiv_url = "http://arxiv.org/"

def get_all_categories() -> list:
    '''
    获取arXiv所有有效分类
    '''
    # arXiv的主要分类列表
    main_categories = [
        "astro-ph", "cond-mat", "gr-qc", "hep-ex", "hep-lat", "hep-ph", "hep-th",
        "math-ph", "nlin", "nucl-ex", "nucl-th", "physics", "quant-ph", "math",
        "cs", "q-bio", "q-fin", "stat", "eess", "econ"
    ]
    return main_categories

def get_authors(authors, first_author = False) -> str:
    '''
    authors: list of authors
    return: str
    '''
    if not authors:
        return "None"

    if first_author:
        return authors[0].name

    authors_str = ""
    for author in authors:
        authors_str += author.name + ", "
    authors_str = authors_str[:-2]  # 去掉最后一个", "
    return authors_str

def get_daily_papers(topic, query, max_results=1000, start_date=None, end_date=None):
    '''
    获取每日论文信息，支持按日期范围查询
    '''
    # 初始化
    start = 0
    batch_size = 100
    empty_page_count = 0
    max_empty_pages = 3
    full_content = {}
    
    # 初始化existing_data变量
    existing_data = None
    
    # 新增论文计数器
    new_papers_count = 0
    
    try:
        # 如果提供了日期范围，则修改查询语句
        if start_date and end_date:
            # 将日期格式从 YYYY-MM-DD 转换为 YYYYMMDD
            start_date_fmt = start_date.replace("-", "")
            end_date_fmt = end_date.replace("-", "")
            date_query = f"submittedDate:[{start_date_fmt} TO {end_date_fmt}]"
            
            # 如果原有查询语句不为空，则组合查询
            if query:
                query = f"{query} AND {date_query}"
            else:
                query = date_query
            
            # 在日期查询时，如果max_results为默认值，则设置为None（不限制）
            # 但如果用户明确指定了max_results，则使用用户指定的值
            if max_results == 100:  # 100是默认值
                max_results = None
        
        logging.info(f"开始查询: topic={topic}, query='{query}', max_results={max_results}")
        
        # 创建搜索参数
        search_params = {
            'search_query': query,
            'sortBy': 'submittedDate',
            'sortOrder': 'descending'
        }
        
        # 如果max_results不为None，则添加到参数中
        if max_results is not None:
            search_params['max_results'] = min(max_results, 1000)  # arXiv API限制最大1000
        else:
            search_params['max_results'] = 100  # 默认批次大小
        
        # 加载现有数据用于去重
        existing_data = load_existing_metadata_files()
        initial_existing_count = len(existing_data['arxiv-metadata-oai-snapshot'])
        
        # 分批获取结果以避免空页面问题
        full_content = {}  # 只初始化一次
        start = 0
        batch_size = 100  # 每批获取100个结果
        
        # 如果max_results为None，表示获取所有结果
        target_results = max_results if max_results is not None else float('inf')
        
        empty_page_count = 0  # 连续空页面计数器
        max_empty_pages = 3   # 最大允许连续空页面数
        
        while start < target_results and empty_page_count < max_empty_pages:
            # 设置当前批次的参数
            batch_params = search_params.copy()
            batch_params['start'] = start
            batch_params['max_results'] = min(batch_size, target_results - start) if target_results != float('inf') else batch_size
            
            logging.info(f"请求页面: start={start}, max_results={batch_params['max_results']}")
            
            # 构建URL
            import urllib.parse
            url_params = urllib.parse.urlencode(batch_params)
            url = f"https://export.arxiv.org/api/query?{url_params}"
            logging.debug(f"请求URL: {url}")
            
            # 手动请求API以更好地处理错误
            import urllib.request
            import xml.etree.ElementTree as ET
            import time
            
            # 添加延迟以避免过于频繁的请求
            time.sleep(5)
            
            try:
                # 增加重试机制
                max_retries = 5
                retry_count = 0
                content = None
                
                while retry_count < max_retries:
                    try:
                        response = urllib.request.urlopen(url)
                        content = response.read().decode('utf-8')
                        break  # 成功获取数据，跳出重试循环
                    except urllib.error.HTTPError as e:
                        if e.code == 503:  # 服务不可用
                            retry_count += 1
                            wait_time = 10 * retry_count  # 递增等待时间
                            logging.error(f"HTTP错误: {e.code} - {e.reason}，重试 {retry_count}/{max_retries}，等待 {wait_time} 秒")
                            if retry_count < max_retries:
                                logging.info(f"服务暂时不可用，等待{wait_time}秒后重试")
                                time.sleep(wait_time)
                                continue
                            else:
                                logging.error("达到最大重试次数，放弃请求")
                                raise
                        else:
                            raise  # 其他HTTP错误直接抛出
                    except Exception as e:
                        retry_count += 1
                        if retry_count < max_retries:
                            wait_time = 5 * retry_count
                            logging.error(f"请求失败: {e}，重试 {retry_count}/{max_retries}，等待 {wait_time} 秒")
                            time.sleep(wait_time)
                            continue
                        else:
                            logging.error("达到最大重试次数，放弃请求")
                            raise
                
                # 检查是否成功获取内容
                if content is None:
                    raise Exception("无法获取API响应内容")
                
                # 解析XML响应
                root = ET.fromstring(content)
                
                # 检查是否有错误
                entry_count = 0
                entries = root.findall('{http://www.w3.org/2005/Atom}entry')
                
                # 处理所有entry
                for entry in entries:
                    try:
                        # 检查是否是搜索信息条目（而非论文条目）
                        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                        if title_elem is not None and title_elem.text and 'title' in title_elem.text.lower() and 'result' in title_elem.text.lower():
                            # 这是搜索信息条目，不是论文条目
                            continue
                    
                        entry_count += 1
                        
                        # 提取论文信息
                        entry_id_elem = entry.find('{http://www.w3.org/2005/Atom}id')
                        title_elem = entry.find('{http://www.w3.org/2005/Atom}title')
                        summary_elem = entry.find('{http://www.w3.org/2005/Atom}summary')
                        
                        if entry_id_elem is None or title_elem is None:
                            continue
                            
                        entry_id = entry_id_elem.text
                        title = title_elem.text
                        
                        # 从entry_id提取论文ID（去除版本号）
                        paper_id = entry_id.split('/abs/')[-1] if '/abs/' in entry_id else entry_id
                        ver_pos = paper_id.find('v')
                        if ver_pos != -1:
                            paper_id = paper_id[:ver_pos]
                        
                        # 如果该论文已经存在，跳过
                        if paper_id in full_content:
                            continue
                        
                        # 提取其他信息
                        authors = []
                        author_elems = entry.findall('{http://www.w3.org/2005/Atom}author')
                        for author_elem in author_elems:
                            name_elem = author_elem.find('{http://www.w3.org/2005/Atom}name')
                            if name_elem is not None:
                                authors.append(type('Author', (), {'name': name_elem.text})())
                        
                        published_elem = entry.find('{http://www.w3.org/2005/Atom}published')
                        updated_elem = entry.find('{http://www.w3.org/2005/Atom}updated')
                        
                        categories = []
                        category_elems = entry.findall('{http://www.w3.org/2005/Atom}category')
                        for cat_elem in category_elems:
                            term = cat_elem.get('term')
                            if term:
                                categories.append(term)
                        
                        # 获取主要分类
                        primary_category = categories[0] if categories else None
                        
                        # 获取评论、journal_ref、doi等信息
                        comment = None
                        journal_ref = None
                        doi = None
                        
                        # 从links中查找相关信息
                        links = []
                        link_elems = entry.findall('{http://www.w3.org/2005/Atom}link')
                        for link_elem in link_elems:
                            links.append(link_elem.get('href'))
                        
                        # 保存完整元数据
                        paper_authors = get_authors(authors)
                        paper_first_author = get_authors(authors, first_author=True)
                        
                        abstract = summary_elem.text.replace("\n", " ") if summary_elem is not None else ""
                        
                        publish_time = published_elem.text[:10] if published_elem is not None else ""
                        update_time = updated_elem.text[:10] if updated_elem is not None else ""
                        
                        # 准备作者解析数据
                        authors_parsed = []
                        for author in authors:
                            # 解析作者名字为 [last, first, middle] 格式
                            name_parts = author.name.split()
                            if len(name_parts) >= 2:
                                last = name_parts[-1]
                                first = name_parts[0]
                                middle = ' '.join(name_parts[1:-1]) if len(name_parts) > 2 else ''
                                authors_parsed.append([last, first, middle])
                            else:
                                authors_parsed.append([author.name, '', ''])

                        full_content[paper_id] = {
                            "id": paper_id,
                            "authors": paper_authors,
                            "title": title,
                            "comments": comment,
                            "journal-ref": journal_ref,
                            "doi": doi,
                            "categories": categories,
                            "abstract": abstract,
                            "update_date": update_time,
                            "authors_parsed": authors_parsed,
                            "primary_category": primary_category,
                            "publish_time": publish_time,
                            "entry_id": entry_id,
                            "links": links
                        }
                        
                        logging.debug(f"处理结果 {len(full_content)}: {paper_id}")
                        
                    except Exception as e:
                        logging.error(f"处理论文条目时出错: {e}", exc_info=True)
                        continue
                
                # 更新空页面计数器
                if entry_count == 0:
                    empty_page_count += 1
                    logging.info(f"当前批次未获取到结果，空页面计数: {empty_page_count}")
                    if empty_page_count >= max_empty_pages:
                        logging.warning(f"达到最大连续空页面数({max_empty_pages})，停止获取")
                        break
                else:
                    empty_page_count = 0  # 重置计数器
                    
                start += batch_size
                logging.info(f"当前批次返回 {entry_count} 个结果，总计 {len(full_content)} 个结果")
                
                # 每批次获取到数据后就保存，防止中断时丢失数据
                if entry_count > 0:
                    logging.info(f"获取到 {entry_count} 条新数据，立即保存...")
                    try:
                        # 获取当前批次新增的条目
                        current_items = list(full_content.items())[-entry_count:]
                        batch_data = {}
                        batch_new_count = 0
                        
                        for paper_id, paper_data in current_items:
                            # 使用统一的ID处理逻辑检查是否已存在
                            clean_paper_id = normalize_arxiv_id(paper_data.get('id', paper_id))
                            if clean_paper_id not in existing_data['arxiv-metadata-oai-snapshot']:
                                batch_data[paper_id] = paper_data
                                batch_new_count += 1  # 统计真正新增的论文数量
                        
                        if len(batch_data) > 0:
                            new_count, total_count, updated_existing_data = save_metadata_files(batch_data, existing_data)
                            existing_data = updated_existing_data  # 更新existing_data引用
                            new_papers_count += batch_new_count  # 更新新增论文计数器
                            logging.info(f"数据保存完成，新增{batch_new_count}条记录，总共有{total_count}条记录，等待5秒后继续获取...")
                            time.sleep(5)  # 写入完成后等待5秒再继续获取
                        else:
                            logging.info("本批次数据均已存在，无需保存")
                    except Exception as e:
                        logging.error(f"保存时出错: {e}", exc_info=True)
                        logging.error("[保存失败] 批量数据保存过程中出现错误")
                
            except urllib.error.HTTPError as e:
                logging.error(f"HTTP错误: {e.code} - {e.reason}")
                if e.code == 503:  # 服务不可用，等待后重试
                    logging.info("服务暂时不可用，等待10秒后重试")
                    time.sleep(10)
                    continue
                else:
                    break
            except Exception as e:
                logging.error(f"获取数据时发生错误: {e}", exc_info=True)
                break
        
        logging.info(f"成功获取 {len(full_content)} 篇论文的元数据，其中新增论文数量: {new_papers_count}")
        # 确保返回的是字典类型
        if not isinstance(full_content, dict):
            full_content = dict(full_content)
        return full_content, new_papers_count
    except Exception as e:
        logging.error(f"查询过程中发生错误: {e}", exc_info=True)
        raise

def load_existing_metadata_files(skip_no_date_files: bool = False) -> Dict[str, Set[str]]:
    '''
    加载已有的元数据文件，用于避免重复获取相同数据
    返回一个字典，只包含arxiv-metadata-oai-snapshot类型文件的ID集合
    
    Args:
        skip_no_date_files: 是否跳过无日期后缀的文件
    '''
    existing_data = {
        'arxiv-metadata-oai-snapshot': set(),
        'authors-parsed': set(),
        'internal-citations': set()
    }
    
    metadata_dir = './metadata'
    if not os.path.exists(metadata_dir):
        logging.info("元数据目录不存在，将创建新目录")
        return existing_data

    now = datetime.datetime.now()
    current_year_month = now.strftime("%Y%m")
    logging.debug(f"当前年月: {current_year_month}")

    # 使用正则表达式更可靠地匹配和解析文件名
    for filename in os.listdir(metadata_dir):
        # 处理arxiv-metadata-oai-snapshot文件（包括带日期和不带日期的）
        arxiv_pattern = r'arxiv-metadata-oai-snapshot(-(\d{6}))?\.json$'
        arxiv_match = re.search(arxiv_pattern, filename)
        if arxiv_match:
            file_year_month = arxiv_match.group(2)  # 可能为None
            
            # 如果选择跳过无日期后缀的文件且当前文件无日期后缀，则跳过
            if skip_no_date_files and not file_year_month:
                logging.debug(f"跳过无日期后缀的arXiv元数据文件: {filename}")
                continue
                
            if file_year_month:
                logging.debug(f"发现arXiv元数据文件: {filename}, 提取年月: {file_year_month}")
            else:
                logging.debug(f"发现arXiv元数据文件: {filename}, 无日期后缀")
            
            # 如果有日期后缀，则检查是否小于等于当前年月
            if not file_year_month or file_year_month <= current_year_month:
                file_path = os.path.join(metadata_dir, filename)
                logging.info(f"加载arXiv元数据文件: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        line_count = 0
                        for line_num, line in enumerate(f, 1):
                            line = line.strip()
                            if not line:  # 跳过空行
                                continue
                                
                            try:
                                data = json.loads(line)
                                if 'id' in data:
                                    # 从完整ID中提取论文ID (例如: http://arxiv.org/abs/2108.09112v1 -> 2108.09112)
                                    paper_id = data['id']
                                    paper_id = normalize_arxiv_id(paper_id)
                                    existing_data['arxiv-metadata-oai-snapshot'].add(paper_id)
                                    line_count += 1
                                    # 记录前5个ID用于调试
                                    if line_count <= 5:
                                        logging.debug(f"  已加载ID (arxiv): {paper_id}")
                            except json.JSONDecodeError as e:
                                logging.warning(f"第{line_num}行JSON解析错误: {e}")
                                continue
                        logging.info(f"从 {filename} 加载 {line_count} 条arXiv元数据记录")
                except Exception as e:
                    logging.error(f"读取arXiv元数据文件 {filename} 时出错: {e}", exc_info=True)

    # 明确记录加载结果
    logging.info(f"已加载现有元数据记录数:")
    logging.info(f"  arxiv-metadata-oai-snapshot: {len(existing_data['arxiv-metadata-oai-snapshot'])}")
    
    return existing_data

def normalize_arxiv_id(arxiv_id: str) -> str:
    """将各种格式的arXiv ID标准化为不带版本号的基本ID"""
    if not arxiv_id:
        return ""
    
    # 处理URL
    if '/abs/' in arxiv_id:
        arxiv_id = arxiv_id.split('/abs/')[-1]
    elif 'arxiv.org' in arxiv_id:
        arxiv_id = arxiv_id.split('/')[-1]
    
    # 移除版本号
    ver_pos = arxiv_id.find('v')
    if ver_pos != -1:
        return arxiv_id[:ver_pos]
    return arxiv_id

def save_metadata_files(new_dict, existing_data=None, skip_no_date_files: bool = False) -> tuple:
    '''
    以每行一个 JSON 对象的格式保存元数据文件
    '''
    now = datetime.datetime.now()
    year_month = now.strftime("%Y%m")
    metadata_dir = './metadata'
    os.makedirs(metadata_dir, exist_ok=True)
    logging.info(f"确保元数据目录存在: {metadata_dir}")

    if existing_data is None:
        existing_data = load_existing_metadata_files(skip_no_date_files)
        
    logging.info(f"加载的现有数据统计:")
    logging.info(f"  arxiv-metadata-oai-snapshot: {len(existing_data['arxiv-metadata-oai-snapshot'])}")
    logging.info(f"新数据总量: {len(new_dict)}")

    # 保存 arxiv-metadata-oai-snapshot 文件
    arxiv_file = os.path.join(metadata_dir, f'arxiv-metadata-oai-snapshot-{year_month}.json')
    new_entries = 0
    try:
        # 确保文件以换行符结尾，避免JSON格式错误
        if os.path.exists(arxiv_file) and os.path.getsize(arxiv_file) > 0:
            with open(arxiv_file, 'rb+') as f:
                f.seek(0, 2)  # 先移动到文件末尾
                f.seek(f.tell() - 1, 0)  # 再回退一个字节
                last_char = f.read(1)
                if last_char != b'\n':
                    f.write(b'\n')
        
        with open(arxiv_file, 'a', encoding='utf-8') as f:
            for paper_id, paper_data in new_dict.items():
                # 使用统一的ID处理逻辑
                full_paper_id = paper_data.get('id', paper_id)
                clean_paper_id = normalize_arxiv_id(full_paper_id)
                
                # 调试日志
                logging.debug(f"处理ID: 原始={full_paper_id}, 处理后={clean_paper_id}")
                
                if clean_paper_id not in existing_data['arxiv-metadata-oai-snapshot']:
                    # 确保每行都是独立的JSON对象
                    json_line = json.dumps(paper_data, ensure_ascii=False)
                    f.write(json_line + '\n')
                    new_entries += 1
                    existing_data['arxiv-metadata-oai-snapshot'].add(clean_paper_id)  # 添加到已存在集合中
                    if new_entries <= 5:  # 只记录前5个新条目
                        logging.info(f"成功写入新条目 (arxiv): {clean_paper_id}")
                else:
                    logging.debug(f"跳过已存在的论文: {clean_paper_id}")
        
        logging.info(f"成功在 {arxiv_file} 中写入 {new_entries} 个新条目")
        if new_entries > 0:
            logging.info(f"[保存成功] arxiv-metadata-oai-snapshot 文件新增 {new_entries} 条记录")
        else:
            logging.info(f"[保存提示] arxiv-metadata-oai-snapshot 文件没有新增记录")
    except Exception as e:
        logging.error(f"写入文件 {arxiv_file} 时出错: {e}", exc_info=True)
        logging.error(f"[保存失败] arxiv-metadata-oai-snapshot 文件保存失败")
        logging.error(f"当前工作目录: {os.getcwd()}")
        logging.error(f"目录权限: {oct(os.stat(metadata_dir).st_mode)[-3:]}")
        # 检查文件是否可写
        if os.access(metadata_dir, os.W_OK):
            logging.info(f"目录 {metadata_dir} 可写")
        else:
            logging.error(f"目录 {metadata_dir} 不可写")
        raise

    # 返回新条目数和总计数，以及更新后的existing_data
    total_arxiv = len(existing_data['arxiv-metadata-oai-snapshot']) 
    logging.info(f"[保存完成] 本次保存操作总计新增条目数: arxiv-metadata-oai-snapshot={new_entries}")
    return new_entries, total_arxiv, existing_data

def generate_report(report_dict, include_category_stats=False) -> str:
    '''
    生成元数据获取报告，分为两个版块：本次获取情况和累计获取情况
    '''
    now = datetime.datetime.now()
    report_date = now.strftime("%Y-%m-%d %H:%M:%S")
    year_month = now.strftime("%Y%m")
    
    # 重新加载现有数据确保准确性
    existing_data = load_existing_metadata_files()
    
    report_content = f"""
# 元数据获取报告
**报告生成时间**: {report_date}

## 本次获取情况
- 新增论文数量: {report_dict['new_papers_count']}
- 处理的分类数量: {report_dict['categories_count']}
- 成功处理的分类: {', '.join(report_dict['successful_categories'])}
- 处理失败的分类: {', '.join(report_dict['failed_categories']) if report_dict['failed_categories'] else '无'}

### 各分类论文获取情况:
"""
    
    for category, count in report_dict['category_paper_counts'].items():
        report_content += f"- {category}: {count} 篇论文\n"
    
    report_content += f"""

### 失败分类详情:
"""
    
    for category, error in report_dict['category_errors'].items():
        report_content += f"- {category}: {error}\n"
    
    report_content += f"""

## 累计获取情况
- arxiv-metadata-oai-snapshot 总数: {len(existing_data['arxiv-metadata-oai-snapshot'])}

### 各分类累计论文数量:
"""
    
    # 统计各分类的累计论文数量（可选功能）
    category_counts = {}
    if include_category_stats:
        try:
            # 从现有数据中统计各分类数量
            metadata_dir = './metadata'
            arxiv_file_pattern = f'arxiv-metadata-oai-snapshot-{year_month}.json'
            arxiv_file_path = os.path.join(metadata_dir, arxiv_file_pattern)
            
            if os.path.exists(arxiv_file_path):
                with open(arxiv_file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            data = json.loads(line)
                            # 从categories字段统计分类
                            categories = data.get('categories', [])
                            if isinstance(categories, list):
                                for category in categories:
                                    # 处理各种格式的分类
                                    if '.' in category:
                                        # 标准格式如 cs.AI, math.CO 等
                                        main_category = category.split('.')[0]
                                    elif '/' in category:
                                        # 旧格式如 acc-phys/9507001
                                        main_category = category.split('/')[0]
                                    else:
                                        # 主分类或MSC代码等
                                        main_category = category
                                    
                                    # 统计所有分类
                                    category_counts[main_category] = category_counts.get(main_category, 0) + 1
                            elif isinstance(categories, str):
                                # 处理逗号分隔的分类字符串
                                cats = [cat.strip() for cat in categories.split(',')]
                                for category in cats:
                                    if '.' in category:
                                        main_category = category.split('.')[0]
                                    elif '/' in category:
                                        main_category = category.split('/')[0]
                                    else:
                                        main_category = category
                                    
                                    # 统计所有分类
                                    category_counts[main_category] = category_counts.get(main_category, 0) + 1
                        except json.JSONDecodeError:
                            continue
            
            # 添加报告数据中的分类统计
            if 'category_stats' in report_dict:
                for category, count in report_dict['category_stats'].items():
                    category_counts[category] = category_counts.get(category, 0) + count
            
            # 按分类名排序输出
            if category_counts:
                for category in sorted(category_counts.keys()):
                    report_content += f"- {category}: {category_counts[category]} 篇论文\n"
            else:
                report_content += "- 暂无分类统计数据\n"
                
        except Exception as e:
            logging.warning(f"统计分类数量时出错: {e}")
            report_content += "- 分类统计信息不可用\n"
    else:
        report_content += "- 分类统计已跳过（如需统计请使用 --include-category-stats 参数）\n"
    
    report_content += f"""

## 文件保存情况
- 元数据文件: arxiv-metadata-oai-snapshot-{year_month}.json

---
*报告由 arxiv-daily 脚本自动生成*
"""
    
    # 保存报告到metadata目录
    metadata_dir = './metadata'
    report_file = os.path.join(metadata_dir, f'metadata-report-{year_month}.md')
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logging.info(f"元数据获取报告已保存到: {report_file}")
        
        # 额外验证报告内容
        logging.info("报告内容预览:")
        logging.info(report_content[:500] + "..." if len(report_content) > 500 else report_content)
    except Exception as e:
        logging.error(f"保存报告时出错: {e}", exc_info=True)
    
    return report_file

def main():
    parser = argparse.ArgumentParser(description='获取arXiv论文元数据')
    
    parser.add_argument('--max-results', type=int, default=100,
                        help='每个分类最大获取论文数量 (默认: 100)')
    
    parser.add_argument('--date-range', type=str,
                        help='日期范围查询 (格式: YYYY-MM-DD,YYYY-MM-DD)')
    
    parser.add_argument('--skip-no-date-files', action='store_true',
                        help='跳过无日期后缀的元数据文件')
    
    parser.add_argument('--include-category-stats', action='store_true',
                        help='在报告中包含各分类累计论文数量统计')
    
    args = parser.parse_args()
    max_results = args.max_results
    
    # 解析日期范围参数
    start_date = None
    end_date = None
    if args.date_range:
        start_date, end_date = args.date_range.split(',')
        start_date = start_date.strip()
        end_date = end_date.strip()
    
    # 标记是否明确指定了all_categories参数
    import sys
    args.all_categories_specified = '--all_categories' in sys.argv
    
    # 如果提供了日期参数，验证日期格式
    if start_date:
        try:
            datetime.datetime.strptime(start_date, '%Y-%m-%d')
        except ValueError:
            logging.error("开始日期格式错误，请使用 YYYY-MM-DD 格式")
            return
    
    if end_date:
        try:
            datetime.datetime.strptime(end_date, '%Y-%m-%d')
        except ValueError:
            logging.error("结束日期格式错误，请使用 YYYY-MM-DD 格式")
            return
    
    initial_count = 0  # 初始化 initial_count 以修复作用域问题
    
    # 如果提供了日期范围，使用特定的查询模式
    if args.date_range:
        # 按日期范围查询的逻辑
        start_date, end_date = args.date_range.split(',')
        start_date = start_date.strip()
        end_date = end_date.strip()
        
        logging.info(f"开始按日期范围查询: {start_date} 到 {end_date}")
        full_content, new_papers_count = get_daily_papers("date_range", "", 
                                          max_results=max_results,
                                          start_date=start_date, 
                                          end_date=end_date)
        
        logging.info(f"日期范围查询完成，共获取 {len(full_content)} 篇论文，新增 {new_papers_count} 篇")
        
        # 保存数据
        all_category_data = full_content
        logging.info(f"开始保存完整元数据，共 {len(all_category_data)} 条记录")
        
        # 修复报告数据更新逻辑
        existing_data = load_existing_metadata_files(args.skip_no_date_files)
        initial_count = len(existing_data['arxiv-metadata-oai-snapshot'])
        new_count, total_count, updated_data = save_metadata_files(all_category_data, existing_data, skip_no_date_files=args.skip_no_date_files)
        final_count = len(updated_data['arxiv-metadata-oai-snapshot'])
        
        # 使用get_daily_papers函数返回的new_papers_count作为新增论文数量
        report_data['new_papers_count'] = new_papers_count
        report_data['existing_papers_count'] = initial_count
        
        # 生成报告前再次验证数据
        logging.info("生成报告前验证现有数据...")
        logging.info(f"  arxiv-metadata-oai-snapshot 总数: {final_count}")
        logging.info(f"  新增论文数量: {report_data['new_papers_count']}")
        
        # 生成报告
        report_file = generate_report(report_data)
        
        logging.info("完整元数据保存完成")
        logging.info(f"元数据报告已生成: {report_file}")
    else:
        # 原有的按分类查询逻辑
        categories = get_all_categories()
        all_category_data = {}
        
        # 报告数据
        report_data = {
            'new_papers_count': 0,
            'existing_papers_count': 0,
            'categories_count': len(categories),
            'successful_categories': [],
            'failed_categories': [],
            'category_paper_counts': {},
            'category_errors': {},
            'category_stats': {}  # 添加分类统计信息
        }
        
        logging.info(f"开始收集 {len(categories)} 个分类的论文数据")
        
        total_new_papers = 0
        for category in categories:
            # 为每个分类获取论文
            query = f"cat:{category}*"
            try:
                logging.info(f"开始查询分类: {category}, 查询语句: {query}")
                full_content, new_papers_count = get_daily_papers(category, query, max_results=max_results, 
                                              start_date=start_date, end_date=end_date)
                logging.info(f"分类 {category} 返回 {len(full_content)} 篇论文，其中新增 {new_papers_count} 篇")
                all_category_data.update(full_content)
                report_data['successful_categories'].append(category)
                report_data['category_paper_counts'][category] = len(full_content)
                total_new_papers += new_papers_count
                logging.info(f'成功收集分类 {category} 的论文数据，共 {len(full_content)} 篇论文，新增 {new_papers_count} 篇')
            except Exception as e:
                report_data['failed_categories'].append(category)
                report_data['category_errors'][category] = str(e)
                logging.error(f"收集分类 {category} 的论文时出错: {e}", exc_info=True)

        logging.info(f"总共收集到 {len(all_category_data)} 篇论文")
        if not all_category_data:
            logging.error("没有收集到任何论文数据，请检查查询条件和网络连接")
            # 生成一个空报告
            report_data['new_papers_count'] = 0
            report_file = generate_report(report_data)
            logging.info(f"空报告已生成: {report_file}")
            return

        # 数据已在每批次获取时保存，此处无需再次保存
        logging.info("数据已在获取过程中保存到文件，跳过最终保存步骤")
        
        # 重新加载数据以获取准确计数
        final_existing_data = load_existing_metadata_files(args.skip_no_date_files)
        final_count = len(final_existing_data['arxiv-metadata-oai-snapshot'])
        # 修复新增论文数量计算逻辑
        report_data['new_papers_count'] = total_new_papers
        report_data['existing_papers_count'] = initial_count
        
        # 生成报告前再次验证数据
        logging.info("生成报告前验证现有数据...")
        logging.info(f"  arxiv-metadata-oai-snapshot 总数: {final_count}")
        logging.info(f"  新增论文数量: {report_data['new_papers_count']}")
        
        # 生成报告
        report_file = generate_report(report_data, args.include_category_stats)
        
        logging.info("完整元数据保存完成")
        logging.info(f"元数据报告已生成: {report_file}")

if __name__ == "__main__":
    main()