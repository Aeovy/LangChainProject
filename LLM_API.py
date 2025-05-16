from model import LLM_Base,LLM_QWQ,LLM_Qwen3
from langchain_tools import tools, tools_dict
import os
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
load_dotenv()
# LLM=LLM_Qwen3(model_name=os.getenv("OPENAI_MODEL_NAME"),api_key=os.getenv("OPENAI_API_KEY"),
#             base_url=os.getenv("OPENAI_BASE_URL"),temperature=0.6,maxtoken=8192,
#             tools=tools,tools_dict=tools_dict)
LLM=LLM_Qwen3(model_name=os.getenv("LMSTUDIO_MODEL_NAME"),api_key=os.getenv("LMSTUDIO_API_KEY"),
                base_url=os.getenv("LMSTUDIO_BASE_URL"),temperature=0.6,maxtoken=8192,
                tools=tools,tools_dict=tools_dict)

from pydantic import BaseModel
from fastapi.responses import StreamingResponse
import uvicorn
import random
import json
from fastapi import FastAPI
# 创建FastAPI应用
app = FastAPI()

# 定义请求模型
class RequestData(BaseModel):
    query: str
    conversationId: str

# 创建生成响应的函数
async def generate_responses(data:RequestData, random_number):
    for msg in LLM.qwen3_chat(query=data.query,Conversion_ID=data.conversationId,ThinkingMode=True):
        # 为每个字符生成JSON响应
        response = {
            "id": str(random_number),
            "role": "assistant",
            "content": msg            
        }
        #print(f"生成的响应: {response}")
        yield json.dumps(response) + "\n"

# 创建API端点
@app.post("/api")
async def process_data(data: RequestData):
    # 打印接收到的数据
    print(f"接收到的数据: {data}")
    
    # 生成随机数
    random_number = random.randint(1, 1000)
    
    # 返回流式响应
    return StreamingResponse(
        generate_responses(data, random_number),
        media_type="application/json"
    )
    
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=4865)