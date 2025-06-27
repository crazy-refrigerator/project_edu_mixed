import os
from flask import Flask, request, render_template, url_for, redirect, send_file, send_from_directory
from image_text_editor import extract_text_and_boxes, replace_text_in_image
from image_color_edit import replace_line_color
from werkzeug.utils import secure_filename

app = Flask(__name__)

# 配置路径
UPLOAD_FOLDER = 'uploads'
OUTPUT_FOLDER = 'outputs'
RESULT_FOLDER = 'results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


@app.route('/', methods=['GET', 'POST'])
def index():
    """
    首页：用户上传图片
    """
    if request.method == 'POST':
        # 上传图片文件
        if 'file' not in request.files:
            return "No file uploaded", 400
        file = request.files['file']

        if file.filename == '':
            return "No selected file", 400

        # 保存上传的图片
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 重定向至修改页面
        return redirect(url_for('edit_options', filename=filename))

    return render_template('combine_upload.html')


@app.route('/edit/<filename>', methods=['GET', 'POST'])
def edit_options(filename):
    """
    修改页面：文字修改与颜色修改
    """
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    # 提取图片中的文字及其位置信息
    text_boxes = extract_text_and_boxes(filepath)

    if request.method == 'POST':
        # 获取用户输入的文字修改选项
        original_text = request.form.get('original_text', '').strip()
        replacement_text = request.form.get('replacement_text', '').strip()

        # 获取用户输入的颜色修改选项
        target_color = request.form.get('target_color', '').strip()
        replacement_color = request.form.get('replacement_color', '').strip()

        # 执行文字修改
        output_filepath = os.path.join(app.config['OUTPUT_FOLDER'], filename)
        if original_text and replacement_text:
            replace_text_in_image(filepath, original_text, replacement_text, output_filepath)
        else:
            # 如果未进行文字修改，直接复制原文件到输出路径
            os.system(f'cp "{filepath}" "{output_filepath}"')

        # 执行颜色修改
        result_filepath = os.path.join(app.config['RESULT_FOLDER'], f"result_{filename}")
        if target_color and replacement_color:
            replace_line_color(output_filepath, target_color, replacement_color, result_filepath)
        else:
            # 如果未进行颜色修改，直接复制文字修改后的文件到结果路径
            os.system(f'cp "{output_filepath}" "{result_filepath}"')

        # 重定向至结果页面
        return redirect(url_for('result', filename=f"result_{filename}"))

    return render_template('combine_edit_options.html', filename=filename, text_boxes=text_boxes)


@app.route('/result/<filename>')
def result(filename):
    """
    显示最终修改后的图片
    """
    return render_template('combine_result.html', result_image=filename)


@app.route('/uploads/<filename>')
def serve_upload(filename):
    """
    提供上传图片的访问路径
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/outputs/<filename>')
def serve_output(filename):
    """
    提供文字修改后图片的访问路径
    """
    return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


@app.route('/results/<filename>')
def serve_result(filename):
    """
    提供最终修改后图片的访问路径
    """
    return send_from_directory(app.config['RESULT_FOLDER'], filename)


@app.route('/download/<filename>')
def download_image(filename):
    """
    下载修改后的图片
    """
    result_filepath = os.path.join(app.config['RESULT_FOLDER'], filename)
    return send_file(result_filepath, mimetype='image/png', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)