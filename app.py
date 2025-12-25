import sys
import os

# 1. 解决中文编码
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

import streamlit as st
from crewai import Agent, Task, Crew, Process
from crewai.tools import tool
import akshare as ak
import requests
from bs4 import BeautifulSoup  # 导入网页解析库

# ================= 页面配置 =================
st.set_page_config(page_title="AI 股市全能分析师", page_icon="🇨🇳", layout="wide")
st.title("🇨🇳 AI 股市全能分析师 (必应联网版)")

# ================= 侧边栏 =================
with st.sidebar:
    st.header("⚙️ 设 置")
    # 默认值留空
    api_key = st.text_input("请输入 DeepSeek API Key", type="password", value="")

    st.markdown("---")
    st.header("🔍 分析目标")
    stock_code = st.text_input("股票代码 (6位)", value="300750")
    stock_name = st.text_input("股票名称", value="宁德时代")

# ================= 核心逻辑 =================
if st.button("🚀 开始真实联网分析"):
    if not api_key.startswith("sk-"):
        st.error("❌ 请先在左侧输入正确的 API Key！")
        st.stop()

    os.environ["OPENAI_API_KEY"] = api_key
    os.environ["OPENAI_API_BASE"] = "https://api.deepseek.com"
    os.environ["OPENAI_MODEL_NAME"] = "deepseek-chat"

    with st.spinner(f'🤖 正在连接必应中国(Bing CN)搜索【{stock_name}】的真实新闻...'):

        # --- 工具 1: 查资金 (AkShare) ---
        @tool("Stock Fund Flow Tool")
        def stock_fund_flow(code: str):
            """查询A股资金流向数据"""
            try:
                market_map = {"6": "sh", "0": "sz", "3": "sz"}
                market = market_map.get(code[0], "sz")
                df = ak.stock_individual_fund_flow(stock=code, market=market)
                latest = df.iloc[-1]
                return f"日期:{latest['日期']}, 收盘价:{latest['收盘价']}, 主力净流入:{latest['主力净流入-净额']}元"
            except Exception as e:
                return f"资金查询失败: {str(e)}"


        # --- 工具 2: 搜新闻 (Bing CN 爬虫版) ---
        @tool("News Search Tool")
        def search_news(keyword: str):
            """
            使用必应中国搜索最新财经新闻。
            """
            print(f"正在搜索: {keyword}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            # 构造必应搜索链接
            url = f"https://cn.bing.com/search?q={keyword} 最新财经新闻"

            try:
                response = requests.get(url, headers=headers, timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')

                # 寻找搜索结果 (Bing的网页结构通常在 li.b_algo 里)
                results = soup.select('li.b_algo')

                news_summary = ""
                # 只取前 3 条，防止内容太多
                for i, item in enumerate(results[:3]):
                    title_tag = item.find('h2')
                    link_tag = item.find('a')
                    snippet_tag = item.find('p')

                    if title_tag and snippet_tag:
                        title = title_tag.get_text()
                        link = link_tag['href']
                        snippet = snippet_tag.get_text()
                        news_summary += f"新闻{i + 1}: {title}\n链接: {link}\n摘要: {snippet}\n\n"

                if not news_summary:
                    return "未搜索到有效新闻，可能是反爬虫策略拦截。"

                return news_summary

            except Exception as e:
                return f"搜索出错: {str(e)}"


        # --- 角色定义 ---
        scout = Agent(
            role='数据侦探',
            goal='获取资金数据',
            backstory='只相信数字的专家。',
            tools=[stock_fund_flow],
            verbose=False
        )

        reporter = Agent(
            role='财经记者',
            goal='从互联网搜索真实新闻',
            backstory='擅长使用搜索引擎挖掘市场消息。',
            tools=[search_news],
            verbose=False
        )

        analyst = Agent(
            role='首席投资顾问',
            goal='写出深度研报',
            backstory='顶级基金经理，擅长结合资金面和消息面分析。',
            verbose=False
        )

        # --- 任务定义 ---
        task_data = Task(
            description=f'查询 {stock_code} 的资金流向。',
            agent=scout,
            expected_output='资金数据'
        )

        task_news = Task(
            description=f'去网上搜一下 "{stock_name}" 最近有没有什么大事。',
            agent=reporter,
            expected_output='新闻摘要'
        )

        task_report = Task(
            description='''
            根据【真实资金数据】和【真实新闻搜索结果】，写一份分析报告。
            分析：当前的新闻是利好还是利空？这是否解释了今天的资金流向？
            ''',
            agent=analyst,
            expected_output='Markdown格式的研报',
            context=[task_data, task_news]
        )

        # --- 启动 ---
        crew = Crew(
            agents=[scout, reporter, analyst],
            tasks=[task_data, task_news, task_report],
            process=Process.sequential
        )

        result = crew.kickoff()

    # ================= 结果展示 =================
    st.success("✅ 真实联网分析完成！")
    st.markdown("### 📊 深度投研报告")
    st.markdown(result)