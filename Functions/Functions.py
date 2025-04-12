from datetime import datetime
from typing import Dict, Any, List
def validate_date_format(date_string):
    """验证日期是否符合YYYY-MM-DD格式并返回有效的日期字符串或None"""
    if not date_string:
        return None
        
    try:
        # 尝试解析日期，验证格式和有效性
        parsed_date = datetime.strptime(date_string, "%Y-%m-%d")
        # 再次格式化以确保格式一致
        return parsed_date.strftime("%Y-%m-%d")
    except ValueError:
        try:
            # 如果包含时分秒，解析后只返回日期部分
            parsed_date = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            return parsed_date.strftime("%Y-%m-%d")
        except ValueError:
            # 日期格式无效时返回None
            return None
def extract_bilibili_video_info(video_dict: Dict[str, Any]) -> Dict[str, Any]:
    """从B站API返回的视频字典中提取有意义的信息
    
    Args:
        video_dict: B站API返回的视频信息字典
        
    Returns:
        包含关键信息的精简字典
    """
    # 时间戳转换为可读格式
    pubdate = datetime.fromtimestamp(video_dict.get('pubdate', 0)).strftime('%Y-%m-%d %H:%M:%S')
    
    # 构建视频完整URL
    video_url = f"https://www.bilibili.com/video/{video_dict.get('bvid', '')}"
    
    # 构建作者主页URL
    author_url = f"https://space.bilibili.com/{video_dict.get('mid', '')}"
    
    # 处理视频封面URL
    pic_url = video_dict.get('pic', '')
    if pic_url and pic_url.startswith('//'):
        pic_url = f"https:{pic_url}"
    
    # 提取关键信息
    extracted_info = {
        "标题": video_dict.get('title', '').replace('<em class="keyword">', '').replace('</em>', ''),
        "BV号": video_dict.get('bvid', ''),
        "视频链接": video_url,
        "作者": video_dict.get('author', ''),
        "作者主页": author_url,
        "分区": video_dict.get('typename', ''),
        "描述": video_dict.get('description', ''),
        "时长": video_dict.get('duration', ''),
        "发布时间": pubdate,
        "播放量": video_dict.get('play', 0),
        "点赞数": video_dict.get('like', 0),
        "弹幕数": video_dict.get('danmaku', 0),
        "评论数": video_dict.get('review', 0),
        "收藏数": video_dict.get('favorites', 0),
        "标签": video_dict.get('tag', '').split(',')
    }
    
    return extracted_info