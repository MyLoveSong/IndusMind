#!/usr/bin/env python3
"""
Local QWEN3-8B Model Server with OpenAI-compatible API
Serves the fine-tuned QWEN3-8B model with LoRA adapters
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
from peft import PeftModel
import uvicorn

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Model configuration
BASE_MODEL_PATH = "/home/xzy/QWEN3-8B/QWEN3-8B/models/Qwen/Qwen3-8B"
LORA_ADAPTER_PATH = "/home/xzy/QWEN3-8B/QWEN3-8B/finetune_output/lora_full"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL_LOADED = False
MODEL = None
TOKENIZER = None

class ChatMessage(BaseModel):
    role: str = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")

class ChatCompletionRequest(BaseModel):
    model: str = Field(default="Qwen/Qwen3-8B", description="Model name")
    messages: List[ChatMessage] = Field(..., description="List of messages")
    max_tokens: int = Field(default=1800, description="Maximum tokens to generate")
    temperature: float = Field(default=0.35, description="Sampling temperature")
    top_p: float = Field(default=0.9, description="Top-p sampling")
    stream: bool = Field(default=False, description="Whether to stream the response")

class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Dict[str, Any]]
    usage: Dict[str, int]

def load_model():
    """Load the fine-tuned model with LoRA adapters"""
    global MODEL, TOKENIZER, MODEL_LOADED

    if MODEL_LOADED:
        return

    try:
        logger.info("Loading tokenizer...")
        # Check if path exists
        if not os.path.exists(BASE_MODEL_PATH):
            raise FileNotFoundError(f"Model path does not exist: {BASE_MODEL_PATH}")

        TOKENIZER = AutoTokenizer.from_pretrained(
            BASE_MODEL_PATH,
            trust_remote_code=True,
            padding_side="left"
        )

        # Add pad token if not exists
        if TOKENIZER.pad_token is None:
            TOKENIZER.pad_token = TOKENIZER.eos_token

        logger.info("Loading base model...")
        # Use 4-bit quantization for memory efficiency
        quantization_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_quant_type="nf4"
        )

        # Check if model files exist
        config_path = os.path.join(BASE_MODEL_PATH, "config.json")
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Model config not found: {config_path}")

        model = AutoModelForCausalLM.from_pretrained(
            BASE_MODEL_PATH,
            quantization_config=quantization_config,
            device_map="auto",
            trust_remote_code=True,
            torch_dtype=torch.float16
        )

        logger.info("Loading LoRA adapter...")
        MODEL = PeftModel.from_pretrained(
            model,
            LORA_ADAPTER_PATH,
            device_map="auto"
        )

        MODEL.eval()
        MODEL_LOADED = True
        logger.info("Model loaded successfully!")

    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

def generate_response(messages: List[ChatMessage], max_tokens: int = 1800, temperature: float = 0.35, top_p: float = 0.9) -> str:
    """Generate response from the model"""
    if not MODEL_LOADED:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # Prepare the conversation
        conversation = []
        system_message = None

        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            elif msg.role == "user":
                if system_message:
                    conversation.append({"role": "system", "content": system_message})
                    system_message = None
                conversation.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                conversation.append({"role": "assistant", "content": msg.content})

        # Apply chat template
        if hasattr(TOKENIZER, 'apply_chat_template'):
            prompt = TOKENIZER.apply_chat_template(
                conversation,
                tokenize=False,
                add_generation_prompt=True
            )
        else:
            # Fallback for older tokenizers
            prompt = ""
            for msg in conversation:
                if msg["role"] == "system":
                    prompt += f"System: {msg['content']}\n\n"
                elif msg["role"] == "user":
                    prompt += f"User: {msg['content']}\n\nAssistant: "
                elif msg["role"] == "assistant":
                    prompt += f"Assistant: {msg['content']}\n\n"

        logger.info(f"Generated prompt: {prompt[:200]}...")

        # Tokenize input
        inputs = TOKENIZER(prompt, return_tensors="pt", padding=True, truncation=True)
        inputs = {k: v.to(DEVICE) for k, v in inputs.items()}

        # Generate response
        with torch.no_grad():
            outputs = MODEL.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
                pad_token_id=TOKENIZER.pad_token_id,
                eos_token_id=TOKENIZER.eos_token_id,
                repetition_penalty=1.1
            )

        # Decode response
        response_text = TOKENIZER.decode(outputs[0][inputs['input_ids'].shape[1]:], skip_special_tokens=True)
        response_text = response_text.strip()

        logger.info(f"Generated response: {response_text[:200]}...")
        return response_text

    except Exception as e:
        logger.error(f"Error generating response: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info("Starting model server...")
    load_model()
    yield
    # Shutdown
    logger.info("Shutting down model server...")

# Create FastAPI app
app = FastAPI(
    title="QWEN3-8B Local Model Server",
    description="OpenAI-compatible API for fine-tuned QWEN3-8B model",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "running",
        "model": "Qwen/Qwen3-8B (Fine-tuned with LoRA)",
        "device": DEVICE,
        "model_loaded": MODEL_LOADED
    }

@app.get("/health")
async def health():
    """Detailed health check"""
    return {
        "status": "healthy" if MODEL_LOADED else "loading",
        "timestamp": int(time.time()),
        "model_info": {
            "base_model": BASE_MODEL_PATH,
            "lora_adapter": LORA_ADAPTER_PATH,
            "device": DEVICE,
            "cuda_available": torch.cuda.is_available(),
            "loaded": MODEL_LOADED
        }
    }

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """OpenAI-compatible chat completions endpoint"""
    try:
        # Check authorization if configured
        auth_token = os.getenv("LOCAL_QWEN_API_KEY") or os.getenv("LOCAL_QWEN_TOKEN")
        if auth_token:
            auth_header = request.headers.get("authorization", "")
            if not auth_header or auth_token not in auth_header:
                raise HTTPException(status_code=401, detail="Unauthorized - invalid token")

        # Generate response
        response_text = generate_response(
            messages=request.messages,
            max_tokens=request.max_tokens,
            temperature=request.temperature,
            top_p=request.top_p
        )

        # Create OpenAI-compatible response
        response = ChatCompletionResponse(
            id=f"chatcmpl-{int(time.time())}",
            created=int(time.time()),
            model=request.model,
            choices=[{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_text
                },
                "finish_reason": "stop"
            }],
            usage={
                "prompt_tokens": 0,  # Could be calculated if needed
                "completion_tokens": len(response_text.split()),
                "total_tokens": len(response_text.split())
            }
        )

        return response

    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    port = int(os.getenv("MODEL_SERVER_PORT", "8001"))
    host = os.getenv("MODEL_SERVER_HOST", "127.0.0.1")

    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(
        "model_server:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )
