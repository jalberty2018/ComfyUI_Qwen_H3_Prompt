---
name: h3-seamless-multishot-writing
description: Write seamless MiniMax H3 multi-shot scripts for ComfyUI-H3-Multishot using exact --- separator lines, repeated continuity anchors, stable shot handoffs, and progressive physical actions. Use for chained scenes, continuous takes, or stories that need two to eight H3 clips.
---

# H3 Seamless Multishot Writing

Write a sequence of H3 shot prompts that can be passed directly to ComfyUI-H3-Multishot.

## Workflow

1. Read `references/multishot-format.md` and apply its boundary, continuity, dialogue, action, framing, and audio rules.
2. Plan the requested number of shots as one progressing scene. Give every shot a distinct physical change.
3. Lock reusable sentences for recurring identity, clothing, voice, environment, lighting, and continuous camera framing before drafting the blocks.
4. Reuse those locked sentences word-for-word wherever they apply. Change expression and action only in separate sentences.
5. Write each shot as one continuous English paragraph in the required repeated order.
6. Put `---` by itself on exactly one line between adjacent shots.

## Output

- Return plain text only, never JSON or Markdown fences.
- Return no title, shot number, field label, explanation, or text outside the shot blocks.
- Use exactly one `---` separator line between adjacent non-empty blocks.
- Preserve user-provided dialogue, lyrics, and visible text exactly.
