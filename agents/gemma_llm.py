from typing import Optional
import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline

MODEL_ID = os.environ.get("GEMMA_MODEL_ID", "google/gemma-2b-it")
MAX_NEW_TOKENS = int(os.environ.get("GEMMA_MAX_NEW_TOKENS", "128"))

def create_gemma_llm(model_id: Optional[str] = None, max_new_tokens: int = MAX_NEW_TOKENS):
    model_id = model_id or MODEL_ID

    tokenizer = AutoTokenizer.from_pretrained(
        model_id,
        use_fast=True,
        token=os.environ.get("HF_TOKEN"),
    )

    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cpu",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        trust_remote_code=True,
        token=os.environ.get("HF_TOKEN"),
    )

    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
    )

    return HuggingFacePipeline(pipeline=pipe)
