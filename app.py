from flask import Flask, request, render_template, send_file
from ppt_templates import (
    create_title_slide,
    create_full_text_slide,
    create_text_above_image_slide,
    create_custom_slide
)
from PIL import Image
import os
from pptx import Presentation
import shutil
import re

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
TEMP_FOLDER = "temp"
OUTPUT_FILE = "output.pptx"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["TEMP_FOLDER"] = TEMP_FOLDER


def save_image(image_file):
    """
    保存上传的图片，处理不支持的格式（如 WEBP）。
    """
    os.makedirs(app.config["TEMP_FOLDER"], exist_ok=True)
    original_path = os.path.join(app.config["UPLOAD_FOLDER"], image_file.filename)
    image_file.save(original_path)

    # 检查图片格式并转换
    try:
        with Image.open(original_path) as img:
            if img.format == "WEBP":  # 转换为 PNG
                new_path = os.path.join(app.config["TEMP_FOLDER"], f"{os.path.splitext(image_file.filename)[0]}.png")
                img.convert("RGB").save(new_path, "PNG")
                return new_path
            else:
                return original_path
    except Exception as e:
        raise ValueError(f"Error processing image {image_file.filename}: {str(e)}")


def parse_content(raw_content, image_mapping):
    """
    解析用户输入文本并生成幻灯片内容。
    """
    lines = raw_content.split("\n")
    slides = []
    current_title = None
    current_content = []
    image_counter = 0  # 用于图片计数

    for line in lines:
        line = line.strip()

        if line.lower().startswith("[title]:"):  # 主标题
            slides.append({"type": "title", "content": line[8:].strip()})
            current_title = None
            current_content = []

        elif re.match(r"^\d+\s+.+", line):  # 一级标题
            if current_title and current_content:
                slides.append({"type": "text", "title": current_title, "content": "\n".join(current_content)})
            slides.append({"type": "section_title", "content": line.strip()})
            current_title = line.strip()
            current_content = []

        elif re.match(r"^\d+\.\d+\s+.+", line):  # 二级标题
            if current_title and current_content:
                slides.append({"type": "text", "title": current_title, "content": "\n".join(current_content)})
            current_title = line.strip()
            current_content = []

        elif "[image]" in line:  # 图片标记
            if image_counter < len(image_mapping):
                image_path = list(image_mapping.values())[image_counter]
                image_title = list(image_mapping.keys())[image_counter]
                image_counter += 1
                slides.append({
                    "type": "image",
                    "title": current_title,
                    "content": "\n".join(current_content),
                    "image_path": image_path,
                    "image_title": image_title
                })
                current_content = []
            else:
                raise ValueError(f"More [image] markers than images provided. Missing image for marker: {line}")

        else:  # 正文内容
            current_content.append(line)

    if current_title and current_content:
        slides.append({"type": "text", "title": current_title, "content": "\n".join(current_content)})

    return slides


def generate_ppt(slides, font_size):
    """
    根据解析内容生成 PPT。
    """
    prs = Presentation()

    for slide in slides:
        if slide["type"] == "title":
            create_title_slide(prs, slide["content"])
        elif slide["type"] == "section_title":
            create_title_slide(prs, slide["content"], title_font_size=36)
        elif slide["type"] == "text":
            create_full_text_slide(prs, slide["title"], slide["content"], font_size=font_size)
        elif slide["type"] == "image":
            with Image.open(slide["image_path"]) as img:
                width, height = img.size
                layout = "horizontal" if width > height else "vertical"
            if layout == "horizontal":
                create_text_above_image_slide(
                    prs,
                    slide["title"],
                    slide["content"],
                    slide["image_path"],
                    slide["image_title"],
                    font_size=font_size,
                )
            else:
                create_custom_slide(
                    prs,
                    slide["title"],
                    slide["content"],
                    slide["image_path"],
                    slide["image_title"],
                    font_size=font_size,
                )

    prs.save(OUTPUT_FILE)
    return OUTPUT_FILE


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_content = request.form["content"]
        font_size = int(request.form.get("font_size", 18))
        image_files = request.files.getlist("images")
        image_order = request.form.get("file_order", "")
        image_mapping = {}

        if image_order:
            order = list(map(int, image_order.split(',')))
            image_files = [image_files[i] for i in order]

        for image_file in image_files:
            try:
                saved_path = save_image(image_file)
                image_name = os.path.splitext(image_file.filename)[0]
                image_mapping[image_name] = saved_path
            except ValueError as e:
                return f"Error: {str(e)}"

        slides = parse_content(raw_content, image_mapping)
        ppt_file = generate_ppt(slides, font_size)

        return send_file(ppt_file, as_attachment=True)

    return render_template("index.html")


if __name__ == "__main__":
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    app.run(debug=True)