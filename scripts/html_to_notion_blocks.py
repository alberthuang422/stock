#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HTML 报告 → Notion blocks 转换器
用法: python html_to_notion_blocks.py <input.html> <output.json>
输出: 一个 JSON 数组, 每个元素是 Notion API block 对象。
支持: h1/h2/h3、p、table、ul/ol、li、strong/b 加粗、em/i 斜体、code。
表格单元格内联 markdown 基础的 bold/italic 不处理 (Notion 表格单元只支持 rich_text)。
"""
import json
import re
import sys
from bs4 import BeautifulSoup, NavigableString

INLINE_RICH_MAX = 2000  # Notion rich_text 单段长度上限, 超长截断


def _rich_text_from_node(node):
    """把单个 inline 节点转成 rich_text 数组 (支持 strong/em/code/a 混合)。"""
    parts = []

    def walk(n, bold=False, italic=False, code=False):
        if isinstance(n, NavigableString):
            t = str(n)
            if not t:
                return
            parts.append({
                "type": "text",
                "text": {"content": t[:INLINE_RICH_MAX]},
                "annotations": {
                    "bold": bold, "italic": italic,
                    "strikethrough": False, "underline": False, "code": code,
                },
            })
            return
        if getattr(n, "name", None) is None:
            return
        tag = n.name
        if tag in ("strong", "b"):
            for c in n.children:
                walk(c, bold=True, italic=italic, code=code)
        elif tag in ("em", "i"):
            for c in n.children:
                walk(c, bold=bold, italic=True, code=code)
        elif tag == "code":
            for c in n.children:
                walk(c, bold=bold, italic=italic, code=True)
        elif tag == "a":
            href = n.get("href", "") or ""
            txt = "".join(str(c) for c in n.strings)
            parts.append({
                "type": "text",
                "text": {"content": txt[:INLINE_RICH_MAX], "link": {"url": href}},
                "annotations": {"bold": False, "italic": False, "strikethrough": False,
                                "underline": False, "code": False},
            })
        elif tag == "br":
            parts.append({"type": "text", "text": {"content": "\n"},
                          "annotations": {}})
        else:
            for c in n.children:
                walk(c, bold=bold, italic=italic, code=code)

    walk(node)
    # 合并相邻纯文本
    merged = []
    for p in parts:
        if p["type"] == "text" and not p["text"].get("link") and p["annotations"] == {
                "bold": False, "italic": False, "strikethrough": False,
                "underline": False, "code": False}:
            if merged and merged[-1]["type"] == "text" and not merged[-1]["text"].get("link") \
                    and merged[-1]["annotations"] == p["annotations"]:
                merged[-1]["text"]["content"] += p["text"]["content"]
                continue
        merged.append(p)
    return merged


def _clean_text(s):
    s = re.sub(r"\u00a0", " ", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def parse_html(html):
    soup = BeautifulSoup(html, "html.parser")
    # 去除 script/style/svg/canvas (图表不可转)
    for tag in soup.find_all(["script", "style", "svg", "canvas", "iframe", "nav", "footer",
                              "button", "input", "form"]):
        tag.decompose()
    return soup


def convert(soup):
    """深度优先遍历文档树, 按出现在页面的顺序收集所有可转换元素。"""
    blocks = []
    body = soup.body or soup
    # 跳过导航/页脚等区块
    SKIP_CONTAINERS = {"nav", "footer", "header", "aside", "script", "style"}

    def add_rich(blk_type, node, **extra):
        rt = _rich_text_from_node(node)
        if not rt:
            return
        blk = {"object": "block", "type": blk_type,
               blk_type: {"rich_text": rt, **extra}}
        blocks.append(blk)

    def add_table(table_el):
        rows = []
        for tr in table_el.find_all("tr"):
            cells = tr.find_all(["td", "th"])
            if not cells:
                continue
            row = []
            for c in cells:
                txt = _clean_text(c.get_text(" "))
                row.append([{"type": "text", "text": {"content": txt[:INLINE_RICH_MAX]}}])
            rows.append(row)
        if not rows:
            return
        has_header = bool(table_el.find("th"))
        blocks.append({
            "object": "block", "type": "table",
            "table": {
                "table_width": max(len(r) for r in rows),
                "has_column_header": has_header,
                "has_row_header": False,
                "children": [
                    {"object": "block", "type": "table_row",
                     "table_row": {"cells": r}} for r in rows
                ],
            },
        })

    def walk(el):
        for child in el.find_all(recursive=False):
            name = child.name
            if name in SKIP_CONTAINERS:
                continue
            if name in ("h1", "h2", "h3", "h4"):
                add_rich("heading_" + name, child)
            elif name == "p":
                add_rich("paragraph", child)
            elif name in ("ul", "ol"):
                for li in child.find_all("li", recursive=False):
                    add_rich("bulleted_list_item" if name == "ul" else "numbered_list_item", li)
            elif name == "table":
                add_table(child)
            elif name in ("blockquote", "q"):
                add_rich("quote", child)
            elif name == "pre":
                code = _clean_text(child.get_text())
                if code:
                    blocks.append({"object": "block", "type": "code",
                                   "code": {"rich_text": [{"type": "text", "text": {"content": code}}],
                                            "language": "plain text"}})
            elif name == "hr":
                blocks.append({"object": "block", "type": "divider", "divider": {}})
            elif name in ("div", "section", "article", "main", "li"):
                walk(child)

    walk(body)
    return blocks


def main():
    infile, outfile = sys.argv[1], sys.argv[2]
    with open(infile, "r", encoding="utf-8") as f:
        html = f.read()
    soup = parse_html(html)
    blocks = convert(soup)
    with open(outfile, "w", encoding="utf-8") as f:
        json.dump(blocks, f, ensure_ascii=False, indent=1)
    print(f"blocks: {len(blocks)}")


if __name__ == "__main__":
    main()