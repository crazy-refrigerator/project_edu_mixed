import os
import uuid
import fitz  # PyMuPDF
import re
from datetime import datetime
import json
import requests

def allowed_file(filename):
    """检查文件是否允许上传"""
    ALLOWED_EXTENSIONS = {'pdf'}
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def parse_page_range(page_spec, total_pages):
    """解析页码范围，返回页码索引列表（0-based）"""
    if not page_spec:
        return list(range(total_pages))

    # 如果输入是字符串
    if isinstance(page_spec, str):
        # 处理连续范围 "3-5"
        if '-' in page_spec:
            try:
                start, end = map(int, page_spec.split('-'))
                return list(range(max(0, start - 1), min(total_pages, end)))
            except:
                return []

        # 处理逗号分隔列表 "1,3,5"
        elif ',' in page_spec:
            try:
                pages = []
                for part in page_spec.split(','):
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages.extend(range(max(0, start - 1), min(total_pages, end)))
                    else:
                        page_num = int(part) - 1
                        if 0 <= page_num < total_pages:
                            pages.append(page_num)
                return list(set(pages))  # 去重
            except:
                return []

        # 单个页码 "5"
        else:
            try:
                page_num = int(page_spec) - 1
                return [page_num] if 0 <= page_num < total_pages else []
            except:
                return []

    return []