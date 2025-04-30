import streamlit as st

st.set_page_config(page_title="基督之家 ‧ 第一家 ‧ 教会奉献常见问题解答", layout="centered")
import time

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

import time

quote_area = st.empty()

quote_area.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC&family=Playfair+Display&display=swap');

@keyframes fadeInOut {
    0% { opacity: 0; }
    15% { opacity: 1; }
    85% { opacity: 1; }
    100% { opacity: 0; }
}
.fade-in-out {
    animation: fadeInOut 4s ease-in-out forwards;
}

.bible-verse-box {
    background: linear-gradient(to bottom right, rgba(255,255,255,0.8), rgba(240,240,240,0.85));
    padding: 30px 40px;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    display: inline-block;
}
</style>

<div class="fade-in-out" style="text-align: center; margin-top: 60px; margin-bottom: 60px;">
  <div class="bible-verse-box" style="font-family: 'Noto Serif SC', serif; font-size: 20px; line-height: 2; color: #444;">
    <div style="margin-bottom: 18px;">
        “你们要将当纳的十分之一全然送入仓库，使我家有粮，<br>
        以此试试我，是否为你们敞开天上的窗户，<br>
        倾福与你们，甚至无处可容。”<br>
        —— 《马拉基书》第三章第十节
    </div>
    <div style="font-family: 'Playfair Display', serif; font-size: 16px; color: #666;">
        “Bring the whole tithe into the storehouse, that there may be food in my house.<br>
        ‘Test me in this,’ says the Lord Almighty,<br>
        ‘and see if I will not throw open the floodgates of heaven and pour out so much blessing that there will not be room enough to store it.’<br>
        — Malachi 3:10 (NIV)
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

import time
time.sleep(4)
quote_area.empty()


col_logo, col_link = st.columns([3, 5])

with col_logo:
    st.image("logo.png", width=300)

with col_link:
    st.markdown(
        """
        <div style="padding-top: 24px; text-align: right;">
            <a href="https://the-home-of-christ-490912.churchcenter.com/home" target="_blank"
               style="
                   font-size: 16px;
                   color: #000;
                   text-decoration: none;
                   border: 1px solid #000;
                   padding: 6px 12px;
                   border-radius: 6px;
               ">
                👉 开始用 Church Center 奉献
            </a>
        </div>
        """,
        unsafe_allow_html=True
    )


st.markdown("""
<div style='text-align: center; margin-top: 16px; margin-bottom: 20px;'>
    <h1 style='font-size: 34px; font-weight: 600; margin-bottom: 0;'>
        教会奉献 - Church Center 常见问题解答
    </h1>
</div>
""", unsafe_allow_html=True)


# 搜索区域
st.markdown("""
<h4 style='font-size: 22px; font-weight: 400; margin-top: 20px;'>
<strong>🔍 请输入您的问题（例如：如何设定定期奉献？）</strong>
</h4>
""", unsafe_allow_html=True)

query = st.text_input("", placeholder="请在此输入问题/Enter your question here...（支持简体 / 繁體 / English）")


# ✅ 合并处理
if query:
    results = retriever.get_relevant_documents(query)
    if results:
        context = results[0].page_content
        st.markdown("### 💡 最相关的答案")
        st.markdown(f"👉 {context}")

        if st.checkbox("✍️ 使用 AI 智能补充回答"):
            prompt = f"""
你是一个教会的问答助手。请根据以下问题与相关内容以及Church Center软件的了解，用简洁、清楚、亲切的语气回答提问者的问题。回复的文字和提问者所使用文字保持一致。

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
st.markdown("""
<h4 style='font-size: 22px; font-weight: 500; margin-top: 36px; margin-bottom: 12px;'>
<strong>📋 全部常见问题 / General Questions</strong>
</h4>
""", unsafe_allow_html=True)



# 创建两列，实现图标+提示语 与 radio 同行
col1, col2 = st.columns([1.2, 4])

with col1:
    st.markdown(
        "<div style='font-size:16px; padding-top: 6px;'>🌍 请选择语言：</div>",
        unsafe_allow_html=True
    )

with col2:
    lang = st.radio("", ["中文(简)", "中文(繁)", "English"], horizontal=True, label_visibility="collapsed")

# 明确地根据选择项设定语言代码
if lang == "中文(简)":
    lang_code = "zh"
elif lang == "中文(繁)":
    lang_code = "zh-TW"
else:
    lang_code = "en"

filtered_df = df[df["lang"] == lang_code]

for i, (_, row) in enumerate(filtered_df.iterrows()):
    st.markdown(f"**Q{i + 1}: {row['question']}**")
    st.markdown(f"👉 {row['answer']}")
    st.markdown("<hr style='margin-top: 16px; margin-bottom: 24px;'>", unsafe_allow_html=True)

