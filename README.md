How to use:
1.使用Openai风格API
2.在根目录下创建一个.env文件，在其中写入形如：
OPENAI_API_KEY="XXX"
OPENAI_MODEL_NAME="qwen-max-latest"
OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"

OLLAMA_API_KEY="OLLAMA_API_KEY"
OLLAMA_BASE_URL="http://localhost:11434/v1"
OLLAMA_MODEL_NAME="qwq"

LMSTUDIO_API_KEY="LMSTUDIO_API_KEY"
LMSTUDIO_BASE_URL="http://localhost:1234/v1"
LMSTUDIO_MODEL_NAME="qwen2.5-14b-instruct"

LMSTUDIO_EMBEDDING_MODEL_NAME="text-embedding-mxbai-embed-large-v1"
LMSTUDIO_EMBEDDING_BASE_URL="http://localhost:1234"
LMSTUDIO_EMBEDDING_API_KEY="LMSTUDIO_EMBEDDING_API_KEY" 

的环境变量，可以自行更改其中的模型。
3.在RAG文件夹中的Data文件夹中放入你的文件，并运行RAG.py,RAG_USE仅用于测试向量数据库
4.使用Use_LLM.py即可对话
TODO：
1.把RAG改成Light RAG，以支持知识图谱
2.使用fastapi开放出接口，以供前端使用