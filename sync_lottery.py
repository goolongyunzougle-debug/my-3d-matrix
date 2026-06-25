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

def fetch_from_sina_lottery():
    print("🔄 正在通过新浪彩票全球公开网关拉取今日福彩 3D 试机号...")
    
    # 🚀 目标网站：新浪彩票 3D 试机号/开奖历史页（绝无海外 IP 拦截，无弹窗）
    url = "https://lottery.sina.com.cn/trend/fc3d/shijihao.html"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # 新浪彩票中文网页通常采用 gb2312 或 gbk 编码，强转防止乱码
        response.encoding = 'gbk' 
        html_text = response.text
        
        print(f"📡 成功下载网页快照，长度: {len(html_text)} 字节")
        
        # 新浪网页中表格结构的特征：第一行永远是最新一期
        # 匹配形如：<td class="period">2026165</td> ... <td class="sjh">3 4 4</td>
        # 我们用极其精准的 HTML 结构正则表达式将其捞出
        pattern = r'<td[^>]*class="period"[^>]*>(\d{7})</td>.*?<td[^>]*class="sjh"[^>]*>(\d)\s*(\d)\s*(\d)</td>'
        
        match = re.search(pattern, html_text, re.DOTALL)
        
        if match:
            issue_number = match.group(1)
            draw_numbers_array = [match.group(2), match.group(3), match.group(4)]
            
            print(f"✅ [直连拦截成功] 纯正彩神通数据已锁定！")
            print(f"📡 拦截期号: {issue_number}")
            print(f"📡 试机号数组: {draw_numbers_array}")
            return issue_number, draw_numbers_array
            
        # ---------------- 🎯 最终防御线（中彩网触屏版） ----------------
        print("💡 新浪模板微调，启用最终防御线（中彩网直连）...")
        backup_url = "http://m.zhcw.com/3d/shijihao/"
        res_b = requests.get(backup_url, headers=headers, timeout=12)
        res_b.encoding = 'utf-8'
        
        # 匹配中彩网的 7位期号 与 3个试机号数字
        b_issue = re.search(r'(\d{7})期', res_b.text)
        b_nums = re.search(r'试机号[：:]\s*(\d)\s*(\d)\s*(\d)', res_b.text)
        
        if b_issue and b_nums:
            print(f"🎉 [防御线拦截成功] 期号: {b_issue.group(1)}, 试机号: {[b_nums.group(1), b_nums.group(2), b_nums.group(3)]}")
            return b_issue.group(1), [b_nums.group(1), b_nums.group(2), b_nums.group(3)]
            
        print("⚠️ 网页模板均未匹配到格式化试机号数据。")
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
    issue, nums = fetch_from_sina_lottery()
    if issue and nums:
        update_supabase(issue, nums)
