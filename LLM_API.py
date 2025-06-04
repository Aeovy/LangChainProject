from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, Generator
import uvicorn
import time
import hashlib
import uuid
import os
from dotenv import load_dotenv
from model import LLM_Base, LLM_QWQ, LLM_Qwen3
from langchain_tools import tools, tools_dict
import asyncio
from fastapi.responses import StreamingResponse
import json

# 加载环境变量
load_dotenv()

# 创建FastAPI应用实例
app = FastAPI(title="LLM API Backend", version="1.0.0")

# 用于存储用户信息的内存变量（实际项目中应使用数据库）
users_database: Dict[str, Dict[str, Any]] = {}

# 全局LLM实例
llm_instance = None

# 初始化LLM
def init_llm():
    """初始化LLM实例"""
    global llm_instance
    try:
        llm_instance = LLM_Qwen3(
            model_name=os.getenv("OPENAI_MODEL_NAME"),
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL"),
            temperature=0.6,
            maxtoken=8192,
            tools=tools,
            tools_dict=tools_dict
        )
        print("LLM实例初始化成功")
    except Exception as e:
        print(f"LLM实例初始化失败: {e}")
        # 备用方案：使用LMStudio
        try:
            llm_instance = LLM_Qwen3(
                model_name=os.getenv("LMSTUDIO_MODEL_NAME"),
                api_key=os.getenv("LMSTUDIO_API_KEY"),
                base_url=os.getenv("LMSTUDIO_BASE_URL"),
                temperature=0.6,
                maxtoken=8192,
                tools=tools,
                tools_dict=tools_dict
            )
            print("LMStudio LLM实例初始化成功")
        except Exception as e2:
            print(f"LMStudio LLM实例初始化也失败: {e2}")

# 初始化默认测试用户
def init_default_users():
    """初始化默认测试用户"""
    admin_user_id = str(uuid.uuid4())
    admin_api_key = generate_api_key()
    
    users_database[admin_user_id] = {
        'username': 'admin',
        'email': 'admin@test.com',
        'password_hash': hash_password('123456'),
        'api_key': admin_api_key,
        'conversations': {}  # 存储用户的对话历史
    }
    
    print(f"默认用户已创建:")
    print(f"用户名: admin")
    print(f"邮箱: admin@test.com") 
    print(f"密码: 123456")
    print(f"API Key: {admin_api_key}")

# 定义MessageRole枚举
class MessageRole(str):
    Human = "Human"
    Ai = "Ai"
    Title = "Title"

# 定义Message数据模型
class Message(BaseModel):
    Role: str
    Content: str

# 用户注册请求模型
class RegisterRequest(BaseModel):
    UserName: str
    Password: str
    Email: str

# 用户登录请求模型
class LoginRequest(BaseModel):
    UserID: str  # 可以是用户名或邮箱
    Password: str

# 聊天请求数据模型
class ChatRequest(BaseModel):
    Message: Message
    ApiKey: Optional[str]
    Model: str
    EnableThink: bool
    ConversationId: Optional[str] = None  # 添加会话ID
    Stream: bool = False  # 添加流式传输选项

# 标题请求数据模型
class TitleRequest(BaseModel):
    Message: Message
    ApiKey: Optional[str]
    Model: str
    ConversationId: Optional[str] = None

# 响应数据模型
class ServerResponse(BaseModel):
    IsRequestSuccess: bool

class ChatResponse(ServerResponse):
    Message: Message
    ConversationId: Optional[str] = None

class TitleResponse(ChatResponse):
    pass

class LoginResponse(ServerResponse):
    Message: Optional[str] = None
    ApiKey: Optional[str] = None

class RegisterResponse(ServerResponse):
    Message: Optional[str] = None

# 工具函数：生成密码哈希
def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

# 工具函数：生成API Key
def generate_api_key() -> str:
    return str(uuid.uuid4()).replace('-', '')

# 工具函数：验证API Key
def validate_api_key(api_key: str) -> Optional[Dict[str, Any]]:
    """验证API Key并返回用户信息"""
    for user_id, user_data in users_database.items():
        if user_data.get('api_key') == api_key:
            return user_data
    return None

# 工具函数：获取或创建会话ID
def get_or_create_conversation_id(user_data: Dict[str, Any], conversation_id: Optional[str] = None) -> str:
    """获取或创建会话ID"""
    if conversation_id and conversation_id in user_data['conversations']:
        return conversation_id
    
    # 创建新的会话ID
    new_conversation_id = str(uuid.uuid4())
    user_data['conversations'][new_conversation_id] = {
        'created_at': time.time(),
        'messages': []
    }
    return new_conversation_id

# 初始化
init_default_users()
init_llm()

# 根路径
@app.get("/")
async def root():
    return {"message": "LLM API Backend is running", "llm_ready": llm_instance is not None}

# 注册接口
@app.post("/api/register", response_model=RegisterResponse)
async def register(request: RegisterRequest):
    try:
        # 验证必填字段
        if not request.UserName:
            return RegisterResponse(
                IsRequestSuccess=False,
                Message="用户名不能为空"
            )
        
        if not request.Email:
            return RegisterResponse(
                IsRequestSuccess=False,
                Message="邮箱不能为空"
            )
        
        if not request.Password:
            return RegisterResponse(
                IsRequestSuccess=False,
                Message="密码不能为空"
            )
        
        # 检查用户名是否已存在
        for user_id, user_data in users_database.items():
            if user_data['username'] == request.UserName:
                return RegisterResponse(
                    IsRequestSuccess=False,
                    Message="用户名已存在"
                )
            if user_data['email'] == request.Email:
                return RegisterResponse(
                    IsRequestSuccess=False,
                    Message="邮箱已被注册"
                )
        
        # 创建新用户
        user_id = str(uuid.uuid4())
        api_key = generate_api_key()
        
        users_database[user_id] = {
            'username': request.UserName,
            'email': request.Email,
            'password_hash': hash_password(request.Password),
            'api_key': api_key,
            'conversations': {}
        }
        
        print(f"用户注册成功: {request.UserName}, Email: {request.Email}")
        
        return RegisterResponse(
            IsRequestSuccess=True,
            Message=None
        )
        
    except Exception as e:
        print(f"注册错误: {e}")
        return RegisterResponse(
            IsRequestSuccess=False,
            Message=f"注册失败: {str(e)}"
        )

# 登录接口
@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    try:
        # 验证必填字段
        if not request.UserID:
            return LoginResponse(
                IsRequestSuccess=False,
                Message="用户ID不能为空"
            )
        
        if not request.Password:
            return LoginResponse(
                IsRequestSuccess=False,
                Message="密码不能为空"
            )
        
        # 查找用户（通过用户名或邮箱）
        user_found = None
        password_hash = hash_password(request.Password)
        
        for user_id, user_data in users_database.items():
            # 检查用户名或邮箱匹配，且密码正确
            if ((user_data['username'] == request.UserID or user_data['email'] == request.UserID) 
                and user_data['password_hash'] == password_hash):
                user_found = user_data
                break
        
        if user_found:
            print(f"用户登录成功: {request.UserID}")
            return LoginResponse(
                IsRequestSuccess=True,
                Message=None,
                ApiKey=user_found['api_key']
            )
        else:
            print(f"登录失败: {request.UserID}")
            return LoginResponse(
                IsRequestSuccess=False,
                Message="用户名/邮箱或密码错误"
            )
        
    except Exception as e:
        print(f"登录错误: {e}")
        return LoginResponse(
            IsRequestSuccess=False,
            Message=f"登录失败: {str(e)}"
        )

# Chat接口 - 返回AI响应
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 如果请求流式传输，返回StreamingResponse
    if request.Stream:
        return await chat_stream_handler(request)
    else:
        # 保持原有的非流式逻辑
        return await chat_normal_handler(request)

# 流式处理函数
async def chat_stream_handler(request: ChatRequest):
    """处理流式聊天请求"""
    
    # 验证逻辑（与原有逻辑相同）
    if llm_instance is None:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'LLM服务未初始化，请联系管理员', 'type': 'error'})}\n\n"]),
            media_type="text/plain"
        )
    
    if not request.ApiKey:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': 'API Key不能为空', 'type': 'error'})}\n\n"]),
            media_type="text/plain"
        )
    
    user_data = validate_api_key(request.ApiKey)
    if not user_data:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': '无效的API Key', 'type': 'error'})}\n\n"]),
            media_type="text/plain"
        )
    
    if not request.Model:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': '模型不能为空', 'type': 'error'})}\n\n"]),
            media_type="text/plain"
        )
    
    if not request.Message or not request.Message.Content:
        return StreamingResponse(
            iter([f"data: {json.dumps({'error': '消息内容不能为空', 'type': 'error'})}\n\n"]),
            media_type="text/plain"
        )
    
    # 获取或创建会话ID
    conversation_id = get_or_create_conversation_id(user_data, request.ConversationId)
    
    # 记录用户消息
    user_data['conversations'][conversation_id]['messages'].append({
        'role': request.Message.Role,
        'content': request.Message.Content,
        'timestamp': time.time()
    })
    
    print(f"流式聊天请求:")
    print(f"模型: {request.Model}")
    print(f"用户消息: {request.Message.Content}")
    print(f"会话ID: {conversation_id}")
    print(f"启用思考模式: {request.EnableThink}")
    
    def generate_stream():
        """生成流式响应"""
        try:
            ai_response_content = ""
            
            # 发送会话ID和开始信号
            yield f"data: {json.dumps({'conversation_id': conversation_id, 'type': 'start', 'success': True})}\n\n"
            
            # 使用qwen3_chat方法获取流式响应
            for chunk in llm_instance.qwen3_chat(
                query=request.Message.Content,
                Conversion_ID=conversation_id,
                ThinkingMode=request.EnableThink
            ):
                ai_response_content += chunk
                
                # 发送流式数据块
                chunk_data = {
                    'content': chunk,
                    'type': 'content',
                    'conversation_id': conversation_id,
                    'success': True
                }
                yield f"data: {json.dumps(chunk_data)}\n\n"
            
            # 记录完整的AI响应
            user_data['conversations'][conversation_id]['messages'].append({
                'role': 'Ai',
                'content': ai_response_content,
                'timestamp': time.time()
            })
            
            # 发送完成信号
            completion_data = {
                'type': 'complete',
                'conversation_id': conversation_id,
                'full_content': ai_response_content,
                'success': True,
                'message': {
                    'Role': 'Ai',
                    'Content': ai_response_content
                }
            }
            yield f"data: {json.dumps(completion_data)}\n\n"
            
            print(f"流式AI响应完成: {ai_response_content[:100]}...")
            
        except Exception as llm_error:
            print(f"流式LLM调用错误: {llm_error}")
            error_data = {
                'type': 'error',
                'error': f"LLM处理失败: {str(llm_error)}",
                'success': False
            }
            yield f"data: {json.dumps(error_data)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "Access-Control-Allow-Methods": "*"
        }
    )

# 非流式处理函数（保持原有逻辑）
async def chat_normal_handler(request: ChatRequest) -> ChatResponse:
    """处理非流式聊天请求"""
    try:
        # 检查LLM实例是否可用
        if llm_instance is None:
            return ChatResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Ai", Content="LLM服务未初始化，请联系管理员")
            )
        
        # 验证API Key
        if not request.ApiKey:
            return ChatResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Ai", Content="API Key不能为空")
            )
        
        user_data = validate_api_key(request.ApiKey)
        if not user_data:
            return ChatResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Ai", Content="无效的API Key")
            )
        
        # 验证其他必填字段
        if not request.Model:
            return ChatResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Ai", Content="模型不能为空")
            )
        
        if not request.Message or not request.Message.Content:
            return ChatResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Ai", Content="消息内容不能为空")
            )
        
        # 获取或创建会话ID
        conversation_id = get_or_create_conversation_id(user_data, request.ConversationId)
        
        # 记录用户消息
        user_data['conversations'][conversation_id]['messages'].append({
            'role': request.Message.Role,
            'content': request.Message.Content,
            'timestamp': time.time()
        })
        
        print(f"处理聊天请求:")
        print(f"模型: {request.Model}")
        print(f"用户消息: {request.Message.Content}")
        print(f"会话ID: {conversation_id}")
        print(f"启用思考模式: {request.EnableThink}")
        
        # 调用LLM生成响应
        try:
            ai_response_content = ""
            
            # 使用qwen3_chat方法获取流式响应
            for chunk in llm_instance.qwen3_chat(
                query=request.Message.Content,
                Conversion_ID=conversation_id,
                ThinkingMode=request.EnableThink
            ):
                ai_response_content += chunk
            
            # 记录AI响应
            user_data['conversations'][conversation_id]['messages'].append({
                'role': 'Ai',
                'content': ai_response_content,
                'timestamp': time.time()
            })
            
            # 创建AI响应消息
            ai_message = Message(
                Role="Ai",
                Content=ai_response_content
            )
            
            print(f"AI响应: {ai_response_content}")
            
            # 返回AI响应
            return ChatResponse(
                IsRequestSuccess=True,
                Message=ai_message,
                ConversationId=conversation_id
            )
            
        except Exception as llm_error:
            print(f"LLM调用错误: {llm_error}")
            return ChatResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Ai", Content=f"LLM处理失败: {str(llm_error)}")
            )
        
    except Exception as e:
        print(f"聊天错误: {e}")
        return ChatResponse(
            IsRequestSuccess=False,
            Message=Message(Role="Ai", Content=f"处理失败: {str(e)}")
        )

# GetTitle接口 - 返回标题
@app.post("/api/getTitle", response_model=TitleResponse)
async def get_title(request: TitleRequest):
    try:
        # 检查LLM实例是否可用
        if llm_instance is None:
            return TitleResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Title", Content="LLM服务未初始化，请联系管理员")
            )
        
        # 验证API Key
        if not request.ApiKey:
            return TitleResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Title", Content="API Key不能为空")
            )
        
        user_data = validate_api_key(request.ApiKey)
        if not user_data:
            return TitleResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Title", Content="无效的API Key")
            )
        
        # 验证其他必填字段
        if not request.Model:
            return TitleResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Title", Content="模型不能为空")
            )
        
        if not request.Message or not request.Message.Content:
            return TitleResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Title", Content="消息内容不能为空")
            )
        
        # 获取会话ID
        conversation_id = request.ConversationId or str(uuid.uuid4())
        
        print(f"生成标题请求:")
        print(f"模型: {request.Model}")
        print(f"消息: {request.Message.Content}")
        print(f"会话ID: {conversation_id}")
        
        # 构造生成标题的提示词
        title_prompt = f"请为以下对话内容生成一个简短的标题（不超过20个字符）：\n{request.Message.Content}"
        
        try:
            title_content = ""
            
            # 使用LLM生成标题
            for chunk in llm_instance.qwen3_chat(
                query=title_prompt,
                Conversion_ID=conversation_id + "_title",  # 使用不同的会话ID避免混淆
                ThinkingMode=False  # 生成标题不需要思考模式
            ):
                title_content += chunk
            
            # 清理标题内容，确保简短
            title_content = title_content.strip().split('\n')[0][:50]  # 取第一行，最多50字符
            
            # 创建标题响应消息
            title_message = Message(
                Role="Title",
                Content=title_content
            )
            
            print(f"生成的标题: {title_content}")
            
            # 返回标题响应
            return TitleResponse(
                IsRequestSuccess=True,
                Message=title_message,
                ConversationId=conversation_id
            )
            
        except Exception as llm_error:
            print(f"LLM生成标题错误: {llm_error}")
            return TitleResponse(
                IsRequestSuccess=False,
                Message=Message(Role="Title", Content=f"标题生成失败: {str(llm_error)}")
            )
        
    except Exception as e:
        print(f"获取标题错误: {e}")
        return TitleResponse(
            IsRequestSuccess=False,
            Message=Message(Role="Title", Content=f"处理失败: {str(e)}")
        )

# 健康检查端点
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "service": "LLM API Backend",
        "llm_ready": llm_instance is not None,
        "users_count": len(users_database)
    }

# 获取用户列表（调试用）
@app.get("/debug/users")
async def get_users():
    return {
        "total_users": len(users_database),
        "users": [
            {
                "username": user_data['username'],
                "email": user_data['email'],
                "has_api_key": bool(user_data.get('api_key')),
                "conversations_count": len(user_data.get('conversations', {}))
            }
            for user_data in users_database.values()
        ]
    }

# 获取用户会话列表
@app.get("/api/conversations")
async def get_conversations(api_key: str):
    """获取用户的会话列表"""
    user_data = validate_api_key(api_key)
    if not user_data:
        raise HTTPException(status_code=401, detail="无效的API Key")
    
    conversations = []
    for conv_id, conv_data in user_data.get('conversations', {}).items():
        conversations.append({
            "conversation_id": conv_id,
            "created_at": conv_data.get('created_at'),
            "message_count": len(conv_data.get('messages', [])),
            "last_message": conv_data.get('messages', [])[-1] if conv_data.get('messages') else None
        })
    
    return {"conversations": conversations}

# 如果直接运行此文件，启动服务器
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)