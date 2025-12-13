from typing import Optional
import os
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain_community.llms import HuggingFacePipeline
import torch

# Model id - gemma-2b is recommended for POC
MODEL_ID = os.environ.get("GEMMA_MODEL_ID", "google/gemma-2b-it")
# Optional: allow overriding max new tokens via env
MAX_NEW_TOKENS = int(os.environ.get("GEMMA_MAX_NEW_TOKENS", "256"))

def create_gemma_llm(model_id: Optional[str] = None, max_new_tokens: int = MAX_NEW_TOKENS):
    """
    Returns a LangChain-compatible LLM using Gemma 2B loaded locally via transformers.
    This runs on CPU by default (device_map='cpu') and is suitable for GitHub Actions runners.
    """
    model_id = model_id or MODEL_ID

    # Load tokenizer and model (CPU-friendly)
    tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True,token=os.environ.get("HF_TOKEN"))

    # Use low_cpu_mem_usage to reduce peak memory where supported
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        device_map="cpu",
        torch_dtype=torch.float32,
        low_cpu_mem_usage=True,
        trust_remote_code=True,  # Gemma models often require trust_remote_code,
        token=os.environ.get("HF_TOKEN")
    )

    # Build HF pipeline
    gen_pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device= -1,  # CPU
        max_new_tokens=max_new_tokens,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )

    # Wrap for LangChain
    llm = HuggingFacePipeline(pipeline=gen_pipe)
    return llm


# Example usage:
# from app_core.llm.gemma_llm import create_gemma_llm
# llm = create_gemma_llm()
# out = llm("Summarize: ...")
# print(out)
