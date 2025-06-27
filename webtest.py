import os
import uuid
from flask import Flask, render_template, request, redirect, url_for, jsonify
from google_image_collector import search_images  # 确保 google_image_collector 模块已正确安装
import json
from utils import allowed_file  # 确保 utils.py 文件中有 allowed_file 函数

app = Flask(__name__)

# 配置文件上传和图片存储路径
UPLOAD_FOLDER = 'static/uploads'
EXTRACTED_FOLDER = 'extracted_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['EXTRACTED_FOLDER'] = EXTRACTED_FOLDER

# 确保目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(EXTRACTED_FOLDER, exist_ok=True)

# Google API 配置
GOOGLE_API_KEY = "AIzaSyB9xG-u-XeiiNMvKoCEdbs03x6JjuDuhkk"  # 替换为你的 Google API 密钥
GOOGLE_CX = "2267132ab0d5a4c95"  # 替换为你的 Google 自定义搜索引擎 ID

def allowed_file(filename):
    """检查文件是否为允许的类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def is_title(paragraph):
    """
    判断段落是否为标题：
    - 以数字或数字+小数点开头
    - 不包含完整句子（没有句号）
    - 文本长度较短
    """
    if paragraph[0].isdigit():
        # 检查是否为数字或数字+小数点
        if paragraph.split()[0].replace('.', '', 1).isdigit():
            # 判断是否是标题：长度较短，且不包含句号
            return len(paragraph) <= 50 and '.' not in paragraph[-1]
    return False

def parse_text(text):
    """解析输入文本，将段落分为标题和正文，并在正文段落后插入加号框"""
    blocks = []
    paragraphs = text.split('\n')  # 按换行切分段落
    is_first_title = True  # 标记是否为第一个大标题 `[Title]:`

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        # 处理 `[Title]:` 作为大标题
        if is_first_title and paragraph.startswith('[Title]:'):
            title_content = paragraph.replace('[Title]:', '').strip()
            blocks.append({'type': 'title', 'content': title_content})
            is_first_title = False
            continue

        # 判断是否为标题
        if is_title(paragraph):
            blocks.append({'type': 'title', 'content': paragraph})
        elif '[image]' in paragraph:
            # 处理正文段落中的 `[image]`
            parts = paragraph.split('[image]')
            for part in parts[:-1]:
                if part.strip():
                    blocks.append({'type': 'text', 'content': part.strip()})
                    blocks.append({'type': 'add-button', 'content': ''})  # 插入加号框
                blocks.append({'type': 'image', 'content': ''})  # 插入图片框
            if parts[-1].strip():
                blocks.append({'type': 'text', 'content': parts[-1].strip()})
                blocks.append({'type': 'add-button', 'content': ''})  # 插入加号框
        else:
            # 普通正文段落
            blocks.append({'type': 'text', 'content': paragraph})
            blocks.append({'type': 'add-button', 'content': ''})  # 在正文段落后插入加号框

    return blocks

@app.route('/', methods=['GET', 'POST'])
def index():
    """输入页面"""
    if request.method == 'POST':
        text = request.form['text']
        return render_template('step2.html', blocks=parse_text(text))
    return render_template('step1.html')

@app.route('/update_image', methods=['POST'])
@app.route('/update_image', methods=['POST'])
def update_image():
    """更新解析页面中的图片"""
    data = request.get_json()

    # 验证数据
    image_url = data.get('image_url', '').strip()
    index = data.get('index', None)

    if not image_url or index is None:
        return jsonify({'error': 'Invalid image URL or index'}), 400

    try:
        index = int(index)  # 确保 index 是整数
    except ValueError:
        return jsonify({'error': 'Index must be an integer'}), 400

    blocks = session.get('blocks', [])
    if 0 <= index < len(blocks) and blocks[index]['type'] == 'add-button':
        blocks[index] = {'type': 'image', 'content': image_url}
        blocks.insert(index + 1, {'type': 'add-button', 'content': ''})
        session['blocks'] = blocks

        return jsonify({'message': 'Image updated successfully!'}), 200
    else:
        return jsonify({'error': 'Index out of range or invalid block type'}), 400

@app.route('/editor', methods=['GET'])
def editor():
    """渲染编辑页面"""
    if 'blocks' not in session:
        # 初始化 blocks 数据
        session['blocks'] = [
            {'type': 'text', 'content': '示例文本'},
            {'type': 'add-button', 'content': ''},
        ]
    return render_template('editor.html', blocks=session['blocks'])

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

@app.route('/select_image', methods=['POST'])
def select_image():
    """处理图片选择"""
    data = request.get_json()
    image_url = data.get('image_url', '')

    if not image_url:
        return jsonify({'error': 'No image URL provided'}), 400

    # 在这里可以处理图片地址，例如存储到数据库或直接返回
    # 当前逻辑只是返回成功状态
    return jsonify({'message': 'Image selected successfully!', 'image_url': image_url}), 200

@app.route('/download_image', methods=['POST'])
def download_image():
    """处理图片下载"""
    data = request.get_json()
    image_url = data.get('image_url', '')
    index = int(data.get('index', -1))  # 获取加号框的索引

    if not image_url or index == -1:
        return jsonify({'error': 'Invalid image URL or index'}), 400

    try:
        # 下载图片
        response = requests.get(image_url, stream=True)
        if response.status_code == 200:
            # 保存图片到服务器
            filename = os.path.join(IMAGE_FOLDER, os.path.basename(image_url))
            with open(filename, 'wb') as f:
                for chunk in response.iter_content(1024):
                    f.write(chunk)

            # 更新会话中的 blocks
            blocks = session.get('blocks', [])
            if 0 <= index < len(blocks) and blocks[index]['type'] == 'add-button':
                # 替换加号框为图片
                blocks[index] = {'type': 'image', 'content': filename}
                # 在图片后添加新的加号框
                blocks.insert(index + 1, {'type': 'add-button', 'content': ''})
                session['blocks'] = blocks

            return jsonify({'redirect_url': url_for('editor')})
        else:
            return jsonify({'error': 'Failed to download image from URL'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)