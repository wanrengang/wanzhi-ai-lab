/** 与后端同域部署时留空；本地可设 import.meta.env.VITE_API_BASE */
const base = (import.meta.env.VITE_API_BASE as string | undefined) ?? "";

async function parseJson<T>(res: Response): Promise<T> {
  const text = await res.text();
  let data: unknown;
  try {
    data = text ? JSON.parse(text) : {};
  } catch {
    throw new Error(`无效 JSON 响应: ${text.slice(0, 200)}`);
  }
  if (!res.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data
        ? String((data as { detail: unknown }).detail)
        : res.statusText;
    throw new Error(detail || `HTTP ${res.status}`);
  }
  return data as T;
}

export async function health(): Promise<{ status: string; service: string }> {
  const res = await fetch(`${base}/health`);
  return parseJson(res);
}

/** 从检查点拉取 user/assistant 文本，用于刷新页面后恢复对话区 */
export async function fetchChatHistory(threadId: string): Promise<{
  thread_id: string;
  messages: { role: string; content: string }[];
}> {
  const res = await fetch(`${base}/api/v1/chat/${encodeURIComponent(threadId)}/history`);
  return parseJson(res);
}

/** 历史会话列表（thread_id + 首条预览） */
export async function fetchChatThreads(): Promise<{
  threads: { thread_id: string; preview: string }[];
}> {
  const res = await fetch(`${base}/api/v1/chat/threads`);
  return parseJson(res);
}

export async function chat(body: {
  message: string;
  thread_id: string;
  file_paths?: string[];
}): Promise<{ thread_id: string; response: string; tool_calls: { name: string; args: Record<string, unknown> }[] }> {
  const res = await fetch(`${base}/api/v1/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson(res);
}

/** 上传数据文件，返回服务器路径供对话 file_paths 使用 */
export async function uploadDataFile(file: File): Promise<{ path: string; filename: string }> {
  const fd = new FormData();
  fd.append("file", file);
  const res = await fetch(`${base}/api/v1/upload`, { method: "POST", body: fd });
  return parseJson(res);
}

export async function search(body: { query: string; max_results?: number }): Promise<{
  query: string;
  total: number;
  results: { title: string; url: string; snippet: string }[];
}> {
  const res = await fetch(`${base}/api/v1/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ max_results: 8, ...body }),
  });
  return parseJson(res);
}

export async function analyzeUpload(file: File, question: string): Promise<{ task_id: string; status: string; message: string }> {
  const fd = new FormData();
  fd.append("file", file);
  fd.append("question", question);
  const res = await fetch(`${base}/api/v1/analyze`, { method: "POST", body: fd });
  return parseJson(res);
}

export async function analyzeStatus(taskId: string): Promise<{
  task_id: string;
  status: "processing" | "completed" | "failed";
  result: string | null;
  error: string | null;
}> {
  const res = await fetch(`${base}/api/v1/analyze/${encodeURIComponent(taskId)}`);
  return parseJson(res);
}

export async function listDatasources(): Promise<
  { name: string; connection_url: string; description: string; status: string }[]
> {
  const res = await fetch(`${base}/api/v1/datasource`);
  return parseJson(res);
}

export async function addDatasource(body: {
  name: string;
  connection_url: string;
  description?: string;
}): Promise<{ name: string; connection_url: string; description: string; status: string }> {
  const res = await fetch(`${base}/api/v1/datasource`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  return parseJson(res);
}

/** SSE：流式对话（与后端 GET 约定一致）；file_paths 为服务器上的绝对路径 */
export function streamChat(
  threadId: string,
  message: string,
  filePaths: string[],
  onEvent: (ev: { event: string; data: unknown }) => void,
): { close: () => void } {
  const prefix = base.replace(/\/$/, "");
  const q = new URLSearchParams();
  q.set("message", message);
  for (const p of filePaths) {
    q.append("file_paths", p);
  }
  const raw = `${prefix}/api/v1/chat/${encodeURIComponent(threadId)}/stream?${q.toString()}`;
  const url = raw.startsWith("http") ? raw : new URL(raw, window.location.origin).href;
  const es = new EventSource(url);

  const onAny = (eventName: string) => (e: MessageEvent) => {
    let data: unknown = e.data;
    try {
      data = JSON.parse(e.data as string);
    } catch {
      /* 保持字符串 */
    }
    onEvent({ event: eventName, data });
  };

  es.addEventListener("start", onAny("start"));
  es.addEventListener("message", onAny("message"));
  es.addEventListener("tool_call", onAny("tool_call"));
  es.addEventListener("tool_result", onAny("tool_result"));
  es.addEventListener("stream_error", onAny("stream_error"));
  es.addEventListener("done", onAny("done"));
  es.onerror = () => {
    onEvent({ event: "transport_error", data: { message: "SSE 连接中断" } });
    es.close();
  };

  return {
    close: () => es.close(),
  };
}
