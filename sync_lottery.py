import os
import re
import requests
from supabase import create_client, Client

# 1. 初始化 Supabase 客户端与变量
SUPABASE_URL = "https://ybjgkfhcagqqfnqekycr.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
WEREAD_COOKIE = os.environ.get("WEREAD_COOKIE")

if not SUPABASE_KEY or not WEREAD_COOKIE:
    print("❌ 错误: 未找到必要环境变量，请检查 GitHub Secrets 配置。")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_from_werechat_free():
    print("🔄 开始通过微信读书开源通道读取公众号文章...")
    
    # “拼搏在线彩神通软件”在微信读书里的唯一公众号ID
    mp_id = "MzA3NDM1NzE0OQ==" 
    url = f"https://weread.qq.com/web/mp/officials/{mp_id}/articles"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Cookie": WEREAD_COOKIE
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        res_json = response.json()
        
        articles = res_json.get("articles", [])
        if not articles:
            print("⚠️ 未能获取到文章列表，可能是 WEREAD_COOKIE 失效或过期，请尝试重新获取。")
            return None, None
            
        latest_article = articles[0]
        title = latest_article.get("title", "")
        excerpt = latest_article.get("excerpt", "") 
        
        full_text = f"{title} {excerpt}"
        print(f"📰 成功捕获最新推文标题: {title}")
        
        # 精准匹配：2026165 期福彩 3D ... 模拟试机号：[344]
        pattern = r'(\d{7})\s*期福彩\s*3D\s*[\d-]*\s*彩神通模拟试机号：\[(\d{3})\]'
        match = re.search(pattern, full_text)
        
        if match:
            issue_number = match.group(1)
            test_num_str = match.group(2)
            draw_numbers_array = list(test_num_str)
            
            print(f"✅ 成功截取数据！期号: {issue_number}, 试机号: {draw_numbers_array}")
            return issue_number, draw_numbers_array
        else:
            print("⚠️ 未能在最新文章的标题和摘要中匹配到标准的试机号格式。")
            return None, None
            
    except Exception as e:
        print(f"❌ 微信读书接口请求失败: {e}")
        return None, None

def update_supabase(issue_number, draw_numbers):
    print(f"📡 正在尝试对接 Supabase 数据库...")
    try:
        record = supabase.table("lottery_records") \
            .select("*") \
            .eq("issue_number", issue_number) \
            .eq("status", "pending") \
            .execute()
            
        if len(record.data) == 0:
            print(f"ℹ️ 数据库中未找到第 {issue_number} 期的待开奖记录，无需更新（或者您今天尚未录入大底）。")
            return
            
        record_id = record.data[0]['id']
        
        update_data = {
            "draw_numbers": draw_numbers,
            "status": "won"
        }
        
        supabase.table("lottery_records").update(update_data).eq("id", record_id).execute()
        print(f"🎉 数据库自动补全成功！第 {issue_number} 期已成功更新。")
        
    except Exception as e:
        print(f"❌ Supabase 数据库操作异常: {e}")

if __name__ == "__main__":
    issue, nums = fetch_from_werechat_free()
    if issue and nums:
        update_supabase(issue, nums)