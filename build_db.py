import re
import os
from pathlib import Path
from collections import Counter
import json

from openai import OpenAI
import chromadb


# 1. 读取并切分文档
chunks = []
chunk_size = 500

def split_into_chunks(text, source, title="", source_url=""):
    paragraphs = [p.strip() for p in text.splitlines() if p.strip()]
    chunks_list = []
    current_chunk = ""
    overlap_size = 50

    for paragraph in paragraphs:
        # 如果整个段落放入后不超过 500 字，就直接保留
        if len(current_chunk) + len(paragraph) <= chunk_size:
            current_chunk += paragraph + "\n"
            continue

        # 当前片段已达到一定长度，先保存
        if current_chunk.strip():
            chunks_list.append({
                "source": source,
                "title": title,
                "source_url": source_url,
                "text": current_chunk.strip()
            })

        # 保留上一片段末尾约 50 字作为重叠
        overlap = current_chunk[-overlap_size:] if current_chunk else ""

        # 当前段落本身不超过 500 字，就作为新片段的开头
        if len(paragraph) <= chunk_size:
            current_chunk = overlap + paragraph + "\n"
        else:
            # 超长段落才按句子切分
            sentences = re.split(r"(?<=[。！？；])", paragraph)
            current_chunk = overlap

            for sentence in sentences:
                sentence = sentence.strip()
                if not sentence:
                    continue

                if len(current_chunk) + len(sentence) > chunk_size:
                    chunks_list.append({
                        "source": source,
                        "title": title,
                        "source_url": source_url,
                        "text": current_chunk.strip()
                    })
                    current_chunk = current_chunk[-overlap_size:]

                current_chunk += sentence

    # 保存最后剩余的片段
    if current_chunk.strip():
        chunks_list.append({
            "source": source,
            "title": title,
            "source_url": source_url,
            "text": current_chunk.strip()
        })

    chunks.extend(chunks_list)

# 读取爬虫抓取的 JSON 制度
json_path = Path("crawled_policies/policies.json")

if json_path.exists():
    policies = json.loads(json_path.read_text(encoding="utf-8"))

    for policy in policies:
        content = policy.get("content", "").strip()
        if not content:
            continue

        split_into_chunks(
            content,
            source=policy.get("title", "未知制度"),
            title=policy.get("title", ""),
            source_url=policy.get("source_url", "")
        )

    print(f"已读取爬虫制度：{len(policies)} 篇")
else:
    print("未找到 policies.json，跳过爬虫数据。")


if not chunks:
    raise ValueError("没有读取到文档内容！")

print(f"读取与切分完成，共 {len(chunks)} 段。")
print("各文档片段数量：")
print(Counter(item["source"] for item in chunks))



# 2. 使用阿里云百炼 API 生成向量
api_key = os.getenv("DASHSCOPE_API_KEY")
if not api_key:
    raise ValueError("未找到 DASHSCOPE_API_KEY 环境变量！")

client_api = OpenAI(
    api_key=api_key,
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

texts = [item["text"] for item in chunks]
embeddings = []

print(f"正在生成向量，共 {len(texts)} 段文本……")

# 分批调用，避免单次请求内容过多
batch_size = 10

for start in range(0, len(texts), batch_size):
    batch = texts[start:start + batch_size]

    response = client_api.embeddings.create(
        model="text-embedding-v4",
        input=batch
    )

    # 按返回的索引排序，确保向量与文本对应
    results = sorted(response.data, key=lambda item: item.index)
    embeddings.extend([item.embedding for item in results])

    print(f"已完成 {len(embeddings)}/{len(texts)} 段")

# 3. 保存到本地向量数据库
db_client = chromadb.PersistentClient(path="./chroma_db")

# 每次运行重新构建，避免旧数据重复
try:
    db_client.delete_collection("university_policies")
except Exception:
    pass

collection = db_client.create_collection("university_policies")

collection.add(
    ids=[str(i) for i in range(len(chunks))],
    documents=texts,
    embeddings=embeddings,
    metadatas=[
        {
            "source": item["source"],
            "title": item.get("title", ""),
            "source_url": item.get("source_url", ""),
            "chunk_id": i
        }
        for i, item in enumerate(chunks)
    ]
)

print(f"知识库建立成功！共存入 {len(chunks)} 段文本。")


from collections import Counter

print("\n各文档片段数量：")
print(Counter(item["source"] for item in chunks))