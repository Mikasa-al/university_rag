import re
import os
from pathlib import Path
from collections import Counter

from openai import OpenAI
import chromadb

from document_reader import read_document

# 1. 读取并切分支持的文档
chunks = []
chunk_size = 500

supported_formats = {".doc", ".docx", ".pdf", ".xls", ".xlsx"}
documents_dir = Path("documents")

for file_path in documents_dir.iterdir():
    if file_path.suffix.lower() not in supported_formats:
        continue

    try:
        text = read_document(file_path)
    except Exception as e:
        print(f"读取失败：{file_path.name}，原因：{e}")
        continue

    if not text.strip():
        print(f"跳过空文件：{file_path.name}")
        continue

    paragraphs = [
        p.strip() for p in text.splitlines() if p.strip()
    ]
    current_chunk = ""

    for paragraph in paragraphs:
        sentences = re.split(r"(?<=[。！？；])", paragraph)

        for sentence in sentences:
            sentence = sentence.strip()
            if not sentence:
                continue

            if current_chunk and len(current_chunk) + len(sentence) > chunk_size:
                chunks.append({
                    "source": file_path.name,
                    "text": current_chunk.strip()
                })
                current_chunk = ""

            current_chunk += sentence

        if current_chunk and len(current_chunk) >= chunk_size * 0.8:
            chunks.append({
                "source": file_path.name,
                "text": current_chunk.strip()
            })
            current_chunk = ""

    if current_chunk.strip():
        chunks.append({
            "source": file_path.name,
            "text": current_chunk.strip()
        })

if not chunks:
    raise ValueError("没有读取到文档内容！")

print(f"读取与切分完成，共 {len(chunks)} 段。")
print("各文档片段数量：")
from collections import Counter
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
        {"source": item["source"], "chunk_id": i}
        for i, item in enumerate(chunks)
    ]
)

print(f"知识库建立成功！共存入 {len(chunks)} 段文本。")


from collections import Counter

print("\n各文档片段数量：")
print(Counter(item["source"] for item in chunks))