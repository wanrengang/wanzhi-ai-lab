"""通过 GitHub REST API 获取公开仓库元数据（无需登录；避免直接抓 HTML 页面）。"""

from __future__ import annotations

import re

import httpx
from langchain.tools import tool

_API = "https://api.github.com"
_HEADERS = {
    "Accept": "application/vnd.github+json",
    "User-Agent": "DeepAgent-Pro/0.1",
    "X-GitHub-Api-Version": "2022-11-28",
}


def _parse_owner_repo(text: str) -> tuple[str, str] | None:
    t = (text or "").strip()
    if not t:
        return None
    # https://github.com/owner/repo[/...]
    m = re.search(r"github\.com[/:]([^/]+)/([^/#\s?]+)", t, re.I)
    if m:
        return m.group(1), m.group(2)
    # owner/repo
    if "/" in t and not t.startswith("http"):
        parts = t.split("/")
        if len(parts) >= 2 and parts[0] and parts[1]:
            return parts[0], parts[1].split()[0]
    return None


@tool
def github_repo_info(repo: str, include_releases: bool = True, max_releases: int = 5) -> str:
    """查询 GitHub 公开仓库信息与最近 releases（官方 API，非网页抓取）。

    当用户给出 GitHub 链接或 ``owner/repo`` 并想了解项目、版本说明时使用；
    不要声称「无法访问 GitHub」，应优先调用本工具。

    Args:
        repo: 仓库，可为 ``owner/repo`` 或完整 ``https://github.com/owner/repo`` 链接
        include_releases: 是否拉取最近若干条 Release 标题与说明
        max_releases: 最多返回几条 release，默认 5，最大 10
    """
    parsed = _parse_owner_repo(repo)
    if not parsed:
        return (
            "无法解析仓库。请传入 ``owner/repo``（如 langchain-ai/deepagents）"
            "或完整 GitHub 链接。"
        )
    owner, name = parsed
    n = max(1, min(int(max_releases), 10))

    try:
        with httpx.Client(timeout=25, headers=_HEADERS, follow_redirects=True) as client:
            r = client.get(f"{_API}/repos/{owner}/{name}")
            if r.status_code == 404:
                return f"仓库不存在或不可见: {owner}/{name}"
            r.raise_for_status()
            repo_json = r.json()

            out: list[str] = []
            out.append(f"仓库: {repo_json.get('full_name', owner + '/' + name)}")
            out.append(f"描述: {repo_json.get('description') or '（无）'}")
            out.append(f"Stars: {repo_json.get('stargazers_count')}  Forks: {repo_json.get('forks_count')}")
            out.append(f"默认分支: {repo_json.get('default_branch')}")
            out.append(f"主页: {repo_json.get('homepage') or '（无）'}")
            lic = repo_json.get("license") or {}
            out.append(f"License: {lic.get('spdx_id') or lic.get('name') or '（无）'}")
            out.append(f"最近推送: {repo_json.get('pushed_at')}")
            topics = repo_json.get("topics") or []
            if topics:
                out.append(f"Topics: {', '.join(topics)}")
            out.append(f"README 入口（网页）: https://github.com/{owner}/{name}#readme")

            if include_releases:
                rr = client.get(
                    f"{_API}/repos/{owner}/{name}/releases",
                    params={"per_page": n},
                )
                if rr.status_code == 200:
                    rels = rr.json()
                    if isinstance(rels, list) and rels:
                        out.append("\n--- Releases（最近） ---")
                        for rel in rels[:n]:
                            tag = rel.get("tag_name", "")
                            published = rel.get("published_at", "")
                            body = (rel.get("body") or "").strip()
                            if len(body) > 1200:
                                body = body[:1200] + "\n…（说明已截断）"
                            out.append(f"\n· {tag}  ({published})\n{body or '（无说明）'}")
                    else:
                        out.append("\n（暂无 Release 或仅 tag，可建议用户查看仓库 Tags 页）")
                else:
                    out.append(f"\n（读取 releases 失败: HTTP {rr.status_code}）")

            return "\n".join(out)
    except httpx.HTTPStatusError as e:
        return f"GitHub API 错误: {e.response.status_code} {e.response.text[:500]}"
    except Exception as e:
        return f"请求 GitHub API 失败: {e}"
