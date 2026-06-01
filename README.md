# PlanBench

[![Blog](https://img.shields.io/badge/Blog-PlanGPT-blue)](https://plangpt.github.io/)
[![HuggingFace](https://img.shields.io/badge/🤗-Dataset-yellow)](https://huggingface.co/datasets/chichi56/PlanBench)
[![GitHub](https://img.shields.io/badge/GitHub-PlanBench-black)](https://github.com/zhuchichi56/PlanBench)

**PlanBench** is a benchmark for evaluating LLMs on urban planning tasks, including both text-based QA and vision-based QA.

| Subset | Items | Type | Description |
|--------|-------|------|-------------|
| **PlanBench** | 405 | Text | Urban planning exam questions (memory, understanding, analysis, application, evaluation) |
| **PlanBench-V** (subset) | 300 | Vision | Planning map understanding with critical-point scoring |
| **PlanBench-V** (full) | 1,567 | Vision | Full vision benchmark |

## Data

### Download

- **GitHub** (this repo): `planbench/data/` and `planbench-v/data/` contain the question JSONs
- **HuggingFace** (includes images): [chichi56/PlanBench](https://huggingface.co/datasets/chichi56/PlanBench)

```bash
# Clone with data
git clone https://github.com/zhuchichi56/PlanBench.git
cd PlanBench

# Download images from HuggingFace (required for vision tasks)
pip install huggingface_hub
huggingface-cli download chichi56/PlanBench --repo-type dataset --local-dir .
```

### Data Format

**PlanBench (text)** — `planbench/data/planbench.json`:
```json
{
  "instruction": "问题文本...",
  "response": "参考答案...",
  "type": "记忆能力",
  "answer": "简答",
  "explanation": "解析..."
}
```

**PlanBench-V (vision)** — `planbench-v/data/planbench-v-subset.json`:
```json
{
  "type": "要素",
  "image_id": "22-1",
  "image_url": "images/22-1.png",
  "question": "请描述国家重点湿地。",
  "answer": "...",
  "critical_points": ["[1] ...", "[2] ...", "[3] ..."]
}
```

## Quick Start

### 1. Install Dependencies

```bash
pip install openai httpx tqdm
```

### 2. Run Inference

`inference.py` uses an OpenAI-compatible backend (OpenRouter by default). Any
OpenAI-compatible endpoint works by overriding `OPENROUTER_BASE_URL`.

```bash
export OPENROUTER_API_KEY="sk-or-..."

# PlanBench-V (vision)
python inference.py \
    --model google/gemini-2.5-pro \
    --data planbench-v/data/planbench-v-subset.json \
    --image-dir planbench-v/images \
    --output planbench-v/results/gemini-2.5-pro.json

# PlanBench (text)
python inference.py \
    --model openai/gpt-4o-mini \
    --data planbench/data/planbench.json \
    --output planbench/results/gpt-4o-mini.json

# Limit to first 5 items for testing
python inference.py --model openai/gpt-4o-mini \
    --data planbench-v/data/planbench-v-subset.json \
    --image-dir planbench-v/images \
    --output planbench-v/results/test.json --limit 5
```

### 3. Run Evaluation (Judge)

`eval.py` scores inference outputs using a judge model.

```bash
# Score vision answers (judge needs image access)
python eval.py \
    --judge openai/gpt-4o-mini \
    --input planbench-v/results/gemini-2.5-pro.json \
    --image-dir planbench-v/images \
    --output planbench-v/results/gemini-2.5-pro-scored.json

# Score text answers
python eval.py \
    --judge openai/gpt-4o-mini \
    --input planbench/results/gpt-4o-mini.json \
    --output planbench/results/gpt-4o-mini-scored.json
```

**Scoring**:
- **PlanBench-V**: Each answer is checked against `critical_points`. Score = (matched / total) × 2. Range: 0–2.
- **PlanBench**: Judge evaluates analysis logic (0–1) + answer correctness (0–1). Range: 0–2.

### 4. Concurrency

Both scripts support `--max-workers N` for parallel processing:

```bash
python inference.py --model openai/gpt-4o-mini \
    --data planbench-v/data/planbench-v-subset.json \
    --image-dir planbench-v/images \
    --output planbench-v/results/test.json --max-workers 8
```

## Repo Structure

```
PlanBench/
├── README.md
├── inference.py              # Unified inference (OpenAI-compatible backend)
├── eval.py                   # Unified evaluation / judge
├── planbench/
│   ├── data/
│   │   └── planbench.json    # 405 text items
│   └── results/              # Text eval results
└── planbench-v/
    ├── data/
    │   ├── planbench-v-subset.json   # 300 vision items
    │   └── planbench-v-full.json     # 1,567 vision items
    ├── images/                       # Planning map images
    └── results/                      # Vision eval results
```

## PlanBench-V Results (Vision, Judge: gpt-4o-mini, 300-item stratified subset)

Numbers match Table 2 in the IJGIS paper. Overall is a per-item (micro) average over the 300-item subset, so it is not the unweighted mean of the eight sub-task columns.

### First Round (2025)

| Rank | Model | Elem. Recog. | Caption | Classification | Spatial Reasoning | Domain Reasoning | Association | Scheme Eval. | Decision Making | **Overall** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | GPT-4o | 1.051 | 1.878 | 1.406 | 1.305 | 1.564 | 1.527 | 1.223 | 1.429 | **1.342** |
| 2 | Qwen2.5-VL-72B-AWQ | 1.299 | 1.825 | 1.406 | 1.248 | 1.263 | 1.253 | 1.153 | 1.090 | **1.288** |
| 3 | InternVL3-9B | 1.173 | 1.878 | 1.297 | 1.260 | 1.435 | 1.297 | 0.921 | 0.903 | **1.271** |
| 4 | Qwen2.5-VL-7B | 1.101 | 1.628 | 1.089 | 0.865 | 1.110 | 1.069 | 0.802 | 1.054 | **1.050** |
| 5 | InternVL3-14B | 0.931 | 1.580 | 1.177 | 0.793 | 0.998 | 1.098 | 0.709 | 0.917 | **0.980** |
| 6 | Qwen2-VL-72B-AWQ | 1.010 | 1.367 | 1.125 | 0.746 | 0.967 | 1.114 | 0.670 | 0.632 | **0.963** |
| 7 | Qwen2-VL-7B | 0.902 | 1.386 | 1.031 | 0.716 | 0.943 | 0.979 | 0.857 | 0.657 | **0.910** |
| 8 | InternVL3-8B | 0.992 | 1.783 | 1.026 | 0.798 | 0.751 | 0.926 | 0.631 | 1.073 | **0.909** |
| 9 | Qwen2.5-VL-3B | 0.862 | 1.554 | 0.953 | 0.691 | 0.870 | 0.970 | 0.697 | 0.936 | **0.876** |
| 10 | GPT-4o-mini | 0.664 | 0.890 | 1.021 | 0.789 | 1.030 | 0.963 | 0.636 | 1.175 | **0.866** |
| 11 | Qwen2-VL-2B | 0.744 | 0.925 | 0.948 | 0.500 | 0.656 | 0.926 | 0.537 | 0.792 | **0.731** |

### Second Round (2026, agentic reasoning models)

| Rank | Model | Elem. Recog. | Caption | Classification | Spatial Reasoning | Domain Reasoning | Association | Scheme Eval. | Decision Making | **Overall** |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | Qwen3.6-Plus | 1.751 | 1.950 | 1.672 | 1.670 | 1.744 | 1.619 | 1.619 | 1.710 | **1.701** |
| 2 | Gemini-2.5-Pro | 1.408 | 1.775 | 1.656 | 1.444 | 1.425 | 1.468 | 1.439 | 1.525 | **1.472** |
| 3 | GPT-5.4 | 1.233 | 1.900 | 1.562 | 1.383 | 1.486 | 1.438 | 1.586 | 1.508 | **1.431** |
| 4 | Kimi-K2.6 | 1.518 | 1.516 | 1.344 | 1.414 | 1.376 | 1.365 | 1.440 | 1.317 | **1.417** |
| 5 | Claude-Opus-4.7 | 1.186 | 1.825 | 1.320 | 1.295 | 1.558 | 1.493 | 1.434 | 1.321 | **1.384** |
| 6 | Qwen3.6-Flash | 1.318 | 1.636 | 1.297 | 1.353 | 1.476 | 1.351 | 1.046 | 1.441 | **1.353** |

Per-model scored JSON files for Gemini-2.5-Pro, GPT-5.4, and Claude-Opus-4.7 are under `planbench-v/results/`.

## PlanBench Results (Text, Judge: gpt-4o-mini, 405 items)

Score = answer accuracy (%). Cognitive levels: Remember, Understand, Apply, Analyze, Evaluate.

| Rank | Model | Score | Remember | Understand | Apply | Analyze | Evaluate |
|------|-------|-------|----------|------------|-------|---------|----------|
| 1 | Qwen3-32B | **80.9%** | 97.5 | 86.4 | 95.1 | 86.1 | 39.5 |
| 2 | Qwen3-14B | **80.6%** | 97.5 | 77.8 | 92.6 | 86.8 | 48.1 |
| 3 | QwQ-32B | **80.4%** | 95.1 | 85.2 | 91.4 | 91.9 | 38.3 |
| 4 | Qwen3-8B | **80.0%** | 93.8 | 80.2 | 90.1 | 90.4 | 45.7 |
| 5 | Qwen3-4B | **78.8%** | 95.1 | 72.8 | 90.1 | 89.3 | 46.9 |
| 6 | Qwen3-30B-A3B | **78.4%** | 97.5 | 79.0 | 88.9 | 89.5 | 37.0 |
| 7 | Qwen3-1.7B | **74.1%** | 95.1 | 79.0 | 76.5 | 85.1 | 34.6 |
| 8 | glm-4-9b-chat | **73.3%** | 91.4 | 72.8 | 84.0 | 79.9 | 38.3 |
| 9 | Meta-Llama-3-8B-Instruct | **70.6%** | 95.1 | 58.0 | 72.8 | 78.8 | 48.1 |
| 10 | Qwen2.5-3B-Instruct | **70.3%** | 98.8 | 66.7 | 92.6 | 64.0 | 29.6 |
| 11 | Qwen2.5-7B-Instruct | **69.5%** | 98.8 | 70.4 | 81.5 | 65.9 | 30.9 |
| 12 | Qwen2-VL-7B-Instruct | **68.2%** | 93.8 | 65.4 | 76.5 | 65.7 | 39.5 |
| 13 | DeepSeek-R1-Distill-Llama-8B | **68.1%** | 93.8 | 64.2 | 75.3 | 78.8 | 28.4 |
| 14 | DeepSeek-R1-Distill-Qwen-7B | **68.0%** | 96.3 | 69.1 | 77.8 | 73.4 | 23.5 |
| 15 | Qwen3-0.6B | **55.9%** | 90.1 | 55.6 | 46.9 | 74.8 | 12.3 |
| 16 | Llama-3.1-Tulu-3-8B | **49.0%** | 60.5 | 56.8 | 30.9 | 80.8 | 16.0 |
| 17 | chatglm3-6b | **48.3%** | 80.2 | 37.5 | 44.4 | 58.3 | 21.0 |
| 18 | Qwen2.5-0.5B-Instruct | **39.3%** | 65.4 | 21.0 | 25.9 | 69.4 | 14.8 |

Per-model raw eval results are under `planbench/results/`.

## OpenRouter Setup

1. Get an API key from [openrouter.ai](https://openrouter.ai/)
2. Set the environment variable:
   ```bash
   export OPENROUTER_API_KEY="sk-or-v1-..."
   ```
3. Use any model available on OpenRouter:
   ```bash
   python inference.py --model google/gemini-2.5-pro ...
   python inference.py --model anthropic/claude-sonnet-4 ...
   python inference.py --model openai/gpt-4o ...
   ```

## Citation

If you use PlanBench in your research, please cite:

```bibtex
@misc{zhu2024plangptenhancingurbanplanning,
      title={PlanGPT: Enhancing Urban Planning with Tailored Language Model and Efficient Retrieval},
      author={He Zhu and Wenjia Zhang and Nuoxian Huang and Boyang Li and Luyao Niu and Zipei Fan and Tianle Lun and Yicheng Tao and Junyou Su and Zhaoya Gong and Chenyu Fang and Xing Liu},
      year={2024},
      eprint={2402.19273},
      archivePrefix={arXiv},
      primaryClass={cs.CL},
      url={https://arxiv.org/abs/2402.19273},
}

@misc{deng2025urban,
    title = {Urban Planning Bench: A Comprehensive Benchmark for Evaluating Urban Planning Capabilities in Large Language Models},
    author = {Yijie Deng and He Zhu and Wen Wang and Minxin Chen and Junyou Su and Wenjia Zhang},
    year = {2025},
    institution = {Behavioral and Spatial AI Lab, Tongji University and Peking University; College of Architecture and Urban Planning, Tongji University},
    note = {†Equal contribution. *Corresponding author: wenjiazhang@tongji.edu.cn},
}
```

## License

Released for academic research use. See dataset card on HuggingFace for terms.
