/**
 * 部分模型会在正文里夹带思考类标签（如 MiniMax 的 think / redacted 等），
 * 会原样出现在气泡里。Markdown 渲染前剥离。
 */
export function stripThinkTags(raw: string): string {
  if (!raw) return raw;
  let t = raw;

  const patterns: RegExp[] = [
    new RegExp("<redacted_thinking>[\\s\\S]*?<\\/think>", "gi"),
    new RegExp("<thinking>[\\s\\S]*?<\\/thinking>", "gi"),
    new RegExp("<reasoning>[\\s\\S]*?<\\/reasoning>", "gi"),
    new RegExp("<redacted_thinking>[\\s\\S]*?<\\/redacted_thinking>", "gi"),
    new RegExp("<think>[\\s\\S]*?<\\/redacted_reasoning>", "gi"),
  ];

  for (const re of patterns) {
    t = t.replace(re, "");
  }

  return t.replace(/\n{3,}/g, "\n\n").trim();
}
