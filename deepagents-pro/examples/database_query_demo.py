"""
数据库查询演示 - 电商业务分析场景

演示如何通过 DeepAgent-Pro 对电商数据库进行自然语言查询和分析。

前置条件：
1. 确保 test.db 已创建（运行 python scripts/create_business_db.py）
2. 确保服务已启动（python -m uvicorn deepagent_pro.main:app --reload）

使用方式：
    python examples/database_query_demo.py
"""

import httpx
import time
import json
from typing import List, Dict

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=120)


def print_section(title: str):
    """打印分节标题"""
    print("\n" + "=" * 60, flush=True)
    print(f"  {title}", flush=True)
    print("=" * 60, flush=True)


def print_query_result(question: str, response: str, max_len: int = 800):
    """打印查询结果"""
    print(f"\n📝 问题: {question}", flush=True)
    print(f"🤖 回复:\n{response[:max_len]}", flush=True)
    if len(response) > max_len:
        print(f"\n... (省略 {len(response, flush=True) - max_len} 字符)")


def check_service():
    """检查服务是否运行"""
    try:
        r = client.get("/health")
        assert r.status_code == 200
        print("✅ 服务状态: 正常运行", flush=True)
        return True
    except Exception:
        print("❌ 错误: 服务未启动！请先运行:", flush=True)
        print("   python -m uvicorn deepagent_pro.main:app --reload", flush=True)
        return False


def demo_register_datasource():
    """场景一：注册数据源"""
    print_section("场景一：注册电商数据库数据源")

    resp = client.post("/api/v1/datasource", json={
        "name": "ecommerce",
        "connection_url": "sqlite:///D:/code/deepagent-pro/data/test.db",
        "description": "电商业务数据库 - 包含用户、商品、订单、评价等10张表"
    })

    if resp.status_code == 200:
        result = resp.json()
        print(f"✅ 数据源注册成功:", flush=True)
        print(f"   名称: {result['name']}", flush=True)
        print(f"   连接: {result['connection_url']}", flush=True)
        print(f"   描述: {result['description']}", flush=True)
        print(f"   状态: {result['status']}", flush=True)
        return True
    else:
        print(f"❌ 注册失败: {resp.text}", flush=True)
        return False


def demo_list_tables():
    """场景二：查看数据库表结构"""
    print_section("场景二：查看数据库表结构")

    resp = client.post("/api/v1/chat", json={
        "message": "列出 ecommerce 数据库中的所有表，并说明每个表的作用",
        "thread_id": "db-demo-tables"
    })

    if resp.status_code == 200:
        data = resp.json()
        print_query_result(
            "列出数据库表结构",
            data['response']
        )
        print("\n📊 工具调用:", flush=True)
        for tc in data.get('tool_calls', []):
            print(f"   - {tc['name']}", flush=True)


def demo_sales_analysis():
    """场景三：销售趋势分析"""
    print_section("场景三：销售趋势分析")

    questions = [
        "统计 ecommerce 数据库最近3个月的订单数量和总销售额",
        "分析各月份的平均客单价（订单总金额/订单数）",
        "找出销售额最高的前5个订单"
    ]

    thread_id = "db-demo-sales"

    for idx, question in enumerate(questions, 1):
        print(f"\n--- 问题 {idx}/3 ---", flush=True)
        resp = client.post("/api/v1/chat", json={
            "message": question,
            "thread_id": thread_id
        })

        if resp.status_code == 200:
            data = resp.json()
            print_query_result(question, data['response'])
            time.sleep(1)  # 避免请求过快


def demo_customer_analysis():
    """场景四：高价值客户分析"""
    print_section("场景四：高价值客户分析")

    resp = client.post("/api/v1/chat", json={
        "message": """分析 ecommerce 数据库的高价值客户：
1. 找出总消费金额最高的前10名客户
2. 统计这些客户的等级分布（bronze/silver/gold/platinum）
3. 分析高价值客户的订单数量和平均客单价""",
        "thread_id": "db-demo-customers"
    })

    if resp.status_code == 200:
        data = resp.json()
        print_query_result("高价值客户分析", data['response'], max_len=1200)


def demo_product_analysis():
    """场景五：商品分析"""
    print_section("场景五：商品分析")

    questions = [
        "查询 ecommerce 数据库中哪些商品的评价最高（4.5分以上），并列出这些商品的库存情况",
        "找出库存数量最多的前5个商品，以及它们所属的分类"
    ]

    thread_id = "db-demo-products"

    for idx, question in enumerate(questions, 1):
        print(f"\n--- 问题 {idx}/2 ---", flush=True)
        resp = client.post("/api/v1/chat", json={
            "message": question,
            "thread_id": thread_id
        })

        if resp.status_code == 200:
            data = resp.json()
            print_query_result(question, data['response'])
            time.sleep(1)


def demo_complex_query():
    """场景六：复杂联表查询"""
    print_section("场景六：复杂联表查询分析")

    resp = client.post("/api/v1/chat", json={
        "message": """对 ecommerce 数据库进行综合分析：

1. 统计每个商品分类的订单数量和销售总额
2. 找出订单数量最多但总销售额不是最高的分类（可能有低价跑量情况）
3. 分析该分类下的热销商品（销量前3）

请用表格形式展示结果，并给出你的业务洞察。""",
        "thread_id": "db-demo-complex"
    })

    if resp.status_code == 200:
        data = resp.json()
        print_query_result("复杂联表查询分析", data['response'], max_len=1500)
        print("\n📊 工具调用详情:", flush=True)
        for tc in data.get('tool_calls', []):
            args_str = json.dumps(tc['args'], ensure_ascii=False)[:100]
            print(f"   🔧 {tc['name']}: {args_str}...", flush=True)


def demo_multi_turn_analysis():
    """场景七：多轮对话深入分析"""
    print_section("场景七：多轮对话深入分析")

    thread_id = "db-demo-multiturn"

    # 第1轮：初步查询
    print("\n>>> 第1轮：查询各分类销售情况", flush=True)
    resp = client.post("/api/v1/chat", json={
        "message": "查询 ecommerce 数据库每个商品分类的销售总额，按降序排列",
        "thread_id": thread_id
    })

    if resp.status_code == 200:
        data = resp.json()
        print(f"🤖 回复: {data['response'][:600]}...", flush=True)

    # 第2轮：深入追问
    print("\n>>> 第2轮：追问销售最高的分类详情", flush=True)
    resp = client.post("/api/v1/chat", json={
        "message": "刚才查询结果中，销售额最高的分类是什么？请列出该分类下销量前5的商品",
        "thread_id": thread_id
    })

    if resp.status_code == 200:
        data = resp.json()
        print(f"🤖 回复: {data['response'][:600]}...", flush=True)

    # 第3轮：进一步分析
    print("\n>>> 第3轮：分析这些商品的客户评价", flush=True)
    resp = client.post("/api/v1/chat", json={
        "message": "查看这些热销商品的评价情况，平均评分是多少？有没有差评？",
        "thread_id": thread_id
    })

    if resp.status_code == 200:
        data = resp.json()
        print(f"🤖 回复: {data['response'][:600]}...", flush=True)


def demo_stream_query():
    """场景八：流式查询（实时展示分析过程）"""
    print_section("场景八：流式查询 - 实时查看分析过程")

    url = f"{BASE}/api/v1/chat/db-demo-stream/stream"
    params = {
        "message": "分析 ecommerce 数据库：哪些商品的库存可能积压（库存高但最近30天没有订单）？"
    }

    print("📝 问题: 哪些商品的库存可能积压？", flush=True)
    print("🔄 开始接收流式事件...\n", flush=True)

    with httpx.stream("GET", url, params=params, timeout=180) as resp:
        event_count = 0
        tool_calls = 0

        for line in resp.iter_lines():
            if not line.strip():
                continue

            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()
                try:
                    parsed = json.loads(data)

                    if event_type == "start":
                        print(f"🚀 {parsed.get('thread_id', '', flush=True)} - 开始分析")

                    elif event_type == "tool_call":
                        tool_calls += 1
                        name = parsed.get('name', '')
                        args = parsed.get('args', {})
                        print(f"🔧 工具调用 #{tool_calls}: {name}", flush=True)
                        if name == "execute_sql":
                            query = args.get('query', '')[:80]
                            print(f"   SQL: {query}...", flush=True)

                    elif event_type == "tool_result":
                        name = parsed.get('name', '')
                        content = parsed.get('content', '')[:100]
                        print(f"✓ 结果: {name} → {content}...", flush=True)

                    elif event_type == "message":
                        content = parsed.get('content', '')
                        if content and len(content) < 200:
                            print(f"💬 {content}", flush=True)

                    elif event_type == "done":
                        print(f"\n✅ 分析完成", flush=True)
                        print(f"   总事件数: {event_count}", flush=True)
                        print(f"   工具调用数: {tool_calls}", flush=True)

                    event_count += 1

                except json.JSONDecodeError:
                    pass


# 场景列表（名称 → 函数），方便按编号选择
DEMOS = {
    "1": ("注册数据源", demo_register_datasource),
    "2": ("查看表结构", demo_list_tables),
    "3": ("销售趋势分析", demo_sales_analysis),
    "4": ("高价值客户分析", demo_customer_analysis),
    "5": ("商品分析", demo_product_analysis),
    "6": ("复杂联表查询", demo_complex_query),
    "7": ("多轮对话分析", demo_multi_turn_analysis),
    "8": ("流式查询", demo_stream_query),
}


def main():
    """主函数

    用法:
        python -u examples/database_query_demo.py            # 运行全部场景
        python -u examples/database_query_demo.py 1 3 4     # 只运行场景 1、3、4
    """
    import argparse

    parser = argparse.ArgumentParser(description="DeepAgent-Pro 数据库查询演示")
    parser.add_argument("scenes", nargs="*", help="要运行的场景编号（1-8），不传则全部运行")
    args = parser.parse_args()

    # 确定要运行的场景
    if args.scenes:
        selected = []
        for s in args.scenes:
            if s in DEMOS:
                selected.append((s, DEMOS[s]))
            else:
                print(f"⚠ 场景 {s} 不存在，可选: {list(DEMOS.keys(, flush=True))}")
                return
    else:
        selected = list(DEMOS.items())

    print("\n" + "=" * 60, flush=True)
    print("  DeepAgent-Pro - 数据库查询演示", flush=True)
    print("  电商业务分析场景", flush=True)
    print("=" * 60, flush=True)

    # 检查服务
    if not check_service():
        return

    print(f"\n⏱ 将运行 {len(selected, flush=True)} 个场景，预计耗时 {len(selected) * 0.5:.0f}-{len(selected)} 分钟")
    print("📋 运行场景:", flush=True)
    for idx, (key, (name, _)) in enumerate(selected, 1):
        print(f"   {idx}. {name}", flush=True)
    print(, flush=True)

    try:
        for idx, (key, (name, func)) in enumerate(selected, 1):
            print(f"\n[进度 {idx}/{len(selected, flush=True)}]", flush=True)
            func()
            time.sleep(1)

        print_section("演示完成")
        print("\n✅ 所有场景演示完毕！", flush=True)
        print("\n💡 提示：", flush=True)
        print("   - 通过 Web UI http://localhost:8000 继续探索", flush=True)
        print("   - 数据源 'ecommerce' 已注册，可直接使用", flush=True)

    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断演示", flush=True)
    except Exception as e:
        print(f"\n\n❌ 演示出错: {e}", flush=True)
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
