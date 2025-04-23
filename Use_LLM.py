from model import LLM_Model,LLM_QWQ
from langchain_tools import tools, tools_dict
import os
from dotenv import load_dotenv
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
if __name__ == "__main__":
   commands = WordCompleter(["exit","clear"])
   #LLM=LLM_Model(model_type="openai",temperature=0.6,tools=tools,tools_dict=tools_dict)
   load_dotenv()
   LLM=LLM_QWQ(model_name=os.getenv("OPENAI_MODEL_NAME"),api_key=os.getenv("OPENAI_API_KEY"),
               base_url=os.getenv("OPENAI_BASE_URL"),temperature=0.6,maxtoken=8192,
               tools=tools,tools_dict=tools_dict)
   conversion_id=input("请输入会话ID:")
   
   while True:
    qurey=prompt("Human:",
                 multiline=True,
                 completer=commands,
                 complete_while_typing=True,
                 )
    print("\n")
    if qurey.lower()=="exit":
        break
    elif qurey.lower()=="clear":
        # 清空终端
        os.system('cls' if os.name == 'nt' else 'clear')
    else:
        print("AI:")
        # LLM.qwq_chat_print(qurey=qurey,Conversion_ID=conversion_id)
        for msg in LLM.qwq_chat(qurey=qurey,Conversion_ID=conversion_id):
            print(msg,end="",flush=True)
        print("\n")