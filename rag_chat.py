import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

from search_db import search_policies

def get_api_client():
    """初始化阿里云百炼兼容 OpenAI 的客户端。"""
    api_key = os.getenv("DASHSCOPE_API_KEY")

    if not api_key:
        raise ValueError(
            "未找到 DASHSCOPE_API_KEY 环境变量，请先配置 API Key。"
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
    )


def answer_question(question: str, top_k: int = 3) -> dict:
    """
    基于高校制度知识库回答问题。

    返回：
    {
        "answer": str,
        "sources": list[dict],
        "supported": bool
    }
    """
    question = question.strip()

    if not question:
        return {
            "answer": "请输入你的问题。",
            "sources": [],
            "supported": False
        }

    # 第一步：调用 A 负责的检索模块
    try:
        results = search_policies(question, top_k=top_k)

        # 过滤距离过大的检索结果
        distance_threshold = 0.7
        results = [
            item for item in results
            if item.get("distance") is not None
               and item["distance"] <= distance_threshold
        ]

    except Exception as e:
        return {
            "answer": f"知识库检索失败，请检查数据库和 API 配置。错误：{e}",
            "sources": [],
            "supported": False
        }

    if not results:
        return {
            "answer": "暂时没有检索到相关制度原文，无法可靠回答这个问题。",
            "sources": [],
            "supported": False
        }

    # 只使用真实检索结果构建来源，不让模型生成来源信息
    sources = []

    for item in results:
        sources.append({
            "source": item.get("source", "未知来源"),
            "source_url": item.get("source_url", ""),
            "chunk_id": item.get("chunk_id"),
            "text": item.get("text", ""),
            "distance": item.get("distance")
        })

    # 去掉没有正文的结果
    valid_sources = [
        item for item in sources
        if item["text"] and item["text"].strip()
    ]

    if not valid_sources:
        return {
            "answer": "检索结果中没有可用的制度原文，暂时无法回答。",
            "sources": sources,
            "supported": False
        }

    # 第二步：整理检索到的制度原文

    # 第二步：整理检索到的制度原文
    context_parts = []

    for i, item in enumerate(valid_sources, start=1):
        context_parts.append(
            f"【候选制度片段 {i}】\n"
            f"文件：{item['source']}\n"
            f"片段编号：{item['chunk_id']}\n"
            f"检索距离：{item['distance']}\n"
            f"原文：\n{item['text']}"
        )

    context = "\n\n".join(context_parts)


    # 第三步：调用通义千问生成回答
    try:
        client = get_api_client()

        response = client.chat.completions.create(
            model=os.getenv("DASHSCOPE_CHAT_MODEL", "qwen-plus"),
            messages=[
                {
                    "role": "system",

                    "content": (
                        "你是高校规章制度问答助手。"
                        "只能根据提供的制度原文回答，不得编造规定。"
                        "回答前必须逐一检查候选片段的文件名称、条款内容和用户问题是否相关。"
                        "文件名称相似或主题相近，不代表片段能够支持答案。"
                        "只使用直接包含答案依据的片段，不得用无关片段推导结论。"
                        "如果片段只提到某项评审工作的主要依据，不得将其扩大解释为完整的申请资格条件。"
                        "如果现有原文不足以回答，必须明确说明依据不足。"
                        "区分原文明确规定的内容与进一步解释。"
                        "涉及金额、时间、条件和条款编号时，必须忠实于原文。"
                        "不得把旧文件中的规定直接说成当前最新政策。"
                        "不得编造制度名称、条款编号、资格条件或来源链接。"
                        "回答应简洁清楚，并尽可能指出支持结论的具体条款。"
                    )

                },
                {
                    "role": "user",
                    "content": (
                        f"用户问题：\n{question}\n\n"
                        f"检索到的制度原文：\n{context}\n\n"
                        "请根据上述原文回答问题。"
                        "如果原文不足以支持明确结论，请直接说明。"
                    )
                }
            ],
            temperature=0.1
        )

        answer = response.choices[0].message.content

        if not answer:
            answer = "模型没有返回有效回答，请稍后重试。"

        # 根据模型回答中的明确提示，初步识别依据不足的情况

        # 根据模型回答中的明确提示，初步识别依据不足的情况
        insufficient_markers = [
            "无法回答这个问题",
            "无法可靠回答",
            "无法根据现有制度确认",
            "现有依据不足",
            "原文没有提供足够依据",
            "无法确认相关条件",
            "无法回答",
            "无法确认",
            "依据不足",
            "无法根据现有制度",
            "无法明确回答",
            "不足以支持",
            "不足以回答",
            "原文不足以",
            "现有原文不足",
            "缺乏足够依据",
            "无法确定",
            "未能提供足够",
        ]

        supported = bool(answer.strip()) and not any(
            marker in answer for marker in insufficient_markers
        )

        return {
            "answer": answer,
            "sources": valid_sources,
            "supported": supported
        }

    except Exception as e:
        return {
            "answer": f"大模型调用失败，请检查 API 配置或网络连接。错误：{e}",
            "sources": valid_sources,
            "supported": False
        }


if __name__ == "__main__":
    print("高校制度智答 - RAG 问答测试")
    print("输入 exit 退出")

    while True:
        question = input("\n请输入问题：").strip()

        if question.lower() == "exit":
            break

        result = answer_question(question)

        print("\n【回答】")
        print(result["answer"])

        print("\n【来源】")

        if not result["sources"]:
            print("没有可展示的来源。")
        else:
            for i, source in enumerate(result["sources"], start=1):
                print(f"\n来源 {i}")
                print("文件：", source["source"])
                print("片段编号：", source["chunk_id"])
                print("原文：", source["text"])
                print("官网链接：", source.get("source_url") or "暂无链接")

        print("\n【状态】")
        print("有依据标记：", result["supported"])
