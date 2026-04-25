"""
数据可视化演示 - 多种图表类型展示

演示 DeepAgent-Pro 的数据可视化能力，涵盖：
- 折线图（趋势分析）
- 柱状图（分类比较）
- 散点图（关系分析）
- 饼图（占比分布）
- 直方图（数值分布）
- 箱线图（离群值检测）
- 热力图（相关性分析）

前置条件：
1. 确保服务已启动（python -m uvicorn deepagent_pro.main:app --reload）

使用方式：
    python -u examples/visualization_demo.py            # 运行全部
    python -u examples/visualization_demo.py 1 2 3     # 只运行场景 1、2、3
"""

import os
import csv
import random
import httpx
import time
import json
from datetime import datetime, timedelta
from pathlib import Path

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=120)

DATA_DIR = Path("data/uploads")
DATA_DIR.mkdir(parents=True, exist_ok=True)


# ── 工具函数 ──


def p(text: str = ""):
    print(text, flush=True)


def print_section(title: str):
    p(f"\n{'=' * 60}")
    p(f"  {title}")
    p("=" * 60)


def print_query_result(question: str, response: str, max_len: int = 800):
    p(f"\n📝 问题: {question}")
    p(f"🤖 回复:\n{response[:max_len]}")
    if len(response) > max_len:
        p(f"\n... (省略 {len(response) - max_len} 字符)")


def check_service():
    try:
        r = client.get("/health")
        assert r.status_code == 200
        p("✅ 服务状态: 正常运行")
        return True
    except Exception:
        p("❌ 服务未启动！请先运行:")
        p("   python -m uvicorn deepagent_pro.main:app --reload")
        return False


def chat(message: str, thread_id: str) -> dict:
    """发送对话请求"""
    resp = client.post("/api/v1/chat", json={
        "message": message,
        "thread_id": thread_id,
    })
    return resp.json()


# ── 数据生成 ──


def generate_monthly_sales_csv() -> str:
    """生成月度销售数据 CSV（12个月 × 5个区域）"""
    path = DATA_DIR / "viz_monthly_sales.csv"
    regions = ["华北", "华东", "华南", "西南", "东北"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["月份", "区域", "销售额", "成本", "订单数", "客户数"])
        for month in range(1, 13):
            for region in regions:
                base = random.randint(8000, 25000)
                cost = int(base * random.uniform(0.5, 0.75))
                orders = random.randint(50, 300)
                customers = int(orders * random.uniform(0.5, 0.9))
                writer.writerow([f"{month}月", region, base, cost, orders, customers])
    p(f"📊 生成月度销售数据: {path} ({sum(1 for _ in open(path)) - 1} 行)")
    return str(path)


def generate_product_performance_csv() -> str:
    """生成商品表现数据 CSV"""
    path = DATA_DIR / "viz_product_performance.csv"
    categories = ["电子产品", "服装", "食品", "家居", "运动户外"]
    products = [
        "智能手机", "笔记本电脑", "蓝牙耳机", "运动鞋", "羽绒服",
        "T恤", "电饭煲", "冰箱", "跑步机", "瑜伽垫",
        "零食礼包", "咖啡", "沙发", "台灯", "手表",
    ]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["商品", "分类", "月销量", "单价", "评分", "退货率", "库存周转天数"])
        for product in products:
            cat = random.choice(categories)
            sales = random.randint(100, 5000)
            price = round(random.uniform(50, 8000), 2)
            rating = round(random.uniform(3.0, 5.0), 1)
            return_rate = round(random.uniform(0.5, 15.0), 1)
            turnover = random.randint(5, 90)
            writer.writerow([product, cat, sales, price, rating, return_rate, turnover])
    p(f"📊 生成商品表现数据: {path} ({sum(1 for _ in open(path)) - 1} 行)")
    return str(path)


def generate_employee_csv() -> str:
    """生成员工数据 CSV（适合箱线图/直方图）"""
    path = DATA_DIR / "viz_employees.csv"
    departments = ["技术部", "市场部", "销售部", "运营部", "人事部"]
    levels = ["初级", "中级", "高级", "总监"]
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["姓名", "部门", "级别", "工龄", "月薪", "绩效评分", "项目数"])
        for i in range(1, 81):
            dept = random.choice(departments)
            level = random.choice(levels)
            years = random.randint(1, 20)
            base_salary = {"初级": 8000, "中级": 15000, "高级": 25000, "总监": 40000}[level]
            salary = int(base_salary * random.uniform(0.8, 1.3))
            score = round(random.uniform(60, 100), 1)
            projects = random.randint(1, 12)
            writer.writerow([f"员工{i:03d}", dept, level, years, salary, score, projects])
    p(f"📊 生成员工数据: {path} ({sum(1 for _ in open(path)) - 1} 行)")
    return str(path)


# ── 演示场景 ──


def demo_0_prepare_data():
    """场景0：准备演示数据"""
    print_section("场景零：准备演示数据")

    paths = {
        "monthly_sales": generate_monthly_sales_csv(),
        "product_performance": generate_product_performance_csv(),
        "employees": generate_employee_csv(),
    }

    p("\n📁 数据文件准备完成:")
    for name, path in paths.items():
        size = os.path.getsize(path)
        p(f"   {name}: {path} ({size:,} bytes)")

    return paths


def demo_1_line_chart(paths: dict):
    """场景1：折线图 - 月度销售趋势"""
    print_section("场景一：折线图 — 月度销售趋势分析")

    file_path = paths["monthly_sales"]

    resp = chat(
        f"加载文件 {file_path}，分析各区域的月度销售趋势，"
        "用折线图展示每个区域12个月的销售额变化，"
        "并在图表中标注销售额最高和最低的月份",
        thread_id="viz-line-001",
    )
    print_query_result("各区域月度销售趋势折线图", resp["response"])
    _print_tool_calls(resp)


def demo_2_bar_chart(paths: dict):
    """场景2：柱状图 - 区域销售对比"""
    print_section("场景二：柱状图 — 区域销售额对比")

    file_path = paths["monthly_sales"]

    resp = chat(
        f"基于文件 {file_path}，用柱状图展示各区域的总销售额对比，"
        "同时在柱子上标注具体金额，分析哪个区域表现最好、哪个需要加强",
        thread_id="viz-bar-001",
    )
    print_query_result("区域销售额柱状图", resp["response"])
    _print_tool_calls(resp)


def demo_3_scatter_chart(paths: dict):
    """场景3：散点图 - 销量与价格关系"""
    print_section("场景三：散点图 — 商品销量与价格关系分析")

    file_path = paths["product_performance"]

    resp = chat(
        f"加载文件 {file_path}，用散点图分析商品单价与月销量的关系，"
        "判断是否存在价格越高销量越低的趋势，找出性价比最高的商品",
        thread_id="viz-scatter-001",
    )
    print_query_result("商品销量与价格关系散点图", resp["response"])
    _print_tool_calls(resp)


def demo_4_pie_chart(paths: dict):
    """场景4：饼图 - 分类销售占比"""
    print_section("场景四：饼图 — 商品分类销售占比")

    file_path = paths["product_performance"]

    resp = chat(
        f"基于文件 {file_path}，用饼图展示各商品分类的月销量占比，"
        "标注百分比，分析哪个分类是销售主力",
        thread_id="viz-pie-001",
    )
    print_query_result("商品分类销售占比饼图", resp["response"])
    _print_tool_calls(resp)


def demo_5_hist_and_box(paths: dict):
    """场景5：直方图 + 箱线图 — 薪资分布"""
    print_section("场景五：直方图 & 箱线图 — 员工薪资分布分析")

    file_path = paths["employees"]

    # 直方图
    p("\n--- 5a: 直方图 ---")
    resp = chat(
        f"加载文件 {file_path}，用直方图分析员工月薪的分布情况，"
        "判断薪资分布是否偏态，大部分员工薪资集中在哪个区间",
        thread_id="viz-hist-001",
    )
    print_query_result("员工月薪分布直方图", resp["response"])
    _print_tool_calls(resp)

    time.sleep(2)

    # 箱线图
    p("\n--- 5b: 箱线图 ---")
    resp = chat(
        f"基于文件 {file_path}，用箱线图比较各部门的薪资分布差异，"
        "找出哪些部门存在薪资离群值（异常高或异常低）",
        thread_id="viz-box-001",
    )
    print_query_result("各部门薪资箱线图", resp["response"])
    _print_tool_calls(resp)


def demo_6_heatmap(paths: dict):
    """场景6：热力图 - 相关性分析"""
    print_section("场景六：热力图 — 数据相关性分析")

    file_path = paths["product_performance"]

    resp = chat(
        f"加载文件 {file_path}，生成数值列的相关性热力图，"
        "分析哪些指标之间有强相关性（如评分与退货率、销量与价格等），给出业务洞察",
        thread_id="viz-heatmap-001",
    )
    print_query_result("商品指标相关性热力图", resp["response"])
    _print_tool_calls(resp)


def demo_7_comprehensive(paths: dict):
    """场景7：综合分析 — 生成完整分析报告（含多个图表）"""
    print_section("场景七：综合分析 — 一键生成多图表分析报告")

    file_path = paths["monthly_sales"]

    resp = chat(
        f"对文件 {file_path} 进行全面分析，生成完整的销售分析报告，要求：\n\n"
        "1. 数据概览：总销售额、总订单数、平均客单价\n"
        "2. 趋势分析：用折线图展示月度销售额趋势\n"
        "3. 区域对比：用柱状图对比各区域销售表现\n"
        "4. 占比分析：用饼图展示各区域销售额占比\n"
        "5. 关键发现：总结3条最重要的业务洞察\n\n"
        "请依次生成图表并汇总分析结论。",
        thread_id="viz-comprehensive-001",
    )
    print_query_result("综合销售分析报告（多图表）", resp["response"], max_len=1500)

    p("\n📊 生成的图表:")
    chart_dir = DATA_DIR / "charts"
    if chart_dir.exists():
        for f in sorted(chart_dir.glob("*.png")):
            mtime = datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M:%S")
            p(f"   📈 {f.name} ({f.stat().st_size:,} bytes, {mtime})")


def _print_tool_calls(resp: dict):
    """打印工具调用摘要"""
    tool_calls = resp.get("tool_calls", [])
    if tool_calls:
        p(f"\n🔧 工具调用 ({len(tool_calls)} 次):")
        for tc in tool_calls:
            name = tc.get("name", "")
            args = tc.get("args", {})
            if name == "create_chart":
                chart_type = args.get("chart_type", "?")
                title = args.get("title", "")
                p(f"   - create_chart: {chart_type} | {title}")
            elif name == "create_heatmap":
                title = args.get("title", "")
                p(f"   - create_heatmap: {title}")
            elif name in ("load_csv", "load_excel"):
                fp = args.get("file_path", "")
                p(f"   - {name}: {Path(fp).name}")
            else:
                p(f"   - {name}")


# ── 场景注册 ──

DEMOS = {
    "0": ("准备演示数据", lambda paths=None: demo_0_prepare_data()),
    "1": ("折线图 — 月度销售趋势", lambda paths=None: demo_1_line_chart(paths)),
    "2": ("柱状图 — 区域销售对比", lambda paths=None: demo_2_bar_chart(paths)),
    "3": ("散点图 — 销量与价格关系", lambda paths=None: demo_3_scatter_chart(paths)),
    "4": ("饼图 — 分类销售占比", lambda paths=None: demo_4_pie_chart(paths)),
    "5": ("直方图 & 箱线图 — 薪资分布", lambda paths=None: demo_5_hist_and_box(paths)),
    "6": ("热力图 — 相关性分析", lambda paths=None: demo_6_heatmap(paths)),
    "7": ("综合分析 — 多图表报告", lambda paths=None: demo_7_comprehensive(paths)),
}


def main():
    import argparse

    parser = argparse.ArgumentParser(description="DeepAgent-Pro 数据可视化演示")
    parser.add_argument("scenes", nargs="*", help="场景编号（0-7），不传则全部运行")
    args = parser.parse_args()

    p(f"\n{'=' * 60}")
    p("  DeepAgent-Pro - 数据可视化演示")
    p("=" * 60)

    if not check_service():
        return

    # 确定要运行的场景
    if args.scenes:
        selected_keys = []
        for s in args.scenes:
            if s in DEMOS:
                selected_keys.append(s)
            else:
                p(f"⚠ 场景 {s} 不存在，可选: {list(DEMOS.keys())}")
                return
    else:
        selected_keys = list(DEMOS.keys())

    p(f"\n⏱ 将运行 {len(selected_keys)} 个场景")
    p("📋 场景列表:")
    for key in selected_keys:
        p(f"   {key}. {DEMOS[key][0]}")

    # 先准备数据
    paths = demo_0_prepare_data()
    if "0" in selected_keys:
        selected_keys = [k for k in selected_keys if k != "0"]

    try:
        for idx, key in enumerate(selected_keys, 1):
            p(f"\n[进度 {idx}/{len(selected_keys)}]")
            DEMOS[key][1](paths)
            time.sleep(1)

        print_section("演示完成")

        # 列出所有生成的图表
        chart_dir = DATA_DIR / "charts"
        if chart_dir.exists():
            charts = sorted(chart_dir.glob("*.png"))
            p(f"\n📁 共生成 {len(charts)} 个图表文件:")
            for f in charts:
                size_kb = f.stat().st_size / 1024
                p(f"   📈 {f.name} ({size_kb:.0f} KB)")

        p("\n💡 提示:")
        p("   - 图表文件保存在 data/uploads/charts/ 目录")
        p("   - 通过 Web UI http://localhost:8000 可在线查看")

    except KeyboardInterrupt:
        p("\n\n⚠ 用户中断演示")
    except Exception as e:
        p(f"\n\n❌ 演示出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
