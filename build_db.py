
from pathlib import Path
from docx import Document
from sentence_transformers import SentenceTransformer
import chromadb

# 1. 读取并切分所有 Word 文档
chunks = []
chunk_size = 300

for file_path in Path("documents").glob("*.docx"):
    doc = Document(file_path)
    text = "\n".join(
        p.text.strip()
        for p in doc.paragraphs
        if p.text.strip()
    )

    for start in range(0, len(text), chunk_size):
        content = text[start:start + chunk_size].strip()
        if content:
            chunks.append({
                "source": file_path.name,
                "text": content
            })

if not chunks:
    raise ValueError("没有读取到文档内容！")

# 2. 将文本转换成向量
print("正在加载向量模型，首次运行可能需要下载……")
model = SentenceTransformer("paraphrase-multilingual-MiniLM-L12-v2")
texts = [item["text"] for item in chunks]
embeddings = model.encode(texts).tolist()

# 3. 保存到本地向量数据库
client = chromadb.PersistentClient(path="./chroma_db")

# 每次运行重新构建，避免旧数据重复
try:
    client.delete_collection("university_policies")
except Exception:
    pass

collection = client.create_collection("university_policies")
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
