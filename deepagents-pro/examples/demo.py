"""
DeepAgent-Pro 使用示例

后端演示脚本（均需在项目根配置 ``.env`` 中的 API Key，除非仅 ``--dry-run``）：
  ``store_backend_demo.py`` — StoreBackend（LangGraph Store）；
  ``local_shell_backend_demo.py`` — LocalShellBackend（需 ``--accept-risk``）；
  ``sandbox_backend_demo.py`` — LangSmithSandbox（``--live`` 需 LangSmith 模板）；
  ``composite_backend_demo.py`` — CompositeBackend 多路由；
  ``memory_backends_demo.py`` — State vs Store 对照；
  ``filesystem_backend_demo.py`` — FilesystemBackend 映射磁盘。

使用前确保服务已启动:
    python -m uvicorn deepagent_pro.main:app --reload

然后运行本脚本:
    python examples/demo.py
"""

import httpx
import time
import json

BASE = "http://localhost:8000"
client = httpx.Client(base_url=BASE, timeout=120)


def demo_1_chat_simple():
    """
    场景一：直接对话提问

    就像跟 ChatGPT 聊天一样，发一条消息，得到回复。
    thread_id 是对话 ID，同一个 ID 的消息会保持上下文连续。
    """
    print("\n【场景一】直接对话提问")
    print("-" * 40)

    resp = client.post("/api/v1/chat", json={
        "message": "你好，你能做什么？",
        "thread_id": "demo-001",
    })

    data = resp.json()
    print(f"智能体回复:\n{data['response']}\n")


def demo_2_analyze_csv():
    """
    场景二：上传 CSV 文件，让智能体分析

    步骤：
    1. POST /api/v1/analyze  上传文件 + 提问 → 得到 task_id
    2. GET  /api/v1/analyze/{task_id}  轮询查结果（因为分析需要时间）
    """
    print("\n【场景二】上传 CSV 文件分析")
    print("-" * 40)

    # 第一步：上传文件
    with open("data/uploads/sales_demo.csv", "rb") as f:
        resp = client.post("/api/v1/analyze", files={
            "file": ("sales_demo.csv", f, "text/csv"),
        }, data={
            "question": "帮我分析各区域的销售额对比，哪个区域表现最好？",
        })

    task_id = resp.json()["task_id"]
    print(f"任务已提交，task_id = {task_id}")

    # 第二步：轮询等待结果
    print("等待分析完成...")
    for i in range(20):
        time.sleep(5)
        resp = client.get(f"/api/v1/analyze/{task_id}")
        result = resp.json()
        status = result.get("status", "unknown")

        if status == "completed":
            print(f"\n分析完成！用时约 {(i+1)*5} 秒")
            print(f"分析报告:\n{result.get('result', '')}\n")
            return
        elif status == "failed":
            print(f"分析失败: {result.get('error', '未知错误')}")
            return
        else:
            print(f"  仍在分析中... ({(i+1)*5}秒)")

    print("超时，任务仍在进行中")


def demo_3_multi_turn_chat():
    """
    场景三：多轮对话分析数据

    关键点：同一个 thread_id 的多条消息共享上下文。
    先告诉智能体数据文件路径，然后连续追问。
    """
    print("\n【场景三】多轮对话分析")
    print("-" * 40)
    thread = "demo-multiturn-001"

    # 第 1 轮：告诉智能体数据在哪
    print(">>> 第 1 轮：加载数据")
    resp = client.post("/api/v1/chat", json={
        "message": "请加载文件 data/uploads/sales_demo.csv 并告诉我数据概况",
        "thread_id": thread,
    })
    print(f"回复:\n{resp.json()['response'][:500]}\n")

    # 第 2 轮：追问具体分析
    print(">>> 第 2 轮：追问分析")
    resp = client.post("/api/v1/chat", json={
        "message": "哪个月的利润最高？利润率是多少？",
        "thread_id": thread,
    })
    print(f"回复:\n{resp.json()['response'][:500]}\n")


def demo_4_datasource():
    """
    场景四：管理数据库连接

    先注册一个数据库连接，之后可以让智能体直接查询这个数据库。
    """
    print("\n【场景四】数据库连接管理")
    print("-" * 40)

    # 添加数据源
    resp = client.post("/api/v1/datasource", json={
        "name": "业务数据库",
        "connection_url": "sqlite:///data/analysis.db",
        "description": "公司业务数据",
    })
    print(f"添加数据源: {resp.json()}")

    # 查看所有数据源
    resp = client.get("/api/v1/datasource")
    print(f"已配置的数据源: {json.dumps(resp.json(), ensure_ascii=False, indent=2)}")


def demo_5_stream():
    """
    场景五：SSE 流式响应（实时看到分析过程）

    用 GET 请求 + message 参数，服务器会以 SSE 事件流的方式逐步返回结果。
    适合前端实时展示"正在思考..."的效果。
    """
    print("\n【场景五】SSE 流式响应")
    print("-" * 40)

    url = f"{BASE}/api/v1/chat/demo-stream-001/stream?message=你好，简单介绍你自己"
    print("开始接收流式事件:")

    with httpx.stream("GET", url, timeout=120) as resp:
        for line in resp.iter_lines():
            if line.startswith("event:"):
                event_type = line[len("event:"):].strip()
            elif line.startswith("data:"):
                data = line[len("data:"):].strip()
                try:
                    parsed = json.loads(data)
                    if event_type == "message":
                        content = parsed.get("content", "")
                        if content:
                            print(f"  [{event_type}] {content[:200]}")
                    elif event_type == "tool_call":
                        print(f"  [工具调用] {parsed.get('name', '')}")
                    elif event_type in ("start", "done"):
                        print(f"  [{event_type}] {data}")
                except json.JSONDecodeError:
                    pass
    print()


if __name__ == "__main__":
    print("=" * 50)
    print("  DeepAgent-Pro 接口使用演示")
    print("=" * 50)

    # 先检查服务是否运行
    try:
        r = client.get("/health")
        assert r.status_code == 200
        print("服务状态: 正常运行\n")
    except Exception:
        print("错误: 服务未启动！请先运行:")
        print("  python -m uvicorn deepagent_pro.main:app --reload")
        exit(1)

    # 按需选择要运行的演示
    # 你可以注释掉不需要的场景

    demo_1_chat_simple()       # 简单对话
    demo_4_datasource()        # 数据库管理（不调用 LLM，速度快）
    demo_2_analyze_csv()       # 上传文件分析（会调用 LLM，耗时较长）
    demo_3_multi_turn_chat() # 多轮对话（会调用 LLM 两次）
    demo_5_stream()          # 流式响应

    print("\n演示完成！")
