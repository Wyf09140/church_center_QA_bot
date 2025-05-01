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

if "verse_displayed" not in st.session_state:
    st.session_state.verse_displayed = False

quote_area = st.empty()
if not st.session_state.verse_displayed:

    quote_area.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC&family=Playfair+Display&display=swap');

    @keyframes fadeInOut {{
        0% {{ opacity: 0; }}
        15% {{ opacity: 1; }}
        85% {{ opacity: 1; }}
        100% {{ opacity: 0; }}
    }}
    .fade-in-out {{
        animation: fadeInOut 3s ease-in-out forwards;
    }}

    .bible-verse-box {{
        background: linear-gradient(to bottom right, rgba(255,255,255,0.8), rgba(240,240,240,0.85));
        padding: 30px 40px;
        border-radius: 12px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        display: inline-block;
    }}
    </style>

    <div class="fade-in-out" style="text-align: center; margin-top: 60px; margin-bottom: 60px;">
    <div class="bible-verse-box" style="font-family: 'Noto Serif SC', serif; font-size: 20px; line-height: 2; color: #444;">
        <div style="margin-bottom: 18px;">
            「你們要將當納的十分之一全然送入倉庫，使我家有糧，<br>
            以此試試我，是否為你們敞開天上的窗戶，<br>
            傾福與你們，甚至無處可容。」<br>
            —— 《馬拉基書》第三章第十節
        </div>
        <div style="font-family: 'Playfair Display', serif; font-size: 16px; color: #666;">
            “Bring the whole tithe into the storehouse, that there may be food in my house.”<br>
            ‘Test me in this,’ says the Lord Almighty,<br>
            ‘and see if I will not throw open the floodgates of heaven and pour out so much blessing<br>
            that there will not be room enough to store it.’<br>
            — Malachi 3:10 (NIV)
        </div>
    </div>
    </div>
    """, unsafe_allow_html=True)

    time.sleep(3)
    quote_area.empty()
    st.session_state.verse_displayed = True


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

# 创建两列，实现图标+提示语 与 radio 同行
col1, col2 = st.columns([1.2, 1.9])

with col1:
    st.markdown(
        "<div style='font-size:16px; padding-top: 6px;white-space: nowrap;'>🌍 請選擇語言 / Choose the language：</div>",
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

titles = {
    "zh": "教会奉献 - Church Center 常见问题解答",
    "zh-TW": "教會奉獻 - Church Center 常見問題解答",
    "en": "Church Center Giving - Frequently Asked Questions"
}

st.markdown(f"""
<div style='text-align: center; margin-top: 16px; margin-bottom: 20px;'>
    <h1 style='font-size: 34px; font-weight: 600; margin-bottom: 0;'>
         {titles[lang_code]}
    </h1>
</div>
""", unsafe_allow_html=True)


# 搜索区域
search_prompts = {
    "zh": "🔍 请输入您的问题（例如：如何设定定期奉献？）",
    "zh-TW": "🔍 請輸入您的問題（例如：如何設定定期奉獻？）",
    "en": "🔍 Please enter your question (e.g., How to set up recurring giving?)"
}


st.markdown(f"""
<h4 style='font-size: 22px; font-weight: 400; margin-top: 20px;'>
<strong>{search_prompts[lang_code]}</strong>
</h4>
""", unsafe_allow_html=True)


query = st.text_input("", placeholder="请在此輸入問題/Enter your question here...（支持简体 / 繁體 / English）")

if query:
    results = retriever.get_relevant_documents(query)
    if results:
        context = results[0].page_content

        prompt = f"""
你是一个教会的问答助手服务于Menlo Park的基督之家-第一家。请根据以下问题与相关内容以及Church Center软件的了解，用简洁、清楚、亲切的语气回答提问者的问题。表达简短的感谢。
回复的文字和提问者所使用文字保持一致。

问题: {query}
相关内容: {context}

请生成回答：
        """

        client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
        )

        ai_answer = response.choices[0].message.content.strip()
        st.markdown("### 🙋 回答")
        st.success(ai_answer)


# 📋 展示全部 Q&A
st.markdown("---")
qa_titles = {
    "zh": "📋 全部常见问题",
    "zh-TW": "📋 全部常見問題",
    "en": "📋 All Frequently Asked Questions"
}

st.markdown(f"""
<h4 style='font-size: 22px; font-weight: 400; margin-top: 20px;'>
<strong>{qa_titles[lang_code]}</strong>
</strong>
""", unsafe_allow_html=True)



filtered_df = df[df["lang"] == lang_code]

for i, (_, row) in enumerate(filtered_df.iterrows()):
    st.markdown(f"**Q{i + 1}: {row['question']}**")
    st.markdown(f"👉 {row['answer']}")
    st.markdown("<hr style='margin-top: 16px; margin-bottom: 24px;'>", unsafe_allow_html=True)

