
from rag_chat import answer_question


def run_test(question, expected_supported):
    print("\n" + "=" * 60)
    print("测试问题：", question)

    result = answer_question(question)

    # 检查返回数据结构
    assert isinstance(result, dict), "返回结果必须是字典"
    assert "answer" in result, "缺少 answer 字段"
    assert "sources" in result, "缺少 sources 字段"
    assert "supported" in result, "缺少 supported 字段"

    assert isinstance(result["answer"], str), "answer 必须是字符串"
    assert isinstance(result["sources"], list), "sources 必须是列表"
    assert isinstance(result["supported"], bool), "supported 必须是布尔值"

    print("回答：", result["answer"])
    print("来源数量：", len(result["sources"]))
    print("有依据标记：", result["supported"])

    if result["supported"] != expected_supported:
        print("测试结果：状态与预期不一致")
        return False

    print("测试结果：通过")
    return True


if __name__ == "__main__":
    cases = [
        (
            "国家助学贷款的资金可以用于哪些方面？",
            True,
        ),
        (
            "国家助学贷款的利息由谁承担？",
            True,
        ),
        (
            "郑州大学学生申请奖学金需要满足什么条件？",
            False,
        ),
    ]

    passed = 0

    for question, expected in cases:
        try:
            if run_test(question, expected):
                passed += 1
        except Exception as e:
            print("测试异常：", repr(e))

    print("\n" + "=" * 60)
    print(f"测试完成：{passed}/{len(cases)} 项通过")
