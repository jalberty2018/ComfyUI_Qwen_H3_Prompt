# Seamless H3 multishot format

This local adaptation is based on the render-verified prompting guidance in
[`ComfyUI-H3-Multishot` v2.6.5](https://github.com/jlucasmcrell/ComfyUI-H3-Multishot/tree/v2.6.5),
especially [`PROMPTING.md`](https://github.com/jlucasmcrell/ComfyUI-H3-Multishot/blob/v2.6.5/PROMPTING.md).
The upstream project is distributed under the MIT License. These instructions are paraphrased and specialized for
the Qwen H3 prompt node.

## Parser contract

The downstream parser splits plain text with the regular expression `(?m)^---\s*$`.

```text
First shot paragraph.
---
Second shot paragraph.
---
Third shot paragraph.
```

The separator is structural data:

- use exactly three ASCII hyphens;
- put it on its own line;
- put one separator between adjacent blocks;
- never put a separator before the first block or after the last block;
- never use `---` decoratively inside a block.

## Repeated shot structure

Weave every block into one natural prose paragraph in this order:

1. recurring character identity and appearance anchors;
2. clothing and, for speaking characters, voice anchors;
3. current expression, gaze, or posture in separate changeable sentences;
4. the inherited opening arrangement and short boundary hold for shots after the first;
5. one clear physical action in chronological order;
6. visual style and palette;
7. camera type, framing, and motion;
8. environment and lighting;
9. diegetic sound;
10. background music or its explicit absence.

Copy stable identity, clothing, voice, room, lighting, and continuous-camera sentences word-for-word across every
block where they apply. Do not paraphrase these anchors. Current expression and shot-specific action must remain
separate so the scene can progress without changing the anchors.

## Boundary handoff

- Shot 1 establishes the scene and ends in a stable arrangement.
- Every later shot opens with exactly the previous closing arrangement: the same people and props in the same
  positions, with the same framing and camera phrase.
- Hold that inherited arrangement for about two seconds before new dialogue or action. Give the hold subtle life,
  such as breathing, a small weight shift, or an eyeline change; do not describe a frozen frame.
- End every shot settled, with dialogue complete and about two seconds reserved for the next handoff.
- Move location, staging, or camera changes into the middle of a shot after the opening hold, never across a boundary.

## Progression

Every shot must create one visible physical state that did not exist in the previous shot. Prefer an affirmative,
irreversible change: a paper is torn and dropped, a drawer is opened and left open, an object changes hands, or a
light is switched on. A mood change, look, or camera move alone is not enough. Avoid negated action descriptions;
state what visibly happens.

## Dialogue and faces

- A spoken line must fit entirely inside one shot; never split it across `---`.
- Budget time for the opening hold, unhurried dialogue/action, and stable ending.
- Speaking faces stay readable and no wider than a medium close-up.
- A recurring character ends the shot with the face visible and settled rather than turned away or covered.
- For a silent visible character, describe closed lips and breathing affirmatively so the model does not invent speech.

## Physical motion

Describe body mechanics only when visible in the chosen framing. For walking, describe foot contact with the named
surface. For a turn, describe head, shoulders, then hips in order. For object handling, describe hand contact and
weight transfer. When camera and subject both move, state their relationship explicitly. Do not mention feet or floor
in a face-framed close shot because those details can pull the composition away from the face.

