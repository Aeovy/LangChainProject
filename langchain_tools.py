from langchain_core.tools import tool
import time 
import sys
import inspect
import ast
from RAG.RAG import MyVectordb
import os
from typing import Any, Union
import bilibili_api
from bilibili_api import sync
from bilibili_api.search import SearchObjectType
import Functions.Functions as Functions
from Functions.AgentCoding import CodeAgent

@tool
def createfile(content:str,filename:str)->Union[dict[str,str], Exception]:
    """
    功能:创建文件并写入内容。
    成功时返回创建完成的文件的绝对路径。
    失败时返回异常信息。
    写入代码时,不推荐写入阻塞代码。
    参数:
        content: 要写入文件的内容
        filename: 文件名(包含扩展名)
    """
    result=CodeAgent.CreateFile(code=content,filename=filename)
    return result
@tool
def runpythonfile(PythonFilePath:str)->Union[str, Exception]:
    """
    功能:运行指定的Python文件。
    可以获得代码中print输出的结果。
    参数:
        PythonFilePath: 要运行的Python文件的绝对路径
    返回:
        str: 运行结果或错误信息
    """
    result=CodeAgent.RunPython(PythonFilePath=PythonFilePath)
    return result
@tool
def get_time(format_type: str = "default") -> str:
    """
    时间工具,返回当前系统时间(支持多种格式)。
    参数:
        format_type: 指定返回时间格式，支持以下选项：
            - "default": 标准格式 (YYYY-MM-DD HH:MM:SS)
            - "date": 仅返回日期 (YYYY-MM-DD)
            - "time": 仅返回时间 (HH:MM:SS)
            - "full": 完整格式，包含星期 (YYYY-MM-DD HH:MM:SS 星期X)

    返回值:
        str: 按指定格式返回当前系统时间的字符串
    """
    now = time.time()
    local_time = time.localtime(now)
    
    if format_type.lower() == "date":
        return time.strftime("%Y-%m-%d", local_time)
    elif format_type.lower() == "time":
        return time.strftime("%H:%M:%S", local_time)
    elif format_type.lower() == "full":
        weekday = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"][local_time.tm_wday]
        basic = time.strftime("%Y-%m-%d %H:%M:%S", local_time)
        return f"{basic} {weekday}"
    else:  # default
        return time.strftime("%Y-%m-%d %H:%M:%S", local_time)
@tool
def search_bilibili(keyword: str,content_type:str,content_categorie:str=None,time_start:str=None,time_end:str=None,result_num:int=20)-> dict :
    """
    当用户需要在Bilibili(B站，哔哩哔哩)上搜索时，可以使用此工具。
    content_type参数用于指定要搜索的内容的类型，可选值包括：
    ["视频","番剧","影视"  "直播","专栏","话题","用户","直播间用户"],默认为"视频"。
    content_categorie参数用于指定内容的分类，可选值包括：
    ["番剧", "电影", "国创", "电视剧", "综艺", "纪录片", "动画",
    "游戏", "鬼畜", "音乐", "舞蹈", "影视", "娱乐", "知识","科技数码", 
    "资讯", "美食", "小剧场", "汽车", "时尚美妆","体育运动"]。
    如果不指定类型，则搜索所有类型的视频。
    time_start参数用于指定搜索的内容的时间范围的起始时间，time_end参数用则用于指定结束时间，格式为："YYYY-MM-DD"。
    result_num参数用于指定返回结果的数量，默认为20。
    """
    #get content_categories_id
    content_categorie_id=None
    content_categories=["番剧", "电影", "国创", "电视剧", "综艺", "纪录片", "动画", 
                        "游戏", "鬼畜", "音乐", "舞蹈", "影视", "娱乐", "知识", 
                        "科技数码", "资讯", "美食", "小剧场", "汽车", "时尚美妆",
                        "体育运动"]
    if content_categorie in content_categories:
        content_categorie_id = bilibili_api.video_zone.get_zone_info_by_name(content_categorie)[0]["tid"]
    #get content_type
    types_map={
        "视频":SearchObjectType.VIDEO,
        "番剧":SearchObjectType.BANGUMI,
        "影视":SearchObjectType.FT,
        "直播":SearchObjectType.LIVE,
        "专栏":SearchObjectType.ARTICLE,
        "话题":SearchObjectType.TOPIC,
        "用户":SearchObjectType.USER,
        "直播间用户":SearchObjectType.LIVEUSER
    }
    content_type=types_map.get(content_type,SearchObjectType.VIDEO)
    #验证时间合法性
    time_start=Functions.validate_date_format(time_start)
    time_end=Functions.validate_date_format(time_end)
    
    try:
        API_result=sync(bilibili_api.search.search_by_type(keyword=keyword,search_type=content_type,
                                                    video_zone_type=content_categorie_id,
                                                    time_start=time_start,
                                                    time_end=time_end,
                                                    ))
        API_result=API_result["result"]
        return_result=[]
        for item in API_result[:result_num]:
            return_result.append(Functions.extract_bilibili_video_info(item))
        return return_result
    except Exception as e:
        e="出错了:"+str(e)
        return e
@tool
def rag(query:str,k:int=3)->list[dict[str,str]]:
    """当用户提出RAG需求(或数据库内搜索要求)、开放性问题或不确定答案是否在知识库中时,请使用此工具搜索相关知识。
    ⚠️检索前优化非常关键，为提高检索质量，请务必应用以下策略：

    1. 查询改写(Query Rewriting):
       - 将用户口语化、含糊的问题改写成更正式、精确的表述
       - 例如:"关于去年最热门的AI技术"→"2024年人工智能领域最受关注的技术进展"

    2. 查询扩展(Query Expansion):
       - 生成多个语义相关的查询词，覆盖不同角度
       - 例如:"太阳能电池效率"→同时查询"光伏电池转换效率"、"高效太阳能电池材料"

    3. 查询分解(Query Decomposition):
       - 将复杂问题拆解为多个子问题，逐一查询
       - 例如:"如何在紧张工作中保持身心健康"→分解为"工作压力管理技巧"+"工作环境中的运动方法"+"职场心理健康维护"

    使用说明：
    - 遇到复杂问题时，先进行分解，再对每个子问题应用查询改写和扩展
    - 对每个优化后的查询进行单独检索，可能需要多次调用此工具
    - 最后汇总不同查询的结果，形成全面回答
    - 参数说明：
        query: 要查询的关键词（字符串）
        k: 返回结果数量,默认为3(可根据问题范围进行调整）

    若多次尝试后仍未检索到有效信息，请如实告知用户："数据库中未找到相关内容"。

    返回结果：
        list[dict[str, str]] —— 每个字典格式为：
        {
            "content": "文档内容",
            "source": "文档来源"
        }
    """
    try:
        docs=MyVectordb.qurey_vector_db(query,k)
    except Exception as e:
        return e
    result=[]
    for doc in docs:
        temp={
            "content":doc.page_content,
            "source":f"{os.path.basename(doc.metadata.get('source','unknown'))},第{doc.metadata.get('page', 'unknown')}页",
        }
        result.append(temp)
    if len(result)==0:
        return "数据库中没有相关信息"
    else:
        return result



def parse_tools_from_source(module):
    source = inspect.getsource(module)
    tree = ast.parse(source)
    tools = []
    tools_dict = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for decorator in node.decorator_list:
                decorator_name = None
                if isinstance(decorator, ast.Name):
                    decorator_name = decorator.id
                elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name):
                    decorator_name = decorator.func.id
                if decorator_name == "tool":
                    func_name = node.name
                    func = getattr(module, func_name)
                    tools.append(func)
                    tools_dict[func_name] = func
    return tools, tools_dict

current_module = sys.modules[__name__]
tools, tools_dict = parse_tools_from_source(current_module)




