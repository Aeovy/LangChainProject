from model import LLM_Model,LLM_QWQ
from langchain_tools import tools, tools_dict
import os
from dotenv import load_dotenv
if __name__ == "__main__":
   #LLM=LLM_Model(model_type="openai",temperature=0.6,tools=tools,tools_dict=tools_dict)
   load_dotenv()
   LLM=LLM_QWQ(model_name=os.getenv("OPENAI_MODEL_NAME"),api_key=os.getenv("OPENAI_API_KEY"),
               base_url=os.getenv("OPENAI_BASE_URL"),temperature=0.6,maxtoken=8192,
               tools=tools,tools_dict=tools_dict)
   conversion_id=input("请输入会话ID:")
   while True:
    qurey=input("Human:")
    print("\n")
    if qurey.lower()=="exit":
        break
    else:
        LLM.qwq_chat_print(qurey=qurey,Conversion_ID=conversion_id)
        
        print("\n")