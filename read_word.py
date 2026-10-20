
from pathlib import Path
from docx import Document

word_folder = Path("documents")
word_files = list(word_folder.glob("*.docx"))

if not word_files:
    print("没有找到 Word 文件。")
else:
    for file_path in word_files:
        doc = Document(file_path)

        print(f"\n{'=' * 40}")
        print("文件名：", file_path.name)
        print("=" * 40)

        for paragraph in doc.paragraphs:
            if paragraph.text.strip():
                print(paragraph.text)

    print("\n所有 Word 文件读取完成！")
