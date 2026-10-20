
from pathlib import Path

from pypdf import PdfReader

# 获取项目中的 PDF 文件
pdf_folder = Path("documents")
pdf_files = list(pdf_folder.glob("*.pdf"))

if not pdf_files:
    print("没有找到 PDF 文件，请检查 documents 文件夹。")
else:
    pdf_path = pdf_files[0]
    reader = PdfReader(str(pdf_path))

    print("文件名：", pdf_path.name)
    print("总页数：", len(reader.pages))

    # 先读取第一页
    text = reader.pages[0].extract_text()
    print("\n第一页内容：")
    print(text[:1000] if text else "第一页没有提取到文字")
