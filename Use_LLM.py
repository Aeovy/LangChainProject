from model import LLM_Model
from langchain_tools import tools, tools_dict
if __name__ == "__main__":
   LLM=LLM_Model(model_type="openai",temperature=0.6,tools=tools,tools_dict=tools_dict)
   conversion_id=input("请输入会话ID:")
   while True:
    qurey=input("Human:")
    print("\n")
    if qurey.lower()=="exit":
        break
    else:
        print("AI:",end="")
        LLM.chat_sync(qurey,conversion_id)
        print("\n")