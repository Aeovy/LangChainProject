from RAG import MyVectordb
import os



query = "毛泽东思想活的灵魂"
results = MyVectordb.qurey_vector_db(query)

# 显示结果
print(f"\n查询: '{query}'")
print(f"找到 {len(results)} 个相关文档:\n")

for i, doc in enumerate(results[:2]):
    print(os.path.basename(doc.metadata.get('source',"unknown")))  # 显示文件名
    print(f"内容: {doc.page_content[0:10]}...")  # 只显示前200个字符
    print(f"来源: 第{doc.metadata.get('page', '未知')}页")
    print("-" * 50)