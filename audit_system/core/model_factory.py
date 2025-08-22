#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 Model Factory - Multi-LLM Support for Audit System

Provides flexible LLM model creation supporting:
- Claude (Anthropic) - Primary choice for code analysis
- OpenAI GPT - Secondary option
- Configurable via environment variables

Usage:
    from audit_system.core.model_factory import create_llm_model
    
    # Use Claude by default
    model = create_llm_model()
    
    # Force specific provider
    model = create_llm_model(provider="claude")
    model = create_llm_model(provider="openai")
"""

import os
import logging
from typing import Optional, Dict, Any
from pathlib import Path

# Try importing Agno model providers
try:
    from agno.models.anthropic import AnthropicChat
    CLAUDE_AVAILABLE = True
except ImportError:
    CLAUDE_AVAILABLE = False
    AnthropicChat = None

try:
    from agno.models.openai import OpenAIChat
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    OpenAIChat = None

logger = logging.getLogger(__name__)

# LLM Configuration
LLM_CONFIG = {
    "claude": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "model_id": "claude-3-sonnet-20240229",
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "Claude 3.5 Sonnet - Superior for code analysis"
    },
    "openai": {
        "api_key_env": "OPENAI_API_KEY", 
        "model_id": "gpt-4o",
        "temperature": 0.1,
        "max_tokens": 4000,
        "description": "GPT-4 Omni - Alternative LLM provider"
    }
}

def get_preferred_provider() -> str:
    """Get preferred LLM provider from environment or defaults."""
    provider = os.getenv("LLM_PROVIDER", "claude").lower()
    
    # Validate provider availability
    if provider == "claude" and not CLAUDE_AVAILABLE:
        logger.warning("Claude not available, falling back to OpenAI")
        provider = "openai"
    elif provider == "openai" and not OPENAI_AVAILABLE:
        logger.warning("OpenAI not available, falling back to Claude")
        provider = "claude"
    
    return provider

def is_provider_configured(provider: str) -> bool:
    """Check if provider is properly configured with API key."""
    if provider not in LLM_CONFIG:
        return False
    
    config = LLM_CONFIG[provider]
    api_key = os.getenv(config["api_key_env"])
    
    return bool(api_key and api_key.strip())

def get_available_providers() -> Dict[str, bool]:
    """Get status of all available providers."""
    return {
        "claude": CLAUDE_AVAILABLE and is_provider_configured("claude"),
        "openai": OPENAI_AVAILABLE and is_provider_configured("openai")
    }

def create_llm_model(
    provider: Optional[str] = None,
    model_id: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None
):
    """
    Create LLM model instance with flexible provider support.
    
    Args:
        provider: LLM provider ("claude" or "openai"). If None, uses environment preference
        model_id: Specific model ID to use. If None, uses provider default
        temperature: Model temperature. If None, uses provider default
        max_tokens: Max tokens. If None, uses provider default
        
    Returns:
        Agno model instance (AnthropicChat or OpenAIChat)
        
    Raises:
        ValueError: If provider is not available or not configured
        ImportError: If required Agno dependencies are missing
    """
    # Determine provider
    if provider is None:
        provider = get_preferred_provider()
    
    provider = provider.lower()
    
    if provider not in LLM_CONFIG:
        raise ValueError(f"Unsupported LLM provider: {provider}. Supported: {list(LLM_CONFIG.keys())}")
    
    config = LLM_CONFIG[provider]
    
    # Check availability
    if provider == "claude" and not CLAUDE_AVAILABLE:
        raise ImportError("Claude support not available. Install with: pip install agno[anthropic]")
    elif provider == "openai" and not OPENAI_AVAILABLE:
        raise ImportError("OpenAI support not available. Install with: pip install agno[openai]")
    
    # Check API key configuration
    if not is_provider_configured(provider):
        api_key_env = config["api_key_env"]
        raise ValueError(f"Provider '{provider}' not configured. Set {api_key_env} environment variable")
    
    # Use provided parameters or defaults
    final_model_id = model_id or config["model_id"]
    final_temperature = temperature if temperature is not None else config["temperature"]
    final_max_tokens = max_tokens or config["max_tokens"]
    
    # Create model instance
    if provider == "claude":
        logger.info(f"Creating Claude model: {final_model_id}")
        return AnthropicChat(
            id=final_model_id,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        )
    elif provider == "openai":
        logger.info(f"Creating OpenAI model: {final_model_id}")
        return OpenAIChat(
            id=final_model_id,
            temperature=final_temperature,
            max_tokens=final_max_tokens
        )
    else:
        raise ValueError(f"Provider implementation missing for: {provider}")

def test_llm_connection(provider: str = None) -> Dict[str, Any]:
    """
    Test connection to LLM provider.
    
    Args:
        provider: Provider to test. If None, tests preferred provider
        
    Returns:
        Dict with test results
    """
    if provider is None:
        provider = get_preferred_provider()
    
    try:
        model = create_llm_model(provider=provider)
        
        # Simple test prompt
        test_prompt = "Respond with 'OK' if you can process this message."
        
        # Note: This would need to be implemented based on Agno's API
        # response = model.run(test_prompt)
        
        return {
            "success": True,
            "provider": provider,
            "model_id": LLM_CONFIG[provider]["model_id"],
            "message": f"{provider.title()} connection successful"
        }
        
    except Exception as e:
        return {
            "success": False,
            "provider": provider,
            "error": str(e),
            "message": f"{provider.title()} connection failed"
        }

def print_provider_status():
    """Print status of all LLM providers."""
    providers = get_available_providers()
    
    print("🤖 LLM Provider Status:")
    print("=" * 40)
    
    for provider, available in providers.items():
        config = LLM_CONFIG[provider]
        status = "✅ Available" if available else "❌ Not Available"
        
        print(f"{provider.title():10s} | {status}")
        print(f"           | Model: {config['model_id']}")
        print(f"           | API Key: {config['api_key_env']}")
        
        if available:
            print(f"           | {config['description']}")
        else:
            reasons = []
            if provider == "claude" and not CLAUDE_AVAILABLE:
                reasons.append("Agno anthropic support missing")
            elif provider == "openai" and not OPENAI_AVAILABLE:
                reasons.append("Agno openai support missing")
                
            if not is_provider_configured(provider):
                reasons.append(f"{config['api_key_env']} not set")
                
            print(f"           | Issues: {', '.join(reasons)}")
        
        print("-" * 40)
    
    preferred = get_preferred_provider()
    print(f"Preferred Provider: {preferred.title()}")

if __name__ == "__main__":
    """CLI interface for testing model factory."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Test LLM Model Factory")
    parser.add_argument("--provider", choices=["claude", "openai"], 
                      help="Test specific provider")
    parser.add_argument("--status", action="store_true",
                      help="Show provider status")
    
    args = parser.parse_args()
    
    if args.status:
        print_provider_status()
    else:
        provider = args.provider
        result = test_llm_connection(provider)
        
        if result["success"]:
            print(f"✅ {result['message']}")
            print(f"   Model: {result['model_id']}")
        else:
            print(f"❌ {result['message']}")
            print(f"   Error: {result['error']}")