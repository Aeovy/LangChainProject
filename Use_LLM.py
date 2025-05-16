from model import LLM_Base,LLM_QWQ,LLM_Qwen3
from langchain_tools import tools, tools_dict
import os
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
if __name__ == "__main__":
   commands = WordCompleter(["exit","clear","enable_thinking","disable_thinking"],ignore_case=True)
   #LLM=LLM_Model(model_type="openai",temperature=0.6,tools=tools,tools_dict=tools_dict)
   load_dotenv()
   LLM=LLM_Qwen3(model_name=os.getenv("OPENAI_MODEL_NAME"),api_key=os.getenv("OPENAI_API_KEY"),
               base_url=os.getenv("OPENAI_BASE_URL"),temperature=0.6,maxtoken=8192,
               tools=tools,tools_dict=tools_dict)
#    LLM=LLM_QWQ(model_name=os.getenv("LMSTUDIO_MODEL_NAME"),api_key=os.getenv("LMSTUDIO_API_KEY"),
#                 base_url=os.getenv("LMSTUDIO_BASE_URL"),temperature=0.6,maxtoken=8192,
#                 tools=tools,tools_dict=tools_dict)
   conversion_id=input("请输入会话ID:")
   EnableThinking:bool=True
   while True:
    qurey=prompt("Human:",
                 multiline=True,
                 completer=commands,
                 complete_while_typing=True,
                 )
    #print("\n")
    if qurey.lower()=="exit":
        break
    elif qurey.lower()=="clear":
        # 清空终端
        os.system('cls' if os.name == 'nt' else 'clear')
    elif qurey.lower()=="enable_thinking":
        EnableThinking=True
        print("开启推理模式")
    elif qurey.lower()=="disable_thinking":
        EnableThinking=False
        print("关闭推理模式")
    else:
        print("\nAI:")
        #qurey=f"{'/think' if EnableThinking else '/no_think'} {qurey}"
        # LLM.qwq_chat_print(qurey=qurey,Conversion_ID=conversion_id)
        for msg in LLM.qwen3_chat(query=qurey,Conversion_ID=conversion_id,ThinkingMode=EnableThinking):
           #print(msg,flush=True)
            print(msg,end="",flush=True)
        print("\n")