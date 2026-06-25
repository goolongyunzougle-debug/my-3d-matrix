import os
import sys
import requests
from supabase import create_client, Client

# 1. 初始化 Supabase 客户端
SUPABASE_URL = "https://ybjgkfhcagqqfnqekycr.supabase.co"
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_KEY:
    print("❌ 错误: 未找到必要环境变量，请检查 GitHub Secrets 配置。")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def run_manual_injection():
    # 🚀 这允许你随时通过 GitHub Actions 界面、或者本地运行，直接把数字当作参数传进去！
    # 比如：python sync_lottery.py 2026165 344
    if len(sys.argv) >= 3:
        issue_number = sys.argv[1]
        draw_numbers_array = list(sys.argv[2])
        print(f"✅ [手动注入模式] 成功接收外部指定数据！期号: {issue_number}, 试机号: {draw_numbers_array}")
        return issue_number, draw_numbers_array
        
    print("🔄 正在通过高速免封锁协议，直接向主数据库请求同步流...")
    try:
        # 🚀 方案 B：如果未手动指定，直接去拉取由国内秒级无障碍同步上去的影子数据
        # 无论微信怎么封海外IP，这条通道使用标准的 https 协议，永远畅通无阻
        res = requests.get("https://raw.githubusercontent.com/goolongyunzougle-debug/lottery_records/main/today.json", timeout=10)
        if res.status_code == 200:
            data = res.json()
            print(f"✅ [影子通道同步成功] 期号: {data['issue']}, 试机号: {list(data['nums'])}")
            return str(data['issue']), list(data['nums'])
    except Exception:
        pass
        
    print("⚠️ 本次执行未检测到注入参数或外部数据快照。")
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
    issue, nums = run_manual_injection()
    if issue and nums:
        update_supabase(issue, nums)
