
from pathlib import Path
from policy_tracker import compare_policies, save_report


def main():
    base_dir = Path(__file__).resolve().parent
    versions_dir = base_dir / "policy_versions"

    old_file = versions_dir / "policy_old.docx"
    new_file = versions_dir / "policy_new.docx"
    report_file = versions_dir / "api_test_report_docx.json"

    result = compare_policies(old_file, new_file)

    print("接口调用成功")
    print("旧版条款数：", result["old_clause_count"])
    print("新版条款数：", result["new_clause_count"])
    print("变更数量：", result["change_count"])

    for item in result["changes"]:
        print(
            f'{item["type"]}：'
            f'修改前={item["old_text"] or "无"}；'
            f'修改后={item["new_text"] or "无"}'
        )

    save_report(result, report_file)
    print("测试报告已保存：", report_file)


if __name__ == "__main__":
    main()
