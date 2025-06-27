import requests

def search_images(query, api_key, cx, count=5):
    """
    使用 Google Custom Search JSON API 搜索图片。

    :param query: 搜索关键词
    :param api_key: Google API 密钥
    :param cx: 自定义搜索引擎 ID
    :param count: 返回的图片数量
    :return: 图片搜索结果列表
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "cx": cx,
        "key": api_key,
        "searchType": "image",
        "num": count,
    }

    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        results = []
        for item in data.get("items", []):
            results.append({
                "title": item.get("title"),
                "link": item.get("link"),
                "thumbnail": item.get("image", {}).get("thumbnailLink"),
                "contextLink": item.get("image", {}).get("contextLink")
            })
        return results
    else:
        raise Exception(f"Google API 请求失败: {response.status_code}, {response.text}")