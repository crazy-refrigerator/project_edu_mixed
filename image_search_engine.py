import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify
from google_image_collector import search_images
import json
from utils import allowed_file

app = Flask(__name__)
app.config['EXTRACTED_FOLDER'] = 'extracted_images'

# 确保目录存在
os.makedirs(app.config['EXTRACTED_FOLDER'], exist_ok=True)

# Google API 配置
GOOGLE_API_KEY = "AIzaSyB9xG-u-XeiiNMvKoCEdbs03x6JjuDuhkk"  # 替换为你的 Google API 密钥
GOOGLE_CX = "2267132ab0d5a4c95"  # 替换为你的 Google 自定义搜索引擎 ID

@app.route('/image_search_engine', methods=['GET', 'POST'])
def image_search_engine():
    """图片搜索引擎页面"""
    if request.method == 'POST':
        query = request.form.get('query', '')
        image_count = int(request.form.get('image_count', 5))
        if not query:
            return render_template('image_search_engine.html', error='请输入搜索关键词')

        try:
            # 调用 Google 图片搜索 API
            search_results = search_images(query, GOOGLE_API_KEY, GOOGLE_CX, count=image_count)
        except Exception as e:
            return render_template('image_search_engine.html', error=str(e))

        # 保存搜索结果
        unique_id = str(uuid.uuid4())
        os.makedirs(os.path.join(app.config['EXTRACTED_FOLDER'], unique_id), exist_ok=True)
        metadata_path = os.path.join(app.config['EXTRACTED_FOLDER'], unique_id, "search_metadata.json")
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(search_results, f, ensure_ascii=False, indent=2)

        return redirect(url_for('search_results', unique_id=unique_id))

    return render_template('image_search_engine.html')


@app.route('/search_results/<unique_id>')
def search_results(unique_id):
    """搜索结果页面"""
    extracted_dir = os.path.join(app.config['EXTRACTED_FOLDER'], unique_id)
    metadata_path = os.path.join(extracted_dir, "search_metadata.json")

    # 读取元数据
    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            search_results = json.load(f)
    except:
        search_results = {}

    return render_template('search_results.html', search_results=search_results, unique_id=unique_id)


if __name__ == '__main__':
    app.run(debug=True)