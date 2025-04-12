from RAG import MyVectordb
import os



query = "模型编辑"
results = MyVectordb.qurey_vector_db(query)

# 显示结果
print(f"\n查询: '{query}'")
print(f"找到 {len(results)} 个相关文档:\n")

for i, doc in enumerate(results[:2]):
    print(os.path.basename('unknown'))
    print(f"内容: {doc.page_content}...")  # 只显示前200个字符
    print(f"来源: 第{doc.metadata.get('page', '未知')}页")
    print("-" * 50)