
import streamlit as st
import tempfile
from pathlib import Path

from rag_chat import answer_question
from policy_tracker import compare_policies

st.set_page_config(
    page_title="高校制度智答",
    page_icon="🎓",
    layout="wide",
)

st.title("🎓 高校制度智答")
st.subheader("郑州大学公开制度智能问答与变更追踪平台")

st.markdown(
    "帮助师生查询学校公开制度、查看原文依据，并追踪制度文件变化。"
)

# 侧边栏：页面导航
st.sidebar.title("功能导航")
page = st.sidebar.radio(
    "请选择功能",
    ["项目首页", "制度智能问答", "制度更新追踪"],
)

if page == "项目首页":
    st.header("欢迎使用高校制度智答")

    st.write(
        "本项目面向郑州大学公开发布的规章制度，"
        "目标是实现制度检索、原文问答和制度版本变化追踪。"
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("💬 制度智能问答")
        st.write("输入问题，查询相关制度内容。")

    with col2:
        st.subheader("🔄 制度更新追踪")
        st.write("上传同一制度的新旧版本，查看条款差异。")

    st.info("请通过左侧导航使用智能问答或制度版本比较功能。")

elif page == "制度智能问答":
    st.header("💬 制度智能问答")

    question = st.text_area(
        "请输入你想了解的制度问题",
        placeholder="例如：学生受到纪律处分有哪些规定？",
        height=120,
    )

    if st.button("提交问题", type="primary"):
        if not question.strip():
            st.warning("请先输入问题。")
        else:
            try:
                with st.spinner("正在检索制度并生成回答，请稍候……"):
                    result = answer_question(question.strip(), top_k=3)

                if result.get("supported"):
                    st.success("已完成制度检索与回答")

                    st.subheader("📖 回答")
                    st.markdown(result.get("answer", "暂时没有生成回答。"))

                    sources = result.get("sources", [])

                    if sources:
                        st.subheader("📚 参考制度依据")

                        for i, source in enumerate(sources, start=1):
                            title = source.get("source", "未知制度文件")

                            with st.expander(f"依据 {i}：{title}"):
                                st.write("相关原文：")
                                st.write(source.get("text", "暂无原文内容"))

                                if source.get("distance") is not None:
                                    st.caption(
                                        f"检索距离：{source['distance']:.4f}"
                                    )
                    else:
                        st.warning("本次回答没有返回可展示的引用来源。")

                else:
                    st.warning(
                        "暂时没有检索到足够可靠的制度依据，"
                        "建议调整问题或核对学校发布的制度原文。"
                    )

                    if result.get("answer"):
                        st.write(result["answer"])

            except Exception as e:
                st.error(
                    "问答过程中出现问题，请检查 API 配置、"
                    "知识库和运行终端中的错误信息。"
                )
                st.caption(f"错误详情：{e}")

elif page == "制度更新追踪":
    st.header("🔄 制度更新追踪")

    st.write(
        "上传同一份制度的旧版和新版文件，"
        "系统将按段落比较文本并展示差异。"
    )

    st.warning(
        "请确认两个文件属于同一份制度。"
        "比较结果仅表示文本差异，不代表已确认学校正式发布了制度更新。"
    )

    old_file = st.file_uploader(
        "上传旧版制度（.txt 或 .docx）",
        type=["txt", "docx"],
        key="old_policy",
    )

    new_file = st.file_uploader(
        "上传新版制度（.txt 或 .docx）",
        type=["txt", "docx"],
        key="new_policy",
    )

    if st.button("比较制度版本", type="primary"):
        if old_file is None or new_file is None:
            st.warning("请先上传旧版和新版两个文件。")
        elif old_file.name == new_file.name:
            st.warning("两个文件的名称相同，请确认分别选择了旧版和新版。")
        else:
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    old_path = Path(temp_dir) / f"old_{Path(old_file.name).name}"
                    new_path = Path(temp_dir) / f"new_{Path(new_file.name).name}"

                    old_path.write_bytes(old_file.getvalue())
                    new_path.write_bytes(new_file.getvalue())

                    with st.spinner("正在比较两个版本……"):
                        result = compare_policies(old_path, new_path)

                st.success("版本比较完成")

                col1, col2, col3 = st.columns(3)

                col1.metric("旧版条款数", result["old_clause_count"])
                col2.metric("新版条款数", result["new_clause_count"])
                col3.metric("检测到的差异数", result["change_count"])

                changes = result.get("changes", [])

                if not changes:
                    st.info("未检测到条款差异。")
                else:
                    st.subheader("📋 变更详情")

                    for index, change in enumerate(changes, start=1):
                        change_type = change.get("type", "未知")
                        labels = {
                            "新增": "➕",
                            "删除": "➖",
                            "修改": "✏️",
                        }
                        icon = labels.get(change_type, "📄")

                        with st.expander(
                            f"{icon} 差异 {index}：{change_type}"
                        ):
                            if change.get("old_text"):
                                st.markdown("**旧版内容**")
                                st.text(change["old_text"])

                            if change.get("new_text"):
                                st.markdown("**新版内容**")
                                st.text(change["new_text"])

                st.caption(
                    "说明：当前采用段落顺序比较。段落拆分、合并或顺序调整，"
                    "也可能被识别为差异；结果需要人工核对。"
                )

            except Exception as e:
                st.error("比较失败，请检查文件格式及内容。")
                st.caption(f"错误详情：{e}")

st.divider()
st.caption("高校制度智答 · 创新项目开发版")
