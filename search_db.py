
import os
import chromadb
from openai import OpenAI

client_api = OpenAI(
    api_key=os.getenv("DASHSCOPE_API_KEY"),
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

# 连接本地知识库
db = chromadb.PersistentClient(path="./chroma_db")
collection = db.get_collection("university_policies")
print("知识库总片段数：", collection.count())
# 输入测试问题
question = input("请输入你的问题：")


# 将问题转换成向量
response = client_api.embeddings.create(
    model="text-embedding-v4",
    input=question
)
query_vector = response.data[0].embedding

# 检索最相关的3段文本
results = collection.query(
    query_embeddings=[query_vector],
    n_results=2
)

for i, text in enumerate(results["documents"][0]):
    metadata = results["metadatas"][0][i]

    print(f"\n【结果{i + 1}】")
    print("来源：", metadata["source"])
    print("片段编号：", metadata["chunk_id"])
    print("内容：", text[:200])