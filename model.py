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
            memory.add_message(SystemMessage(content="""你是一个专业且乐于助人的AI助手。请遵循以下指导原则：

        1. 回答准确性：提供客观、准确的信息来回答用户问题。
        2. 时间处理：你的内置系统时间可能不准确。对于任何涉及当前日期、时间或有时效性的查询，必须先使用时间工具获取准确时间。
        3. 信息查找：当你不确定答案时，应主动使用搜索工具查找信息。
        4. 诚实应对：如果搜索结果无法解答用户问题或与问题无关，请明确说明："我无法回答这个问题。我已使用[工具名称]搜索，但未能找到相关答案。"
        5. 工具使用：根据需要合理使用可用工具，在需要具体数据、最新信息或专业知识时优先考虑工具调用。
        6. 回答风格：保持回答简洁、条理清晰，必要时使用项目符号或分段增强可读性。

        请始终保持礼貌和专业，避免臆测信息。""" ))
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
                
                pass
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
            if isReasoning and chunk.additional_kwargs.get("reasoning_content","")!="<think>":
                if StartThink==False:
                    StartThink=True
                    yield "<think>\n"+chunk.additional_kwargs["reasoning_content"]
                else:
                    yield chunk.additional_kwargs["reasoning_content"]
            if isContent: 
                if EndThink==False and chunk.additional_kwargs.get("reasoning_content","")!="<think>":
                    EndThink=True
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
