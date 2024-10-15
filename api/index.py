from http.server import BaseHTTPRequestHandler

import re
import pandas as pd
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.models import PostbackEvent, TextSendMessage, MessageEvent, TextMessage
from linebot.models import *
import os
import requests
from groq import Groq
from my_commands.lottery_gpt import lottery_gpt
from my_commands.gold_gpt import gold_gpt
from my_commands.platinum_gpt import platinum_gpt
from my_commands.money_gpt import money_gpt
from my_commands.one04_gpt import one04_gpt
from my_commands.partjob_gpt import partjob_gpt
from my_commands.crypto_coin_gpt import crypto_gpt
from linebot.exceptions import LineBotApiError, InvalidSignatureError
from my_commands.stock.stock_gpt import stock_gpt
from my_commands.girlfriend_gpt import girlfriend_gpt

app = Flask(__name__)

# 管理每個聊天室的角色模式（獨立狀態）
chat_roles = {}

# SET BASE URL
base_url = os.getenv("BASE_URL")
# Channel Access Token
line_bot_api = LineBotApi(os.getenv('CHANNEL_ACCESS_TOKEN'))
# Channel Secret
handler = WebhookHandler(os.getenv('CHANNEL_SECRET'))
# 初始化 Groq API client
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 初始化對話歷史
conversation_history = {}
# 設定最大對話記憶長度
MAX_HISTORY_LEN = 10

# 讀取 CSV 檔案，將其轉換為 DataFrame
stock_data_df = pd.read_csv('name_df.csv')

# 根據股號查找對應的股名
def get_stock_name(stock_id):
    result = stock_data_df[stock_data_df['股號'] == int(stock_id)]
    if not result.empty:
        return result.iloc[0]['股名']
    return None

# 建立 GPT 模型
def get_reply(messages):
    print ("* app.py get_reply")
    try:
        response = groq_client.chat.completions.create(
            model="llama3-groq-8b-8192-tool-use-preview",
            messages=messages,
            max_tokens=2000,
            temperature=1.2
        )
        reply = response.choices[0].message.content
        return reply
    except Exception as groq_err:
        reply = f"GROQ API 發生錯誤: {groq_err.message}"
        return reply

# Vercel 入口點
@app.route("/api/callback", methods=['POST'])
def callback():
    signature = request.headers.get('X-Line-Signature')
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'

# 根據 event 取得聊天室 ID
def get_chat_id(event):
    if event.source.type == 'user':
        return event.source.user_id  # 單人聊天
    elif event.source.type == 'group':
        return event.source.group_id  # 群組聊天
    elif event.source.type == 'room':
        return event.source.room_id  # 聊天室
    else:
        return None

# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    global conversation_history
    chat_id = get_chat_id(event)  # 獲取聊天室 ID
    user_message = event.message.text

    # 初始化使用者的對話歷史
    if chat_id not in conversation_history:
        conversation_history[chat_id] = []

    # 初始化該聊天室的角色模式為 "base"（預設模式）
    if chat_id not in chat_roles:
        chat_roles[chat_id] = 'base'

    # 將訊息加入對話歷史
    conversation_history[chat_id].append({"role": "user", "content": user_message + ", 請以繁體中文回答我問題"})

    # 台股代碼邏輯：必須以 4-5 個數字開頭，後面可選擇性有一個英文字母
    stock_code = re.search(r'^\d{4,5}[A-Za-z]?\b', user_message)
    # 美股代碼邏輯：必須以 1-5 個字母開頭
    stock_symbol = re.search(r'^[A-Za-z]{1,5}\b', user_message)

    # 限制對話歷史長度
    if len(conversation_history[chat_id]) > MAX_HISTORY_LEN * 2:
        conversation_history[chat_id] = conversation_history[chat_id][-MAX_HISTORY_LEN * 2:]

    # 定義彩種關鍵字列表
    lottery_keywords = ["威力彩", "大樂透", "539", "雙贏彩", "3星彩", "三星彩", "4星彩", "四星彩", "38樂合彩", "39樂合彩", "49樂合彩", "運彩"]

    # 判斷是否為彩種相關查詢
    if any(keyword in user_message for keyword in lottery_keywords):
        reply_text = lottery_gpt(user_message)  # 呼叫對應的彩種處理函數
    elif user_message.lower().startswith("大盤") or user_message.lower().startswith("台股"):
        reply_text = stock_gpt("大盤")
    elif user_message.lower().startswith("美盤") or user_message.lower().startswith("美股"):
        reply_text = stock_gpt("美盤")
    elif any(user_message.lower().startswith(currency.lower()) for currency in ["金價", "金", "黃金", "gold"]):
        reply_text = gold_gpt()
    elif any(user_message.lower().startswith(currency.lower()) for currency in ["鉑", "鉑金", "platinum", "白金"]):
        reply_text = platinum_gpt()
    elif user_message.lower().startswith(tuple(["日幣", "日元", "jpy", "換日幣"])):
        reply_text = money_gpt("JPY")
    elif any(user_message.lower().startswith(currency.lower()) for currency in ["美金", "usd", "美元", "換美金"]):
        reply_text = money_gpt("USD")
    elif user_message.startswith("104:"):
        reply_text = one04_gpt(user_message[4:])
    elif user_message.startswith("pt:"):
        reply_text = partjob_gpt(user_message[3:])
    elif user_message.startswith("cb:"):
        coin_id = user_message[3:].strip()
        reply_text = crypto_gpt(coin_id)
    elif user_message.startswith("$:"):
        coin_id = user_message[2:].strip()
        reply_text = crypto_gpt(coin_id)
    elif stock_code:
        stock_id = stock_code.group()
        reply_text = stock_gpt(stock_id)
    elif stock_symbol:
        stock_id = stock_symbol.group()
        reply_text = stock_gpt(stock_id)
    elif user_message.startswith("比特幣"):
        reply_text = crypto_gpt("bitcoin")
    elif user_message.startswith("狗狗幣"):
        reply_text = crypto_gpt("dogecoin")
    elif user_message.startswith("老婆"):
        chat_roles[chat_id] = 'gf'  # 該聊天室進入 "老婆模式"
        reply_text = girlfriend_gpt("主人")
    elif user_message.startswith("離婚"):
        chat_roles[chat_id] = 'base'  # 回到預設模式
        reply_text = get_reply(conversation_history[chat_id])  # 呼叫 Groq API 取得回應
    else:
        # 根據該聊天室的角色模式進行回應
        if chat_roles[chat_id] == 'gf':
            reply_text = girlfriend_gpt("主人")
        else:
            # 傳送最新對話歷史給 Groq
            messages = conversation_history[chat_id][-MAX_HISTORY_LEN:]
            try:
                reply_text = get_reply(messages)  # 呼叫 Groq API 取得回應
            except Exception as e:
                reply_text = f"GROQ API 發生錯誤: {str(e)}"

    # 如果 `reply_text` 為空，設定一個預設回應
    if not reply_text:
        reply_text = "抱歉，目前無法提供回應，請稍後再試。"

    # 回應使用者
    try:
        line_bot_api.reply_message(event.reply_token, TextSendMessage(reply_text))
    except LineBotApiError as e:
        print(f"LINE 回覆失敗: {e}")

    # 將 GPT 的回應加入對話歷史
    conversation_history[chat_id].append({"role": "user", "content": user_message})  # 加入歷史對話
    conversation_history[chat_id].append({"role": "assistant", "content": reply_text})

@handler.add(PostbackEvent)
def handle_postback(event):
    print(event.postback.data)

# 健康檢查端點
@app.route('/api/healthz', methods=['GET'])
def health_check():
    return 'OK', 200

# Flask 應用
def vercel_handler(request):
    return app(request)



class handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type','text/plain')
        self.end_headers()
        self.wfile.write('Hello, world!'.encode('utf-8'))
        return
