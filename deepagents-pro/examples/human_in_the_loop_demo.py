"""
DeepAgent Human-in-the-Loop 演示

本示例展示如何在敏感操作前添加人工审批环节：

1. 配置 interrupt_on 对敏感工具启用中断
2. Agent 执行到敏感工具时暂停，等待人工决策
3. 通过 Command(resume={"decisions": decisions}) 恢复执行
4. 支持 approve（批准）、reject（拒绝）、edit（修改参数）

运行::

    pip install -e .
    python examples/human_in_the_loop_demo.py

参考文档：https://docs.langchain.com/oss/python/deepagents/human-in-the-loop
"""

from __future__ import annotations

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
import sys
if _SRC.is_dir() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from langchain.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.types import Command

from deepagents import create_deep_agent, SubAgent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend
from langgraph.checkpoint.memory import MemorySaver

from deepagent_pro.agent.core import build_model
from deepagent_pro.config import get_settings


# ============== 路径转换工具 ==============

UPLOADS_DIR = _REPO_ROOT / "data" / "uploads"


def virtual_to_real_path(virtual_path: str) -> Path:
    if virtual_path.startswith("/data/"):
        return UPLOADS_DIR / virtual_path[6:]
    return UPLOADS_DIR / virtual_path.lstrip("/data/")


def ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


# ============== HITL 审批处理辅助函数 ==============

from typing import Any, TypedDict

from langgraph.types import GraphOutput


class InterruptInfo(TypedDict):
    action_requests: list[dict[str, Any]]
    review_configs: dict[str, list[str]]


def parse_interrupts(result: GraphOutput) -> InterruptInfo:
    """解析 GraphOutput 中的中断信息。

    Args:
        result: agent.invoke() 返回的 GraphOutput 对象

    Returns:
        InterruptInfo，包含 action_requests 和 review_configs
    """
    action_requests: list[dict[str, Any]] = []
    review_configs: dict[str, list[str]] = {}

    if not result.interrupts:
        return InterruptInfo(action_requests=[], review_configs={})

    for interrupt in result.interrupts:
        interrupt_value = getattr(interrupt, "value", {}) or {}
        if not isinstance(interrupt_value, dict):
            continue

        # 提取 action_requests
        ar = interrupt_value.get("action_requests", [])
        if isinstance(ar, list):
            action_requests.extend(ar)

        # 提取 review_configs，建立 action_name -> allowed_decisions 的映射
        configs = interrupt_value.get("review_configs", []) or []
        if isinstance(configs, list):
            for cfg_item in configs:
                action_name = cfg_item.get("action_name", "")
                allowed = cfg_item.get("allowed_decisions", ["approve", "reject", "edit"])
                if action_name:
                    review_configs[action_name] = allowed

    return InterruptInfo(action_requests=action_requests, review_configs=review_configs)


def collect_decisions(
    action_requests: list[dict[str, Any]],
    review_configs: dict[str, list[str]],
    auto_approve: bool,
) -> list[dict[str, Any]]:
    """收集审批决策。

    Args:
        action_requests: 中断中的操作请求列表
        review_configs: 操作名到允许决策的映射
        auto_approve: True=自动批准，False=交互式输入

    Returns:
        decisions 列表
    """
    decisions: list[dict[str, Any]] = []

    for req in action_requests:
        tool_name = req.get("name", "unknown")
        tool_args = req.get("args", {})
        allowed = review_configs.get(tool_name, ["approve", "reject", "edit"])

        print(f"\n--- 待审批操作 ---")
        print(f"工具: {tool_name}")
        print(f"参数: {tool_args}")
        print(f"允许操作: {allowed}")

        if auto_approve:
            decisions.append({"type": "approve"})
            print("✓ [自动] 已批准")
            continue

        opts = "/".join(allowed)
        decision = input(f"\n输入决策 ({opts}): ").strip().lower()

        if decision == "approve" and "approve" in allowed:
            decisions.append({"type": "approve"})
            print("✓ 已批准")
        elif decision == "reject" and "reject" in allowed:
            decisions.append({"type": "reject"})
            print("✗ 已拒绝")
        elif decision == "edit" and "edit" in allowed:
            print(f"原始参数: {tool_args}")
            new_args: dict[str, str] = {}
            for key, value in tool_args.items():
                new_value = input(f"  修改 {key} (回车保持 '{value}'): ").strip()
                new_args[key] = new_value if new_value else str(value)
            decisions.append({
                "type": "edit",
                "edited_action": {"name": tool_name, "args": new_args},
            })
            print(f"✓ 已修改参数: {new_args}")
        else:
            decisions.append({"type": "approve"})
            print("✓ 默认批准")

    return decisions


def handle_interrupt_cycle(
    result: GraphOutput,
    agent: Any,
    cfg: dict[str, Any],
    auto_approve: bool,
) -> GraphOutput:
    """处理多轮中断循环，直到无中断为止。

    Args:
        result: 初始 agent.invoke() 返回的 GraphOutput
        agent: DeepAgent 实例
        cfg: 配置字典，包含 thread_id
        auto_approve: True=自动批准，False=交互式输入

    Returns:
        最终的 GraphOutput（无中断时）
    """
    while result.interrupts:
        print(f"\n⚠️  检测到 {len(result.interrupts)} 个中断！Agent 暂停等待人工审批\n")

        interrupt_info = parse_interrupts(result)
        decisions = collect_decisions(
            interrupt_info["action_requests"],
            interrupt_info["review_configs"],
            auto_approve,
        )

        print("\n>>> 提交人工决策，恢复执行...")
        try:
            result = agent.invoke(
                Command(resume={"decisions": decisions}),
                config=cfg,
                version="v2",
            )
        except Exception as e:
            print(f"执行出错: {e}")
            return result

    return result


def print_final_reply(result: GraphOutput) -> None:
    """打印 Agent 最终回复。"""
    messages = result.value.get("messages", []) if hasattr(result.value, "get") else []
    if messages:
        last = messages[-1]
        content = getattr(last, "content", str(last))
        print("\n--- Agent 最终回复 ---")
        print(content[:500] if content else "(空回复)")
    else:
        print("\n--- Agent 最终回复 ---")
        print(str(result)[:500])


# ============== 需要审批的工具 ==============

@tool
def send_email(to: str, subject: str, body: str) -> str:
    """发送邮件（敏感操作，需要人工审批）。

    Args:
        to: 收件人邮箱
        subject: 邮件主题
        body: 邮件正文

    Returns:
        发送结果
    """
    return f"邮件已发送至 {to}，主题：{subject}"


@tool
def delete_file(file_path: str) -> str:
    """删除文件（敏感操作，需要人工审批）。

    Args:
        file_path: 要删除的文件路径

    Returns:
        删除结果
    """
    real_path = virtual_to_real_path(file_path)
    if real_path.exists():
        real_path.unlink()
        return f"文件已删除：{file_path}"
    return f"文件不存在：{file_path}"


@tool
def write_data(content: str, output_filename: str = "output.txt") -> str:
    """写入数据到文件。

    Args:
        content: 要写入的内容
        output_filename: 输出文件名

    Returns:
        写入结果
    """
    output_file = virtual_to_real_path(output_filename)
    ensure_dir(output_file)
    output_file.write_text(content, encoding="utf-8")
    return f"数据已写入 {output_filename}"


# ============== 构建启用 HITL 的 Agent ==============

def build_hitl_agent():
    """构建支持人工审批的 Agent。"""
    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)

    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/data/": FilesystemBackend(
                root_dir=str(UPLOADS_DIR.resolve()),
                virtual_mode=True,
            ),
        },
    )

    # 配置 interrupt_on：对敏感工具启用人工审批
    agent = create_deep_agent(
        name="hitl-demo",
        model=build_model(),
        tools=[send_email, delete_file, write_data],
        checkpointer=MemorySaver(),  # 必须使用 checkpointer
        backend=backend,
        system_prompt="""你是智能助手，可以帮助用户发送邮件、删除文件和写入数据。

对于以下操作，系统会自动暂停并等待人工审批：
- send_email：发送邮件
- delete_file：删除文件

你可以先执行其他操作，等待用户审批后再执行敏感操作。""",
        # interrupt_on 配置：对敏感工具启用中断
        interrupt_on={
            "send_email": True,           # 发送邮件需要审批
            "delete_file": True,         # 删除文件需要审批
            "write_data": False,         # 写入数据不需要审批
        },
    )
    return agent


# ============== 演示流程 ==============

def demo_hitl_flow(auto_approve: bool = False) -> None:
    """演示 Human-in-the-Loop 流程。

    Args:
        auto_approve: True = 自动批准所有操作（无需人工），False = 模拟人工审批
    """
    print("\n" + "=" * 60)
    print("【演示】Human-in-the-Loop 人工审批流程" + ("（自动批准模式）" if auto_approve else "（人工审批模式）"))
    print("=" * 60)

    agent = build_hitl_agent()
    cfg: dict[str, Any] = {"configurable": {"thread_id": "hitl-demo-1"}}

    user_input = "请帮我发送一封邮件到 test@example.com，主题是'测试邮件'，内容是'这是一封测试邮件'"

    print(f">>> 用户请求: {user_input}\n")

    # 第一次调用：Agent 会在 send_email 处中断
    print(">>> 第 1 步：Agent 执行到 send_email 时中断...")
    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=cfg,
            version="v2",
        )
    except Exception as e:
        print(f"执行出错: {e}")
        return

    if not result.interrupts:
        print("没有中断，执行完成")
        print_final_reply(result)
        return

    # 处理多轮中断循环
    result = handle_interrupt_cycle(result, agent, cfg, auto_approve)
    print_final_reply(result)


def demo_auto_approve():
    """演示自动批准的场景（无需人工干预）。"""
    print("\n" + "=" * 60)
    print("【演示】自动批准非敏感操作")
    print("=" * 60)

    agent = build_hitl_agent()
    cfg = {"configurable": {"thread_id": "hitl-demo-2"}}

    user_input = "请写入数据 'Hello, HITL!' 到 /data/hello.txt"

    print(f">>> 用户请求: {user_input}\n")
    print("write_data 配置为无需审批，应直接执行\n")

    result = agent.invoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=cfg,
        version="v2",
    )

    if result.interrupts:
        print("⚠️  检测到中断（不应该发生）")
    else:
        print("✓ 无中断，直接执行完成")

    last = result.value["messages"][-1]
    print("\n--- Agent 回复 ---")
    print(getattr(last, "content", str(last))[:300])


def demo_subagent_hitl(auto_approve: bool = False) -> None:
    """演示子代理的独立中断配置。

    Args:
        auto_approve: True = 自动批准所有操作（无需人工），False = 模拟人工审批
    """
    print("\n" + "=" * 60)
    print("【演示】子代理独立中断配置" + ("（自动批准模式）" if auto_approve else "（人工审批模式）"))
    print("=" * 60)

    # 定义带中断的子代理
    sensitive_subagent = SubAgent(
        name="sensitive-executor",
        description="执行敏感操作的子代理。当需要发送邮件或删除文件时，使用此子代理。",
        system_prompt="""你是敏感操作执行器，可以发送邮件或删除文件。

工作流程：
1. 根据用户请求调用 send_email 或 delete_file 工具
2. 这些是敏感操作，系统会自动暂停等待人工审批
3. 等待审批结果后继续执行
4. 返回执行结果的简洁摘要（不超过 50 字）""",
        model=build_model(),
        tools=[send_email, delete_file],
        # 子代理独立的中断配置，覆盖父代理设置
        interrupt_on={
            "send_email": True,
            "delete_file": {"allowed_decisions": ["approve", "reject"]},  # 不允许 edit
        },
    )

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    backend = CompositeBackend(
        default=StateBackend(),
        routes={},
    )

    agent = create_deep_agent(
        name="subagent-hitl-demo",
        model=build_model(),
        tools=[],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt="""你是协调者。当用户请求发送邮件或删除文件时，必须使用 task() 工具调用 sensitive-executor 子代理处理。

不要在回复中解释你要做什么——直接调用 task() 工具即可。
task() 工具会自动暂停等待人工审批，你不需要额外说明。""",
        subagents=[sensitive_subagent],
    )

    cfg: dict[str, Any] = {"configurable": {"thread_id": "subagent-hitl-demo"}}

    user_input = "请帮我发送一封邮件到 admin@example.com，主题是'子代理测试'，内容是'这是一封通过子代理发送的测试邮件'"

    print(f">>> 用户请求: {user_input}\n")

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=cfg,
            version="v2",
        )
    except Exception as e:
        print(f"执行出错: {e}")
        return

    if not result.interrupts:
        print("执行完成")
        return

    result = handle_interrupt_cycle(result, agent, cfg, auto_approve)
    print("✓ 子代理执行完成")


def demo_reject_flow(auto_approve: bool = False) -> None:
    """演示拒绝场景：拒绝邮件后 Agent 继续执行写入操作。

    Args:
        auto_approve: True = 自动批准（这里设为 False 以演示 reject），False = 模拟人工审批
    """
    print("\n" + "=" * 60)
    print("【演示】拒绝场景" + ("（自动批准模式）" if auto_approve else "（人工审批模式）"))
    print("=" * 60)

    agent = build_hitl_agent()
    cfg: dict[str, Any] = {"configurable": {"thread_id": "hitl-reject-1"}}

    user_input = "请帮我发送一封邮件到 test@example.com，主题是'拒绝测试'，内容是'这封邮件会被拒绝'，同时写入日志到 /data/reject_log.txt"

    print(f">>> 用户请求: {user_input}\n")
    print("提示：邮件将被拒绝，但写入日志操作应正常执行\n")

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=cfg,
            version="v2",
        )
    except Exception as e:
        print(f"执行出错: {e}")
        return

    if not result.interrupts:
        print("没有中断，执行完成")
        print_final_reply(result)
        return

    # 手动处理：第一个中断是邮件，需要 reject
    interrupt_info = parse_interrupts(result)
    decisions: list[dict[str, Any]] = []

    for req in interrupt_info["action_requests"]:
        tool_name = req.get("name", "unknown")
        tool_args = req.get("args", {})
        allowed = interrupt_info["review_configs"].get(tool_name, ["approve", "reject", "edit"])

        print(f"\n--- 待审批操作 ---")
        print(f"工具: {tool_name}")
        print(f"参数: {tool_args}")
        print(f"允许操作: {allowed}")

        if auto_approve:
            decisions.append({"type": "approve"})
            print("✓ [自动] 已批准")
        else:
            opts = "/".join(allowed)
            # 对于 demo_reject_flow，我们强制使用 reject 来演示
            decision = input(f"\n输入决策 ({opts})，输入 r 直接拒绝: ").strip().lower()
            if decision == "r" or decision == "reject":
                decisions.append({"type": "reject"})
                print("✗ 已拒绝（演示：Agent 将跳过邮件继续执行后续操作）")
            elif decision == "approve" and "approve" in allowed:
                decisions.append({"type": "approve"})
                print("✓ 已批准")
            else:
                decisions.append({"type": "reject"})
                print("✗ 默认拒绝")

    print("\n>>> 恢复执行...")
    try:
        result = agent.invoke(
            Command(resume={"decisions": decisions}),
            config=cfg,
            version="v2",
        )
    except Exception as e:
        print(f"执行出错: {e}")
        return

    if result.interrupts:
        result = handle_interrupt_cycle(result, agent, cfg, auto_approve)

    print_final_reply(result)


def demo_multi_interrupt(auto_approve: bool = False) -> None:
    """演示多轮中断：同一请求触发多个敏感操作。

    Args:
        auto_approve: True = 自动批准所有操作（无需人工），False = 模拟人工审批
    """
    print("\n" + "=" * 60)
    print("【演示】多轮中断" + ("（自动批准模式）" if auto_approve else "（人工审批模式）"))
    print("=" * 60)

    UPLOADS_DIR.mkdir(parents=True, exist_ok=True)
    backend = CompositeBackend(
        default=StateBackend(),
        routes={
            "/data/": FilesystemBackend(
                root_dir=str(UPLOADS_DIR.resolve()),
                virtual_mode=True,
            ),
        },
    )

    # 构建支持多敏感操作的 Agent
    agent = create_deep_agent(
        name="hitl-multi-demo",
        model=build_model(),
        tools=[send_email, delete_file, write_data],
        checkpointer=MemorySaver(),
        backend=backend,
        system_prompt="""你是智能助手，可以帮助用户发送邮件、删除文件和写入数据。

对于以下操作，系统会自动暂停并等待人工审批：
- send_email：发送邮件
- delete_file：删除文件

你可以先执行其他操作，等待用户审批后再执行敏感操作。""",
        interrupt_on={
            "send_email": True,
            "delete_file": True,
            "write_data": False,
        },
    )

    cfg: dict[str, Any] = {"configurable": {"thread_id": "hitl-multi-1"}}

    # 同时请求多个敏感操作
    user_input = "请帮我发送一封邮件到 test@example.com，主题是'多轮中断测试'，内容是'测试多轮中断'，然后删除 /data/test_delete.txt"

    print(f">>> 用户请求: {user_input}\n")
    print("提示：请求同时触发 send_email 和 delete_file，期望两次中断\n")

    try:
        result = agent.invoke(
            {"messages": [HumanMessage(content=user_input)]},
            config=cfg,
            version="v2",
        )
    except Exception as e:
        print(f"执行出错: {e}")
        return

    if not result.interrupts:
        print("没有中断，执行完成")
        print_final_reply(result)
        return

    result = handle_interrupt_cycle(result, agent, cfg, auto_approve)
    print_final_reply(result)


def print_concepts():
    """打印 HITL 核心概念"""
    print("""
Human-in-the-Loop 核心概念
=========================

1. interrupt_on 配置
   - True：启用中断，允许 approve/edit/reject
   - False：禁用中断
   - {"allowed_decisions": [...]}: 自定义允许的操作

2. 决策类型
   - approve：按原始参数执行
   - reject：跳过该操作
   - edit：修改参数后再执行

3. 执行流程
   ① agent.invoke() → 执行到敏感工具时中断
   ② 检查 result.interrupts
   ③ 提取 action_requests
   ④ 创建 decisions 列表
   ⑤ Command(resume={"decisions": decisions}) 恢复

4. 子代理中断
   - 子代理可独立配置 interrupt_on
   - 设置后完全替换父代理配置

5. 注意事项
   - 必须使用 checkpointer
   - 恢复时使用相同的 thread_id
   - decisions 顺序与 action_requests 一致
""")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Human-in-the-Loop 演示")
    parser.add_argument("--auto", action="store_true", help="自动批准所有操作（无需人工干预）")
    args = parser.parse_args()

    print_concepts()

    settings = get_settings()
    if not (settings.minimax_api_key or "").strip():
        print("错误：未配置 MINIMAX_API_KEY（见 .env）。\n")
        exit(1)

    # 演示 1：完整 HITL 流程（支持人工审批或自动批准）
    demo_hitl_flow(auto_approve=args.auto)

    # 演示 2：自动批准非敏感操作
    demo_auto_approve()

    # 演示 3：子代理中断配置（支持人工审批或自动批准）
    demo_subagent_hitl(auto_approve=args.auto)

    # 演示 4：拒绝场景
    demo_reject_flow(auto_approve=args.auto)

    # 演示 5：多轮中断
    demo_multi_interrupt(auto_approve=args.auto)

    print("\n演示结束。\n")


if __name__ == "__main__":
    main()
