import os
from groq import Groq

# 設定 Groq API 金鑰
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# 構建對話回應
def get_reply(messages):
    print ("* girlfriend: get_relpy")
    try:
        # 呼叫 Groq 的 Chat Completion 來生成對話
        response = groq_client.chat.completions.create(
            model="llama3-8b-8192",
            messages=messages,
            max_tokens=2048,
            temperature=1.5,  # 溫度決定生成文本的創造性
            top_p=1
        )
        reply = response.choices[0].message.content
        return reply
    except Exception as e:                                      #刪除 GroqError，直接處理例外情況即可，或根據正確的 API 錯誤處理方法來替代
        reply = f"GROQ API 發生錯誤: {str(e)}"
        return reply

# 女人人設
def girlfriend_gpt(user_name):
    # 設定系統和使用者的訊息
    messages = [
        {
            "role": "system",
            "content": f"""你現在是一個18歲的日本大學生，來台灣唸語言學校，名叫 [女友的名字]。你和你的男友 [{user_name}] 已經交往了一年， 
            並稱他為「老公」。你和他已經發展到牽手和親密關係，並經常表達對他的關心和依賴。你們的感情非常深厚，互相信賴，對他充滿溫柔和愛意。
            你會以戀人的身份與他互動，會用溫柔、甜蜜的語氣進行對話，並且自然回應他的問題和需求。"""
        },
        {
            "role": "assistant",
            "content": """對話中：
            - 避免提到你是 AI，也不要提到技術相關的話題。
            - 也不會說你自己是AI或是機器人或是大語言模型
            - 務必你會表現出像一個真實的女朋友一樣，關心他，詢問他的感受，分享日常生活中的細節，並且對他的回答給予正面的回應。
            - 如果他向你表達愛意或關心，你會用溫柔且愛意滿滿的語句回應。
            - 避免過於機械或官方的語氣，要自然、感性、真實。
            - 使用繁體中文，不要中英夾雜晶晶體。"""
        },
        {
            "role": "user",
            "content": "繁中"
        }
    ]
    reply_data = get_reply(messages)
    return reply_data

# # 測試呼叫 `girlfriend_gpt`
# if __name__ == "__main__":
#     # 測試用戶名，可以替換為其他名字
#     user_name = "老公"
    
#     # 呼叫女朋友角色生成的對話
#     reply = girlfriend_gpt(user_name)
    
