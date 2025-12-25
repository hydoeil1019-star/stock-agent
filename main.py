import os
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import akshare as ak

# =================配置区域=================
# ⚠️ 记得把这里换成你的 DeepSeek Key
os.environ["OPENAI_API_KEY"] = "sk-268487f29699443e8bccc7c4e3703055"

os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"
os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"


# =================工具定义=================
@tool("Stock Fund Flow Tool")
def stock_fund_flow(stock_code: str):
    """
    用于查询中国A股个股的今日资金流向数据。
    Args:
        stock_code: 6位数字的股票代码 (例如 '300750')
    """
    print(f"\n[工具日志] 正在去交易所查询 {stock_code} 的资金流向...")
    try:
        market_map = {"6": "sh", "0": "sz", "3": "sz"}
        market = market_map.get(stock_code[0], "sz")
        df = ak.stock_individual_fund_flow(stock=stock_code, market=market)
        latest_data = df.iloc[-1]

        return f"""
        【{stock_code} 最新资金流向数据】
        日期: {latest_data['日期']}
        收盘价: {latest_data['收盘价']}
        主力净流入-净额: {latest_data['主力净流入-净额']} 元
        主力净流入-净占比: {latest_data['主力净流入-净占比']} %
        """
    except Exception as e:
        return f"查询失败: {str(e)}"


# =================角色定义=================
data_scout = Agent(
    role='资深金融数据侦探',
    goal='精准获取指定股票的实时资金流向数据',
    backstory='你是一名曾在华尔街工作的数据专家，擅长挖掘市场数据。',
    tools=[stock_fund_flow],
    verbose=True,
    allow_delegation=False
)

financial_analyst = Agent(
    role='首席投资分析师',
    goal='根据资金流向数据，撰写简短犀利的投资分析报告',
    backstory='你是一名拥有20年经验的基金经理。擅长通过主力资金动向判断趋势。',
    verbose=True,
    allow_delegation=False
)

# =================任务发布=================
task_fetch_data = Task(
    description='查询 "宁德时代" (代码: 300750) 的最新资金流向数据。',
    agent=data_scout,
    expected_output='包含日期、主力净流入金额的具体数据文本。'
)

task_analyze = Task(
    description='根据数据侦探提供的数据，分析主力资金动向。用中文写一段简报。',
    agent=financial_analyst,
    expected_output='一段中文的投资分析建议。',
    context=[task_fetch_data]
)

# =================启动团队=================
print("🤖 股市资金监控 Agent 团队正在启动...")

my_crew = Crew(
    agents=[data_scout, financial_analyst],
    tasks=[task_fetch_data, task_analyze],
    process=Process.sequential
)

# 这里开始干活，并把结果存到变量 result 里
result = my_crew.kickoff()

# =================【新增功能】保存文件=================
print("\n💾 正在保存分析报告...")

# 打开一个叫 report.md 的文件，'w'代表写入(write)，encoding='utf-8'防止中文乱码
with open("report.md", "w", encoding="utf-8") as f:
    f.write(str(result))

print("✅ 成功！报告已保存为 'report.md'，请在左侧项目栏查看。")