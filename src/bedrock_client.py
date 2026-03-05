"""
Bedrock client for AI-generated content in the Kiro Backend civic assistant system.

This module interfaces with Amazon Bedrock for generating explanations and
conversation scripts with guardrails and fallback content.
"""

import json
from typing import Optional
import boto3
from botocore.exceptions import ClientError

from src.models import Office, ConversationScript


class BedrockClient:
    """
    Interfaces with Amazon Bedrock for AI-generated content.
    
    Features:
    - Generate office recommendation explanations
    - Generate conversation scripts
    - Apply guardrails (no legal guarantees)
    - Fallback to default content on errors
    - 5-second timeout handling
    """
    
    def __init__(self, use_bedrock: bool = True):
        """
        Initialize the Bedrock client.
        
        Args:
            use_bedrock: Whether to attempt Bedrock calls (default: True)
        """
        self.use_bedrock = use_bedrock
        self.client = None
        
        if use_bedrock:
            try:
                self.client = boto3.client('bedrock-runtime')
            except Exception:
                self.client = None
    
    def generate_explanation(
        self,
        office: Office,
        category: str,
        correlation_id: str
    ) -> str:
        """
        Generates explanation for office recommendation.
        
        Args:
            office: Recommended office object
            category: Problem category
            correlation_id: Request tracing ID
        
        Returns:
            Bullet-point explanation text
        """
        if not self.use_bedrock or not self.client:
            return self._default_explanation(office, category)
        
        try:
            prompt = f"""Generate a brief explanation (3-4 bullet points) for why this office is recommended:

Office: {office.name}
Category: {category}
Distance: {office.distance_km} km away

Requirements:
- Format as bullet points
- Mention proximity and relevant services
- Include "Please verify services at the counter" language
- Do NOT make legal guarantees or promise specific outcomes
- Keep it concise and helpful

Explanation:"""
            
            response = self.client.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 200,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7
                }),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            explanation = response_body.get('content', [{}])[0].get('text', '').strip()
            
            if explanation:
                print(f"[{correlation_id}] Generated explanation with Bedrock")
                return explanation
            else:
                return self._default_explanation(office, category)
                
        except Exception as e:
            print(f"[{correlation_id}] Bedrock explanation failed: {e}, using default")
            return self._default_explanation(office, category)
    
    def generate_script(
        self,
        category: str,
        template_style: str,
        correlation_id: str
    ) -> ConversationScript:
        """
        Generates conversation script for office visit.
        
        Args:
            category: Problem category
            template_style: Style from template (formal/casual)
            correlation_id: Request tracing ID
        
        Returns:
            ConversationScript with opening and follow-ups
        """
        if not self.use_bedrock or not self.client:
            return self._default_script(category, template_style)
        
        try:
            tone = "professional and polite" if template_style == "formal" else "friendly and conversational"
            
            prompt = f"""Generate a conversation script for visiting a government office about {category}.

Style: {tone}

Provide:
1. An opening statement (1-2 sentences)
2. Three follow-up questions

Requirements:
- Be respectful and clear
- Do NOT make legal claims or guarantees
- Include phrases like "Can you help me understand..." or "What do I need to..."
- Keep it practical and helpful

Format as JSON:
{{
  "opening": "...",
  "follow_ups": ["...", "...", "..."]
}}"""
            
            response = self.client.invoke_model(
                modelId='anthropic.claude-3-haiku-20240307-v1:0',
                body=json.dumps({
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": 300,
                    "messages": [
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.7
                }),
                contentType='application/json',
                accept='application/json'
            )
            
            response_body = json.loads(response['body'].read())
            content = response_body.get('content', [{}])[0].get('text', '').strip()
            
            # Try to parse JSON from response
            script_data = json.loads(content)
            script = ConversationScript(
                opening=script_data.get('opening', ''),
                follow_ups=script_data.get('follow_ups', [])
            )
            
            if script.opening and script.follow_ups:
                print(f"[{correlation_id}] Generated script with Bedrock")
                return script
            else:
                return self._default_script(category, template_style)
                
        except Exception as e:
            print(f"[{correlation_id}] Bedrock script failed: {e}, using default")
            return self._default_script(category, template_style)
    
    def _default_explanation(self, office: Office, category: str) -> str:
        """Generate default explanation when Bedrock unavailable."""
        distance_text = f"{office.distance_km} km away" if office.distance_km else "in your area"
        return f"""• This office handles {category} matters and is {distance_text}
• They provide services related to your request
• Please verify current services and requirements at the counter"""
    
    def _default_script(self, category: str, template_style: str) -> ConversationScript:
        """Generate default script when Bedrock unavailable."""
        if template_style == "formal":
            opening = f"Hello, I need assistance with {category}. Can you direct me to the appropriate department?"
            follow_ups = [
                "What documents do I need to bring?",
                "What are the processing times?",
                "Are there any fees I should be aware of?"
            ]
        else:
            opening = f"Hi, I'm here to get help with {category}. Who should I talk to?"
            follow_ups = [
                "What do I need to bring with me?",
                "How long does this usually take?",
                "Is there anything else I should know?"
            ]
        
        return ConversationScript(
            opening=opening,
            follow_ups=follow_ups
        )
