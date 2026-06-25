import os
import re
import requests
from supabase import create_client, Client

# 1. 初始化 Supabase 客户端与变量
SUPABASE_URL = "https://ybjgkfhcagqqfnqekycr.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ 错误: 未找到必要环境变量，请检查 GitHub Secrets 配置。")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def fetch_official_cst():
    print("🔄 正在通过微信官方公开网关，读取【拼搏在线彩神通软件】专属数据...")
    
    # 🚀 直接请求 wemp.app 提供的公众号最新图文快照（它会同步微信原文的所有汉字）
    url = "https://wemp.app/accounts/gh_3e70d44be5f8"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        html_content = response.text
        
        # 调试：打印网页内容长度，确认拿到了数据
        print(f"📡 成功下载网页数据，长度: {len(html_content)} 字节")
        
        # 🚀 极其宽松的模糊匹配规则！只要网页里同时包含“期”和“试机号：[xxx]”，就能被精准抠出来
        # 这样可以完美防止因为空格、换行或者标题截断导致的匹配失败
        
        # 1. 尝试寻找 7 位期号
        issue_match = re.search(r'(\d{7})\s*期', html_content)
        
        # 2. 尝试寻找形如 试机号：[344] 或者 试机号:[344] 或者 模拟试机号:[344]
        # [0-9]{3} 代表找连续的 3 个数字
        num_match = re.search(r'试机号[^\[]*\[([0-9]{3})\]', html_content)
        
        if issue_match and num_match:
            issue_number = issue_match.group(1)
            test_num_str = num_match.group(1)
            draw_numbers_array = list(test_num_str)
            
            print(f"✅ [核心算法] 成功拦截【彩神通】官方数据！")
            print(f"📡 截获期号: {issue_number}")
            print(f"📡 截获试机号: {draw_numbers_array}")
            return issue_number, draw_numbers_array
            
        # 🚀 降级容错方案：如果网站把中括号去掉了，直接找“试机号”后面的三个连续数字
        print("💡 启动降级容错规则匹配...")
        alt_num_match = re.search(r'试机号[：:\s]*([0-9])\s*([0-9])\s*([0-9])', html_content)
        if issue_match and alt_num_match:
            issue_number = issue_match.group(1)
            draw_numbers_array = [alt_num_match.group(1), alt_num_match.group(2), alt_num_match.group(3)]
            print(f"✅ [容错算法] 成功拦截【彩神通】官方数据！期号: {issue_number}, 试机号: {draw_numbers_array}")
            return issue_number, draw_numbers_array

        print("⚠️ 未能在网页中匹配到标准的期号或试机号文本结构。")
        # 打印网页前500个字，看看是不是遇到了验证码或者拦截
        print(f"📄 网页头部快照: \n{html_content[:500]}")
        return None, None
            
    except Exception as e:
        print(f"❌ 解析官方历史流发生异常: {e}")
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
    issue, nums = fetch_official_cst()
    if issue and nums:
        update_supabase(issue, nums)
