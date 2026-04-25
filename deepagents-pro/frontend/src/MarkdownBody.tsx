import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { stripThinkTags } from "./stripThinkTags";

type Props = {
  text: string;
  className?: string;
};

/** 助手回复：渲染 Markdown + GFM（表格、删除线等） */
export function MarkdownBody({ text, className }: Props) {
  const clean = stripThinkTags(text);
  if (!clean.trim()) return null;
  return (
    <div className={`md-content ${className ?? ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          a: ({ href, children }) => (
            <a href={href} target="_blank" rel="noopener noreferrer">
              {children}
            </a>
          ),
        }}
      >
        {clean}
      </ReactMarkdown>
    </div>
  );
}
