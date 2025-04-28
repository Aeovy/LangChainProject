# LangChain项目使用指南

## 环境配置

1. 本项目使用OpenAI风格API接口
2. 在根目录下创建`.env`文件，包含以下环境变量：

```
# OpenAI兼容接口
OPENAI_API_KEY="XXX"
OPENAI_MODEL_NAME="qwen-max-latest"
OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

# Ollama配置
OLLAMA_API_KEY="OLLAMA_API_KEY"
OLLAMA_BASE_URL="http://localhost:11434/v1"
OLLAMA_MODEL_NAME="qwq"

# LMStudio配置
LMSTUDIO_API_KEY="LMSTUDIO_API_KEY"
LMSTUDIO_BASE_URL="http://localhost:1234/v1"
LMSTUDIO_MODEL_NAME="qwen2.5-14b-instruct"

# LMStudio Embedding配置
LMSTUDIO_EMBEDDING_MODEL_NAME="text-embedding-mxbai-embed-large-v1"
LMSTUDIO_EMBEDDING_BASE_URL="http://localhost:1234"
LMSTUDIO_EMBEDDING_API_KEY="LMSTUDIO_EMBEDDING_API_KEY"
```

您可以根据需要自行更改模型配置。

## RAG系统使用

- 在`RAG/RAG.py`中可以使用本地LMStudio的embedding模型，修改`embed_model`变量的初始化类为`LMStudioEmbeddings`即可
- 在RAG文件夹中的Data文件夹中放入您的文件，并运行`RAG.py`
- `RAG_USE.py`仅用于测试向量数据库

## 对话系统

- 使用`Use_LLM.py`即可开始对话

## 待办事项

- [ ] 将RAG改进为Light RAG，以支持知识图谱
- [ ] 使用FastAPI开放接口，以供前端使用
- [ ] 增加AgentCoding的多系统支持