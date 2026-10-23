
from pathlib import Path
import json


def generate_markdown_report(json_file, output_file):
    """将制度变更 JSON 转换成可阅读的 Markdown 报告。"""
    json_path = Path(json_file)
    output_path = Path(output_file)

    if not json_path.exists():
        raise FileNotFoundError(f"变更结果文件不存在：{json_path}")

    result = json.loads(json_path.read_text(encoding="utf-8"))

    lines = [
        "# 高校制度变更追踪报告",
        "",
        f"- 旧版文件：{result.get('old_file', '未知')}",
        f"- 新版文件：{result.get('new_file', '未知')}",
        f"- 旧版条款数：{result.get('old_clause_count', 0)}",
        f"- 新版条款数：{result.get('new_clause_count', 0)}",
        f"- 检测到的变更数：{result.get('change_count', 0)}",
        "",
        "## 变更详情",
        "",
    ]

    changes = result.get("changes", [])

    if not changes:
        lines.append("未检测到条款变更。")
    else:
        for index, change in enumerate(changes, start=1):
            lines.extend([
                f"### 变更 {index}：{change.get('type', '未知')}",
                "",
            ])

            old_text = change.get("old_text", "")
            new_text = change.get("new_text", "")

            if old_text:
                lines.extend([
                    "**修改前：**",
                    "",
                    old_text,
                    "",
                ])

            if new_text:
                lines.extend([
                    "**修改后：**",
                    "",
                    new_text,
                    "",
                ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")

    return output_path


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    versions_dir = base_dir / "policy_versions"

    json_file = versions_dir / "change_report.json"
    markdown_file = versions_dir / "change_report.md"

    try:
        output = generate_markdown_report(json_file, markdown_file)
        print("报告生成成功！")
        print("报告位置：", output)
    except Exception as exc:
        print("报告生成失败：", repr(exc))
