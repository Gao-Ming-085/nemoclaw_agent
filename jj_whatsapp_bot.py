import asyncio
import os
from playwright.async_api import async_playwright
from openai import AsyncOpenAI

# ================= [核心參數設定] =================
MAC_IP = "192.168.x.x"
PORT = ""
API_KEY = ""
# 依照你的要求修改模型名稱
MODEL_NAME = "Qwen3.5-0.8B-8bit" 
MODEL_API = f"http://{MAC_IP}:{PORT}/v1"

# 機器人觸發設定
TRIGGER_WORD = "JJ"
BOT_PREFIX = "🤖 [JJ 回覆]"
TARGET_NAME = "claw" # 請確保與 WhatsApp 上的名稱完全一致
SESSION_DIR = os.path.join(os.getcwd(), "whatsapp_session_data")
# ================================================

client = AsyncOpenAI(base_url=MODEL_API, api_key=API_KEY)

async def get_ai_response(user_input):
    """向 Mac 上的 oMLX 請求回覆"""
    try:
        response = await client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是助理 JJ。請用簡短、專業的繁體中文回覆。"},
                {"role": "user", "content": user_input}
            ],
            timeout=15
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"連線到 Mac 失敗 (Error: {e})"

async def main():
    if not os.path.exists(SESSION_DIR):
        os.makedirs(SESSION_DIR)

    async with async_playwright() as p:
        print(f"🚀 JJ 助理啟動中... 模型: {MODEL_NAME}")
        
        # 啟動持久化瀏覽器
        context = await p.chromium.launch_persistent_context(
            user_data_dir=SESSION_DIR,
            headless=False,
            slow_mo=500
        )
        
        page = context.pages[0]
        await page.goto("https://web.whatsapp.com")

        print("⏳ 正在等待 WhatsApp 加載...")
        try:
            await page.wait_for_selector("#side", timeout=120000)
            print("✅ 成功進入 WhatsApp！")
            
            # 點擊進入目標對話
            await page.click(f"span[title='{TARGET_NAME}']")
            print(f"📡 已鎖定 [{TARGET_NAME}]。輸入 '{TRIGGER_WORD} + 問題' 即可喚醒我。")
        except Exception as e:
            print(f"❌ 進入對話失敗: {e}")
            await context.close()
            return

        last_processed_text = ""

        while True:
            try:
                # 抓取最後一則訊息
                messages = await page.query_selector_all("div.copyable-text")
                
                if messages:
                    last_msg_element = messages[-1]
                    raw_text = await last_msg_element.inner_text()
                    
                    # 1. 檢查是否為新訊息
                    if raw_text != last_processed_text:
                        last_processed_text = raw_text
                        clean_msg = raw_text.split('\n')[0].strip()
                        
                        # 2. 判斷邏輯：包含 JJ 且不含機器人前綴（防循環）
                        if TRIGGER_WORD.upper() in clean_msg.upper() and "🤖" not in clean_msg:
                            print(f"🔔 偵測到指令: {clean_msg}")
                            
                            # 提取問題內容
                            query = clean_msg.upper().replace(TRIGGER_WORD.upper(), "").strip()
                            if not query:
                                query = "你好"

                            # 3. 獲取回覆
                            ai_reply = await get_ai_response(query)
                            
                            # 4. 自動發送
                            input_box = await page.wait_for_selector("div[contenteditable='true'][data-tab='10']")
                            final_reply = f"{BOT_PREFIX}: {ai_reply}"
                            
                            await input_box.fill(final_reply)
                            await page.keyboard.press("Enter")
                            
                            # 更新紀錄，避免回覆自己
                            await asyncio.sleep(1)
                            new_msgs = await page.query_selector_all("div.copyable-text")
                            if new_msgs:
                                last_processed_text = await new_msgs[-1].inner_text()
                                
                            print(f"🚀 JJ 已回覆：{ai_reply}")
                
                await asyncio.sleep(1.5)
                
            except Exception:
                await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 JJ 助理休息中。")