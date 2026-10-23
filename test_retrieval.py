
from dotenv import load_dotenv
from search_db import search_policies

load_dotenv()

questions = [
    "国家助学贷款的资金可以用于哪些方面？",
    "国家助学贷款的利息由谁承担？",
    "郑州大学学生申请奖学金需要满足什么条件？",
]

for question in questions:
    print("\n" + "=" * 60)
    print("问题：", question)

    try:
        results = search_policies(question, top_k=3)

        if not results:
            print("没有检索到结果。")
            continue

        for i, item in enumerate(results, start=1):
            print(f"\n候选片段 {i}")
            print("距离：", round(item["distance"], 4))
            print("文件：", item["source"])
            print("片段编号：", item["chunk_id"])
            print("原文：", item["text"][:300])

    except Exception as e:
        print("检索失败：", repr(e))
