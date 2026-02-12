"""Configuration for Venice KB Collector."""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Venice API Doc Sources
GITHUB_REPO = "veniceai/api-docs"
GITHUB_BRANCH = "main"
GITHUB_RAW_BASE = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}"
OPENAPI_URL = f"{GITHUB_RAW_BASE}/swagger.yaml"
LLMS_TXT_URL = f"{GITHUB_RAW_BASE}/llms.txt"
DOCS_JSON_URL = f"{GITHUB_RAW_BASE}/docs.json"
LIVE_DOCS_BASE = "https://docs.venice.ai"
VENICE_API_BASE = "https://api.venice.ai/api/v1"

# GitHub API
GITHUB_API_BASE = "https://api.github.com"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# LLM Configuration
VENICE_API_KEY = os.getenv("VENICE_API_KEY")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.venice.ai/api/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "venice-uncensored")

# Directories
KB_OUTPUT_DIR = Path(os.getenv("KB_OUTPUT_DIR", "./knowledge_base"))
SNAPSHOT_DIR = Path(os.getenv("SNAPSHOT_DIR", "./snapshots"))
CACHE_DIR = Path(os.getenv("CACHE_DIR", "./.cache"))

# Processing Configuration
CHUNK_TARGET_TOKENS = int(os.getenv("CHUNK_TARGET_TOKENS", "2000"))
CHUNK_MAX_TOKENS = int(os.getenv("CHUNK_MAX_TOKENS", "3500"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Pages with JS-rendered dynamic content that need Playwright
DYNAMIC_PAGES = [
    "/models/overview",
    "/models/text",
    "/models/image",
    "/models/audio",
    "/models/video",
    "/models/embeddings",
    "/overview/pricing",
    "/overview/beta-models",
]

# All known MDX content pages (derived from docs.json navigation)
# The build process should also dynamically discover these from docs.json
KNOWN_MDX_PAGES = [
    "overview/about-venice",
    "overview/getting-started",
    "overview/privacy",
    "overview/pricing",
    "overview/deprecations",
    "overview/beta-models",
    "overview/guides/generating-api-key",
    "overview/guides/generating-api-key-agent",
    "overview/guides/ai-agents",
    "overview/guides/postman",
    "overview/guides/integrations",
    "overview/guides/structured-responses",
    "overview/guides/reasoning-models",
    "overview/guides/prompt-caching",
    "overview/guides/claude-code",
    "overview/guides/openclaw-bot",
    "overview/guides/openai-migration",
    "overview/guides/langchain",
    "overview/guides/vercel-ai-sdk",
    "overview/guides/crewai",
    "models/overview",
    "models/text",
    "models/image",
    "models/audio",
    "models/video",
    "models/embeddings",
    "api-reference/api-spec",
    "api-reference/rate-limiting",
    "api-reference/error-codes",
    "api-reference/endpoint/chat/completions",
    "api-reference/endpoint/chat/model_feature_suffix",
    "api-reference/endpoint/image/generate",
    "api-reference/endpoint/image/upscale",
    "api-reference/endpoint/image/edit",
    "api-reference/endpoint/image/multi-edit",
    "api-reference/endpoint/image/background-remove",
    "api-reference/endpoint/image/styles",
    "api-reference/endpoint/image/generations",
    "api-reference/endpoint/audio/speech",
    "api-reference/endpoint/audio/transcriptions",
    "api-reference/endpoint/video/queue",
    "api-reference/endpoint/video/retrieve",
    "api-reference/endpoint/video/quote",
    "api-reference/endpoint/video/complete",
    "api-reference/endpoint/embeddings/generate",
    "api-reference/endpoint/models/list",
    "api-reference/endpoint/models/compatibility_mapping",
    "api-reference/endpoint/models/traits",
    "api-reference/endpoint/characters/list",
    "api-reference/endpoint/api_keys/list",
    "api-reference/endpoint/api_keys/create",
    "api-reference/endpoint/api_keys/delete",
]
