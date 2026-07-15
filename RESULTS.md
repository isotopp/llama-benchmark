# Benchmark results

This document summarizes the complete 32-configuration benchmark run performed
on 14–15 July 2026. The committed source data is in
`benchmark_results_kris/`; each configuration directory contains the prompts,
raw llama.cpp responses, `results.csv`, `summary.txt`, and `server.log`.

## Test matrix

- Models: Qwen 3.6 27B dense and Qwen 3.6 35B-A3B MoE
- Model formats: BF16, Q4_K_M, Q6_K, and Q8_0
- TurboQuant KV cache: Turbo 3 and Turbo 4
- Symmetric mode: on and off
- Workloads: short generation, numeric analysis, code generation, and long
  context
- Repetitions: one warm-up and five measured runs per workload
- Context size: 65,536 tokens

All values below are medians from the five measured runs. Prompt and generation
rates are reported separately because they exercise different parts of the
inference path.

## Overview

| Model family | Mean generation | Observed generation range | Mean prompt processing |
|---|---:|---:|---:|
| 27B dense | 8.59 tok/s | 4.86–13.48 tok/s | 92.38 tok/s |
| 35B-A3B MoE | 58.31 tok/s | 34.29–83.53 tok/s | 494.41 tok/s |

The 35B-A3B MoE was approximately 6.8 times faster in generation and 5.4
times faster in prompt processing than the 27B dense model across this matrix.

### Quantization averages

| Model family | Quantization | Generation | Prompt processing |
|---|---|---:|---:|
| 27B dense | BF16 | 6.31 tok/s | 99.29 tok/s |
| 27B dense | Q4_K_M | 10.89 tok/s | 89.39 tok/s |
| 27B dense | Q6_K | 8.70 tok/s | 88.07 tok/s |
| 27B dense | Q8_0 | 8.47 tok/s | 92.75 tok/s |
| 35B-A3B MoE | BF16 | 39.82 tok/s | 415.89 tok/s |
| 35B-A3B MoE | Q4_K_M | 70.26 tok/s | 506.91 tok/s |
| 35B-A3B MoE | Q6_K | 65.61 tok/s | 515.34 tok/s |
| 35B-A3B MoE | Q8_0 | 57.57 tok/s | 539.51 tok/s |

Q4_K_M was the fastest quantization. Q6_K provides the recommended balance of
speed and expected model fidelity, especially for the MoE model, where it was
about 14% faster in generation than Q8_0. This benchmark measures throughput,
not answer quality; quality comparisons are expectations based on quantization
precision rather than scores produced by this run.

Symmetric mode and Turbo version produced no consistent overall winner. In
paired comparisons, symmetric on averaged 0.994 times the generation speed of
symmetric off, while Turbo 3 averaged 1.014 times the generation speed of Turbo
4. These small and inconsistent differences should be treated as run-to-run
variation. Turbo 3 with symmetric off is a reasonable default; workload-specific
requirements should take precedence.

## Generation throughput

Median generated tokens per second:

| Model | Quantization | Turbo | Symmetric | Short | Numeric | Code | Long context |
|---|---|---:|:---:|---:|---:|---:|---:|
| 27B | BF16 | 3 | on | 9.22 | 6.07 | 8.27 | 6.07 |
| 27B | BF16 | 3 | off | 6.48 | 6.50 | 6.43 | 5.97 |
| 27B | BF16 | 4 | on | 6.30 | 6.33 | 5.84 | 4.86 |
| 27B | BF16 | 4 | off | 5.69 | 5.85 | 5.80 | 5.23 |
| 27B | Q4_K_M | 3 | on | 11.86 | 11.69 | 11.98 | 13.48 |
| 27B | Q4_K_M | 3 | off | 10.29 | 10.51 | 10.28 | 10.48 |
| 27B | Q4_K_M | 4 | on | 9.92 | 9.89 | 10.23 | 11.01 |
| 27B | Q4_K_M | 4 | off | 10.90 | 10.54 | 10.41 | 10.78 |
| 27B | Q6_K | 3 | on | 8.18 | 8.36 | 8.54 | 9.49 |
| 27B | Q6_K | 3 | off | 8.54 | 8.38 | 8.52 | 9.42 |
| 27B | Q6_K | 4 | on | 8.46 | 8.51 | 8.44 | 9.37 |
| 27B | Q6_K | 4 | off | 8.48 | 8.64 | 8.40 | 9.39 |
| 27B | Q8_0 | 3 | on | 8.42 | 8.40 | 8.41 | 8.36 |
| 27B | Q8_0 | 3 | off | 8.55 | 9.42 | 8.91 | 8.43 |
| 27B | Q8_0 | 4 | on | 8.45 | 8.22 | 8.39 | 7.80 |
| 27B | Q8_0 | 4 | off | 8.23 | 8.37 | 8.61 | 8.57 |
| 35B-A3B | BF16 | 3 | on | 34.29 | 34.66 | 35.14 | 41.45 |
| 35B-A3B | BF16 | 3 | off | 36.91 | 37.77 | 38.87 | 47.91 |
| 35B-A3B | BF16 | 4 | on | 38.27 | 37.82 | 38.23 | 51.05 |
| 35B-A3B | BF16 | 4 | off | 40.38 | 40.59 | 40.68 | 43.08 |
| 35B-A3B | Q4_K_M | 3 | on | 58.49 | 57.61 | 56.37 | 73.59 |
| 35B-A3B | Q4_K_M | 3 | off | 68.06 | 69.05 | 69.35 | 82.60 |
| 35B-A3B | Q4_K_M | 4 | on | 70.03 | 70.21 | 70.08 | 82.61 |
| 35B-A3B | Q4_K_M | 4 | off | 70.86 | 70.98 | 70.71 | 83.53 |
| 35B-A3B | Q6_K | 3 | on | 61.08 | 61.13 | 60.98 | 72.59 |
| 35B-A3B | Q6_K | 3 | off | 62.57 | 62.81 | 62.72 | 76.10 |
| 35B-A3B | Q6_K | 4 | on | 61.98 | 62.28 | 62.15 | 76.43 |
| 35B-A3B | Q6_K | 4 | off | 63.01 | 63.51 | 62.88 | 77.55 |
| 35B-A3B | Q8_0 | 3 | on | 53.33 | 53.46 | 53.36 | 64.42 |
| 35B-A3B | Q8_0 | 3 | off | 54.66 | 54.81 | 54.63 | 67.72 |
| 35B-A3B | Q8_0 | 4 | on | 54.41 | 54.55 | 54.30 | 67.61 |
| 35B-A3B | Q8_0 | 4 | off | 54.81 | 55.32 | 55.06 | 68.62 |

## Prompt-processing throughput

Median prompt tokens per second:

| Model | Quantization | Turbo | Symmetric | Short | Numeric | Code | Long context |
|---|---|---:|:---:|---:|---:|---:|---:|
| 27B | BF16 | 3 | on | 84.74 | 98.34 | 114.20 | 128.17 |
| 27B | BF16 | 3 | off | 70.09 | 101.09 | 95.81 | 145.79 |
| 27B | BF16 | 4 | on | 68.86 | 101.23 | 89.81 | 101.16 |
| 27B | BF16 | 4 | off | 65.31 | 97.98 | 91.19 | 134.82 |
| 27B | Q4_K_M | 3 | on | 68.03 | 95.23 | 89.03 | 139.90 |
| 27B | Q4_K_M | 3 | off | 63.35 | 84.32 | 78.87 | 121.01 |
| 27B | Q4_K_M | 4 | on | 59.50 | 85.61 | 83.35 | 116.92 |
| 27B | Q4_K_M | 4 | off | 64.50 | 87.73 | 79.98 | 112.91 |
| 27B | Q6_K | 3 | on | 60.19 | 86.21 | 81.35 | 121.61 |
| 27B | Q6_K | 3 | off | 63.46 | 86.23 | 81.49 | 123.74 |
| 27B | Q6_K | 4 | on | 64.05 | 84.53 | 82.09 | 119.06 |
| 27B | Q6_K | 4 | off | 63.10 | 88.36 | 80.47 | 123.24 |
| 27B | Q8_0 | 3 | on | 66.18 | 92.72 | 88.03 | 128.32 |
| 27B | Q8_0 | 3 | off | 66.05 | 97.23 | 87.10 | 125.79 |
| 27B | Q8_0 | 4 | on | 66.51 | 91.93 | 90.05 | 108.23 |
| 27B | Q8_0 | 4 | off | 66.33 | 91.62 | 88.74 | 129.18 |
| 35B-A3B | BF16 | 3 | on | 221.27 | 334.72 | 363.70 | 611.15 |
| 35B-A3B | BF16 | 3 | off | 218.14 | 371.33 | 418.45 | 699.73 |
| 35B-A3B | BF16 | 4 | on | 229.17 | 369.51 | 374.28 | 730.36 |
| 35B-A3B | BF16 | 4 | off | 296.85 | 412.18 | 415.09 | 588.31 |
| 35B-A3B | Q4_K_M | 3 | on | 244.11 | 376.60 | 373.87 | 544.58 |
| 35B-A3B | Q4_K_M | 3 | off | 324.67 | 486.95 | 519.36 | 788.37 |
| 35B-A3B | Q4_K_M | 4 | on | 360.73 | 536.89 | 548.60 | 775.21 |
| 35B-A3B | Q4_K_M | 4 | off | 360.24 | 544.74 | 529.59 | 796.03 |
| 35B-A3B | Q6_K | 3 | on | 320.98 | 497.35 | 516.24 | 767.57 |
| 35B-A3B | Q6_K | 3 | off | 329.71 | 506.04 | 484.99 | 771.33 |
| 35B-A3B | Q6_K | 4 | on | 309.07 | 492.77 | 487.80 | 754.00 |
| 35B-A3B | Q6_K | 4 | off | 296.41 | 450.27 | 487.05 | 773.86 |
| 35B-A3B | Q8_0 | 3 | on | 356.43 | 532.59 | 524.90 | 791.97 |
| 35B-A3B | Q8_0 | 3 | off | 341.73 | 522.18 | 519.50 | 795.14 |
| 35B-A3B | Q8_0 | 4 | on | 312.56 | 515.28 | 524.75 | 778.88 |
| 35B-A3B | Q8_0 | 4 | off | 325.82 | 495.32 | 497.09 | 797.99 |

## Data-quality note

The machine entered sleep during the first 27B BF16, Turbo 3, symmetric-on
run. This produced a 0.35 tok/s numeric-analysis measurement and an abnormally
slow code-generation warm-up. The tables use medians of five measured runs, so
the numeric outlier does not dominate its reported median; warm-ups are excluded
from all reported medians. The raw measurement is retained for provenance.
