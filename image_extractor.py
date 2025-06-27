import os
from flask import Flask, render_template, request
from werkzeug.utils import secure_filename
from pdf_image_extract import process_pdf_with_regex
from ppt_image_extract import extract_images_from_pptx

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['EXTRACTED_FOLDER'] = 'static/extracted_images'  # 图片保存路径
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['EXTRACTED_FOLDER'], exist_ok=True)


def parse_page_input(pages_input):
    """解析页码范围输入，返回页码列表"""
    if not pages_input:
        return None

    pages = set()
    for part in pages_input.split(','):
        part = part.strip()
        if '-' in part:
            start, end = map(int, part.split('-'))
            pages.update(range(start, end + 1))
        else:
            pages.add(int(part))

    return sorted(pages)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        file = request.files.get('file')
        pages_input = request.form.get('pages', '').strip()

        if not file or not (file.filename.endswith('.pdf') or file.filename.endswith('.pptx')):
            return render_template('image_extract_index.html', error="Please upload a valid PDF or PPTX file.")

        file_ext = os.path.splitext(file.filename)[1].lower()
        unique_id = os.path.splitext(file.filename)[0]
        upload_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_id)
        os.makedirs(upload_path, exist_ok=True)
        file_path = os.path.join(upload_path, secure_filename(file.filename))
        file.save(file_path)

        output_dir = app.config['EXTRACTED_FOLDER']
        results = []

        try:
            if file_ext == '.pdf':
                target_pages = parse_page_input(pages_input)
                results = process_pdf_with_regex(file_path, output_dir, target_pages)
            elif file_ext == '.pptx':
                target_slides = parse_page_input(pages_input)  # 使用与 PDF 相同的解析逻辑
                results = extract_images_from_pptx(file_path, output_dir, target_slides)
        except Exception as e:
            return render_template('image_extract_index.html', error=str(e))

        return render_template('image_extract_result.html', results=results)

    return render_template('image_extract_index.html')


if __name__ == '__main__':
    app.run(debug=True)