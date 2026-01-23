# Performance Report: gpt-4.1-nano

**Generated:** 2026-01-23 06:26:45

---

## Test Configuration

### Use Case: RAG (Retrieval-Augmented Generation)

| Range | Input Tokens | Output Tokens |
|---|---|---|
| Min | 1,000 | 200 |
| Max | 10,000 | 500 |
| **Mean ± Stddev** | **5,500 ± 2,250** | **350 ± 75** |

### Test Settings

- **Cache Prevention**: Prefix caching disabled + Unique prompts enabled for accurate hardware performance measurement

---

## 1. Metrics Description

The following diagram illustrates the key performance metrics measured during LLM inference:

![Inference Metrics](inference.png)

### Key Metrics Explained

- **Time to First Token (TTFT)**: The time elapsed from when the query is sent until the first token is received. This measures the initial response latency and is critical for user-perceived responsiveness.

- **Inter-token Latency (ITL)**: The time between consecutive tokens during generation. Lower ITL means smoother streaming output and better user experience during text generation.

- **End-to-End Latency**: The total time from sending the query to receiving the complete response. This includes TTFT plus the entire generation time.

- **Output Throughput**: The number of tokens generated per second. Higher throughput indicates better generation efficiency.

---

## 2. Performance Testing Metrics

### End-to-End Latency (seconds)

| Concurrent_Users | P25 | P50 | P75 |
| --- | --- | --- | --- |
| 1.0 | 3.685077240249712 | 3.981400729999677 | 4.659817094499886 |
| 10.0 | 2.917407632500272 | 3.5504529965000984 | 3.88635753374956 |
| 20.0 | 2.084189176500104 | 2.3968551725001817 | 2.7656884062503195 |
| 30.0 | 2.718142688249827 | 2.849238541999512 | 3.2051779235000595 |
| 40.0 | 2.873037060499655 | 3.12135269449982 | 3.2821004575000643 |
| 50.0 | 2.2961179265000737 | 2.582553980500052 | 2.9061605030001374 |

### Inter-token Latency (seconds)

| Concurrent_Users | P25 | P50 | P75 |
| --- | --- | --- | --- |
| 1.0 | 0.0098365981287912 | 0.0106241883222361 | 0.0119130511466362 |
| 10.0 | 0.0091011653800348 | 0.009601675348723 | 0.0119597177165807 |
| 20.0 | 0.0073681739341126 | 0.0076331048683009 | 0.008228367909394 |
| 30.0 | 0.0078850353345042 | 0.0082174298135923 | 0.0088205299337807 |
| 40.0 | 0.0090571093083145 | 0.0095165394588235 | 0.0106185976083777 |
| 50.0 | 0.0079950527946834 | 0.0083633045181861 | 0.0087825153211596 |

### Time to First Token (seconds)

| Concurrent_Users | P25 | P50 | P75 |
| --- | --- | --- | --- |
| 1.0 | 0.707339258750153 | 0.9136375045000024 | 1.1413929532495786 |
| 10.0 | 0.9126089782500912 | 1.337208808500236 | 1.4270267617494028 |
| 20.0 | 0.7199125014994934 | 0.7755462789996272 | 0.8058345932502107 |
| 30.0 | 0.9408525512496908 | 0.9933039659999848 | 1.09972359174958 |
| 40.0 | 0.9683523989995138 | 1.3237518070000078 | 1.397888876500474 |
| 50.0 | 0.8375215304999983 | 0.9512028405006276 | 1.0076956739994785 |

### Output Throughput (tokens/s)

| Concurrent_Users | P25 | P50 | P75 |
| --- | --- | --- | --- |
| 1.0 | 101.02026469230876 | 112.79788638215504 | 122.66699634701376 |
| 10.0 | 99.14543797972271 | 120.33239676743152 | 129.72758253117323 |
| 20.0 | 146.95834665391996 | 158.32940364287157 | 159.83399631733684 |
| 30.0 | 137.35282501071086 | 146.56937628370576 | 150.54189956577866 |
| 40.0 | 111.1149104647135 | 128.64267783389283 | 133.35529830577457 |
| 50.0 | 136.86615282004982 | 141.88275122318944 | 149.30064305852375 |


---

## 3. Concurrent Performance Visualization

### Inter-token Latency (seconds)
![Inter-token Latency](inter_token_latency.png)

### End-to-End Latency (seconds)
![End-to-End Latency](end_to_end_latency.png)

### Time to First Token (seconds)
![Time to First Token](time_to_first_token.png)

### Output Throughput (tokens/s)
![Output Throughput](output_throughput.png)

---

## Full Performance Chart

![Performance Chart](performance_chart.png)
