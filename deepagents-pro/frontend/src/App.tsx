import { useChat } from "@ai-sdk/react";
import type { UIMessage } from "ai";
import { generateId } from "ai";
import { useCallback, useEffect, useMemo, useRef, useState, type ComponentProps } from "react";
import { addDatasource, fetchChatHistory, fetchChatThreads, health, listDatasources, uploadDataFile } from "./api";
import { DeepAgentChatTransport } from "./deepagent-chat-transport";
import { MarkdownBody } from "./MarkdownBody";

type Tab = "chat" | "datasource";

function getToolRawName(part: { type: string; toolName?: string }): string {
  if (part.type === "dynamic-tool") return part.toolName ?? "tool";
  if (part.type.startsWith("tool-")) return part.type.replace(/^tool-/, "");
  return "tool";
}

/** 从 LangChain / AI SDK 工具块中取出 web_search 的 query 等参数 */
function webSearchArgs(input: unknown): { query?: string; max_results?: number } {
  if (typeof input === "string") {
    try {
      return webSearchArgs(JSON.parse(input) as unknown);
    } catch {
      return {};
    }
  }
  if (input && typeof input === "object" && input !== null) {
    const o = input as Record<string, unknown>;
    const q = o.query ?? o.keywords;
    return {
      query: typeof q === "string" ? q : undefined,
      max_results: typeof o.max_results === "number" ? o.max_results : undefined,
    };
  }
  return {};
}

function WebSearchToolBubble({ part }: { part: Record<string, unknown> }) {
  const state = part.state as string | undefined;
  const args = webSearchArgs(part.input);
  const out = typeof part.output === "string" ? part.output : part.output != null ? JSON.stringify(part.output, null, 2) : null;

  return (
    <details className="bubble-tools bubble-tools-search" open={state === "input-available" || state === "output-available"}>
      <summary>
        联网搜索
        {args.query ? (
          <span className="search-query-chip">「{args.query.length > 80 ? `${args.query.slice(0, 80)}…` : args.query}」</span>
        ) : null}
        {args.max_results != null ? <span className="search-meta"> · 最多 {args.max_results} 条</span> : null}
        {state ? <span className="search-meta"> · {state}</span> : null}
      </summary>
      {args.query && (
        <p className="search-args">
          <strong>查询</strong>：{args.query}
        </p>
      )}
      {out && (
        <pre className="search-output">{out.length > 6000 ? `${out.slice(0, 6000)}\n…（已截断）` : out}</pre>
      )}
      <details className="search-raw">
        <summary>原始 JSON</summary>
        <pre>{JSON.stringify(part, null, 2)}</pre>
      </details>
    </details>
  );
}

const THREAD_STORAGE_KEY = "deepagent-pro-thread-id";

/** 与阶跃式首页类似的技能入口；默认 general = 通用对话（数据分析智能体） */
type AgentSkillId = "general" | "deep_verify" | "kb_qa" | "image" | "voice";

const SKILL_PREFIX: Record<AgentSkillId, string> = {
  general: "",
  deep_verify: "[场景:深入核查] ",
  kb_qa: "[场景:知识库问答] ",
  image: "[场景:图片创作] ",
  voice: "[场景:语音体验｜语境TTS] ",
};

const SKILL_PILLS: {
  id: AgentSkillId;
  label: string;
  sub?: string;
  comingSoon?: boolean;
}[] = [
  { id: "general", label: "通用对话", sub: "数据分析" },
  { id: "deep_verify", label: "深入核查", comingSoon: true },
  { id: "kb_qa", label: "知识库问答", comingSoon: true },
  { id: "image", label: "图片创作", comingSoon: true },
  { id: "voice", label: "语音体验中心", sub: "基于语境的 TTS", comingSoon: true },
];

const TRY_THESE = [
  "帮我解读这份销售表里的趋势与异常值",
  "用自然语言查一下数据库里最近一周的订单汇总",
  "对比两组 CSV 中「客单价」分布并给结论",
  "介绍下 LangChain 的 Deep Agents 项目能做什么",
];

function chatGreeting(): string {
  const h = new Date().getHours();
  if (h < 12) return "上午好，有什么可以帮你？";
  if (h < 18) return "下午好，有什么可以帮你？";
  return "晚上好，有什么可以帮你？";
}

function newThreadId(): string {
  return crypto.randomUUID();
}

function loadStoredThreadId(): string {
  try {
    const s = sessionStorage.getItem(THREAD_STORAGE_KEY);
    if (s && s.length >= 8) return s;
  } catch {
    /* ignore */
  }
  return newThreadId();
}

function historyRowsToMessages(rows: { role: string; content: string }[]): UIMessage[] {
  return rows.map((row) => ({
    id: generateId(),
    role: row.role === "user" ? "user" : "assistant",
    parts: [{ type: "text" as const, text: row.content }],
  }));
}

/** 受控 details：流式更新时浏览器/原生 details 常被撑成展开，这里默认始终折叠，由用户点击展开 */
function ReasoningCollapsible({ text }: { text: string }) {
  const [open, setOpen] = useState(false);

  const onToggle: ComponentProps<"details">["onToggle"] = (e) => {
    setOpen(e.currentTarget.open);
  };

  return (
    <details className="bubble-reasoning" open={open} onToggle={onToggle}>
      <summary>思考过程</summary>
      <div className="bubble-reasoning-inner" hidden={!open}>
        <MarkdownBody text={text} />
      </div>
    </details>
  );
}

function MessageParts({ message }: { message: UIMessage }) {
  const isAssistant = message.role === "assistant";
  return (
    <>
      {message.parts.map((part, i) => {
        if (part.type === "text") {
          return (
            <div key={`${message.id}-t-${i}`} className={`bubble-body ${isAssistant ? "bubble-body-assistant" : "bubble-body-user"}`}>
              {isAssistant ? (
                <MarkdownBody text={part.text} />
              ) : (
                <span className="bubble-plain">{part.text}</span>
              )}
            </div>
          );
        }
        if (part.type === "reasoning") {
          return <ReasoningCollapsible key={`${message.id}-r-${i}`} text={part.text} />;
        }
        if (part.type === "step-start") {
          return null;
        }
        if (part.type === "file") {
          return (
            <div key={`${message.id}-f-${i}`} className="bubble-files">
              文件：{part.filename ?? part.url}
            </div>
          );
        }
        if (part.type === "dynamic-tool" || (typeof part.type === "string" && part.type.startsWith("tool-"))) {
          const raw = getToolRawName(part as { type: string; toolName?: string });
          if (raw === "web_search") {
            return <WebSearchToolBubble key={`${message.id}-tool-${i}`} part={part as Record<string, unknown>} />;
          }
          return (
            <details key={`${message.id}-tool-${i}`} className="bubble-tools">
              <summary>工具：{raw}</summary>
              <pre>{JSON.stringify(part, null, 2)}</pre>
            </details>
          );
        }
        return null;
      })}
    </>
  );
}

/** 助手气泡是否已有可见回复（正文、思考或工具），用于在首包前显示 loading */
function assistantBubbleHasStartedReply(m: UIMessage): boolean {
  return m.parts.some((p) => {
    if (p.type === "text" && "text" in p && (p as { text: string }).text?.trim()) return true;
    if (p.type === "reasoning" && "text" in p && (p as { text: string }).text?.trim()) return true;
    if (p.type === "dynamic-tool" || (typeof p.type === "string" && p.type.startsWith("tool-"))) return true;
    return false;
  });
}

/** 助手气泡复制用：合并正文 text 片段（参考 deer-flow 等产品的「复制全文」） */
function messagePlainTextForCopy(m: UIMessage): string {
  return m.parts
    .filter((p): p is { type: "text"; text: string } => p.type === "text" && typeof (p as { text?: string }).text === "string")
    .map((p) => p.text)
    .join("\n\n")
    .trim();
}

function BubbleHeader({
  roleLabel,
  copyText,
}: {
  roleLabel: string;
  /** 有内容时显示复制按钮 */
  copyText?: string;
}) {
  const [copied, setCopied] = useState(false);
  const onCopy = async () => {
    if (!copyText) return;
    try {
      await navigator.clipboard.writeText(copyText);
      setCopied(true);
      window.setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  };
  return (
    <div className="bubble-header">
      <div className="bubble-role">{roleLabel}</div>
      {copyText ? (
        <button type="button" className="bubble-copy-btn" onClick={() => void onCopy()} title="复制助手正文">
          {copied ? "已复制" : "复制"}
        </button>
      ) : null}
    </div>
  );
}

export default function App() {
  const [tab, setTab] = useState<Tab>("chat");
  const [ok, setOk] = useState<boolean | null>(null);

  useEffect(() => {
    health()
      .then(() => setOk(true))
      .catch(() => setOk(false));
  }, []);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          DeepAgent<span>-Pro</span>
        </div>
        <div className="health-pill">
          <span className={`health-dot ${ok ? "ok" : ""}`} title="API 健康检查" />
          {ok === null ? "检查中…" : ok ? "API 已连接" : "API 不可用"}
        </div>
        <button type="button" className={`nav-btn ${tab === "chat" ? "active" : ""}`} onClick={() => setTab("chat")}>
          对话分析
        </button>
        <button type="button" className={`nav-btn ${tab === "datasource" ? "active" : ""}`} onClick={() => setTab("datasource")}>
          数据源
        </button>
      </aside>
      <main className="main">
        {tab === "chat" && <ChatPanel />}
        {tab === "datasource" && <DatasourcePanel />}
      </main>
    </div>
  );
}

function ChatPanel() {
  const [threadId, setThreadId] = useState(loadStoredThreadId);
  const [historyReady, setHistoryReady] = useState(false);
  const [threads, setThreads] = useState<{ thread_id: string; preview: string }[]>([]);
  /** 默认开启：走 SSE（/stream）；关闭则一次性 JSON，适合调试或弱网重试 */
  const [streamMode, setStreamMode] = useState(true);
  const [sessionFiles, setSessionFiles] = useState<{ path: string; label: string }[]>([]);
  const [pendingFile, setPendingFile] = useState<File | null>(null);
  const [input, setInput] = useState("");
  const [agentSkill, setAgentSkill] = useState<AgentSkillId>("general");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const threadEndRef = useRef<HTMLDivElement>(null);

  const threadRef = useRef(threadId);
  const streamRef = useRef(streamMode);
  const filePathsRef = useRef<string[]>([]);
  threadRef.current = threadId;
  streamRef.current = streamMode;

  useEffect(() => {
    filePathsRef.current = sessionFiles.map((f) => f.path);
  }, [sessionFiles]);

  useEffect(() => {
    try {
      sessionStorage.setItem(THREAD_STORAGE_KEY, threadId);
    } catch {
      /* ignore */
    }
  }, [threadId]);

  const transport = useMemo(
    () =>
      new DeepAgentChatTransport(() => ({
        threadId: threadRef.current,
        filePaths: filePathsRef.current,
        stream: streamRef.current,
      })),
    [],
  );

  const { messages, sendMessage, status, error, stop, setMessages } = useChat({
    id: threadId,
    transport,
  });

  const busy = status === "streaming" || status === "submitted";

  const showReplyLoading = useMemo(() => {
    if (!busy || !historyReady) return false;
    const last = messages[messages.length - 1];
    if (!last) return false;
    if (last.role === "user") return true;
    if (last.role === "assistant") return !assistantBubbleHasStartedReply(last);
    return false;
  }, [busy, historyReady, messages]);

  const loadThreads = useCallback(() => {
    fetchChatThreads()
      .then((data) => setThreads(data.threads ?? []))
      .catch(() => setThreads([]));
  }, []);

  useEffect(() => {
    loadThreads();
  }, [loadThreads]);

  const prevBusy = useRef(false);
  useEffect(() => {
    if (prevBusy.current && !busy) loadThreads();
    prevBusy.current = busy;
  }, [busy, loadThreads]);

  useEffect(() => {
    let cancelled = false;
    setHistoryReady(false);
    fetchChatHistory(threadId)
      .then((data) => {
        if (cancelled) return;
        if (data.messages?.length) {
          setMessages(historyRowsToMessages(data.messages));
        } else {
          setMessages([]);
        }
      })
      .catch(() => {
        if (!cancelled) setMessages([]);
      })
      .finally(() => {
        if (!cancelled) setHistoryReady(true);
      });
    return () => {
      cancelled = true;
    };
  }, [threadId, setMessages]);

  useEffect(() => {
    threadEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, showReplyLoading]);

  const resetThread = () => {
    try {
      sessionStorage.removeItem(THREAD_STORAGE_KEY);
    } catch {
      /* ignore */
    }
    setThreadId(newThreadId());
    setMessages([]);
    setSessionFiles([]);
    setPendingFile(null);
    setInput("");
    setAgentSkill("general");
    if (fileInputRef.current) fileInputRef.current.value = "";
    loadThreads();
  };

  const removeSessionFile = (path: string) => {
    setSessionFiles((s) => s.filter((f) => f.path !== path));
  };

  const selectThread = (tid: string) => {
    setThreadId(tid);
    setSessionFiles([]);
    setPendingFile(null);
    setInput("");
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const text = input.trim();
    if (!text || busy || !historyReady) return;

    filePathsRef.current = sessionFiles.map((f) => f.path);
    if (pendingFile) {
      try {
        const up = await uploadDataFile(pendingFile);
        filePathsRef.current = [...filePathsRef.current, up.path];
        setSessionFiles((s) => [...s, { path: up.path, label: up.filename }]);
        setPendingFile(null);
        if (fileInputRef.current) fileInputRef.current.value = "";
      } catch (err) {
        window.alert(err instanceof Error ? err.message : String(err));
        return;
      }
    }

    const prefixed = SKILL_PREFIX[agentSkill] + text;
    setInput("");
    await sendMessage({ text: prefixed });
  };

  const isLanding = historyReady && messages.length === 0;
  const skillLabel = useMemo(() => {
    const p = SKILL_PILLS.find((x) => x.id === agentSkill);
    if (!p) return "通用对话";
    return p.sub ? `${p.label} · ${p.sub}` : p.label;
  }, [agentSkill]);

  return (
    <>
      {!isLanding && (
        <>
          <h1>对话分析</h1>
          <p className="sub">
            使用{" "}
            <a href="https://ai-sdk.dev/" target="_blank" rel="noreferrer">
              Vercel AI SDK
            </a>{" "}
            的 <code>useChat</code> 对接 FastAPI；可附加数据文件。需要<strong>行业公开信息、术语或最新资料</strong>时，助手会自行调用{" "}
            <code>web_search</code>。左侧为<strong>历史会话</strong>（服务端检查点）。
          </p>
        </>
      )}
      {isLanding && (
        <div className="chat-landing-page-title">
          <h1 className="chat-landing-h1">对话分析</h1>
          <p className="sub chat-landing-sub">通用智能体 · 数据分析；版式对齐阶跃式首页层级（Instrument Sans + Noto Sans SC）。</p>
        </div>
      )}
      <div className="chat-page-wrap">
        <aside className="chat-history-panel" aria-label="历史会话">
          <div className="chat-history-toolbar">
            <span className="chat-history-title">历史会话</span>
            <button type="button" className="ghost chat-history-refresh" onClick={() => loadThreads()}>
              刷新
            </button>
          </div>
          <ul className="chat-history-list">
            {threads.map((t) => (
              <li key={t.thread_id}>
                <button
                  type="button"
                  className={`chat-history-item ${t.thread_id === threadId ? "active" : ""}`}
                  onClick={() => selectThread(t.thread_id)}
                >
                  <span className="chat-history-preview">{t.preview.trim() || "（无预览）"}</span>
                  <span className="chat-history-meta">{t.thread_id.slice(0, 8)}…</span>
                </button>
              </li>
            ))}
          </ul>
          {threads.length === 0 && (
            <p className="chat-history-empty">暂无记录。发送过消息后会出现；后端使用 SQLite 检查点持久化。</p>
          )}
        </aside>

        <div className={`card chat-card ${isLanding ? "chat-card-landing" : ""}`}>
          {isLanding && (
            <div className="chat-toolbar-slim chat-toolbar-slim-landing">
              <span className="skill-active-badge" title="当前场景（发送时加前缀，便于后续扩展路由）">
                {skillLabel}
              </span>
              <label className="chat-checkbox-label">
                <input type="checkbox" checked={streamMode} onChange={(e) => setStreamMode(e.target.checked)} />
                流式
              </label>
              <button type="button" className="ghost chat-toolbar-slim-btn" onClick={resetThread}>
                新对话
              </button>
              <details className="chat-advanced-inline">
                <summary>线程 ID</summary>
                <label htmlFor="tid-landing" className="visually-hidden">
                  线程 ID
                </label>
                <input id="tid-landing" value={threadId} onChange={(e) => setThreadId(e.target.value)} placeholder="UUID" />
              </details>
            </div>
          )}
          {!isLanding && (
            <details className="chat-advanced">
              <summary>高级：线程 ID · 流式</summary>
              <div className="row two chat-toolbar">
                <div>
                  <label htmlFor="tid">线程 ID</label>
                  <input id="tid" value={threadId} onChange={(e) => setThreadId(e.target.value)} placeholder="UUID" />
                </div>
                <div className="chat-advanced-actions">
                  <label className="chat-checkbox-label">
                    <input type="checkbox" checked={streamMode} onChange={(e) => setStreamMode(e.target.checked)} />
                    流式 (SSE)
                  </label>
                  {busy && (
                    <button type="button" className="ghost" onClick={() => void stop()}>
                      停止
                    </button>
                  )}
                </div>
              </div>
            </details>
          )}

          {!isLanding && (
            <div className="chat-toolbar-slim">
              <span className="skill-active-badge" title="当前场景（会作为前缀发给模型，便于后续路由）">
                {skillLabel}
              </span>
              <button type="button" className="ghost chat-toolbar-slim-btn" onClick={resetThread}>
                新对话
              </button>
              {busy && (
                <button type="button" className="ghost chat-toolbar-slim-btn" onClick={() => void stop()}>
                  停止
                </button>
              )}
            </div>
          )}

          {isLanding && (
            <div className="chat-landing animate-landing-1">
              <h2 className="chat-greeting">{chatGreeting()}</h2>
              <p className="chat-landing-lead">可以问我任何问题；附加数据文件后可做表结构解读与 SQL 分析。</p>
            </div>
          )}

          <div className={`chat-thread ${isLanding ? "chat-thread-landing" : ""}`} role="log">
            {!historyReady && <p className="chat-empty">正在加载对话历史…</p>}
            {historyReady && messages.length > 0 &&
              messages.map((m) => {
                const isUser = m.role === "user";
                const copyText = !isUser ? messagePlainTextForCopy(m) : "";
                return (
                  <div key={m.id} className={`bubble ${isUser ? "user" : "assistant"}`}>
                    <BubbleHeader roleLabel={isUser ? "你" : "助手"} copyText={copyText || undefined} />
                    <MessageParts message={m} />
                  </div>
                );
              })}
            {showReplyLoading && (
              <div className="bubble assistant chat-reply-loading" aria-live="polite" aria-busy="true">
                <div className="bubble-header">
                  <div className="bubble-role">助手</div>
                </div>
                <div className="chat-reply-loading-body">
                  <span className="chat-reply-loading-dots" aria-hidden>
                    <span className="chat-reply-loading-dot" />
                    <span className="chat-reply-loading-dot" />
                    <span className="chat-reply-loading-dot" />
                  </span>
                  <span className="chat-reply-loading-text">
                    {!streamMode
                      ? "正在处理，完成后将一次性显示全文…"
                      : status === "submitted"
                        ? "正在连接…"
                        : "正在生成…"}
                  </span>
                </div>
              </div>
            )}
            <div ref={threadEndRef} />
          </div>

          {sessionFiles.length > 0 && (
            <div className="file-chips">
              <span className="file-chips-label">本对话已关联：</span>
              {sessionFiles.map((f) => (
                <span key={f.path} className="file-chip">
                  {f.label}
                  <button type="button" className="file-chip-remove" onClick={() => removeSessionFile(f.path)} aria-label="移除">
                    ×
                  </button>
                </span>
              ))}
            </div>
          )}

          {pendingFile && <p className="pending-file">待发送时上传：{pendingFile.name}</p>}

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,.xls,.json,.tsv"
            className="visually-hidden"
            id="chat-file"
            onChange={(e) => setPendingFile(e.target.files?.[0] ?? null)}
          />

          <form
            className={`composer ${isLanding ? "composer-landing animate-landing-2" : ""}`}
            onSubmit={(e) => void handleSubmit(e)}
          >
            <div className="composer-shell">
              <div className="composer-actions composer-actions-inner">
                <button type="button" className="ghost composer-icon-btn" onClick={() => fileInputRef.current?.click()} title="附加数据文件">
                  +
                </button>
                {pendingFile && (
                  <button
                    type="button"
                    className="ghost"
                    onClick={() => {
                      setPendingFile(null);
                      if (fileInputRef.current) fileInputRef.current.value = "";
                    }}
                  >
                    取消文件
                  </button>
                )}
              </div>
              <label htmlFor="msg" className="visually-hidden">
                消息
              </label>
              <textarea
                ref={textareaRef}
                id="msg"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder={
                  isLanding
                    ? "可以问我任何问题；需要时先附加数据文件……"
                    : "例如：描述各列含义；或结合公开资料解读某行业指标……"
                }
                rows={isLanding ? 4 : 5}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    void handleSubmit(e);
                  }
                }}
              />
              <div className="composer-bottom-row">
                <span className="composer-hint-muted">Enter 发送 · Shift+Enter 换行</span>
                <button type="submit" className="composer-send-fab primary" disabled={busy || !historyReady} aria-label="发送">
                  {!historyReady ? "…" : busy ? "…" : "➤"}
                </button>
              </div>
            </div>
          </form>

          {isLanding && (
            <>
              <div className="skill-pills animate-landing-3" role="group" aria-label="能力入口">
                {SKILL_PILLS.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    className={`skill-pill ${agentSkill === p.id ? "active" : ""} ${p.comingSoon ? "skill-pill-soon" : ""}`}
                    onClick={() => {
                      setAgentSkill(p.id);
                      textareaRef.current?.focus();
                    }}
                  >
                    <span className="skill-pill-text">
                      <span className="skill-pill-label">{p.label}</span>
                      {p.sub ? <span className="skill-pill-sub">{p.sub}</span> : null}
                    </span>
                    {p.comingSoon ? <span className="skill-pill-badge">扩展</span> : null}
                  </button>
                ))}
              </div>
              <p className="try-these-label animate-landing-4">试试这些：</p>
              <div className="suggestion-grid animate-landing-5">
                {TRY_THESE.map((t) => (
                  <button
                    key={t}
                    type="button"
                    className="suggestion-card"
                    onClick={() => {
                      setInput(t);
                      textareaRef.current?.focus();
                    }}
                  >
                    {t}
                  </button>
                ))}
              </div>
            </>
          )}

          {!isLanding && (
            <div className="skill-pills skill-pills-inline" role="group" aria-label="切换场景">
              {SKILL_PILLS.map((p) => (
                <button
                  key={p.id}
                  type="button"
                  className={`skill-pill ${agentSkill === p.id ? "active" : ""} ${p.comingSoon ? "skill-pill-soon" : ""}`}
                  onClick={() => setAgentSkill(p.id)}
                >
                  <span className="skill-pill-text">
                    <span className="skill-pill-label">{p.label}</span>
                    {p.sub ? <span className="skill-pill-sub">{p.sub}</span> : null}
                  </span>
                  {p.comingSoon ? <span className="skill-pill-badge">扩展</span> : null}
                </button>
              ))}
            </div>
          )}

          {error && <p className="err">{error.message}</p>}
        </div>
      </div>
    </>
  );
}

function DatasourcePanel() {
  const [rows, setRows] = useState<{ name: string; connection_url: string; description: string }[]>([]);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("sqlite+aiosqlite:///./data/analysis.db");
  const [desc, setDesc] = useState("");
  const [err, setErr] = useState<string | null>(null);

  const load = useCallback(() => {
    listDatasources()
      .then(setRows)
      .catch((e) => setErr(e instanceof Error ? e.message : String(e)));
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const add = async () => {
    if (!name.trim()) return;
    setErr(null);
    try {
      await addDatasource({ name: name.trim(), connection_url: url.trim(), description: desc });
      setName("");
      load();
    } catch (e) {
      setErr(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <>
      <h1>数据源</h1>
      <p className="sub">配置 SQLAlchemy 连接串，供智能体 SQL 工具使用（内存存储，重启后丢失）。</p>
      <div className="card">
        <div className="row two">
          <div>
            <label htmlFor="dn">名称</label>
            <input id="dn" value={name} onChange={(e) => setName(e.target.value)} placeholder="my-db" />
          </div>
          <div>
            <label htmlFor="du">连接 URL</label>
            <input id="du" value={url} onChange={(e) => setUrl(e.target.value)} />
          </div>
        </div>
        <label htmlFor="dd">说明</label>
        <input id="dd" value={desc} onChange={(e) => setDesc(e.target.value)} />
        <div style={{ marginTop: "1rem" }}>
          <button type="button" className="primary" onClick={() => void add()}>
            添加
          </button>
        </div>
        {err && <p className="err">{err}</p>}
      </div>
      <div className="card">
        <label>已配置</label>
        <table className="ds-table">
          <thead>
            <tr>
              <th>名称</th>
              <th>连接</th>
              <th>说明</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.name}>
                <td>{r.name}</td>
                <td style={{ wordBreak: "break-all" }}>{r.connection_url}</td>
                <td>{r.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && <p style={{ color: "var(--muted)", fontSize: "0.9rem" }}>暂无数据源</p>}
      </div>
    </>
  );
}
