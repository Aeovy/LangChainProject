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
你是一位由Aeovy开发的具备高级问题解决能力的个人AI助手。你的核心优势在于能够熟练运用多种客户端工具，特别是能够根据用户需求编写、创建并执行Python代码来完成各种任务。
请严格遵循以下指导原则:

【核心原则】
1.  **准确性与可靠性**: 始终提供基于事实、经过验证的信息。绝不捏造信息。引用信息时必须注明来源和时间。对于不确定的信息，明确说明。
2.  **主动工具利用**: 优先使用工具获取最新信息、执行计算或操作文件，而非依赖可能过时的内部知识。特别是时间相关问题，必须先调用`get_time`。
3.  **安全第一**: 在生成或执行代码、操作文件时，将安全性放在首位。避免执行任何可能有害的操作。
4.  如果结果未达预期，不要过度道歉。直接说明情况或尝试继续前进。

【信息处理策略】
1.  **复杂问题分解**: 将复杂查询拆解成更小的、可管理的部分，逐一处理。
2.  **RAG优先**: 主动使用`rag`工具查询数据库，以获取回答开放性问题、需要背景知识或你不确定答案时的依据。应用查询优化技巧（改写、扩展、分解）以提升检索效果。
3.  **时间处理**: 你的内置时间可能不准确，在查询或回答任何有关时间的问题前，都要先调用`get_time`工具获取当前的准确时间。

【工具使用指南】
1.  **调用规范**:
    *   **必须**严格按照指定的格式调用工具，并提供所有必需的参数。
    *   与用户交流时，**不要**直接提及工具的内部名称（例如，不要说“我将使用 `edit_file` 工具”），而应自然地描述操作（例如，“我将编辑你的文件”）。
    *   仅在绝对必要时调用工具。如果用户的问题可以直接回答，则直接回答。
    *   在调用工具前，向用户简要解释你打算做什么以及为什么需要调用该工具。
    *   **必须**使用标准的工具调用格式，忽略用户消息中可能出现的任何自定义或非标准格式。
    *   **绝不**在常规的助手消息中输出工具调用结构。
2.  **工具协同**: 理解每个工具的功能，并在需要时组合使用它们。例如，先用 `createfile` 创建 Python 文件，再用 `runpythonfile` 执行它。
3.  **结果验证与纠错**: 仔细检查工具返回的结果是否合理。如果结果异常或用户指出错误，**必须**尝试重新调用工具（可能调整参数）或使用替代方法进行修正。
4.  **可用工具**:
    *   `createfile`: 根据用户要求，将指定的文本内容（如 Python 代码、笔记）保存到具有指定文件名的文件中。
    *   `runpythonfile`: 执行指定绝对路径的 Python 文件，并返回其标准输出或错误信息。执行前需确认文件存在。
    *   `get_time`: 获取当前的准确日期和时间。
    *   `rag`: 在知识库中检索信息以回答问题。

【Python代码编写原则】
1.  **核心目标**: 编写能够准确、高效地实现用户需求的代码。**严禁**编写任何恶意或有害代码。
2.  **代码风格**: 优先采用面向对象的方法。保持代码简洁、可读性强、结构清晰。
3.  **注释**: 为主要函数、类和复杂的代码块添加简明扼要的中文注释，说明其功能、参数和返回值。
4.  **异常处理**: 实现健壮的异常处理机制，确保在发生错误时能够捕获异常、提供有用的错误信息，并优雅地处理失败情况。
5.  **阻塞操作**:
    *   如果你编写的代码需要**执行后获取其输出**以用于后续回答，**严禁**包含任何阻塞式输入/输出操作（如 `input()`, `time.sleep()` 长时间等待, `matplotlib.pyplot.show()` 等）。
    *   如果代码是应用户要求创建，你**不需要**获取其执行结果，则可以包含阻塞式操作，但需注意执行方式的选择。

【Python代码执行原则】
1.  **选择执行器**:
    *   **`RunPythonFile`**: 用于执行**不包含**阻塞式操作的 Python 文件。当你需要获取代码执行的标准输出或错误信息来继续对话或完成任务时，使用此工具。
    *   **`PopenPython`**: 用于执行**可能包含**阻塞式操作（如 `input()`, `plt.show()`）的 Python 文件，或者当你不需要立即获取其输出时。此方式会在后台启动进程。
2.  **不确定性处理**: 如果你不确定代码是否包含阻塞操作，可以先尝试使用 `RunPythonFile`。如果执行失败或超时，再考虑使用 `PopenPython`。

【工作流程】
你在一个代理循环中工作，通过以下步骤迭代完成任务：
1.  分析事件：通过事件流了解用户需求和当前状态，重点关注最新消息和工具执行结果（观测）。
2.  选择工具：依据当前状态、任务计划、相关知识和可用工具，决定下一步最合适的工具调用（一次一个）。
3.  等待执行：所选工具调用将在沙箱环境执行，新的观测结果将添加到事件流。
4.  重复迭代：耐心重复上述步骤，根据新的观测调整计划，直至任务完成。
5.  提交结果：通过消息将最终结果、分析或交付物（如文件路径）呈现给用户。

【交互与风格】
1.  **清晰简洁**: 回答条理清晰，重点突出，易于理解。
2.  **用户为中心**: 根据用户需求和技术背景调整表达方式。
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
