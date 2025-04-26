import pandas as pd
import openai
import toml
import json
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from oauth2client.service_account import ServiceAccountCredentials
import gspread

# ✅ 从本地 secrets.toml 中加载 API 密钥
secrets = toml.load(".streamlit/secrets.toml")
client = openai.OpenAI(api_key=secrets["OPENAI_API_KEY"])

# ✅ 设置 Google Sheets 授权
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(secrets["GOOGLE_SHEET_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
gs_client = gspread.authorize(creds)

# ✅ 打开 Sheet
sheet_url = "https://docs.google.com/spreadsheets/d/1KqV3hABUUPOcKO1rI_5cwyPONG28FZMu_hjS-WD9opk/edit#gid=0"
sheet = gs_client.open_by_url(sheet_url).sheet1

# ✅ 获取数据
data = sheet.get_all_records()
df = pd.DataFrame(data)

# ✅ 构建向量数据
texts = (df["question"] + " " + df["answer"]).tolist()
embedding_model = OpenAIEmbeddings(openai_api_key=secrets["OPENAI_API_KEY"])
vectorstore = FAISS.from_texts(texts, embedding_model)

# ✅ 保存向量索引
vectorstore.save_local("faiss_index")
print("✅ 向量库构建完成，已保存为 'faiss_index'")
