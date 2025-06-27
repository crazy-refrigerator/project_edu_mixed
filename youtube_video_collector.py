import os
import requests

# 设置你的 YouTube Data API v3 的 API 密钥
API_KEY = 'YOUR_YOUTUBE_API_KEY'
YOUTUBE_API_URL = 'https://www.googleapis.com/youtube/v3/search'

def search_youtube_videos(query, max_results=10):
    """
    调用 YouTube Data API v3 搜索视频
    :param query: 用户搜索的关键字
    :param max_results: 返回结果的最大数量
    :return: 包含视频信息的字典列表
    """
    params = {
        'part': 'snippet',
        'q': query,
        'type': 'video',
        'maxResults': max_results,
        'key': "AIzaSyB9xG-u-XeiiNMvKoCEdbs03x6JjuDuhkk"
    }

    response = requests.get(YOUTUBE_API_URL, params=params)
    if response.status_code == 200:
        results = []
        data = response.json()
        for item in data.get('items', []):
            video_id = item['id']['videoId']
            title = item['snippet']['title']
            thumbnail_url = item['snippet']['thumbnails']['default']['url']
            video_url = f'https://www.youtube.com/watch?v={video_id}'
            results.append({
                'title': title,
                'thumbnail_url': thumbnail_url,
                'video_url': video_url
            })
        return results
    else:
        print(f"Error: Unable to fetch data from YouTube API. Status Code: {response.status_code}")
        return []