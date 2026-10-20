#!/usr/bin/env python3
"""Convert an OpenCode ``session export`` JSON file into a readable Markdown log.

Usage:
    python tools/export_chat.py docs/chat_export.json docs/LLM_CHAT_LOG.md

The raw JSON keeps every byte of the conversation. This converter keeps every
user/assistant message and every tool call, but truncates very long tool inputs
and outputs so the Markdown stays readable. A truncation marker points back to
the raw export.
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOL_LIMIT = 4000


def timestamp(ms):
    if not ms:
        return ""
    return datetime.fromtimestamp(ms / 1000, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def fence(text, language=""):
    text = text.replace("\r\n", "\n")
    # Use a fence longer than any run of backticks in the payload.
    longest = 0
    run = 0
    for char in text:
        if char == "`":
            run += 1
            longest = max(longest, run)
        else:
            run = 0
    ticks = "`" * max(3, longest + 1)
    return f"{ticks}{language}\n{text}\n{ticks}"


def shorten(text, limit=TOOL_LIMIT):
    text = text or ""
    if len(text) <= limit:
        return text
    return text[:limit] + f"\n... [truncated {len(text) - limit} characters; see docs/chat_export.json]"


def tool_input(part):
    state = part.get("state") or {}
    payload = state.get("input")
    if payload is None:
        return ""
    if isinstance(payload, str):
        return payload
    return json.dumps(payload, indent=2, ensure_ascii=False)


def tool_output(part):
    state = part.get("state") or {}
    chunks = []
    for item in state.get("content") or []:
        kind = item.get("type")
        if kind == "text":
            chunks.append(item.get("text", ""))
        elif kind == "blob":
            chunks.append(f"[binary {item.get('mimeType', 'data')}, {len(item.get('blob', ''))} base64 chars]")
        else:
            chunks.append(json.dumps(item, ensure_ascii=False))
    return "\n".join(chunks)


def convert(source, destination):
    data = json.loads(Path(source).read_text())
    info = data.get("info", {})
    messages = data.get("messages", [])

    lines = [
        "# Complete LLM chat history",
        "",
        "This is the full transcript of the OpenCode session used to repair and",
        "complete the Bubble Bobble lab. The raw machine-readable export is",
        "[`chat_export.json`](chat_export.json). Long tool payloads below are",
        "truncated for readability; the JSON contains the complete text.",
        "",
        "| Field | Value |",
        "| --- | --- |",
        f"| Session | `{info.get('id', 'unknown')}` |",
        f"| Title | {info.get('title', 'unknown')} |",
        f"| Agent | `{info.get('agent', 'unknown')}` |",
        f"| Model | `{(info.get('model') or {}).get('providerID', '?')}/{(info.get('model') or {}).get('id', '?')}` |",
        f"| Started | {timestamp((info.get('time') or {}).get('created'))} |",
        f"| Messages | {len(messages)} |",
        "",
        "---",
        "",
    ]

    turn = 0
    for message in messages:
        kind = message.get("type")
        created = timestamp((message.get("time") or {}).get("created"))
        if kind == "user":
            turn += 1
            lines += [f"## Turn {turn} - User", "", f"_{created}_", "", message.get("text", ""), ""]
            continue

        if kind != "assistant":
            continue

        lines += [f"### Assistant ({created})", ""]
        for part in message.get("content") or []:
            part_type = part.get("type")
            if part_type == "text":
                text = part.get("text", "").strip()
                if text:
                    lines += [text, ""]
            elif part_type == "reasoning":
                text = part.get("text", "").strip()
                if text:
                    lines += ["<details><summary>Reasoning / planning</summary>", "", fence(shorten(text, 6000)), "", "</details>", ""]
            elif part_type == "tool":
                name = part.get("name", "tool")
                status = (part.get("state") or {}).get("status", "?")
                lines += [f"**Tool call `{name}`** ({status})", ""]
                payload = tool_input(part)
                if payload:
                    lines += ["Input:", "", fence(shorten(payload), "json"), ""]
                output = tool_output(part)
                if output:
                    lines += ["Output:", "", fence(shorten(output)), ""]
        lines += ["", "---", ""]

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines).rstrip() + "\n")
    print(f"wrote {destination} ({destination.stat().st_size} bytes, {len(messages)} messages)")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("usage: python tools/export_chat.py SESSION.json OUTPUT.md", file=sys.stderr)
        raise SystemExit(2)
    convert(sys.argv[1], sys.argv[2])
