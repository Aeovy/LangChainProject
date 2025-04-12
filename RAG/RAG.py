from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
import requests
import numpy as np
from dotenv import load_dotenv
import os
load_dotenv()

# 自定义嵌入类，基于成功的curl命令构建
class LMStudioEmbeddings( ):
    def __init__(self,model_type:str="lmstudio"):
        
        self.base_url = os.getenv(f"{model_type.upper()}_EMBEDDING_BASE_URL")
        self.model = os.getenv(f"{model_type.upper()}_EMBEDDING_MODEL_NAME")
    
    def embed_documents(self, texts):
        """嵌入文档列表"""
        results = []
        # 逐个处理文本，与curl命令保持一致
        for text in texts:
            embedding = self.embed_query(text)
            results.append(embedding)
        return results
    
    def embed_query(self, text):
        """嵌入单个查询文本"""
        try:
            response = requests.post(
                f"{self.base_url}/v1/embeddings",
                headers={"Content-Type": "application/json"},
                json={
                    "model": self.model,
                    "input": text  # 与curl命令一致，发送单个字符串
                },
                timeout=30
            )
            
            if response.status_code == 200:
                # 解析响应并提取嵌入向量
                result = response.json()
                return result["data"][0]["embedding"]
            else:
                print(f"API错误 ({response.status_code}): {response.text}")
                # 返回零向量作为后备
                raise ConnectionError(f"API错误 ({response.status_code}): {response.text}")
                
        except Exception as e:
            print(f"嵌入请求异常: {str(e)}")
            raise e

# 使用自定义嵌入类
embed_model = LMStudioEmbeddings(model_type="lmstudio")

from langchain_community.document_loaders import PyMuPDFLoader,Docx2txtLoader,ToMarkdownLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class Vectordb:
    def __init__(self, collection_name:str="test_DB", embedding_model:Embeddings=None, persist_directory:str="./RAG/chroma_db"):
        """初始化向量数据库"""
        if embedding_model is None:
            raise ValueError("embedding_model不能为空")
        self.vector_db = Chroma(
            collection_name=collection_name,
            embedding_function=embedding_model,
            persist_directory=persist_directory,
        )
        self.persist_directory = persist_directory
        self.processed_files = set()  # 用于记录已经处理过的文件名
        
        # 尝试加载已处理文件记录
        processed_files_path = os.path.join(persist_directory, "processed_files.txt")
        if os.path.exists(processed_files_path):
            with open(processed_files_path, "r") as f:
                self.processed_files = set(line.strip() for line in f)
                
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=512,
            chunk_overlap=200,
            add_start_index=True,
        )
    
    def save_processed_files(self):
        """保存已处理的文件名列表"""
        processed_files_path = os.path.join(self.persist_directory, "processed_files.txt")
        os.makedirs(self.persist_directory, exist_ok=True)
        with open(processed_files_path, "w") as f:
            for filename in self.processed_files:
                f.write(f"{filename}\n")
    
    def read_file(self,file_path:str):
        # ...原代码保持不变...
        if file_path.endswith(".pdf"):
            return PyMuPDFLoader(file_path).load()
        elif file_path.endswith(".txt"):
            pass
        elif file_path.endswith(".docx"):
            return Docx2txtLoader(file_path).load()
        elif file_path.endswith(".pptx"):
            pass
        elif file_path.endswith(".csv"):
            pass
        elif file_path.endswith(".md"):
            #return UnstructuredMarkdownLoader(file_path).load()
            pass
        else:
            raise TypeError("不支持的文件格式")
    
    def add_file(self, file_path:str):
        """添加文件到向量数据库，基于文件名去重"""
        # 提取文件名(不含路径)
        file_name = os.path.basename(file_path)
        if file_name.startswith("."):
            return
        # 检查文件是否已被处理
        if file_name in self.processed_files:
            print(f"文件 '{file_name}' 已存在于数据库中，跳过。")
            return "existed"
            
        try:
            # 处理文件
            pdf_file = self.read_file(file_path)
            all_splits = self.text_splitter.split_documents(pdf_file)
            all_splits_texts = []
            all_splits_metadatas = []
            for doc in all_splits:
                all_splits_texts.append(doc.page_content)
                # 在元数据中添加文件名，便于追踪
                doc.metadata["source_file"] = file_name
                all_splits_metadatas.append(doc.metadata)
            
            # 将文本添加到向量数据库
            self.vector_db.add_texts(texts=all_splits_texts, metadatas=all_splits_metadatas)
            
            # 记录已处理的文件
            self.processed_files.add(file_name)
            
            # 保存处理记录
            self.save_processed_files()
            print(f"成功添加文件: {file_name}")
            return "success"
            
        except Exception as e:
            print(f"处理文件 '{file_name}' 时出错: {str(e)}")
    
    def add_directory(self, directory_path:str):
        """添加目录中的所有文件"""
        if not os.path.exists(directory_path):
            print(f"目录 '{directory_path}' 不存在")
            return
            
        # 遍历目录中的所有文件
        processed_count = 0
        skipped_count = 0
        for root, _, files in os.walk(directory_path):
            for file in files:
                file_path= os.path.join(root, file)
                status=self.add_file(file_path)
                if status == "success":
                    processed_count += 1
                elif status == "existed":
                    skipped_count += 1
                    
        print(f"目录处理完成: 添加了 {processed_count} 个新文件，跳过了 {skipped_count} 个已存在的文件。")
    
    def qurey_vector_db(self, query_text:str, k:int=5):
        """查询向量数据库并返回最相关的文档"""
        # 执行相似度查询
        docs = self.vector_db.max_marginal_relevance_search(query_text, k=k)
        # 返回结果
        return docs

MyVectordb = Vectordb(embedding_model=embed_model)
if __name__ == "__main__":
    
    #MyVectordb.add_file(file_path="./RAG/Data/第1章 语言模型基础.pdf")
    MyVectordb.add_directory(directory_path="./RAG/Data")



