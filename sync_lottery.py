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

def fetch_absolute_cst_data():
    print("🔄 正在启动深度网页数据清洗，目标：【拼搏在线彩神通软件】...")
    
    # 🚀 使用直接面向海外服务器开放的微信文章聚合索引镜像
    url = "https://www.wemp.app/accounts/gh_3e70d44be5f8"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.8,en;q=0.2"
    }
    
    try:
        # 1. 主线：尝试使用标准境外无阻碍网关
        response = requests.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        html = response.text
        
        print(f"📡 网页快照抓取完毕，正在执行无差别数字提取...")
        
        # 核心清洗算法：不论网页被海外安全策略怎么魔改，公众号原文里“试机号”这三个汉字是必带的。
        # 我们直接提取包含“期”和“试机号”附近的连续纯数字
        issue_match = re.search(r'(\d{7})\s*期', html)
        
        # 寻找“试机号”后面跟着的 3 个数字（中间可能夹杂代码或符号）
        num_blocks = re.findall(r'试机号.*?([0-9]).*?([0-9]).*?([0-9])', html, re.DOTALL)
        
        if issue_match and num_blocks:
            issue_number = issue_match.group(1)
            # 取最新的一组匹配数字
            draw_numbers_array = list(num_blocks[0])
            print(f"✅ [深度清洗成功] 纯正彩神通数据已锁定！期号: {issue_number}, 试机号: {draw_numbers_array}")
            return issue_number, draw_numbers_array

        # 2. 🎮 最终无敌保底：如果上面因为隐私弹窗死锁，我们直接对接老牌彩票核心同步源（作为唯一备用）
        print("💡 网页文本被加密拦截，启动备用核心同步源（3D之家彩神通专栏）...")
        backup_url = "https://3d.3dzhijia.com/shijihao/"
        res_b = requests.get(backup_url, headers=headers, timeout=12)
        res_b.encoding = 'utf-8'
        b_html = res_b.text
        
        b_issue = re.search(r'第\s*(\d{7})\s*期', b_html)
        b_num_match = re.search(r'试机号[：:]\s*<span>(\d)</span>\s*<span>(\d)</span>\s*<span>(\d)</span>', b_html)
        
        if b_issue and b_num_match:
            issue_num = b_issue.group(1)
            nums_arr = [b_num_match.group(1), b_num_match.group(2), b_num_match.group(3)]
            print(f"🎉 [备用网关同步成功] 期号: {issue_num}, 试机号: {nums_arr}")
            return issue_num, nums_arr
            
        print("⚠️ 全渠道解析失败，可能是今晚大厂网关正在维护。")
        return None, None
            
    except Exception as e:
        print(f"❌ 流程发生异常: {e}")
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
    issue, nums = fetch_absolute_cst_data()
    if issue and nums:
        update_supabase(issue, nums)
