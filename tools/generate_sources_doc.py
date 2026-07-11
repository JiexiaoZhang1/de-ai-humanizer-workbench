#!/usr/bin/env python3
"""Generate the committed bilingual source index from adapter metadata."""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ADAPTERS_FILE = ROOT / "data" / "adapters.json"
OUTPUT_FILE = ROOT / "docs" / "SOURCES.md"


def clean(value: Any) -> str:
    return " ".join(str(value or "").replace("|", "\\|").split())


def mode_label(mode: str) -> str:
    labels = {
        "native_skill": "Native skill reference",
        "decomposed_mcp": "MCP reference",
        "decomposed_node_web": "Node/Web reference",
        "decomposed_python": "Python reference",
        "decomposed_reference": "General app/reference",
    }
    return labels.get(mode, clean(mode))


def render(adapters: list[dict[str, Any]]) -> str:
    groups: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for adapter in adapters:
        groups[adapter.get("category", "Other")].append(adapter)

    lines = [
        "# Third-Party Source Index / 第三方来源索引",
        "",
        f"This file is generated from `data/adapters.json` and lists {len(adapters)} upstream repositories referenced by the node registry.",
        "",
        f"本文档由 `data/adapters.json` 生成，列出节点库引用的 {len(adapters)} 个上游仓库。",
        "",
        "## Distribution boundary / 分发边界",
        "",
        "The repositories below are independent works. Their code and Git history are not redistributed in this repository. A user may shallow-clone selected sources into the ignored local cache with `python3 tools/fetch_sources.py`. The downloader does not install dependencies or execute upstream code.",
        "",
        "下列仓库都是彼此独立的作品。本仓库不重新分发它们的代码和 Git 历史。用户可以通过 `python3 tools/fetch_sources.py` 将指定来源浅克隆到被忽略的本地缓存中；下载器不会安装依赖，也不会执行上游代码。",
        "",
        "Each upstream project keeps its own copyright, license, terms, and security posture. A link in this index is attribution and research provenance, not an endorsement, license grant, or claim of ownership. Review the current upstream repository before downloading or using its material.",
        "",
        "每个上游项目保留自己的版权、许可证、使用条款和安全边界。这里的链接只用于注明来源和研究过程，不代表背书、授权或所有权声明。下载或使用任何资料前，请查看上游仓库的当前内容和许可证。",
        "",
        "## Rebuild this file / 重新生成",
        "",
        "```bash",
        "python3 tools/generate_sources_doc.py",
        "```",
        "",
    ]

    for category in sorted(groups):
        items = sorted(groups[category], key=lambda item: item["repo"].lower())
        lines.extend(
            [
                f"## {clean(category)} ({len(items)})",
                "",
                "| Node | Upstream repository | Research mode | Description |",
                "| --- | --- | --- | --- |",
            ]
        )
        for adapter in items:
            repo = clean(adapter["repo"])
            url = f"https://github.com/{repo}"
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{clean(adapter['id'])}`<br>{clean(adapter['name'])}",
                        f"[{repo}]({url})",
                        mode_label(clean(adapter.get("integration_mode"))),
                        clean(adapter.get("description")),
                    ]
                )
                + " |"
            )
        lines.append("")

    lines.extend(
        [
            "## Notes / 说明",
            "",
            "- `prompt_files` in `data/adapters.json` is an allow-list of text paths the local server may inspect when a source is cached.",
            "- Missing optional source files are skipped; the built-in category profile remains available.",
            "- Repository descriptions are research metadata and may summarize upstream wording; consult the linked repository for authoritative information.",
            "- `prompt_files` 是缓存来源存在时允许本地服务读取的文本路径白名单。",
            "- 可选来源文件不存在时会被跳过，节点仍然可以使用内置类别规则。",
            "- 节点描述是调研元数据，权威信息以上游链接中的当前内容为准。",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    with ADAPTERS_FILE.open("r", encoding="utf-8") as handle:
        adapters = json.load(handle)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(render(adapters), encoding="utf-8")
    print(f"Wrote {OUTPUT_FILE.relative_to(ROOT)} with {len(adapters)} sources.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
