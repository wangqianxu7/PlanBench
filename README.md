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

## PlanBench-V Results (Vision, Judge: gpt-4o-mini, 300 items)

| Rank | Model | Overall | Description | Type | Evaluation | Decision | Domain Reasoning | Association | Spatial Relation | Element |
|------|-------|---------|------|------|------|------|----------|------|----------|------|
| 🥇 | gemini-2.5-pro | **1.472/2 (73.6%)** | 1.775 | 1.656 | 1.439 | 1.525 | 1.425 | 1.468 | 1.444 | 1.408 |
| 🥈 | gpt-5.4 | **1.431/2 (71.6%)** | 1.900 | 1.562 | 1.586 | 1.508 | 1.486 | 1.438 | 1.383 | 1.233 |
| 🥉 | claude-opus-4.7 | **1.384/2 (69.2%)** | 1.825 | 1.320 | 1.434 | 1.321 | 1.558 | 1.493 | 1.295 | 1.186 |
| 4 | gpt-4o-mini | **1.084/2 (54.2%)** | 1.244 | 1.342 | 0.901 | 1.155 | 1.079 | 1.110 | 1.151 | 0.918 |

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
