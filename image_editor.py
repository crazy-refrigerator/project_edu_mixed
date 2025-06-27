import pytesseract
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps


# 确保 Tesseract OCR 安装并配置好路径
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

def replace_line_color(input_path, target_color, replacement_color, output_path):
    """
    将图片中指定颜色的线条替换为目标颜色
    :param input_path: 输入图片路径
    :param target_color: 要替换的颜色 (如 #000000)
    :param replacement_color: 替换后的颜色 (如 #FF5733)
    :param output_path: 输出图片路径
    """
    # 打开图片
    img = Image.open(input_path).convert("RGBA")

    # 将颜色转换为 RGBA 格式
    target_color = target_color.lstrip('#')  # 移除 #
    target_rgba = tuple(int(target_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)  # 添加透明度

    replacement_color = replacement_color.lstrip('#')  # 移除 #
    replacement_rgba = tuple(int(replacement_color[i:i+2], 16) for i in (0, 2, 4)) + (255,)

    # 替换颜色
    data = img.getdata()
    new_data = []
    for item in data:
        if item[:3] == target_rgba[:3]:  # 如果颜色匹配
            new_data.append(replacement_rgba)  # 替换为新颜色
        else:
            new_data.append(item)  # 保留原始像素

    # 更新图片数据
    img.putdata(new_data)

    # 保存图片
    img.save(output_path)

def extract_text_and_boxes(image_path):
    """
    提取图片中的文字及其位置信息。
    :param image_path: 图片路径
    :return: OCR 提取的文字和位置信息（字典列表形式）
    """
    image = Image.open(image_path)
    ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

    text_boxes = []
    for i in range(len(ocr_data['text'])):
        text = ocr_data['text'][i].strip()
        if text:  # 忽略空白文本
            x, y, w, h = (ocr_data['left'][i], ocr_data['top'][i],
                          ocr_data['width'][i], ocr_data['height'][i])
            text_boxes.append({
                'text': text,
                'position': (x, y, w, h)
            })
    return text_boxes


def get_dominant_background_color(image, position):
    """
    获取文字区域的主背景色。
    :param image: 原始图片对象
    :param position: 文字区域 (x, y, w, h)
    :return: 主色的 RGB 值
    """
    x, y, w, h = position
    cropped_image = image.crop((x, y, x + w, y + h))  # 裁剪文字区域
    colors = cropped_image.getcolors(cropped_image.size[0] * cropped_image.size[1])
    dominant_color = max(colors, key=lambda item: item[0])[1]  # 返回出现次数最多的颜色
    return dominant_color[:3]  # 只返回 RGB


def get_text_color(image, position, background_color):
    """
    提取文字颜色，使用增强的边缘检测和区域扩展。
    :param image: 原始图片对象
    :param position: 文字区域 (x, y, w, h)
    :param background_color: 背景色
    :return: 文字颜色的 RGB 值
    """
    x, y, w, h = position
    cropped_image = image.crop((x, y, x + w, y + h))

    # 边缘检测并扩展区域
    edges = cropped_image.convert("L").filter(ImageFilter.FIND_EDGES)
    expanded_edges = ImageOps.expand(edges, border=2, fill=255)  # 扩展边缘区域

    colors = cropped_image.getcolors(cropped_image.size[0] * cropped_image.size[1])

    # 排除与背景色接近的部分，提取对比度高的颜色
    text_colors = [color[:3] for count, color in colors if sum(abs(c - b) for c, b in zip(color[:3], background_color)) > 80]

    if text_colors:
        # 返回出现频率最高的颜色
        return max(text_colors, key=lambda c: text_colors.count(c))

    # 如果无法精确提取，默认返回黑色
    return (0, 0, 0)


def calculate_font_size(position, text, font_path="arial.ttf"):
    """
    动态计算字体大小，使替换文字适配原文字区域。
    :param position: 文字区域 (x, y, w, h)
    :param text: 替换的文字
    :param font_path: 字体路径
    :return: 动态适配的字体对象
    """
    x, y, w, h = position
    font_size = 1  # 初始字体大小
    font = ImageFont.truetype(font_path, font_size)
    while font.getsize(text)[0] < w and font.getsize(text)[1] < h:
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
    return font


def replace_text_in_image(image_path, original_text, replacement_text, output_path):
    """
    替换图片中的文字，并用动态背景色和文字色替换文字区域。
    :param image_path: 原图片路径
    :param original_text: 要替换的原始文字
    :param replacement_text: 替换后的文字
    :param output_path: 输出图片路径
    """
    print(f"[DEBUG] 开始替换文字：'{original_text}' -> '{replacement_text}'")
    image = Image.open(image_path)
    draw = ImageDraw.Draw(image)

    # 提取文字及其位置信息
    text_boxes = extract_text_and_boxes(image_path)

    replaced = False  # 标记是否成功替换文字
    for box in text_boxes:
        if box['text'] == original_text:
            x, y, w, h = box['position']
            print(f"[DEBUG] 正在替换文字：'{original_text}'，位置：{x}, {y}, {w}, {h}")

            # 获取文字区域的背景色和文字颜色
            background_color = get_dominant_background_color(image, (x, y, w, h))
            text_color = get_text_color(image, (x, y, w, h), background_color)

            print(f"[DEBUG] 检测到背景色：{background_color}，文字颜色：{text_color}")

            # 动态调整字体大小
            font = calculate_font_size((x, y, w, h), replacement_text)

            # 用动态背景色覆盖原文字
            draw.rectangle([x, y, x + w, y + h], fill=background_color)

            # 在覆盖区域绘制替换文字
            draw.text((x, y), replacement_text, fill=text_color, font=font)
            replaced = True

    if not replaced:
        print(f"[WARNING] 未找到要替换的文字：'{original_text}'")

    # 保存修改后的图片
    image.save(output_path)
    print(f"[DEBUG] 图片已保存到：{output_path}")