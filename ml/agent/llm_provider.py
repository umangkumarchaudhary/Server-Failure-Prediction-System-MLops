"""
LLM Provider - Interface with LLMs for AI Copilot.

Supports:
- OpenAI GPT-4
- Anthropic Claude
- Local models via Ollama
"""
import os
from datetime import datetime
from typing import Dict, List, Optional, Any
from abc import ABC, abstractmethod
import logging
import json

logger = logging.getLogger(__name__)

# Import conditionally
try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import httpx
    HAS_HTTPX = True
except ImportError:
    HAS_HTTPX = False


class LLMProvider(ABC):
    """Abstract base for LLM providers."""
    
    @abstractmethod
    async def generate_incident(
        self,
        event: Any,
        similar_incidents: List[Any],
    ) -> Dict[str, Any]:
        """Generate incident description."""
        pass
    
    @abstractmethod
    async def generate_recommendation(
        self,
        event: Any,
    ) -> str:
        """Generate maintenance recommendation."""
        pass
    
    @abstractmethod
    async def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Free-form chat for copilot interface."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider."""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4-turbo-preview",
    ):
        if not HAS_OPENAI:
            raise ImportError("openai package not installed")
        
        self.client = openai.AsyncOpenAI(
            api_key=api_key or os.getenv("OPENAI_API_KEY")
        )
        self.model = model
    
    async def generate_incident(
        self,
        event: Any,
        similar_incidents: List[Any],
    ) -> Dict[str, Any]:
        """Generate incident description using GPT."""
        # Build context
        similar_context = ""
        if similar_incidents:
            similar_context = "\n\nSimilar past incidents:\n"
            for inc in similar_incidents[:3]:
                similar_context += f"- {inc.title}: {inc.root_cause_analysis}\n"
        
        prompt = f"""You are an AI maintenance copilot analyzing an equipment anomaly.

Event Details:
- Asset ID: {event.asset_id}
- Anomaly Score: {event.data.get('anomaly_score', 0):.2f}
- Risk Level: {event.data.get('risk_level', 'unknown')}
- Timestamp: {event.timestamp.isoformat()}

Top Contributing Factors:
{json.dumps(event.data.get('explanation', {}).get('top_features', [])[:5], indent=2)}
{similar_context}

Generate a professional incident report with:
1. A concise title (one line)
2. A detailed description (2-3 paragraphs)
3. Root cause analysis (1-2 paragraphs)
4. 4-5 suggested corrective actions

Return as JSON with keys: title, description, root_cause, actions (array)"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert industrial maintenance AI assistant."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7,
        )
        
        return json.loads(response.choices[0].message.content)
    
    async def generate_recommendation(
        self,
        event: Any,
    ) -> str:
        """Generate maintenance recommendation."""
        rul = event.data.get("rul_hours", 0)
        
        prompt = f"""You are an AI maintenance copilot. An asset has a predicted remaining useful life of {rul:.0f} hours.

Generate a concise maintenance recommendation (2-3 sentences) that:
1. States the urgency level
2. Recommends when to schedule maintenance
3. Suggests preparation steps

Be professional and actionable."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert industrial maintenance AI assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=200,
        )
        
        return response.choices[0].message.content
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Free-form chat."""
        system_prompt = """You are PredictrAI's maintenance copilot, an AI assistant for predictive maintenance operations.

You help engineers by:
- Explaining anomaly detections and their causes
- Providing maintenance recommendations
- Answering questions about asset health
- Suggesting preventive actions

Be concise, technical, and actionable. Use bullet points when appropriate."""

        if context:
            system_prompt += f"\n\nCurrent context:\n{json.dumps(context, indent=2)}"
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
        )
        
        return response.choices[0].message.content


class OllamaProvider(LLMProvider):
    """Local Ollama provider for self-hosted models."""
    
    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        model: str = "llama3",
    ):
        if not HAS_HTTPX:
            raise ImportError("httpx package not installed")
        
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def _generate(self, prompt: str, system: Optional[str] = None) -> str:
        """Generate text using Ollama."""
        response = await self.client.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model,
                "prompt": prompt,
                "system": system or "You are an expert industrial maintenance AI.",
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json()["response"]
    
    async def generate_incident(
        self,
        event: Any,
        similar_incidents: List[Any],
    ) -> Dict[str, Any]:
        """Generate incident using local model."""
        prompt = f"""Analyze this equipment anomaly and generate an incident report.

Event: Asset {event.asset_id}, Score {event.data.get('anomaly_score', 0):.2f}, Risk: {event.data.get('risk_level')}

Generate JSON with: title, description, root_cause, actions (array of strings)"""

        response = await self._generate(prompt)
        
        try:
            # Try to parse JSON from response
            return json.loads(response)
        except json.JSONDecodeError:
            # Fallback
            return {
                "title": f"Anomaly on asset {event.asset_id}",
                "description": response,
                "root_cause": "Unable to determine from local model",
                "actions": ["Investigate manually", "Check sensor data"],
            }
    
    async def generate_recommendation(
        self,
        event: Any,
    ) -> str:
        """Generate recommendation using local model."""
        rul = event.data.get("rul_hours", 0)
        prompt = f"Asset has {rul:.0f} hours remaining useful life. Give a brief maintenance recommendation."
        return await self._generate(prompt)
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> str:
        """Chat using local model."""
        system = "You are a maintenance AI copilot. Be helpful and technical."
        if context:
            system += f" Context: {json.dumps(context)}"
        return await self._generate(message, system)


class MockLLMProvider(LLMProvider):
    """Mock provider for testing without LLM."""
    
    async def generate_incident(
        self,
        event: Any,
        similar_incidents: List[Any],
    ) -> Dict[str, Any]:
        return {
            "title": f"Anomaly Alert: {event.asset_id}",
            "description": f"An anomaly with score {event.data.get('anomaly_score', 0):.2f} was detected.",
            "root_cause": "Contributing factors identified through SHAP analysis.",
            "actions": [
                "Review recent operational parameters",
                "Check sensor calibration",
                "Compare with baseline measurements",
                "Schedule physical inspection",
            ],
        }
    
    async def generate_recommendation(
        self,
        event: Any,
    ) -> str:
        rul = event.data.get("rul_hours", 0)
        return f"Schedule maintenance within {rul * 0.5:.0f} hours to prevent unplanned downtime."
    
    async def chat(
        self,
        message: str,
        context: Optional[Dict] = None,
    ) -> str:
        return f"I understand you're asking about: {message[:100]}. How can I help further?"


def create_llm_provider(
    provider_type: str = "mock",
    **kwargs,
) -> LLMProvider:
    """Factory function to create LLM provider."""
    if provider_type == "openai":
        return OpenAIProvider(**kwargs)
    elif provider_type == "ollama":
        return OllamaProvider(**kwargs)
    else:
        return MockLLMProvider()
