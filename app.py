from flask import Flask

app = Flask(__name__)

# 函式的裝飾器 (Decorator)：函釋為基礎提供的附加功能
@app.route("/") 
def home():
    return "Hello Flask"

@app.route("/test")
def test():
    return "test"