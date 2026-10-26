
import os
import chromadb
from openai import OpenAI


def search_policies(question, top_k=3):
    """检索学校制度，返回原文、来源、片段编号和距离。"""

    if not os.getenv("DASHSCOPE_API_KEY"):
        raise ValueError("未找到 DASHSCOPE_API_KEY 环境变量！")

    if not question.strip():
        return []

    # 连接知识库
    db = chromadb.PersistentClient(path="./chroma_db")
    collection = db.get_collection("university_policies")

    if collection.count() == 0:
        return []

    # 初始化 API
    client_api = OpenAI(
        api_key=os.getenv("DASHSCOPE_API_KEY"),
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )

    # 将问题转换为向量
    response = client_api.embeddings.create(
        model="text-embedding-v4",
        input=question
    )
    query_vector = response.data[0].embedding

    # 先计算需要检索的候选数量
    candidate_k = min(max(top_k * 5, 10), collection.count())

    # 再执行检索
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=candidate_k,
        include=["documents", "metadatas", "distances"]
    )
    print("知识库总片段数：", collection.count())
    print("本次请求候选数：", candidate_k)

    # 整理为统一的数据结构
    items = []

    for i, text in enumerate(results["documents"][0]):
        metadata = results["metadatas"][0][i]

        items.append({
            "source": metadata.get("source", "未知来源"),
            "title": metadata.get("title", ""),
            "source_url": metadata.get("source_url", ""),
            "chunk_id": metadata.get("chunk_id"),
            "text": text,
            "distance": results["distances"][0][i]
        })

    # 过滤距离过大的结果
    filtered_items = [
        item for item in items
        if item["distance"] <= 0.7
    ]

    # 按距离从小到大排序
    filtered_items.sort(key=lambda item: item["distance"])

    # 返回最相关的片段，不再按制度去重
    return filtered_items[:top_k]


if __name__ == "__main__":
    print("知识库检索测试")
    print("输入 exit 退出")

    while True:
        question = input("\n请输入你的问题：").strip()

        if question.lower() == "exit":
            break

        try:
            results = search_policies(question, top_k=3)

            if not results:
                print("没有检索到相关内容。")
                continue

            for i, item in enumerate(results, start=1):
                print(f"\n【结果{i}】")
                print("来源：", item["source"])
                print("片段编号：", item["chunk_id"])
                print("距离：", round(item["distance"], 4))
                print("内容：", item["text"])
                print("官网链接：", item["source_url"])

        except Exception as e:
            print(f"检索失败：{e}")
