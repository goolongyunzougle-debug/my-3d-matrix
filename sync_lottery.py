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

def fetch_pure_cst_lottery():
    print("🔄 正在通过公开文章镜像网网关，精准锁定【拼搏在线彩神通软件】推文内容...")
    
    # 🚀 使用专用的微信文章聚合网网关，直接请求该公众号的专属历史列表
    # 微信内部 ID：gh_3e70d44be5f8（即拼搏在线彩神通软件）
    url = "https://wemp.app/accounts/gh_3e70d44be5f8"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            print(f"❌ 镜像网关请求失败，状态码: {response.status_code}")
            return None, None
            
        html_content = response.text
        
        # 1. 拦截该公众号最新的文章标题
        # 镜像站的 HTML 结构中，标题通常包裹在后方
        print("📡 正在从该公众号历史流中剥离最新的彩神通文案...")
        
        # 寻找包含“期福彩3D”和“彩神通”字样的最新条目
        # 匹配形如：2026165期福彩3D...彩神通模拟试机号：[344]
        pattern = r'(\d{7})\s*期福彩\s*3D\s*[\d-]*\s*彩神通模拟试机号：\[(\d{3})\]'
        match = re.search(pattern, html_content)
        
        # 备用匹配：如果标题被截断，尝试匹配标题+摘要组合
        if not match:
            # 匹配 7位期号 和 3位试机号
            issue_match = re.search(r'(\d{7})\s*期', html_content)
            num_match = re.search(r'试机号：\[(\d{3})\]', html_content)
            if issue_match and num_match:
                issue_number = issue_match.group(1)
                draw_numbers_array = list(num_match.group(1))
                print(f"✅ [备用规则] 成功拦截【彩神通】专属数据！期号: {issue_number}, 试机号: {draw_numbers_array}")
                return issue_number, draw_numbers_array
        
        if match:
            issue_number = match.group(1)
            test_num_str = match.group(2)
            draw_numbers_array = list(test_num_str)
            
            print(f"✅ [标准规则] 成功拦截【彩神通】专属数据！期号: {issue_number}, 试机号: {draw_numbers_array}")
            return issue_number, draw_numbers_array
            
        # ----------------- 方案 B：如果 wemp 挂了，切入二十一点微信聚合站 -----------------
        print("💡 正在尝试备用【彩神通】文章聚合通道...")
        backup_url = "https://www.v21.cc/wemp/gh_3e70d44be5f8.html"
        backup_res = requests.get(backup_url, headers=headers, timeout=10)
        backup_res.encoding = 'utf-8'
        
        b_match = re.search(pattern, backup_res.text)
        if b_match:
            print(f"✅ [备用网关] 成功拦截【彩神通】专属数据！")
            return b_match.group(1), list(b_match.group(2))
            
        print("⚠️ 未能在该公众号的镜像页面中解析到带有 '彩神通模拟试机号：[xxx]' 的标准格式。")
        return None, None
            
    except Exception as e:
        print(f"❌ 解析该公众号历史流发生异常: {e}")
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
    issue, nums = fetch_pure_cst_lottery()
    if issue and nums:
        update_supabase(issue, nums)
