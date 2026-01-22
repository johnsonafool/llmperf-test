# LLMPerf 開發者指南

## 概述

LLMPerf 是一個 LLM 效能基準測試工具，用於測量大型語言模型的吞吐量和延遲。本工具特別設計用於**硬體效能測試**，提供防止 VLLM KV Cache 機制的功能，確保測試結果反映真實的硬體效能。

---

## 快速開始

### 1. 設定配置檔

編輯 `presets.yml`：

```yaml
# API 設定
api:
  openai_api_key: "your-api-key-here"
  openai_api_base: "https://api.openai.com/v1"

# 基準測試設定
benchmark:
  model_name: "gpt-4.1-nano"
  max_completed_requests: 100
  concurrent_requests: [1, 10, 20, 30, 40, 50]
  request_timeout_seconds: 600

# 使用案例預設
presets:
  rag:
    min_input_tokens: 1000
    max_input_tokens: 10000
    min_output_tokens: 200
    max_output_tokens: 500
  # ... 其他預設
```

### 2. 執行基準測試

```bash
./run.sh
```

腳本會自動執行所有預設（rag、generate、normal）並產生三份獨立的報告。

---

## Docker 使用方式（離線環境）

### 步驟一：建置映像檔（需要網路）

```bash
docker build -t llmperf:latest .
```

### 步驟二：匯出為 .tar 檔案

```bash
docker save llmperf:latest -o llmperf.tar
```

### 步驟三：傳輸到離線環境並載入

```bash
# 在離線環境載入映像檔
docker load -i llmperf.tar
```

### 步驟四：執行測試

```bash
docker run -it --rm \
    -v $(pwd)/presets.yml:/app/presets.yml:ro \
    -v $(pwd)/result_outputs:/app/result_outputs \
    llmperf:latest
```

### 掛載點說明

| 本地路徑 | 容器路徑 | 說明 |
|----------|----------|------|
| `./presets.yml` | `/app/presets.yml` | 測試配置（唯讀） |
| `./result_outputs/` | `/app/result_outputs/` | 測試結果（讀寫） |

---

## 使用案例預設（Presets）詳解

### 三種預設配置

| 預設 | 輸入 Token 範圍 | 輸出 Token 範圍 | 使用場景 |
|------|----------------|----------------|----------|
| **rag** | 1,000 - 10,000 | 200 - 500 | RAG 檢索增強生成：長文本輸入，短回答輸出 |
| **generate** | 100 - 200 | 1,000 - 10,000 | 文本生成：短提示，長輸出（如文章生成） |
| **normal** | 100 - 200 | 200 - 500 | 一般對話：平衡的輸入輸出長度 |

### 背後的實作原理

預設配置使用 **高斯分布採樣** 來產生變化的 token 長度：

```
min_tokens → max_tokens 轉換為 mean ± stddev

計算公式：
  mean = (min + max) / 2
  stddev = (max - min) / 4
```

#### 為什麼是 `(max - min) / 4`？

這是基於常態分布的 **68-95-99.7 法則**：

```
              ←────── 95% 的樣本 ──────→
         ┌────────────────────────────────────┐
         │        │           ▲           │   │
         │        │           │           │   │
        min    mean-2σ      mean      mean+2σ  max
                  ←── 2σ ──→  ←── 2σ ──→
                  ←─────── 4σ total ───────→
```

- 在常態分布中，**95% 的樣本**落在平均值的 **±2 個標準差**範圍內
- 從 `min` 到 `max` 的範圍涵蓋了 **4 個標準差**（左右各 2σ）
- 因此：`σ = (max - min) / 4`

這個設計確保：
- 約 95% 的請求落在 [min, max] 範圍內
- 約 68% 的請求落在 [mean-σ, mean+σ] 範圍內
- 測試結果具有統計意義上的變異性
- 模擬真實使用場景的 token 分布

#### 程式碼實作

```python
# src/llmperf/presets.py
def calculate_mean_stddev(min_val: int, max_val: int) -> Tuple[int, int]:
    mean = (min_val + max_val) // 2
    stddev = (max_val - min_val) // 4    # range / 4
    return mean, max(stddev, 1)          # 確保 stddev 至少為 1
```

#### 範例計算

**RAG 預設的輸入 token：**
```
min_input_tokens: 1000
max_input_tokens: 10000

mean   = (1000 + 10000) / 2 = 5500
stddev = (10000 - 1000) / 4 = 2250

結果：從高斯分布 N(5500, 2250) 中採樣
```

**三種預設的完整計算結果：**

| 預設 | 輸入 mean±stddev | 輸出 mean±stddev |
|------|------------------|------------------|
| rag | 5500 ± 2250 | 350 ± 75 |
| generate | 150 ± 25 | 5500 ± 2250 |
| normal | 150 ± 25 | 350 ± 75 |

---

## 防止 VLLM KV Cache 機制

> **預設行為：** `run.sh` 預設同時啟用 `--disable-prefix-caching` 和 `--unique-prompts`，確保測試具有完全的隨機性，反映真實的硬體效能。

```bash
# run.sh 中的預設設定
TOKEN_ARGS="--use-case $USE_CASE --disable-prefix-caching --unique-prompts"
```

### 為什麼需要防止 KV Cache？

VLLM 使用 **Prefix Caching（前綴快取）** 和 **KV Cache** 來加速推理：

```
請求 1: "Hello, how are you today?"     → 計算 KV Cache
請求 2: "Hello, how are you doing?"     → 重用 "Hello, how are you" 的 KV Cache
```

在效能測試中，這會導致：
- 後續請求的 TTFT（首 Token 延遲）被人為降低
- 無法反映真實的**硬體計算能力**
- 測試結果不具代表性

### 解決方案一：`--disable-prefix-caching`

**原理：** 為每個請求的提示詞加入唯一前綴，強制 VLLM 無法重用 KV Cache。

**實作方式：**
```python
# 啟用時的提示詞格式
prompt = f"[REQ-{unique_id}] Randomly stream lines from the following text..."

# 範例
請求 1: "[REQ-a1b2c3d4] Randomly stream lines..."
請求 2: "[REQ-e5f6g7h8] Randomly stream lines..."
請求 3: "[REQ-i9j0k1l2] Randomly stream lines..."
```

**唯一 ID 生成：**
```python
request_id = f"req_{request_index}_{timestamp_ms}"
# 例如: "req_0_1705912345678"
```

**效果：**
- 每個請求的前綴都不同
- VLLM 無法找到可重用的前綴 KV Cache
- 強制每個請求完整計算所有 token 的 KV 值

### 解決方案二：`--unique-prompts`

**原理：** 確保每個請求的提示詞內容完全不同，防止任何形式的快取重用。

**實作方式：**
```python
# 預設行為（unique_prompts=False）
random.seed(11111)  # 固定種子 → 所有請求使用相同的隨機序列
# 結果：請求內容可能重複

# 啟用 unique_prompts 時
# 不設定固定種子 → 每次執行都是真正的隨機
# 結果：每個請求的內容都是唯一的
```

**提示詞生成過程：**
1. 從 `sonnet.txt`（莎士比亞十四行詩）讀取文本
2. 隨機打亂詩句順序
3. 累加直到達到目標 token 數量
4. 如果需要更多 token，重新打亂並繼續累加

```python
while remaining_prompt_tokens > 0:
    random.shuffle(sonnet_lines)  # 打亂順序
    for line in sonnet_lines:
        prompt += line
        remaining_prompt_tokens -= token_count(line)
```

### 兩種方式的比較

| 特性 | `--disable-prefix-caching` | `--unique-prompts` |
|-----|---------------------------|-------------------|
| 防止前綴快取 | ✅ 完全防止 | ⚠️ 部分防止 |
| 防止內容重複 | ❌ 內容可能相似 | ✅ 完全不同 |
| 推薦使用場景 | 硬體效能測試 | 最大唯一性測試 |
| 效能開銷 | 低（僅加前綴） | 中（每次重新生成） |

### 預設配置（推薦）

`run.sh` **預設啟用兩個選項**，確保測試的完全隨機性：

```bash
# run.sh 預設行為
TOKEN_ARGS="--use-case $USE_CASE --disable-prefix-caching --unique-prompts"
```

這意味著：
- ✅ 每個請求都有唯一的前綴 `[REQ-xxx]`，防止 VLLM 前綴快取
- ✅ 每個請求的內容都完全不同，無固定隨機種子
- ✅ 測試結果反映真實的硬體計算能力
- ✅ 無需額外配置，開箱即用

**如果需要手動執行：**
```bash
python token_benchmark_ray.py \
    --model "your-model" \
    --disable-prefix-caching \
    --unique-prompts \
    ...
```

---

## 測試指標說明

### 主要指標

| 指標 | 說明 |
|------|------|
| **TTFT** (Time to First Token) | 首 Token 延遲：從發送請求到收到第一個 token 的時間 |
| **Inter-Token Latency** | Token 間延遲：生成相鄰 token 之間的平均時間 |
| **E2E Latency** | 端到端延遲：完成整個請求的總時間 |
| **Output Throughput** | 輸出吞吐量：每秒生成的 token 數量 |
| **Requests Per Minute** | 每分鐘完成的請求數量 |

### 統計指標

每個指標都會計算以下統計值：
- **p25, p50, p75, p90, p95, p99**：百分位數
- **mean**：平均值
- **min / max**：最小值 / 最大值
- **stddev**：標準差

---

## 輸出結構

執行 `run.sh` 後的輸出目錄結構：

```
result_outputs/
└── {model_name}_{timestamp}/
    ├── rag/
    │   ├── raw_data/
    │   │   └── performance/
    │   │       ├── 1/           # 1 個並發請求
    │   │       ├── 10/          # 10 個並發請求
    │   │       ├── 20/          # 20 個並發請求
    │   │       └── ...
    │   └── report/
    │       └── performance_report.md
    │
    ├── generate/
    │   ├── raw_data/...
    │   └── report/...
    │
    └── normal/
        ├── raw_data/...
        └── report/...
```

---

## 自訂配置

### 新增自訂預設

在 `presets.yml` 中新增：

```yaml
presets:
  # 現有預設...

  # 自訂預設：超長文本摘要
  summarize:
    description: "長文本摘要 - 超長輸入，中等輸出"
    min_input_tokens: 5000
    max_input_tokens: 20000
    min_output_tokens: 500
    max_output_tokens: 1000

  # 自訂預設：快速問答
  quick_qa:
    description: "快速問答 - 極短輸入輸出"
    min_input_tokens: 50
    max_input_tokens: 100
    min_output_tokens: 50
    max_output_tokens: 100
```

新增的預設會自動被 `run.sh` 執行。

### 調整並發請求數

```yaml
benchmark:
  concurrent_requests: [1, 5, 10, 15, 20, 25, 30]
```

---

## 程式架構

```
llmperf/
├── run.sh                      # 主要執行腳本
├── presets.yml                 # 配置檔（可掛載）
├── Dockerfile                  # Docker 映像檔定義
├── token_benchmark_ray.py      # 基準測試主程式
├── generate_charts.py          # 圖表生成
├── generate_reports.py         # 報告生成
├── result_outputs/             # 測試結果目錄（可掛載）
└── src/llmperf/
    ├── presets.py              # 預設配置載入
    ├── utils.py                # 提示詞生成邏輯
    ├── sonnet.txt              # 測試用文本（莎士比亞十四行詩）
    └── ...
```

---

## 常見問題

### Q: 為什麼要用莎士比亞十四行詩作為測試文本？

**A:** 十四行詩具有以下特點：
- 文本長度適中，可以靈活組合
- 詞彙豐富，避免過度重複
- 是公開領域文本，無版權問題
- 便於跨模型比較（使用相同文本源）

### Q: 如何確保測試結果的可重現性？

**A:**
- 如果不啟用 `--unique-prompts`，程式使用固定種子 `random.seed(11111)`
- 這確保相同配置下產生相同的提示詞序列
- 啟用 `--unique-prompts` 時，每次執行都是唯一的

### Q: 測試時應該用多少並發請求？

**A:** 建議從低到高測試：
- `[1, 10, 20, 30, 40, 50]` 可以觀察系統在不同負載下的表現
- 找出系統的吞吐量瓶頸和延遲拐點
- 高並發時關注錯誤率的變化

---

## 版本資訊

- 結果格式版本：`2023-08-31`
- Tokenizer：`LlamaTokenizerFast` (hf-internal-testing/llama-tokenizer)
