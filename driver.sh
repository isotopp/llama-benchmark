#! /usr/bin/env bash

for model in models/qwen3.6-27b/qwen3.6-27b-bf16.gguf models/qwen3.6-27b/qwen3.6-27b-q4_k_m.gguf models/qwen3.6-27b/qwen3.6-27b-q6_k.gguf models/qwen3.6-27b/qwen3.6-27b-q8_0.gguf models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-bf16.gguf models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q4_k_m.gguf models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q6_k.gguf models/qwen3.6-35b-a3b/qwen3.6-35b-a3b-q8_0.gguf
do
  for turbo in 3 4
  do
    for symmetric in on off
    do
	    uv run llama-benchmark  --model ./${model} --turbo ${turbo} --symmetric ${symmetric}
	  done
	done
done
