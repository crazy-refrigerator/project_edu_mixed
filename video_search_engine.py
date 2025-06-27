from flask import Flask, request, render_template, redirect, url_for
from youtube_video_collector import search_youtube_videos

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('video_search_engine.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '')
    if query:
        results = search_youtube_videos(query)
        return render_template('video_search_results.html', query=query, results=results)
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)