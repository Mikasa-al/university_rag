import json
from pathlib import Path
from document_reader import read_document

json_path = Path("crawled_policies/policies.json")
attachment_dir = Path("crawled_policies/attachments")

policies = json.loads(json_path.read_text(encoding="utf-8"))

for policy in policies:
    title = policy["title"].split(" 2015年")[0].strip()

    for file_path in attachment_dir.glob("*.doc"):
        if file_path.stem == title:
            policy["content"] = read_document(file_path)
            print("已合并：", file_path.name)
            break

json_path.write_text(
    json.dumps(policies, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

print("合并完成，制度总数：", len(policies))