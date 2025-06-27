import os
import re
import fitz  # PyMuPDF

def extract_images(pdf_path, output_dir, target_pages=None):
    """
    从 PDF 中提取原始图片并保存到指定目录。

    :param pdf_path: PDF 文件路径
    :param output_dir: 图片保存目录
    :param target_pages: 需要处理的页码列表，None 表示处理所有页码
    :return: 包含图片路径（相对路径）和元信息的列表
    """
    # 获取 PDF 文件名（无扩展名）
    pdf_name = os.path.splitext(os.path.basename(pdf_path))[0]
    # 构建保存目录
    pdf_output_dir = os.path.join(output_dir, pdf_name)
    os.makedirs(pdf_output_dir, exist_ok=True)

    doc = fitz.open(pdf_path)
    results = []

    for page_index in range(len(doc)):
        page = doc[page_index]
        if target_pages and (page_index + 1 not in target_pages):
            continue

        image_list = page.get_images(full=True)
        if not image_list:
            print(f"[DEBUG] 第 {page_index + 1} 页未找到图片。")
            continue

        for img_index, img in enumerate(image_list):
            try:
                # 提取图片
                xref = img[0]
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]  # 图片格式（如 png、jpeg）

                # 保存图片到文件
                raw_filename = f"page_{page_index + 1}_img_{img_index + 1}.{image_ext}"
                raw_output_path = os.path.join(pdf_output_dir, raw_filename)
                with open(raw_output_path, "wb") as f:
                    f.write(image_bytes)

                # 构建相对路径
                relative_path = os.path.relpath(raw_output_path, "static")

                # 保存图片信息
                results.append({
                    "page": page_index + 1,
                    "image_index": img_index + 1,
                    "image_path": relative_path  # 返回相对路径
                })

                print(f"[DEBUG] 原始图片已保存到 {raw_output_path}。")

            except Exception as e:
                print(f"[ERROR] 提取第 {page_index + 1} 页，第 {img_index + 1} 张图片失败：{e}")

    return results


def extract_figure_number(text):
    """
    使用正则表达式从文本中提取图号。
    :param text: 提取的页面文本
    :return: 提取到的图号或 None
    """
    patterns = [
        r"Fig(?:ure)?\.?\s?\d+(\.\d+)?",  # 匹配 'Fig. 1.1' 或 'Figure 1.2'
        r"图\d+(\.\d+)?",                # 匹配 '图1.1' 或 '图2'
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)
    return None


def process_pdf_with_regex(pdf_path, output_dir, target_pages=None):
    """
    提取 PDF 图片，并使用正则表达式识别图号。无法识别时自动生成序号。

    :param pdf_path: PDF 文件路径
    :param output_dir: 图片保存目录
    :param target_pages: 目标页码列表，仅处理这些页码
    :return: 包含图片路径、图号等信息的列表
    """
    all_results = extract_images(pdf_path, output_dir, target_pages)
    figure_counter = 1  # 自动生成图号的计数器

    doc = fitz.open(pdf_path)  # 打开 PDF，用于提取文本

    for result in all_results:
        page_number = result["page"]
        print(f"[DEBUG] 处理第 {page_number} 页图片：{result['image_path']}")

        try:
            # 提取页面文本
            page_text = doc[page_number - 1].get_text()
            figure_number = extract_figure_number(page_text)

            # 如果未找到图号，则自动生成
            if not figure_number:
                figure_number = f"Figure {figure_counter}"
                figure_counter += 1

            result.update({
                "figure_number": figure_number,
                "page_text": page_text
            })
            print(f"[DEBUG] 图号提取成功：{figure_number}")

        except Exception as e:
            print(f"[ERROR] 图号提取失败：{e}")
            result.update({
                "figure_number": f"Figure {figure_counter}",
                "page_text": "N/A"
            })
            figure_counter += 1

    return all_results