
import streamlit as st

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
        st.write("查看制度新增、更新和版本差异。")

    st.info("当前为开发版，部分功能尚未接入真实后端。")

elif page == "制度智能问答":
    st.header("💬 制度智能问答")

    question = st.text_area(
        "请输入你想了解的制度问题",
        placeholder="例如：国家助学贷款的申请条件是什么？",
    )

    if st.button("提交问题", type="primary"):
        if not question.strip():
            st.warning("请先输入问题。")
        else:
            st.info(
                "已收到你的问题，但真实问答接口尚未接入。"
                "当前不会生成或展示未经验证的制度答案。"
            )
            st.write("你的问题：", question)

elif page == "制度更新追踪":
    st.header("🔄 制度更新追踪")

    st.write("此页面用于后续展示制度新增、更新和新旧版本差异。")

    st.info(
        "当前尚未接入真实版本追踪模块，"
        "因此暂不展示更新记录。"
    )

st.divider()
st.caption("高校制度智答 · 创新项目开发版")
