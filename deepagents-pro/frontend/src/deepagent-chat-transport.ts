/**
 * 将 DeepAgent-Pro（FastAPI）对话 / SSE 流桥接到 Vercel AI SDK 的 UIMessageChunk 流，
 * 以便使用 @ai-sdk/react 的 useChat（见 https://ai-sdk.dev/）。
 */
import type { ChatTransport, UIMessage, UIMessageChunk } from "ai";
import { generateId } from "ai";

const API_BASE = (import.meta.env.VITE_API_BASE as string | undefined)?.replace(/\/$/, "") ?? "";

export type DeepAgentContext = {
  threadId: string;
  filePaths: string[];
  stream: boolean;
};

function lastUserText(messages: UIMessage[]): string {
  const u = [...messages].reverse().find((m) => m.role === "user");
  if (!u) return "";
  return u.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text")
    .map((p) => p.text)
    .join("\n");
}

function enqueueAll(
  controller: ReadableStreamDefaultController<UIMessageChunk>,
  chunks: UIMessageChunk[],
) {
  for (const c of chunks) {
    controller.enqueue(c);
  }
}

export class DeepAgentChatTransport implements ChatTransport<UIMessage> {
  constructor(private readonly getContext: () => DeepAgentContext) {}

  async sendMessages(options: {
    trigger: "submit-message" | "regenerate-message";
    chatId: string;
    messageId: string | undefined;
    messages: UIMessage[];
    abortSignal: AbortSignal | undefined;
  }): Promise<ReadableStream<UIMessageChunk>> {
    const { chatId, messages, abortSignal } = options;
    const text = lastUserText(messages);
    if (!text.trim()) {
      throw new Error("请输入消息内容");
    }

    const { filePaths, stream } = this.getContext();
    const threadId = chatId;

    if (stream) {
      return this.openSseStream(threadId, text, filePaths, abortSignal);
    }
    return this.openJsonResponse(threadId, text, filePaths, abortSignal);
  }

  private async openJsonResponse(
    threadId: string,
    text: string,
    filePaths: string[],
    abortSignal: AbortSignal | undefined,
  ): Promise<ReadableStream<UIMessageChunk>> {
    const url = `${API_BASE}/api/v1/chat`;
    const res = await fetch(url.startsWith("http") ? url : new URL(url, window.location.origin).href, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        thread_id: threadId,
        message: text,
        file_paths: filePaths,
      }),
      signal: abortSignal,
    });
    if (!res.ok) {
      const t = await res.text();
      let detail = t;
      try {
        const j = JSON.parse(t) as { detail?: unknown };
        if (j.detail !== undefined) detail = String(j.detail);
      } catch {
        /* 保持原文 */
      }
      throw new Error(detail || `HTTP ${res.status}`);
    }
    const data = (await res.json()) as {
      response: string;
      tool_calls: { name: string; args: Record<string, unknown> }[];
      tool_results?: { name?: string; content?: string; tool_call_id?: string; status?: string }[];
    };
    let responseText = data.response ?? "";
    const trs = data.tool_results ?? [];
    const toolCalls = data.tool_calls ?? [];

    if (trs.length > 0) {
      const blocks = trs
        .map((tr) => {
          const n = tr.name || "tool";
          const c = String(tr.content ?? "");
          const head = c.length > 12000 ? `${c.slice(0, 12000)}\n…(truncated)` : c;
          return `\n\n【工具输出】${n}\n\`\`\`text\n${head}\n\`\`\`\n`;
        })
        .join("");
      responseText += blocks;
    }

    const textId = generateId();
    const chunks: UIMessageChunk[] = [
      { type: "text-start", id: textId },
      { type: "text-delta", id: textId, delta: responseText },
      { type: "text-end", id: textId },
    ];
    for (const tc of toolCalls) {
      const raw = tc as { name?: string; args?: Record<string, unknown>; id?: string };
      const sid = raw.id && String(raw.id).trim();
      const toolCallId = sid || generateId();
      chunks.push({
        type: "tool-input-available",
        toolCallId,
        toolName: raw.name || "tool",
        input: raw.args ?? {},
        dynamic: true,
      });
      // 仅当服务端 id 与 tool_result.tool_call_id 一致时才发 tool-output，否则会触发 SDK 抛错并整条流失败
      if (sid) {
        const tr = trs.find((r) => (r.tool_call_id && String(r.tool_call_id).trim()) === sid);
        if (tr) {
          const c = String(tr.content ?? "");
          const head = c.length > 12000 ? `${c.slice(0, 12000)}\n…(truncated)` : c;
          chunks.push({
            type: "tool-output-available",
            toolCallId: sid,
            output: head,
          });
        }
      }
    }
    chunks.push({ type: "finish", finishReason: "stop" });

    return new ReadableStream({
      start(controller) {
        enqueueAll(controller, chunks);
        controller.close();
      },
    });
  }

  private openSseStream(
    threadId: string,
    text: string,
    filePaths: string[],
    abortSignal: AbortSignal | undefined,
  ): ReadableStream<UIMessageChunk> {
    const q = new URLSearchParams();
    q.set("message", text);
    for (const p of filePaths) {
      q.append("file_paths", p);
    }
    const path = `${API_BASE}/api/v1/chat/${encodeURIComponent(threadId)}/stream?${q.toString()}`;
    const href = path.startsWith("http") ? path : new URL(path, window.location.origin).href;

    return new ReadableStream<UIMessageChunk>({
      start: (controller) => {
        const es = new EventSource(href);

        const onAbort = () => {
          es.close();
          try {
            controller.close();
          } catch {
            /* 已关闭 */
          }
        };
        abortSignal?.addEventListener("abort", onAbort);

        /** 仅含服务端下发的 tool_call id，用于安全发送 tool-output-available（与 tool_result 对齐） */
        const serverToolCallIds = new Set<string>();

        /**
         * LangGraph stream_mode=messages 常推送「当前 AIMessage 全文」而非 token 增量；
         * 若直接当 text-delta 追加会导致同轮正文重复。这里用前缀关系只推增量。
         */
        let lastEmittedFullText = "";
        let lastGraphNode = "";

        let currentTextId = generateId();
        try {
          controller.enqueue({ type: "text-start", id: currentTextId });
        } catch {
          es.close();
          return;
        }

        const onMessage = (e: MessageEvent) => {
          let parsed: unknown = e.data;
          try {
            parsed = JSON.parse(e.data as string);
          } catch {
            return;
          }
          if (!parsed || typeof parsed !== "object" || !("content" in parsed)) {
            return;
          }
          const raw = parsed as { content?: unknown; node?: string };
          const content = raw.content;
          if (content === undefined || content === null || content === "") {
            return;
          }
          const full = String(content);
          const node = typeof raw.node === "string" ? raw.node : "";
          if (node && lastGraphNode && node !== lastGraphNode) {
            controller.enqueue({ type: "text-end", id: currentTextId });
            currentTextId = generateId();
            controller.enqueue({ type: "text-start", id: currentTextId });
            lastEmittedFullText = "";
          }
          if (node) {
            lastGraphNode = node;
          }

          let piece: string;
          if (lastEmittedFullText.length > 0 && full.startsWith(lastEmittedFullText)) {
            // 累积全文：只推新增后缀
            piece = full.slice(lastEmittedFullText.length);
            lastEmittedFullText = full;
          } else if (lastEmittedFullText.length === 0) {
            piece = full;
            lastEmittedFullText = full;
          } else {
            // 非前缀关系时视为独立增量片段（逐 token 等），避免重复追加累积全文
            piece = full;
            lastEmittedFullText += full;
          }
          if (piece) {
            controller.enqueue({ type: "text-delta", id: currentTextId, delta: piece });
          }
        };

        const onToolCall = (e: MessageEvent) => {
          let parsed: unknown = e.data;
          try {
            parsed = JSON.parse(e.data as string);
          } catch {
            return;
          }
          const o = parsed as { name?: string; args?: unknown; id?: string };
          const sid = o.id && String(o.id).trim();
          const toolCallId = sid || generateId();
          if (sid) {
            serverToolCallIds.add(sid);
          }
          controller.enqueue({
            type: "tool-input-available",
            toolCallId,
            toolName: o.name || "tool",
            input: o.args ?? parsed,
            dynamic: true,
          });
        };

        const onToolResult = (e: MessageEvent) => {
          let parsed: unknown = e.data;
          try {
            parsed = JSON.parse(e.data as string);
          } catch {
            return;
          }
          const o = parsed as { name?: string; content?: string; tool_call_id?: string };
          const c = String(o.content ?? "");
          const head = c.length > 12000 ? `${c.slice(0, 12000)}\n…(truncated)` : c;
          const rid = (o.tool_call_id && String(o.tool_call_id).trim()) || "";
          if (rid && serverToolCallIds.has(rid)) {
            controller.enqueue({
              type: "tool-output-available",
              toolCallId: rid,
              output: head,
            });
            return;
          }
          const n = o.name || "tool";
          const delta = `\n\n【工具输出】${n}\n\`\`\`text\n${head}\n\`\`\`\n`;
          controller.enqueue({ type: "text-delta", id: currentTextId, delta });
        };

        const onStreamError = (e: MessageEvent) => {
          let msg = "流式出错";
          try {
            const p = JSON.parse(e.data as string) as { error?: string };
            if (p.error) msg = p.error;
          } catch {
            /* 忽略 */
          }
          controller.enqueue({ type: "error", errorText: msg });
        };

        const onDone = () => {
          abortSignal?.removeEventListener("abort", onAbort);
          es.removeEventListener("message", onMessage);
          es.removeEventListener("tool_call", onToolCall);
          es.removeEventListener("tool_result", onToolResult);
          es.removeEventListener("stream_error", onStreamError);
          es.removeEventListener("done", onDone);
          es.close();
          try {
            controller.enqueue({ type: "text-end", id: currentTextId });
            controller.enqueue({ type: "finish", finishReason: "stop" });
            controller.close();
          } catch {
            /* 已关闭 */
          }
        };

        es.addEventListener("message", onMessage);
        es.addEventListener("tool_call", onToolCall);
        es.addEventListener("tool_result", onToolResult);
        es.addEventListener("stream_error", onStreamError);
        es.addEventListener("done", onDone);
        es.onerror = () => {
          abortSignal?.removeEventListener("abort", onAbort);
          es.close();
          try {
            controller.enqueue({ type: "error", errorText: "SSE 连接中断" });
            controller.close();
          } catch {
            /*  */
          }
        };
      },
    });
  }

  reconnectToStream(): Promise<ReadableStream<UIMessageChunk> | null> {
    return Promise.resolve(null);
  }
}
