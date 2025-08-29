# arXiv 工具包使用文档

这是一个完整的 arXiv 工具包，包含用于收集 arXiv 论文元数据和将 arXiv PDF 链接转换为 Google Cloud Storage (GCS) 路径的工具。

## 目录

1. [arXiv 论文元数据收集工具](#arxiv-论文元数据收集工具)
2. [Arxiv PDF到GCS路径转换器](#arxiv-pdf到gcs路径转换器)
3. [GCS链接转换规则说明](#gcs链接转换规则说明)

---

## arXiv 论文元数据收集工具

这是一个用于收集 arXiv 论文元数据的工具，支持按分类和日期范围收集论文信息，并将数据保存为结构化的 JSON 文件。

## 功能特性

- 按分类收集 arXiv 论文元数据
- 支持按日期范围收集论文
- 将数据保存为结构化的 JSON 文件
- 支持增量更新，避免重复收集
- 生成收集报告
- 提取PDF下载链接
- 将JSON数据导出为CSV格式
- 清理和去重JSON数据
- 将arXiv PDF链接转换为Google Cloud Storage (GCS)路径

## 安装依赖

在使用此工具之前，请确保安装了所需的依赖项：

```bash
pip install arxiv
```

## 项目文件说明

- `daily_arxiv.py` - 主程序文件，用于收集论文元数据
- `extract_pdf_links.py` - PDF链接提取工具
- `export_to_csv.py` - 将JSON元数据转换为CSV格式
- `clean_json.py` - 清理和去重JSON数据
- `arxiv_converter.py` - 将arXiv PDF链接转换为GCS路径
- `check_gcs_status.py` - 检查GCS存储桶状态
- `config.yaml` - 配置文件
- `./metadata/` - 数据存储目录

## 使用方法

### 基本用法

```bash
python daily_arxiv.py [--max_results N] [--date-range YYYY-MM-DD,YYYY-MM-DD] [--skip_no_date_files] [--include-category-stats]
```

### 参数说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--max-results` | int | 100 | 每个分类最多获取的论文数量 |
| `--date-range` | string | 无 | 日期范围查询 (格式: YYYY-MM-DD,YYYY-MM-DD) |
| `--skip-no-date-files` | flag | False | 是否跳过无日期后缀的文件 |
| `--include-category-stats` | flag | False | 是否在报告中包含各分类累计论文数量统计 |

### 使用示例

#### 1. 按分类收集最新的论文

```
# 收集每个分类最新的100篇论文
python daily_arxiv.py

# 收集每个分类最新的10篇论文
python daily_arxiv.py --max-results 10

# 收集每个分类最新的100篇论文，并在报告中包含分类统计信息
python daily_arxiv.py --include-category-stats
```

#### 2. 按日期范围收集论文

```
# 收集2025年8月1日至28日的所有论文，每个分类最多100篇
python daily_arxiv.py --date-range 2025-08-01,2025-08-28

# 收集2025年8月1日至28日的所有论文，每个分类最多5篇
python daily_arxiv.py --date-range 2025-08-01,2025-08-28 --max-results 5
```

#### 3. 跳过无日期后缀的文件

```
# 收集论文并跳过加载无日期后缀的旧文件
python daily_arxiv.py --date-range 2025-08-01,2025-08-28 --skip-no-date-files

# 收集论文并包含分类统计信息
python daily_arxiv.py --date-range 2025-08-01,2025-08-28 --include-category-stats
```

## PDF链接提取工具

除了收集元数据外，还提供了一个工具用于从元数据文件中提取PDF下载链接。

### 使用方法

```
python extract_pdf_links.py [--file FILE] [--output OUTPUT] [--metadata_dir METADATA_DIR]
```

### 参数说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--file` | string | 无 | 指定要处理的元数据文件路径 |
| `--output` | string | 无 | 输出文件路径 |
| `--metadata_dir` | string | ./metadata | 元数据目录路径 |

### 使用示例

```
# 提取所有元数据文件中的PDF链接
python extract_pdf_links.py --output all_pdf_links.txt

# 提取指定文件中的PDF链接
python extract_pdf_links.py --file ./metadata/arxiv-metadata-oai-snapshot-202508.json --output pdf_links_202508.txt

# 指定元数据目录并提取PDF链接
python extract_pdf_links.py --metadata_dir ./metadata --output pdf_links.txt
```

## JSON数据导出为CSV工具

将JSON格式的元数据转换为CSV格式，便于数据分析和处理。

### 使用方法

```
python export_to_csv.py [--input INPUT] [--output_dir OUTPUT_DIR] [--records_per_file RECORDS_PER_FILE]
```

### 参数说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--input` | string | ./metadata/arxiv-metadata-oai-snapshot-202508.json | 输入的JSON文件路径 |
| `--output_dir` | string | ./csv_output | 输出CSV文件的目录 |
| `--records_per_file` | int | 500 | 每个CSV文件包含的记录数 |

### 使用示例

```
# 将默认JSON文件转换为CSV格式
python export_to_csv.py

# 指定输入文件和输出目录
python export_to_csv.py --input ./metadata/arxiv-metadata-oai-snapshot-202508.json --output_dir ./csv_data

# 指定每个CSV文件包含1000条记录
python export_to_csv.py --records_per_file 1000
```

## JSON数据清理和去重工具

清理和去重JSON格式的元数据文件。

### 使用方法

```
python clean_json.py
```

### 功能说明

- 自动备份原始文件
- 去除重复记录（基于论文ID）
- 保留唯一记录
- 输出处理统计信息

## Arxiv PDF到GCS路径转换器

将arXiv PDF链接转换为Google Cloud Storage (GCS)路径。

### 使用方法

```
python arxiv_converter.py [--file FILE] [--output OUTPUT] [PDF_URL ...]
```

### 参数说明

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--file` | string | 无 | 包含PDF链接的输入文件路径 |
| `--output` | string | 无 | 输出文件路径 |
| `PDF_URL` | string | 无 | 直接提供的PDF链接 |

### 使用示例

```
# 转换单个PDF链接
python arxiv_converter.py https://arxiv.org/pdf/2406.18629.pdf

# 从文件读取多个链接并转换
python arxiv_converter.py --file links.txt --output gcs_links.txt
```

## 输出文件

工具会在 `./metadata` 目录下生成以下文件：

1. `arxiv-metadata-oai-snapshot-YYYYMM.json` - 论文元数据文件，每行一个 JSON 对象

### 文件格式说明

#### arxiv-metadata-oai-snapshot-YYYYMM.json

每行包含一篇论文的完整元数据：

```
{
  "id": "2508.19247v1",
  "authors": "Lin Li, et al.",
  "title": "VoxHammer: Training-Free Precise and Coherent 3D Editing in Native 3D Space",
  "comments": "论文评论信息",
  "journal-ref": "期刊引用信息",
  "doi": "数字对象标识符",
  "categories": ["cs.CV", "cs.GR"],
  "abstract": "论文摘要内容...",
  "update_date": "2025-08-26",
  "authors_parsed": [["Li", "Lin", ""], ...],
  "primary_category": "cs.CV",
  "publish_time": "2025-08-26",
  "entry_id": "http://arxiv.org/abs/2508.19247v1",
  "links": ["http://arxiv.org/abs/2508.19247v1"]
}
```

## 注意事项

1. **API 限制**: arXiv API 有请求频率限制，请不要过于频繁地请求数据，建议在请求之间添加适当的延迟。

2. **日期格式**: 使用 `--date-range` 参数时，请确保日期格式为 `YYYY-MM-DD,YYYY-MM-DD`。

3. **增量更新**: 工具会自动检查已存在的数据文件，避免重复收集相同的数据。

4. **文件命名**: 工具会根据当前年月生成带日期后缀的文件名，例如 `202508` 表示 2025 年 8 月。

5. **性能考虑**: 当处理大量数据时，建议使用 `--skip-no-date-files` 参数跳过加载无日期后缀的旧文件，以提高性能。

6. **网络连接**: 确保网络连接稳定，特别是在收集大量数据时。

## 故障排除

### 1. 收集速度慢

如果收集速度较慢，可以尝试以下方法：
- 减少 `--max-results` 的值
- 使用具体的日期范围而不是收集最新的论文
- 确保网络连接稳定

### 2. 数据重复

工具会自动检测已存在的数据并避免重复收集。如果发现重复数据，请检查：
- 确保 `metadata` 目录中的文件格式正确
- 删除损坏的文件后重新运行工具

### 3. API 错误

如果遇到 API 错误，请检查：
- 网络连接是否正常
- 是否过于频繁地请求数据
- 日期格式是否正确

## 开发说明

### 代码结构

- `daily_arxiv.py` - 主程序文件，用于收集论文元数据
- `extract_pdf_links.py` - PDF链接提取工具
- `export_to_csv.py` - JSON到CSV转换工具
- `clean_json.py` - JSON数据清理工具
- `arxiv_converter.py` - PDF链接到GCS路径转换工具
- `check_gcs_status.py` - GCS存储桶状态检查工具
- `./metadata/` - 数据存储目录

### 主要函数

#### daily_arxiv.py
- `get_daily_papers()` - 获取论文数据
- `load_existing_metadata_files()` - 加载已存在的元数据
- `save_metadata_files()` - 保存元数据到文件
- `generate_report()` - 生成收集报告

#### extract_pdf_links.py
- `extract_pdf_links_from_file()` - 从指定的元数据文件中提取PDF下载链接
- `find_metadata_files()` - 查找metadata目录下的所有arxiv-metadata-oai-snapshot文件

#### export_to_csv.py
- `json_to_csv()` - 将JSON数据转换为CSV格式

#### clean_json.py
- `clean_and_deduplicate_json()` - 清理和去重JSON数据

#### arxiv_converter.py
- `convert_to_gcs_url()` - 将PDF链接转换为GCS路径

### 依赖库

- `arxiv` - arXiv API 客户端 (版本 >= 1.4.0)
- `requests` - HTTP请求库 (版本 >= 2.25.1)
- `json` - JSON 处理 (Python标准库)
- `logging` - 日志记录 (Python标准库)
- `argparse` - 命令行参数解析 (Python标准库)
- `datetime` - 日期处理 (Python标准库)
- `os`, `re` - 文件和正则表达式处理 (Python标准库)
- `csv` - CSV文件处理 (Python标准库)

## 许可证

本项目基于 Alan Global Copyright Protection Agreement (AGCPA v3.0) 开源协议进行授权。© 2024-2025 Alan. 全球保留所有权利。

详细协议内容请参阅 [AGCPA v3.0.md](AGCPA%20v3.0.md) 文件或访问官方链接了解详细信息：[https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg](https://ima.qq.com/note/share?shareId=_AseMbuM8w6eLpIXZlZgMg)

---

## Arxiv PDF到GCS路径转换器

该工具可以将标准的arXiv PDF链接转换为Google Cloud Storage (GCS)路径。

### 转换规则

详细的转换规则请参见 [GCS转换规则说明](#gcs链接转换规则说明) 部分。

简要说明：
1. **提取论文ID**: 从PDF链接中提取论文ID（如 `2406.18629` 或 `9507001`）
2. **获取学科分类**: 优先从本地元数据文件获取，其次从链接或arXiv API获取
3. **解析年月**: 从论文ID解析年月信息（如 `2406` 表示2024年6月）
4. **组合GCS路径**: 根据论文年月使用不同的路径格式
   - 2007年3月之前的论文使用分类路径结构
   - 2007年4月及之后的论文使用 `arxiv/arxiv` 路径结构

### 安装依赖

在使用脚本前，请确保安装了所需的依赖包：

```bash
pip install requests
```

### 使用方法

#### 命令行直接输入URL

```
python arxiv_converter.py https://arxiv.org/pdf/2406.18629.pdf
```

#### 从文件读取多个URL

创建一个包含多个arXiv链接的文本文件（每行一个链接）：

```
https://arxiv.org/pdf/2406.18629.pdf
https://arxiv.org/pdf/9507001v2.pdf
https://arxiv.org/pdf/acc-phys/9507001v2.pdf
```

然后运行：

```
python arxiv_converter.py --file links.txt
```

#### 将结果保存到文件

```
python arxiv_converter.py --file links.txt --output gcs_links.txt
```

#### 编程方式使用

你也可以在自己的Python代码中使用该转换器：

```
from arxiv_converter import convert_to_gcs_url

# 转换单个链接
pdf_url = "https://arxiv.org/pdf/2406.18629.pdf"
gcs_url = convert_to_gcs_url(pdf_url)
print(gcs_url)
```

### 支持的链接格式

转换器支持多种arXiv PDF链接格式：

1. 标准格式：
   ```
   https://arxiv.org/pdf/2406.18629.pdf
   https://arxiv.org/pdf/2406.18629v1.pdf
   ```

2. 早期格式：
   ```
   https://arxiv.org/pdf/9507001.pdf
   https://arxiv.org/pdf/9507001v2.pdf
   ```

3. 带分类格式：
   ```
   https://arxiv.org/pdf/acc-phys/9507001v2.pdf
   ```

### 示例输出

输入链接：
```
https://arxiv.org/pdf/acc-phys/9507001v2.pdf
https://arxiv.org/pdf/astro-ph/0508001v1.pdf
https://arxiv.org/pdf/0703.0003v1.pdf
https://arxiv.org/pdf/0704.0004v1.pdf
https://arxiv.org/pdf/2406.18629v1.pdf
https://arxiv.org/pdf/2505.00009v1.pdf
```

输出GCS路径：
```
gs://arxiv-dataset/arxiv/acc-phys/9507/9507001v2.pdf
gs://arxiv-dataset/arxiv/astro-ph/0508/0508001v1.pdf
gs://arxiv-dataset/arxiv/arxiv/0703/07030003v1.pdf
gs://arxiv-dataset/arxiv/arxiv/0704/07040004v1.pdf
gs://arxiv-dataset/arxiv/arxiv/2406/2406.18629v1.pdf
gs://arxiv-dataset/arxiv/arxiv/2505/2505.00009v1.pdf
```

### 同步延迟说明

**重要提示**：生成的GCS链接格式是有效的，但需要注意同步延迟问题：

1. **7天同步延迟**：arxiv.org网站上发布的论文与GCS存储桶之间存在大约7天的同步延迟：
   - 在论文发布后的7天内，生成的GCS链接虽然格式正确，但可能无法下载到PDF文件
   - 7天后，PDF文件将可以在GCS中访问和下载

2. **链接有效性**：生成的链接始终是格式正确的，即使PDF文件暂时不可用：
   - 链接结构符合GCS存储桶的实际组织方式
   - 一旦同步完成，链接将可正常访问

3. **实际应用建议**：
   - 如果需要立即访问最新论文，请直接从arxiv.org下载
   - 如果可以等待，GCS链接提供了一种更稳定的访问方式
   - 对于较旧的论文，GCS链接通常可以立即访问

### 注意事项

1. **网络依赖**: 脚本需要访问arXiv API获取论文分类信息，因此需要网络连接（除非本地有元数据文件）。
2. **版本处理**: 如果原始链接不包含版本号，默认使用v1版本。
3. **文件存在性**: 生成的GCS链接格式正确，但文件可能并不存在于GCS存储桶中。
4. **本地元数据**: 脚本优先使用本地元数据文件（如果存在），可提高处理速度并减少网络请求。
5. **路径结构**: 2007年4月及之后的论文不需要分类信息，避免了网络请求，提高了处理速度。

### 依赖项

- Python 3.x
- requests库

### 许可证

该工具为开源工具，可根据需要自由使用和修改。

---

## GCS链接转换规则说明

本文档详细说明了如何将arXiv PDF链接转换为Google Cloud Storage (GCS)路径的规则。

### 概述

arXiv论文在GCS存储桶中的存储路径遵循特定的格式。本转换器根据论文ID、分类和年月信息生成正确的GCS路径。

### 转换规则

#### 1. 链接格式识别

转换器支持以下几种arXiv PDF链接格式：

1. 标准格式（带点）：
   ```
   https://arxiv.org/pdf/2406.18629.pdf
   https://arxiv.org/pdf/2406.18629v1.pdf
   ```

2. 无点格式：
   ```
   https://arxiv.org/pdf/9507001.pdf
   https://arxiv.org/pdf/9507001v2.pdf
   ```

3. 带分类格式：
   ```
   https://arxiv.org/pdf/acc-phys/9507001v2.pdf
   https://arxiv.org/pdf/hep-th/9507001v2.pdf
   ```

#### 2. 论文ID提取

从链接中提取论文ID的规则：

- 对于带点格式（如 `2406.18629`）：直接提取
- 对于无点格式（如 `9507001`）：前4位为年月（如 `9507` 表示1995年7月），后面为论文编号

#### 3. 分类信息获取

分类信息的获取优先级如下：

1. 从本地元数据文件获取（优先使用）
2. 从链接中的分类目录获取（如 `acc-phys`）
3. 从arXiv API获取（网络请求）
4. 默认使用 `cs.LG`（计算机科学-学习）

#### 4. 年月解析

从论文ID解析年月信息：

- 对于带点格式（如 `2406.18629`）：前4位即为年月（`2406` 表示2024年6月）
- 对于无点格式（如 `9507001`）：前4位即为年月（`9507` 表示1995年7月）

注意：对于20世纪的论文（年份小于等于99），需要特别处理：
- `9507` 表示1995年7月
- `0507` 表示2005年7月

#### 5. GCS路径格式

根据论文提交年月确定GCS路径格式：

##### 2007年3月之前（包括2007年3月）

使用分类路径结构：
```
gs://arxiv-dataset/arxiv/{category}/{YYMM}/{paper_id}.pdf
```

示例：
```
gs://arxiv-dataset/arxiv/acc-phys/9507/9507001v2.pdf
```

##### 2007年4月及之后

使用统一路径结构：
```
gs://arxiv-dataset/arxiv/arxiv/{YYMM}/{paper_id}.pdf
```

示例：
```
gs://arxiv-dataset/arxiv/arxiv/0704/07040004v1.pdf
```

#### 6. 特殊处理

1. 对于无点格式的论文ID，如果年份在70-99之间，视为1970-1999年
2. 对于无点格式的论文ID，如果年份在00-69之间，视为2000-2069年
3. 如果无法从链接或元数据中获取分类信息，则使用默认分类 `cs.LG`

### 使用示例

#### 命令行使用

```
# 转换单个链接
python arxiv_converter.py https://arxiv.org/pdf/2406.18629.pdf

# 从文件批量转换
python arxiv_converter.py --file links.txt --output gcs_links.txt
```

#### 编程使用

```
from arxiv_converter import convert_to_gcs_url

# 转换单个链接
pdf_url = "https://arxiv.org/pdf/2406.18629.pdf"
gcs_url = convert_to_gcs_url(pdf_url)
print(gcs_url)
# 输出: gs://arxiv-dataset/arxiv/arxiv/2406/2406.18629.pdf
```

### 版本处理

- 如果链接中包含版本号（如 `v1`, `v2`），则保留
- 如果没有版本号，默认使用 `v1`

### 同步延迟说明

**重要提示**：生成的GCS链接格式是有效的，但需要注意以下同步延迟问题：

1. **7天同步延迟**：arxiv.org网站上发布的论文与GCS存储桶之间存在大约7天的同步延迟。这意味着：
   - 在论文发布后的7天内，生成的GCS链接虽然格式正确，但可能无法下载到PDF文件
   - 7天后，PDF文件将可以在GCS中访问和下载

2. **链接有效性**：生成的链接始终是格式正确的，即使PDF文件暂时不可用：
   - 链接结构符合GCS存储桶的实际组织方式
   - 一旦同步完成，链接将可正常访问

3. **实际应用建议**：
   - 如果需要立即访问最新论文，请直接从arxiv.org下载
   - 如果可以等待，GCS链接提供了一种更稳定的访问方式
   - 对于较旧的论文，GCS链接通常可以立即访问

### 注意事项

1. 生成的链接格式是正确的，但并非所有文件都实际存在于GCS存储桶中
2. 早期论文（如1994年）更有可能存在，而较新论文可能不存在
3. 如果需要访问PDF文件，建议直接从arxiv.org下载
4. GCS存储桶的更新可能比arxiv.org网站滞后约一周时间
