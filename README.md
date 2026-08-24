# ComfyUI Qwen H3 Prompt

Generate MiniMax H3 prompts and production plans inside ComfyUI with a local Qwen3.8-27B model and the official MiniMax H3 Skills.

The node starts an isolated local `llama-server` process from inside ComfyUI. Inference does not access the network. When `force unload model` is enabled, the process is stopped after execution so its GPU VRAM and system memory are released without occupying ComfyUI's internal model resources.

## Local adaptation boundaries of the official Skills

The official `h3-prompt-writing` Skill explicitly supports direct portability. The other Skills originally depend on MiniMax Hub features such as canvases, selection cards, and media-generation tools. This node preserves their official creative and domain guidance, but skips asset collection, selection cards, approval gates, and media-generation steps. It produces only the final H3 prompt for the selected input mode and duration.

Unlike the official MiniMax H3 Skills, the Qwen3.8-27B GGUF model used by this node cannot analyze audio. It cannot accurately extract a reference track's melody, BPM, lyrics, timbre, or beat positions. Audio-related prompt text is a newly created sound description, not an analysis or reproduction of reference audio.

The node does not output clarification questions, confirmation requests, alternatives, pre-production packages, or suggested next steps. Optional content that the user did not supply is omitted, including on-screen text, slogans, brand claims, dialogue, voice-over, and lyrics. Essential creative details that were not specified are filled with one conservative, deterministic choice based on the request and reference media.

## Install the node

Install it with ComfyUI Manager or clone it manually:

```bash
cd ComfyUI/custom_nodes/
git clone https://github.com/jalberty2018/ComfyUI_Qwen_H3_Prompt.git
```

## Model directory

Place the Qwen3.8 vision projector and GGUF model in `ComfyUI/models/LLM/Qwen3.8/`.

- Vision projector: download `mmproj-F16.gguf` from [unsloth/Qwen3.8-27B-GGUF](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF).
- GGUF model:
  - For GPUs with more than 20 GB VRAM, `Qwen3.8-27B-Q4_K_M.gguf` from [unsloth/Qwen3.8-27B-GGUF](https://huggingface.co/unsloth/Qwen3.8-27B-GGUF) is recommended.
  - For GPUs with 16 GB VRAM, [soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf](https://huggingface.co/soyaakinohara/qwen3.8-27b-abliterated-3.69bpw-12GB-MTP.gguf) is recommended.
  - Other Qwen3.8 weights compatible with `llama-server` may also be used.

## Use a preinstalled llama-server

Managed containers can provide a native `llama-server` executable through the `MINIMAX_H3_LLAMA_SERVER` environment variable:

```bash
export MINIMAX_H3_LLAMA_SERVER=/opt/llama.cpp/bin/llama-server
```

When this variable is set, the node uses that executable instead of requiring a runtime inside the custom-node directory. The executable is shared, but the node still starts its own authenticated `llama-server` child process on a free `127.0.0.1` port. It does not connect to or replace an already-running HTTP service.

The `comfyui-runtime2` and `run-comfyui-minimax` images configure this path automatically. Do not run `install_runtime.py` inside those containers.

## Install the bundled llama-server runtime

For installations that do not provide `MINIMAX_H3_LLAMA_SERVER`, the project has one cross-platform installer: `install_runtime.py`. It uses only the Python standard library, detects Windows, Linux, or macOS plus the CPU architecture and GPU, and installs a pinned llama.cpp `b10436` runtime. No additional pip packages are required.

For the official portable ComfyUI package on Windows, run this from the node directory:

```bat
cd ComfyUI\custom_nodes\ComfyUI_Qwen_H3_Prompt
..\..\..\python_embeded\python.exe install_runtime.py
```

On Linux and macOS, run:

```bash
python install_runtime.py
```

Run the installer before starting ComfyUI for the first time. It detects the hardware and selects a backend, downloads and verifies files with SHA-256, extracts them safely, checks `llama-server --version` and `--list-devices`, and finally writes a machine-specific `runtime_config.json`. The download cache, source cache, and installed runtime remain under the node's `runtime/` directory.

Installer commands:

```bash
# Show the detected configuration and installation plan without changing files
python install_runtime.py --dry-run

# List the backends supported on the current system and architecture
python install_runtime.py --list-backends

# Select a backend manually
python install_runtime.py --backend vulkan

# Reinstall the runtime
python install_runtime.py --force

# Use only previously verified files from runtime/.downloads/b10436
python install_runtime.py --offline
```

### Automatic backend selection

| System and device | Automatic preference order |
| --- | --- |
| Windows x64 NVIDIA | CUDA 12.4 → Vulkan → CPU |
| Windows x64 AMD | ROCm 7.14 → Vulkan → CPU |
| Windows x64 Intel | SYCL → Vulkan → CPU |
| Windows x64 with an unidentified GPU | Vulkan → CPU |
| Windows ARM64 NVIDIA | CUDA 13.4 preview → CPU |
| Windows ARM64 Qualcomm Adreno | OpenCL → CPU |
| Linux x64 Intel | SYCL FP16 → Vulkan → CPU |
| Linux x64 NVIDIA, AMD, or unidentified GPU | Vulkan → CPU |
| Linux ARM64 | Vulkan → CPU |
| macOS Apple Silicon or Intel | Metal → CPU |

Available Windows backends depend on the architecture and can include `cuda12`, `cuda13`, `rocm`, `sycl`, `vulkan`, `opencl`, and `cpu`.

Official prebuilt Linux backends include `vulkan`, `sycl`, `sycl-fp32`, `openvino`, and `cpu`, depending on the architecture. The official files target Ubuntu; other distributions need compatible glibc and libstdc++ versions. Vulkan and Intel SYCL/OpenVINO also require the appropriate system GPU drivers and runtime libraries.

macOS uses the official package for the active architecture. Metal does not require an additional GPU compute framework, but a Qwen3.8-27B Q4 model and vision projector still require sufficient unified memory.

### Linux CUDA source installation

The official `b10436` release does not provide a prebuilt Linux CUDA archive. NVIDIA Linux users can explicitly build it from source:

```bash
python install_runtime.py --backend cuda --build-from-source
```

The source build does not call `sudo` or modify the system automatically. Before starting, make sure the system has:

- an NVIDIA driver for which `nvidia-smi` works;
- an NVIDIA CUDA Toolkit containing `nvcc`, with `nvcc` on `PATH` or `CUDA_HOME` configured;
- Git, CMake, a C compiler, and a C++ compiler, such as the Ubuntu/Debian `git cmake build-essential` packages.

## Node

Start ComfyUI and add `Qwen H3 Prompt (Local)` from the `😺dzNodes/Qwen_H3_Prompt` category.

![Qwen H3 Prompt node](images/QwenH3Prompt_node.jpg)

Node options:

- `skill`: select `auto`, one of the nine official Skills, or the local `h3-seamless-multishot-writing` Skill. `auto` asks Qwen to route to the appropriate Skill.
- `prompt_profile`: `standard` preserves the official Skill behavior. `uncensored fidelity` preserves requested lawful fictional tone, intensity, profanity, horror, violence, and mature themes without unsolicited sanitizing, moralizing, or warnings. It does not add explicit elements that the user did not request.
- `shot_count`: number of blocks generated by `h3-seamless-multishot-writing`, from 2 through 8. It is ignored by the other Skills.
- `duration`: target H3 video duration; the default is `10.0` seconds. For the Multishot Skill this is the duration of every individual shot, must be 10.0–15.1 seconds, and produces a total runtime of `shot_count × duration`.
- `think_mode`: disabled by default. It switches automatically between Qwen's official instruct and thinking sampling settings.
- `reasoning_effort`: used only when `think_mode` is enabled; the default is `medium`.
- `seed`: ComfyUI seed used for deterministic local inference.
- `reference_images`: dynamically connect between zero and nine individual IMAGE values. Every slot must contain exactly one image; image roles are derived from the number of inputs and the user's prompt.
- `reference_videos`: dynamically connect between zero and three IMAGE batches. Their durations and sampling timestamps are calculated at a fixed 24 fps.
- `video_sample_frames_per_sec`: number of frames sampled from every second of each reference video; the default is `2`.
- `force unload model`: enabled by default. When enabled, the node stops its `llama-server` process and releases memory and VRAM after every run. When disabled, the server remains available for reuse. Errors always force an unload.

### Image inputs and mode routing

The node selects an H3 mode with these rules:

| Input | Routing behavior |
| --- | --- |
| No images or videos | Use T2VA directly |
| One image and no video | Qwen selects I2VA, L2VA, or Ref2VA from the request |
| Two images and no video | Qwen selects FL2VA or Ref2VA from the request |
| Three to nine images | Use Ref2VA directly |
| Any connected reference video | Use Ref2VA directly |

With one or two images, the node does not infer first- or last-frame roles from image count alone. To generate a keyframe-mode prompt, explicitly state each image's temporal role:

```text
# One first-frame image: route to I2VA
Use Picture 1 as the first frame of the target video and continue forward from this scene.

# One last-frame image: route to L2VA
Use Picture 1 as the final frame of the target video and design a natural progression toward it.

# First- and last-frame images: route to FL2VA
Picture 1 is the first frame and Picture 2 is the final frame of the target video. Create a continuous transition between them.
```

If one or two images are only references for identity, product, environment, composition, or visual style, state that explicitly so the node selects Ref2VA:

```text
Use Picture 1 as a reference for the character's identity and clothing, and Picture 2 as a reference for the environment and lighting. Create a product advertisement; neither image is a first or last frame.
```

### Seamless Multishot scripts

Select `h3-seamless-multishot-writing` to generate a script for
[`ComfyUI-H3-Multishot`](https://github.com/jlucasmcrell/ComfyUI-H3-Multishot). The output contains one plain prose
paragraph per shot with exactly one line containing only `---` between adjacent shots:

```text
First shot paragraph.
---
Second shot paragraph.
---
Third shot paragraph.
```

The Skill repeats stable character identity, clothing, voice, environment, lighting, and camera-continuity sentences
word-for-word. Every later shot opens with the preceding closing arrangement, holds it with subtle motion for roughly
two seconds, performs one progressive physical action, and ends settled for the next handoff. The validator rejects
JSON, Markdown, headings, H3 field labels, empty blocks, incorrect block counts, multiline blocks, and separators that
are not exactly three hyphens on their own line.

### Reference videos

Connect at most three reference videos. Every video is an IMAGE batch in chronological frame order. At the fixed interpretation rate of 24 fps, each video must be between 2 and 15 seconds and their combined duration may not exceed 15 seconds.

`video_sample_frames_per_sec` is the number of frames sampled from each one-second window, not the total number of frames sampled from the complete video. It does not change the target video's frame rate.

The default value of `2` suits most actions and camera movements. Use `1` for mostly static product presentations. Increase it to `3` through `8` for fast action or complex transitions. Higher values preserve more motion detail per second, but reduce the area of individual frames in contact sheets and increase image encoding, memory, and inference costs.

Connecting a reference video always selects Ref2VA. The current interface receives only video frames and does not read the source video's audio track.

### Original sound and music descriptions

Qwen creates sound design that matches the user prompt, target duration, reference images, and sampled reference-video frames:

- It describes environmental sound, action sounds, spatial qualities, and sound events that evolve with the visuals.
- It describes the mood, instrumentation, tempo, development, synchronization points, and ending of original instrumental music.
- It does not invent dialogue, narration, lyrics, or singing unless the user explicitly requests them.
- If the user requests only “no background music,” the output uses `non_diegetic_music: N/A` while retaining appropriate environmental and action sounds.
- If the user explicitly requests complete silence or no sound of any kind, the output forces both `overall_soundscape: N/A` and `non_diegetic_music: N/A`.

This is newly created audio direction based on visual content. It is not analysis, reproduction, or preservation of a reference video's original sound.

## VRAM and lifecycle

When `force unload model` is disabled, the server continues to occupy approximately 20 GB of VRAM. A later run can reuse it as long as the model configuration has not changed. Enabling the option on a later run, changing the model configuration, encountering an error, or exiting ComfyUI stops the resident server.

When using this node together with another local Qwen node, avoid keeping both servers resident unless the GPU has enough memory for both model instances.

## Upstream sources and licenses

- The MiniMax H3 Skills come from [`MiniMax-AI/MiniMax-H3`](https://github.com/MiniMax-AI/MiniMax-H3) commit `d21241f0a4b3acbb34c97dae47fa417b7065e438`; the official files are stored under `skills/`.
- The cross-platform runtime installer pins llama.cpp `b10436`, corresponding to full commit `6fed9f6ff7a603b124cb8c5864fca6ea879f9f99`, and verifies downloaded files with SHA-256.
- Linux CUDA source builds use the same pinned tag and commit. The llama.cpp MIT license is stored at `third_party/llama.cpp-LICENSE`.
- This project is intended for study and research. Review the licenses of the respective upstream projects before commercial use.
