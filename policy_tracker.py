
from pathlib import Path
from difflib import SequenceMatcher
from docx import Document
import json


def read_policy(file_path):
    """读取 TXT 或 DOCX 制度文件，并按非空段落拆分。"""
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"制度文件不存在：{path}")

    suffix = path.suffix.lower()

    if suffix == ".txt":
        text = path.read_text(encoding="utf-8")
        clauses = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

    elif suffix == ".docx":
        document = Document(str(path))

        clauses = [
            paragraph.text.strip()
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

    else:
        raise ValueError(
            f"暂不支持该文件格式：{suffix}，请使用 .txt 或 .docx"
        )

    return clauses



def compare_policies(old_file, new_file):
    """比较两个版本的制度文本，返回变更记录。"""
    old_clauses = read_policy(old_file)
    new_clauses = read_policy(new_file)

    matcher = SequenceMatcher(
        None,
        old_clauses,
        new_clauses,
        autojunk=False
    )

    changes = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue

        if tag == "insert":
            for clause in new_clauses[j1:j2]:
                changes.append({
                    "type": "新增",
                    "old_text": "",
                    "new_text": clause
                })

        elif tag == "delete":
            for clause in old_clauses[i1:i2]:
                changes.append({
                    "type": "删除",
                    "old_text": clause,
                    "new_text": ""
                })

        elif tag == "replace":
            old_part = old_clauses[i1:i2]
            new_part = new_clauses[j1:j2]

            paired_count = min(len(old_part), len(new_part))

            for index in range(paired_count):
                changes.append({
                    "type": "修改",
                    "old_text": old_part[index],
                    "new_text": new_part[index]
                })

            for clause in old_part[paired_count:]:
                changes.append({
                    "type": "删除",
                    "old_text": clause,
                    "new_text": ""
                })

            for clause in new_part[paired_count:]:
                changes.append({
                    "type": "新增",
                    "old_text": "",
                    "new_text": clause
                })

    return {
        "old_file": str(old_file),
        "new_file": str(new_file),
        "old_clause_count": len(old_clauses),
        "new_clause_count": len(new_clauses),
        "change_count": len(changes),
        "changes": changes
    }


def save_report(result, output_file):
    """将变更结果保存为 JSON 文件。"""
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    versions_dir = base_dir / "policy_versions"

    old_file = versions_dir / "policy_old.txt"
    new_file = versions_dir / "policy_new.txt"
    report_file = versions_dir / "change_report.json"

    try:
        result = compare_policies(old_file, new_file)

        print("=" * 60)
        print("高校制度版本比较报告")
        print("=" * 60)
        print("旧版条款数：", result["old_clause_count"])
        print("新版条款数：", result["new_clause_count"])
        print("检测到的变更数：", result["change_count"])

        for index, change in enumerate(
            result["changes"], start=1
        ):
            print(f"\n变更 {index}：{change['type']}")

            if change["old_text"]:
                print("修改前：", change["old_text"])

            if change["new_text"]:
                print("修改后：", change["new_text"])

        save_report(result, report_file)
        print("\n报告已保存到：", report_file)

    except Exception as exc:
        print("制度比较失败：", repr(exc))
