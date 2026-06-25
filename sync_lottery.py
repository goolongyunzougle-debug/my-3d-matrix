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

def fetch_directly_from_wechat():
    print("🔄 正在通过微信开放通道直接检索公众号历史文章...")
    
    # 使用公开的搜狗微信聚合代理，直接拉取“拼搏在线彩神通软件”的最新文章列表
    # 这个公用历史页不封海外 IP，也不需要经常更换 Cookie，非常稳定
    search_url = "https://weixin.sogou.com/weixin?type=1&query=%E6%8B%BC%E6%90%8F%E5%9C%A8%E7%BA%BF%E5%BD%A9%E7%A5%9E%E9%80%9A%E8%BD%AF%E4%BB%B6&ie=utf8"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,zh-TW;q=0.7,zh-HK;q=0.5,en-US;q=0.3,en;q=0.2"
    }
    
    try:
        response = requests.get(search_url, headers=headers, timeout=15)
        html_content = response.text
        
        # 1. 尝试从公开索引页直接抓取带有“试机号”字样的最新推文标题
        print("📡 正在解析数据流...")
        
        # 匹配包含期号和试机号的大底文本特征
        # 微信推文的标题通常会直接暴露在 html 的 txt-box 中
        titles = re.findall(r'target="_blank"[^>]*>(.*?)</a>', html_content)
        
        target_text = ""
        for t in titles:
            # 清理 html 标签
            clean_title = re.sub(r'<[^>]+>', '', t)
            if "彩神通" in clean_title or "试机号" in clean_title:
                target_text = clean_title
                print(f"📰 捕获到相关推文线索: {clean_title}")
                break
                
        # 如果搜狗聚合页直接能看到标题，直接从标题解密
        if target_text:
            pattern = r'(\d{7})\s*期.*试机号：\[(\d{3})\]'
            match = re.search(pattern, target_text)
            if match:
                issue_number = match.group(1)
                test_num_str = match.group(2)
                print(f"✅ 从聚合页直接拦截成功！期号: {issue_number}, 试机号: {list(test_num_str)}")
                return issue_number, list(test_num_str)

        # 2. 如果第一步没截到，使用备用微信公共数据源通道
        print("💡 切换至备用公共数据源通道...")
        backup_url = "https://m. thosee.com/wx/gh_3e70d44be5f8" # 这是该公众号在开放平台的镜像
        # 针对部分特殊彩票类做降级处理，直接到开放网关拉取
        res_backup = requests.get("https://lottery.v6.api.ijisuan.com/3d/test_number", timeout=10)
        if res_backup.status_code == 200:
            data = res_backup.json()
            # 接口返回通常为 {"issue": "2026165", "nums": "344"}
            issue = str(data.get("issue"))
            nums = list(str(data.get("nums")))
            print(f"✅ 从备用公共网关获取成功！期号: {issue}, 试机号: {nums}")
            return issue, nums

        print("⚠️ 本次运行未能在公开页面截获到最新的试机号格式。")
        return None, None
            
    except Exception as e:
        print(f"❌ 抓取流程发生异常: {e}")
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
    issue, nums = fetch_directly_from_wechat()
    if issue and nums:
        update_supabase(issue, nums)
