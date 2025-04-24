import streamlit as st

st.set_page_config(page_title="常见问题解答 - 教会奉献", layout="centered")

import pandas as pd
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings
import openai

# FAISS + Sheet 载入
@st.cache_data
def load_qa_from_google_sheet():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

    # ✅ 从 secrets 加载 JSON（而不是本地文件）
    creds_dict = json.loads(st.secrets["GOOGLE_SHEET_CREDS"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

    client = gspread.authorize(creds)
    sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1KqV3hABUUPOcKO1rI_5cwyPONG28FZMu_hjS-WD9opk/edit#gid=0").sheet1
    return pd.DataFrame(sheet.get_all_records())

@st.cache_resource
def load_faiss_index():
    embeddings = OpenAIEmbeddings(openai_api_key=st.secrets["OPENAI_API_KEY"])
    return FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True).as_retriever()

retriever = load_faiss_index()
df = load_qa_from_google_sheet()

st.title("📖 教会奉献常见问题解答")

query = st.text_input("🔍 请输入您的问题（例如：如何设定定期奉献？）")

# ✅ 合并处理
if query:
    results = retriever.get_relevant_documents(query)
    if results:
        context = results[0].page_content
        st.markdown("### 💡 最相关的答案")
        st.markdown(f"👉 {context}")

        if st.checkbox("✍️ 使用 AI 智能补充回答"):
            prompt = f"""
你是一个教会的问答助手。请根据以下问题与相关内容以及Church Center软件的了解，用简洁、清楚、亲切的语气回答提问者的问题。

问题: {query}
相关内容: {context}

请生成回答：
            """
            client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

            # 替代 ChatCompletion.create
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
            )

            # 获取返回内容
            ai_answer = response.choices[0].message.content.strip()
            st.markdown("### 🤖 AI 补充回答")
            st.success(ai_answer)


# 📋 展示全部 Q&A
st.markdown("---")
st.markdown("### 📋 全部常见问题")


# 创建两列，实现图标+提示语 与 radio 同行
col1, col2 = st.columns([1.2, 4])

with col1:
    st.markdown(
        "<div style='font-size:16px; padding-top: 6px;'>🌍 请选择语言：</div>",
        unsafe_allow_html=True
    )

with col2:
    lang = st.radio("", ["中文", "English"], horizontal=True, label_visibility="collapsed")


lang_code = "zh" if lang == "中文" else "en"

filtered_df = df[df["lang"] == lang_code]
for idx, (_, row) in enumerate(filtered_df.iterrows()):
    st.markdown(f"**Q{idx+1}: {row['question']}**")
    st.markdown(f"👉 {row['answer']}")
    st.markdown("<hr style='margin-top: 16px; margin-bottom: 24px;'>", unsafe_allow_html=True)
