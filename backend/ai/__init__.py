"""
Lumint AI Intelligence Layer
============================
Groq LLaMA 3.3 70B versatile client and specialized threat analysts
for forensic documents, phishing URLs, and behavioral fraud campaigns.
"""

from ai.client import ask_groq, get_client
from ai.docshield_ai import DocumentAIResult, analyze_document_ai
from ai.frauddna_ai import CampaignAIResult, analyze_campaign_ai
from ai.phishshield_ai import PhishingAIResult, analyze_phishing_ai

__all__ = [
    "ask_groq",
    "get_client",
    "DocumentAIResult",
    "analyze_document_ai",
    "PhishingAIResult",
    "analyze_phishing_ai",
    "CampaignAIResult",
    "analyze_campaign_ai",
]
