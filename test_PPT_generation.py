from flask import Flask, render_template, request, send_file, flash, redirect
from werkzeug.utils import secure_filename
import os

# 导入现有的模板文件
from templates.ppt_template.template1 import create_custom_slide  # 模板 3
from templates.ppt_template.title_template import create_title_slide  # 模板 4
from templates.ppt_template.template2 import create_text_above_image_slide  # 模板 2
from templates.ppt_template.template3 import create_full_text_slide  # 模板 1

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # 用于闪存消息

# 配置路径
UPLOAD_FOLDER = 'static/uploads'
OUTPUT_FOLDER = 'static/outputs'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # 获取用户选择的模板类型
        template_type = request.form.get('template_type')

        # 获取用户输入内容
        slide_title = request.form.get('slide_title', '').strip()
        slide_text = request.form.get('slide_text', '').strip()
        image_title = request.form.get('image_title', '').strip()

        # 保存上传的图片
        uploaded_image = request.files.get('image')
        image_path = None
        if uploaded_image and uploaded_image.filename != '':
            image_filename = secure_filename(uploaded_image.filename)
            image_path = os.path.join(UPLOAD_FOLDER, image_filename)
            uploaded_image.save(image_path)

        # 校验输入内容
        if template_type == 'template1':  # 模板 1：需要标题和正文
            if not slide_title or not slide_text:
                flash("模板 1 需要标题和正文内容！")
                return redirect('/')
        elif template_type in ['template2', 'template3']:  # 模板 2 和 3：需要标题、正文、图片和图片标题
            if not slide_title or not slide_text or not image_path or not image_title:
                flash("模板 2 和模板 3 需要标题、正文、图片和图片标题！")
                return redirect('/')
        elif template_type == 'template4':  # 模板 4：只需要标题
            if not slide_title:
                flash("模板 4 需要标题！")
                return redirect('/')

        # 设置输出文件路径
        output_ppt_path = os.path.join(OUTPUT_FOLDER, 'output_slide.pptx')

        # 根据选择的模板调用对应的函数
        if template_type == 'template1':
            create_full_text_slide(output_ppt_path, slide_title, slide_text)
        elif template_type == 'template2':
            create_text_above_image_slide(output_ppt_path, slide_title, slide_text, image_path, image_title)
        elif template_type == 'template3':
            create_custom_slide(output_ppt_path, slide_title, slide_text, image_path, image_title)
        elif template_type == 'template4':
            create_title_slide(output_ppt_path, slide_title)

        # 返回生成的 PPT 文件
        return send_file(output_ppt_path, as_attachment=True)

    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)