"""
Enhanced AI Service for Laso Healthcare
Supports multiple AI providers including OpenAI, OpenRouter, and Hugging Face
"""

import json
import time
import uuid
import requests
from typing import Dict, Any, Optional, List
from django.conf import settings
from django.utils import timezone
from django.contrib.auth import get_user_model

from .models_ai_config import AIConfiguration, AIConversation, AIPromptTemplate
from .ai_features import SymptomAnalyzer, DrugInteractionChecker, TreatmentRecommendationEngine

User = get_user_model()


class AIService:
    """
    Enhanced AI Service with multiple provider support
    """
    
    def __init__(self, config: Optional[AIConfiguration] = None):
        self.config = config or AIConfiguration.get_default_config()
        self.symptom_analyzer = SymptomAnalyzer()
        self.drug_checker = DrugInteractionChecker()
        self.treatment_engine = TreatmentRecommendationEngine()
    
    def chat(self, user: User, message: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Main chat interface that routes to appropriate AI provider
        """
        if not self.config:
            return {
                'success': False,
                'error': 'No AI configuration available. Please configure AI settings in admin panel.',
                'response': 'I apologize, but AI services are not currently configured. Please contact your administrator.'
            }
        
        if not session_id:
            session_id = str(uuid.uuid4())
        
        start_time = time.time()
        
        try:
            # Enhance message with medical context if available
            enhanced_message = self._enhance_message_with_context(user, message)
            
            # Route to appropriate provider
            if self.config.provider == 'openai':
                response = self._chat_openai(enhanced_message)
            elif self.config.provider == 'openrouter':
                response = self._chat_openrouter(enhanced_message)
            elif self.config.provider == 'ollama':
                response = self._chat_ollama(enhanced_message)
            elif self.config.provider == 'huggingface':
                response = self._chat_huggingface(enhanced_message)
            elif self.config.provider == 'anthropic':
                response = self._chat_anthropic(enhanced_message)
            else:
                response = self._fallback_response(message)
            
            response_time = time.time() - start_time
            
            # Save conversation
            conversation = AIConversation.objects.create(
                user=user,
                session_id=session_id,
                message=message,
                response=response.get('content', ''),
                ai_config=self.config,
                tokens_used=response.get('tokens_used', 0),
                response_time=response_time
            )
            
            return {
                'success': True,
                'response': response.get('content', ''),
                'session_id': session_id,
                'conversation_id': conversation.id,
                'tokens_used': response.get('tokens_used', 0),
                'response_time': response_time
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'response': 'I apologize, but I encountered an error processing your request. Please try again or contact support if the issue persists.'
            }
    
    def _enhance_message_with_context(self, user: User, message: str) -> str:
        """
        Enhance user message with medical context
        """
        context_parts = [
            f"Patient: {user.get_full_name()}",
            f"User Type: {user.get_user_type_display()}",
        ]
        
        # Add age if available
        if hasattr(user, 'date_of_birth') and user.date_of_birth:
            from datetime import date
            age = date.today().year - user.date_of_birth.year
            context_parts.append(f"Age: {age}")
        
        # Add medical context for patients
        if user.is_patient():
            try:
                from treatments.models_medical_history import MedicalHistory
                
                # Get recent medical history
                recent_conditions = MedicalHistory.objects.filter(
                    patient=user,
                    is_active=True
                ).values_list('condition_name', flat=True)[:5]
                
                if recent_conditions:
                    context_parts.append(f"Medical History: {', '.join(recent_conditions)}")
            except:
                pass
        
        context = " | ".join(context_parts)
        
        enhanced_message = f"""
Medical Context: {context}

Patient Query: {message}

Please provide a helpful, accurate, and medically appropriate response. Always recommend consulting with healthcare professionals for serious medical concerns.
"""
        
        return enhanced_message
    
    def _chat_openai(self, message: str) -> Dict[str, Any]:
        """
        Chat with OpenAI API
        """
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': self.config.model_name or 'gpt-3.5-turbo',
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful medical AI assistant. Provide accurate, helpful information while always recommending professional medical consultation for serious concerns.'
                },
                {
                    'role': 'user',
                    'content': message
                }
            ],
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature
        }
        
        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'content': result['choices'][0]['message']['content'],
                'tokens_used': result.get('usage', {}).get('total_tokens', 0)
            }
        else:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")
    
    def _chat_openrouter(self, message: str) -> Dict[str, Any]:
        """
        Chat with OpenRouter API
        """
        # Use environment variables if available
        api_key = getattr(settings, 'OPENROUTER_API_KEY', None) or self.config.api_key
        model_name = getattr(settings, 'OPENROUTER_MODEL', None) or self.config.model_name or 'deepseek/deepseek-chat-v3.1:free'
        api_url = getattr(settings, 'OPENROUTER_API_URL', None) or self.config.api_url or 'https://openrouter.ai/api/v1/chat/completions'
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://laso-healthcare.com',
            'X-Title': 'Laso Healthcare AI Assistant'
        }
        
        data = {
            'model': model_name,
            'messages': [
                {
                    'role': 'system',
                    'content': 'You are a helpful medical AI assistant for Laso Healthcare. Provide accurate, helpful information while always recommending professional medical consultation for serious concerns.'
                },
                {
                    'role': 'user',
                    'content': message
                }
            ],
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'content': result['choices'][0]['message']['content'],
                'tokens_used': result.get('usage', {}).get('total_tokens', 0)
            }
        else:
            raise Exception(f"OpenRouter API error: {response.status_code} - {response.text}")
    
    def _chat_ollama(self, message: str) -> Dict[str, Any]:
        """
        Chat with Ollama API (local)
        """
        # Use environment variables if available
        api_url = getattr(settings, 'OLLAMA_API_URL', None) or self.config.api_url or 'http://localhost:11434/api/generate'
        model_name = getattr(settings, 'OLLAMA_MODEL', None) or self.config.model_name or 'llama2'
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Ollama uses a different format
        data = {
            'model': model_name,
            'prompt': f"You are a helpful medical AI assistant for Laso Healthcare. Provide accurate, helpful information while always recommending professional medical consultation for serious concerns.\n\nUser: {message}\n\nAssistant:",
            'stream': False,
            'options': {
                'temperature': self.config.temperature,
                'num_predict': self.config.max_tokens
            }
        }
        
        try:
            response = requests.post(
                api_url,
                headers=headers,
                json=data,
                timeout=60  # Ollama can be slower
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    'content': result.get('response', ''),
                    'tokens_used': len(result.get('response', '').split())  # Approximate token count
                }
            else:
                raise Exception(f"Ollama API error: {response.status_code} - {response.text}")
        except requests.exceptions.ConnectionError:
            # Fallback if Ollama is not running
            return {
                'content': "Ollama service is not available. Please ensure Ollama is running locally or use a different AI provider.",
                'tokens_used': 0
            }
    
    def _chat_huggingface(self, message: str) -> Dict[str, Any]:
        """
        Chat with Hugging Face API
        """
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }
        
        # Use a medical-focused model if available
        model = self.config.model_name or 'microsoft/DialoGPT-medium'
        api_url = self.config.api_url or f'https://api-inference.huggingface.co/models/{model}'
        
        data = {
            'inputs': message,
            'parameters': {
                'max_length': self.config.max_tokens,
                'temperature': self.config.temperature,
                'return_full_text': False
            }
        }
        
        response = requests.post(
            api_url,
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                content = result[0].get('generated_text', message)
            else:
                content = "I'm processing your request. Please try again in a moment."
            
            return {
                'content': content,
                'tokens_used': len(content.split())  # Approximate token count
            }
        else:
            raise Exception(f"Hugging Face API error: {response.status_code} - {response.text}")
    
    def _chat_anthropic(self, message: str) -> Dict[str, Any]:
        """
        Chat with Anthropic Claude API
        """
        headers = {
            'x-api-key': self.config.api_key,
            'Content-Type': 'application/json',
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.config.model_name or 'claude-3-sonnet-20240229',
            'max_tokens': self.config.max_tokens,
            'temperature': self.config.temperature,
            'messages': [
                {
                    'role': 'user',
                    'content': message
                }
            ]
        }
        
        response = requests.post(
            'https://api.anthropic.com/v1/messages',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                'content': result['content'][0]['text'],
                'tokens_used': result.get('usage', {}).get('input_tokens', 0) + result.get('usage', {}).get('output_tokens', 0)
            }
        else:
            raise Exception(f"Anthropic API error: {response.status_code} - {response.text}")
    
    def _fallback_response(self, message: str) -> Dict[str, Any]:
        """
        Fallback response using local AI features
        """
        message_lower = message.lower()
        
        # Symptom analysis
        if any(word in message_lower for word in ['symptom', 'feel', 'pain', 'hurt', 'sick']):
            analysis = self.symptom_analyzer.analyze_symptoms(message)
            if analysis['possible_diseases']:
                response = f"Based on your symptoms, here are some possibilities:\n\n"
                for disease in analysis['possible_diseases'][:3]:
                    response += f"• {disease['disease'].title()} (confidence: {disease['confidence']})\n"
                response += f"\nRecommendations:\n"
                for rec in analysis['recommendations']:
                    response += f"• {rec}\n"
                response += f"\n⚠️ This is not a medical diagnosis. Please consult with a healthcare professional."
            else:
                response = "I understand you're experiencing symptoms. Please describe them in more detail, and I recommend consulting with a healthcare professional for proper evaluation."
        
        # Drug interaction check
        elif any(word in message_lower for word in ['medication', 'drug', 'medicine', 'pill']):
            response = "For medication-related questions, I recommend:\n\n• Consult with your pharmacist or doctor\n• Check for drug interactions\n• Follow prescribed dosages\n• Report any side effects\n\nIf you're taking multiple medications, please have them reviewed by a healthcare professional."
        
        # General health advice
        else:
            response = f"Thank you for your question about: {message}\n\nI'm here to provide general health information, but for personalized medical advice, please consult with your healthcare provider. They can give you the most accurate guidance based on your specific situation.\n\nIs there anything specific about your health that you'd like general information about?"
        
        return {
            'content': response,
            'tokens_used': len(response.split())
        }
    
    def analyze_symptoms(self, user: User, symptoms: str) -> Dict[str, Any]:
        """
        Dedicated symptom analysis
        """
        analysis = self.symptom_analyzer.analyze_symptoms(symptoms)
        
        # Enhance with AI if available
        if self.config:
            try:
                prompt = f"Analyze these symptoms and provide medical insights: {symptoms}"
                ai_response = self.chat(user, prompt)
                if ai_response['success']:
                    analysis['ai_insights'] = ai_response['response']
            except:
                pass
        
        return analysis
    
    def check_drug_interactions(self, user: User, medications: List[str]) -> Dict[str, Any]:
        """
        Check for drug interactions
        """
        interactions = self.drug_checker.check_prescription_interactions(medications)
        
        # Enhance with AI if available
        if self.config and medications:
            try:
                med_list = ", ".join(medications)
                prompt = f"Check for interactions between these medications: {med_list}"
                ai_response = self.chat(user, prompt)
                if ai_response['success']:
                    return {
                        'interactions': interactions,
                        'ai_analysis': ai_response['response']
                    }
            except:
                pass
        
        return {'interactions': interactions}
    
    def get_conversation_history(self, user: User, session_id: str, limit: int = 20) -> List[Dict]:
        """
        Get conversation history for a session
        """
        conversations = AIConversation.objects.filter(
            user=user,
            session_id=session_id
        ).order_by('created_at')[:limit]
        
        return [
            {
                'id': conv.id,
                'message': conv.message,
                'response': conv.response,
                'timestamp': conv.created_at.isoformat(),
                'tokens_used': conv.tokens_used
            }
            for conv in conversations
        ]


# Singleton instance - lazy initialization
_ai_service_instance = None

def get_ai_service():
    """Get or create AI service instance"""
    global _ai_service_instance
    if _ai_service_instance is None:
        _ai_service_instance = AIService()
    return _ai_service_instance