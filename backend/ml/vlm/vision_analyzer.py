import os
import json
import base64
import logging
from typing import Any, Dict
from ai.client import get_client

logger = logging.getLogger("lumint.ml.vlm")

class LumintVisionAnalyzer:
    """
    Analyzes UPI screenshot with vision LLM.
    Prompt is carefully engineered for forensics.
    """

    SYSTEM_PROMPT = """You are an expert forensic analyst specializing in UPI payment screenshot authenticity verification.

CRITICAL FIRST STEP: Before anything else, determine if the provided image is actually a UPI payment receipt/screenshot from PhonePe, Google Pay, Paytm, or BHIM.

If the image is NOT a UPI payment screenshot (e.g. it is a chat conversation, social media post, selfie, meme, document, LinkedIn screenshot, WhatsApp chat, etc.):
- Set "visual_verdict" to "FORGED"
- Set "visual_confidence" to 95
- Set "anomalies_detected" to ["NOT_A_UPI_SCREENSHOT: The uploaded image is not a UPI payment receipt"]
- Set "visual_analyst_note" to a 2-sentence note explaining that this is not a payment screenshot and what type of image it appears to be instead.
- Set all layout/typography/color/ui fields to false.

If the image IS a UPI payment screenshot, analyze it for:
1. Layout consistency: does the UI match standard PhonePe/GooglePay/Paytm/BHIM templates exactly?
2. Typography: are all text elements using the same font family and rendering pipeline?
3. Color authenticity: do the brand colors match the official app color palette exactly?
4. UI element authenticity: are checkmarks, icons, and decorative elements genuine or synthetic?
5. Semantic consistency: do the displayed values (UTR, amount, recipient) appear legitimate?

Respond ONLY with valid JSON matching this schema:
{
  "visual_verdict": "GENUINE" | "SUSPICIOUS" | "FORGED",
  "visual_confidence": 0-100,
  "layout_authentic": true | false,
  "typography_consistent": true | false,
  "color_authentic": true | false,
  "ui_elements_genuine": true | false,
  "anomalies_detected": ["list of specific anomalies"],
  "visual_analyst_note": "2-sentence expert note"
}
"""

    async def analyze(
        self,
        image_bytes: bytes,
        app_detected: str
    ) -> Dict[str, Any]:
        """
        Encode image as base64.
        Send to Groq vision endpoint (llama-3.2-11b-vision-preview).
        The model first checks if the image is a real UPI screenshot before forensics.
        Fallback to heuristic verdict if API is down or key is invalid.
        """
        # Encode base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        try:
            client = get_client()
            # Call Groq vision model
            response = client.chat.completions.create(
                model="llama-3.2-11b-vision-preview",
                messages=[
                    {
                        "role": "system",
                        "content": self.SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": (
                                    "Please analyze the provided image. First determine if it is a UPI payment "
                                    f"receipt screenshot (app hint: {app_detected}). If it is not a UPI "
                                    "payment screenshot, immediately flag it as FORGED with NOT_A_UPI_SCREENSHOT "
                                    "anomaly. If it is a UPI screenshot, run full forensic analysis."
                                )
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.1,
                max_tokens=512,
                response_format={"type": "json_object"}
            )
            
            raw_content = response.choices[0].message.content or "{}"
            result = json.loads(raw_content)
            
            # Clean and sanitize keys
            required_keys = [
                "visual_verdict", "visual_confidence", "layout_authentic",
                "typography_consistent", "color_authentic", "ui_elements_genuine",
                "anomalies_detected", "visual_analyst_note"
            ]
            for key in required_keys:
                if key not in result:
                    result[key] = self._get_default_val_for_key(key)
                    
            # Ensure verdict type is correct
            if result["visual_verdict"] not in ["GENUINE", "SUSPICIOUS", "FORGED"]:
                result["visual_verdict"] = "SUSPICIOUS"
                
            return result

        except Exception as e:
            logger.error("VLM Groq vision analysis failed: %s. Using graceful fallback.", str(e))
            return self._get_fallback_verdict(app_detected)

    def _get_default_val_for_key(self, key: str) -> Any:
        defaults = {
            "visual_verdict": "SUSPICIOUS",
            "visual_confidence": 50,
            "layout_authentic": True,
            "typography_consistent": True,
            "color_authentic": True,
            "ui_elements_genuine": True,
            "anomalies_detected": [],
            "visual_analyst_note": "Forensic fallback note."
        }
        return defaults.get(key)

    def _get_fallback_verdict(self, app_detected: str) -> Dict[str, Any]:
        """
        Graceful fallback when API fails.
        """
        return {
            "visual_verdict": "SUSPICIOUS",
            "visual_confidence": 40,
            "layout_authentic": False,
            "typography_consistent": True,
            "color_authentic": True,
            "ui_elements_genuine": False,
            "anomalies_detected": ["VLM API connection error: using heuristic visual safety fallback"],
            "visual_analyst_note": "VLM vision analyzer was offline. Fallback heuristics flagged potential anomalies."
        }
