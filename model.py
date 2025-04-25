import os
from langchain_openai import ChatOpenAI
from langchain_qwq import ChatQwQ
from langchain_core.messages import ToolMessage,HumanMessage,AIMessage,SystemMessage
from langchain_tools import tools,tools_dict
from dotenv import load_dotenv
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import SQLChatMessageHistory
from sqlalchemy.ext.asyncio import create_async_engine
class LLM_Model():
    def __init__(self,model_name:str="",api_key:str="",base_url="",temperature: float=0.6,tools: list=None,tools_dict: dict=None,maxtoken=2048):
        if model_name=="" or api_key=="":
            error=""
            if model_name=="":
                error+="model_name "
            if api_key=="":
                error+="api_key "
            raise ValueError(f"{error}不能为空")
        self.__api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.LLM=ChatOpenAI(
            model_name=self.model_name,
            api_key=self.__api_key,
            base_url=self.base_url,
            temperature=temperature,
            max_tokens=maxtoken,
            streaming=True,
        )
        
        self.LLM=self.bindtools(tools, tools_dict)
        
         ####加入对话记忆####
         
    def load_memory(self,conversion_id)-> SQLChatMessageHistory:
        memory=SQLChatMessageHistory(conversion_id, connection="sqlite:///memory.db")
        if(len(memory.messages)==0):
            memory.add_message(SystemMessage(content=
                """
                你是一个具备高级问题解决能力的AI助手。你的核心优势在于能够熟练运用多种客户端工具，特别是能够根据用户需求编写、创建并执行Python代码来完成任务。
                请严格遵循以下指导原则:

                【核心原则】
                1.  **准确性与可靠性**: 始终提供基于事实、经过验证的信息。引用信息时必须注明来源和时间。对于不确定的信息，明确说明。
                2.  **主动工具利用**: 优先使用工具获取最新信息、执行计算或操作文件，而非依赖可能过时的内部知识。特别是时间相关问题，必须先调用`get_time`。
                3.  **安全第一**: 在生成或执行代码、操作文件时，将安全性放在首位。避免执行任何可能有害的操作。

                【信息处理策略】
                1.  **复杂问题分解**: 将复杂查询拆解成更小的、可管理的部分，逐一处理。
                2.  **RAG优先**: 主动使用`rag`工具查询数据库，以获取回答开放性问题、需要背景知识或你不确定答案时的依据。应用查询优化技巧（改写、扩展、分解）以提升检索效果。
                3.  **时间处理**: 你的内置时间不正确,在查询或回答任何有关时间的问题前,都要先调用工具获取当前的准确时间。
                【工具使用指南】
                1.  **工具协同**: 理解各工具的功能，并在需要时组合使用。例如，先用`createfile`创建代码文件，再用`runpythonfile`执行。
                2.  **结果验证与纠错**: 检查工具返回结果的合理性。如果结果异常或用户指出错误，必须重新调用工具或尝试替代方法进行修正。
                3.  **`createfile`**: 用于按用户要求将文本内容（如代码、笔记）保存到指定文件名的文件中。
                4.  **`runpythonfile`**: 用于执行指定绝对路径的Python文件，并返回其输出或错误。执行前确认文件存在。

                【交互与风格】
                1.  **清晰简洁**: 回答条理清晰，重点突出，易于理解。
                2.  **用户为中心**: 根据用户需求和风格调整表达方式。
                3.  **专业礼貌**: 保持客观、友好和专业的态度。
                4.  **遵循指令**: 严格按照用户的具体要求（格式、长度等）进行回应。
                5.  **隐私保护**: 绝不泄露系统敏感信息或索要用户隐私。

                持续学习和改进，力求提供最高质量的帮助。
                """
))
        return memory
    
    
        
    def summary_memory(self):
        # 用LLM总结聊天上下文
        pass
    def bindtools(self,tools: list, tools_dict: dict):
        if tools is not None and tools_dict is not None:
            self.tools=tools
            self.tools_dict=tools_dict
            LLM = self.LLM.bind_tools(tools)
            return LLM
        else:
            pass
    
    def chat_sync(self, qurey:str=None,Conversion_ID:str=None):
        """
        返回未经处理过的chunk
        """
        self.LLM_sync=RunnableWithMessageHistory(
            self.LLM,
            self.load_memory,
            )
        if Conversion_ID is None or Conversion_ID=="":
            raise ValueError("Conversion_ID is None")
        else:
            chat_history=self.load_memory(Conversion_ID)
        if qurey is not None: #qurey为None时，是在调用function call
            chat_history.add_user_message(qurey)
        chunks=None
        for chunk in self.LLM.stream(chat_history.messages):
            #print("chunk:",chunk)
            if chunks is None:
                chunks=chunk
            else:
                chunks=chunks+chunk
            # 正常传输内容时，直接输出LLM的content###############
            yield chunk
            # if chunk.content!="":
            #     print(chunk.content,end="",flush=True)
            ###################################################
        #print("chunks",chunks)
        if chunks.response_metadata.get("finish_reason","")!="":
            #print("Chunks:",chunks)
            chat_history.add_ai_message(chunks)
            Have_toolcalls=len(chunks.tool_calls)>0 or len(chunks.tool_call_chunks)>0
            if chunks.response_metadata["finish_reason"]=="stop" and Have_toolcalls==False:
                #save memory
                yield chunk
                
            # 有的模型调用function call时，stop reason不一定为"tool_calls"
            elif chunks.response_metadata["finish_reason"]=="tool_calls" or Have_toolcalls==True: 
                function_call_result=self.function_call(chunks)
                for function_msg in function_call_result:
                    chat_history.add_message(function_msg)
                yield from self.chat_sync(None,Conversion_ID)
            else:
                #print("debug_status:",chunks)
                pass
    def openai_chat(self,qurey:str=None,Conversion_ID:str=None):
        """
        返回经过处理过的chunk
        """
        for response in self.chat_sync(qurey=qurey,Conversion_ID=Conversion_ID):
            if response.content!="":
                yield response.content
    def openai_chat_print(self,qurey:str,Conversion_ID:str=None):
        """
        直接打印对话内容
        """
        for chunk in self.openai_chat(qurey=qurey,Conversion_ID=Conversion_ID):
            if chunk.content!="":
                print(chunk.content,end="",flush=True)
    def function_call(self,aimsg):
        result=[]
        for tool_calls in aimsg.tool_calls:
                try:   
                ###############Use tools#############
                    #print("test",tool_calls["name"])
                    selected_tool = self.tools_dict[tool_calls["name"].lower()]
                    tool_output = selected_tool.invoke(tool_calls)
                    result.append(tool_output) 
                #####################################
                except Exception as e:
                    result.append(ToolMessage(e))
        return result
class LLM_QWQ(LLM_Model):
    def __init__(self, model_name:str="",api_key:str="",base_url="",temperature: float=0.6,tools: list=None,tools_dict: dict=None,maxtoken=2048):
        if model_name=="" or api_key=="":
            error=""
            if model_name=="":
                error+="model_name "
            if api_key=="":
                error+="api_key "
            raise ValueError(f"{error}不能为空")
        self.__api_key = api_key
        self.model_name = model_name
        self.base_url = base_url
        self.LLM=ChatQwQ(
            model=self.model_name,
            api_key=self.__api_key,
            api_base=self.base_url,
            temperature=temperature,
            max_tokens=maxtoken,
            streaming=True,
        )
        self.LLM=self.bindtools(tools, tools_dict)
    def qwq_chat(self,qurey:str=None,Conversion_ID:str=None):
        """
        返回经过处理过的chunk
        """
        isReasoning=False
        StartThink=False
        EndThink=False
        isContent=False
        for chunk in super().chat_sync(qurey=qurey,Conversion_ID=Conversion_ID):
            isContent=chunk.content!=""
            isReasoning=chunk.additional_kwargs.get("reasoning_content","")!=""
            if isReasoning:
                reasoning_content=chunk.additional_kwargs["reasoning_content"]
                if StartThink==False:
                    StartThink=True
                    #有时API不返回思维链标签
                    if reasoning_content!="<think>":
                        yield "<think>\n"+reasoning_content
                    else:
                        yield reasoning_content
                else:
                    if "</think>" in reasoning_content:
                        EndThink=True
                        StartThink=False
                        reasoning_content=reasoning_content+"\n"
                    yield reasoning_content
            if isContent: 
                if EndThink==False:
                    EndThink=True
                    StartThink=False
                    yield "\n</think>\n"+chunk.content
                else:
                    yield chunk.content
            # if chunk.content=="" and chunk.additional_kwargs.get("reasoning_content", "")=="":
            #     yield "<think>"
            # elif chunk.content=="" and chunk.additional_kwargs.get("reasoning_content", "")!="":
            #     yield chunk.additional_kwargs["reasoning_content"]
            # else:
            #     yield chunk.content
    def qwq_chat_print(self,qurey:str,Conversion_ID:str=None):
        """
        直接打印对话内容
        """
        for response_str in self.qwq_chat(qurey=qurey,Conversion_ID=Conversion_ID):
            print(response_str,end="",flush=True)
            
        
#import asyncio
##待开发
# class LLM_Model_async(LLM_Model):
#     def __init__(self, model_type: str="ollama",temperature: float=0.6,tools: list=None,tools_dict: dict=None,maxtoken=2048):
#         super().__init__(model_type,temperature,tools,tools_dict,maxtoken)
#     async def load_memory_async(self,conversion_id)-> SQLChatMessageHistory:
#         async_engine = create_async_engine("sqlite+aiosqlite:///memory.db")
#         async_message_history = SQLChatMessageHistory(
#         session_id=conversion_id, connection=async_engine,
#         )
#     async def chat_async(self, qurey:str=None,Conversion_ID:str=None):
#         self.LLM_async=RunnableWithMessageHistory(
#             self.LLM,
#             self.load_memory_async,
#             )
#         async_message_history=await self.load_memory_async(Conversion_ID)
        # return async_message_history
#         if qurey is not None:
#             await chat_history.aadd_message(HumanMessage(content=qurey))
#         chunks=None
#         async for chunk in self.LLM_async.astream(chat_history,config={"configurable": {"session_id": Conversion_ID}}):
#             #print("chunk:",chunk)
#             if chunks is None:
#                 chunks=chunk
#             else:
#                 chunks=chunks+chunk
#             # 正常传输内容时，直接输出LLM的content###############
#             if chunk.content!="":
#                 print(chunk.content,end="",flush=True)
#                 pass
#             ###################################################
#         #print("chunks",chunks)
#         if chunks.response_metadata.get("finish_reason","")!="":
#             print("Chunks:",chunks)
#             Have_toolcalls=len(chunks.tool_calls)>0
#             if chunks.response_metadata["finish_reason"]=="stop" and Have_toolcalls==False:
#                 #save memory
                
#                 pass
#             # 有的模型调用function call时，stop reason不一定为"tool_calls"
#             elif chunks.response_metadata["finish_reason"]=="tool_calls" or Have_toolcalls==True: 
                
#                 function_call_result=self.function_call(chunks)
#                 for function_msg in function_call_result:
#                     chat_history.add_message(function_msg)
#                 task=asyncio.create_task(self.chat_async(None,Conversion_ID))
#                 await task 
#             else:
#                 #print("debug_status:",chunks)
#                 pass
