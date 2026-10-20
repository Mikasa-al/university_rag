
from pathlib import Path
from docx import Document

word_folder = Path("documents")
chunks = []
chunk_size = 300  # 每段约300个字符

for file_path in word_folder.glob("*.docx"):
    doc = Document(file_path)

    # 合并非空段落
    paragraphs = [
        p.text.strip()
        for p in doc.paragraphs
        if p.text.strip()
    ]
    text = "\n".join(paragraphs)

    # 按字符切分，暂时不重叠
    for start in range(0, len(text), chunk_size):
        chunk = text[start:start + chunk_size].strip()

        if chunk:
            chunks.append({
                "source": file_path.name,
                "chunk_id": len(chunks),
                "text": chunk
            })

print("切分完成！")
print("总段数：", len(chunks))

for item in chunks[:3]:
    print("\n文件：", item["source"])
    print("段落编号：", item["chunk_id"])
    print("内容：", item["text"])
