#!/usr/bin/env python3
"""
PlanBench unified inference script.
Generates model answers for both planbench (text) and planbench-v (vision).

Backend: OpenRouter (OpenAI-compatible API, supports vision).
Any other OpenAI-compatible endpoint can be used by setting
OPENROUTER_BASE_URL to the desired URL.

Usage:
  # PlanBench-V (vision)
  python inference.py --model google/gemini-2.5-pro \
      --data planbench-v/data/planbench-v-subset.json \
      --image-dir planbench-v/images --output results/gemini-2.5-pro.json

  # PlanBench (text)
  python inference.py --model openai/gpt-4o-mini \
      --data planbench/data/planbench.json --output results/gpt-4o-mini-text.json
"""

import argparse
import base64
import json
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Optional, Tuple

from tqdm import tqdm


def encode_image(image_path: str) -> Tuple[str, str]:
    with open(image_path, "rb") as f:
        content = f.read()
    ext = os.path.splitext(image_path)[1].lower()
    mime_map = {".png": "image/png", ".jpg": "image/jpeg",
                ".jpeg": "image/jpeg", ".webp": "image/webp"}
    return base64.b64encode(content).decode(), mime_map.get(ext, "image/jpeg")


class OpenRouterBackend:
    """OpenRouter / any OpenAI-compatible API."""

    def __init__(self, model: str, api_key: str = None, base_url: str = None):
        self.model = model
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.base_url = (base_url or os.environ.get(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")).rstrip("/")

    def call(self, prompt: str, image_path: str = None,
             max_retries: int = 3, retry_delay: int = 5) -> str:
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key, base_url=self.base_url)

        content = []
        if image_path:
            b64, mime = encode_image(image_path)
            content.append({"type": "image_url",
                            "image_url": {"url": f"data:{mime};base64,{b64}"}})
        content.append({"type": "text", "text": prompt})

        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=4096,
                )
                return resp.choices[0].message.content or ""
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"  [Retry {attempt+1}] {self.model}: {str(e)[:80]}")
                    time.sleep(retry_delay * (attempt + 1))
                else:
                    return f"[ERROR] {e}"


def get_backend(model: str, **kwargs):
    return OpenRouterBackend(model, **kwargs)


PLANNER_PROMPT_V = """请你仔细观察图片，然后回答以下问题。

问题：{question}

请按照以下格式回答：

<thinking>
（在这里写出你的详细分析过程）
</thinking>

<summary>
（在这里写出你的最终答案摘要）
</summary>
"""

PLANNER_PROMPT_TEXT = """你是一位城市规划师，请阅读以下问题进行思考和回复：

{question}

把思考过程放到<thinking></thinking>中，把回答放到<summary></summary>中。
"""


def parse_response(raw: str) -> Tuple[str, str]:
    thinking_match = re.search(r"<thinking>(.*?)</thinking>", raw, re.DOTALL)
    summary_match = re.search(r"<summary>(.*?)</summary>", raw, re.DOTALL)
    thinking = thinking_match.group(1).strip() if thinking_match else ""
    summary = summary_match.group(1).strip() if summary_match else raw.strip()
    if not thinking and not summary:
        summary = raw.strip()
    return thinking, summary


def process_item(backend, item: Dict, image_dir: str, is_vision: bool) -> Optional[Dict]:
    question = item.get("question") or item.get("instruction", "")
    image_path = None

    if is_vision and item.get("image_url"):
        image_path = os.path.join(image_dir, os.path.basename(item["image_url"]))
        if not os.path.exists(image_path):
            image_path = os.path.join(image_dir, item["image_url"])
        if not os.path.exists(image_path):
            print(f"  [SKIP] Image not found: {item.get('image_id', '?')}")
            return None
        prompt = PLANNER_PROMPT_V.format(question=question)
    else:
        prompt = PLANNER_PROMPT_TEXT.format(question=question)

    raw = backend.call(prompt, image_path)
    thinking, summary = parse_response(raw)

    result = item.copy()
    result["thinking"] = thinking
    result["summary"] = summary
    result["raw_response"] = raw
    return result


def main():
    parser = argparse.ArgumentParser(description="PlanBench unified inference")
    parser.add_argument("--model", required=True, help="Model name/ID")
    parser.add_argument("--data", required=True, help="Path to dataset JSON")
    parser.add_argument("--image-dir", default="planbench-v/images",
                        help="Image directory (for vision tasks)")
    parser.add_argument("--output", required=True, help="Output JSON path")
    parser.add_argument("--max-workers", type=int, default=1)
    parser.add_argument("--limit", type=int, default=0,
                        help="Limit number of items (0=all)")
    args = parser.parse_args()

    with open(args.data, "r", encoding="utf-8") as f:
        data = json.load(f)

    is_vision = any(item.get("image_url") for item in data)
    print(f"Dataset: {len(data)} items, mode={'vision' if is_vision else 'text'}")

    if is_vision:
        data = [item for item in data
                if os.path.exists(os.path.join(args.image_dir,
                                               os.path.basename(item.get("image_url", ""))))
                or os.path.exists(os.path.join(args.image_dir,
                                               item.get("image_url", "")))]
        print(f"Valid (with images): {len(data)}")

    if args.limit > 0:
        data = data[:args.limit]

    backend = get_backend(args.model)
    print(f"Model: {args.model}, Workers: {args.max_workers}")

    os.makedirs(os.path.dirname(args.output) or ".", exist_ok=True)
    results = []

    if args.max_workers <= 1:
        for i, item in enumerate(data):
            result = process_item(backend, item, args.image_dir, is_vision)
            if result:
                results.append(result)
            if (i + 1) % 10 == 0:
                print(f"  [{i+1}/{len(data)}] done")
                with open(args.output, "w", encoding="utf-8") as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    else:
        with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
            futures = {executor.submit(process_item, backend, item,
                                       args.image_dir, is_vision): i
                       for i, item in enumerate(data)}
            for future in tqdm(as_completed(futures), total=len(futures),
                               desc=args.model):
                result = future.result()
                if result:
                    results.append(result)

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nSaved {len(results)} results to {args.output}")


if __name__ == "__main__":
    main()
