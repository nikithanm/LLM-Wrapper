import google.generativeai as genai
from huggingface_hub import InferenceClient
import os
from typing import Dict, Any
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ModelManager:
    def __init__(self):
        # Initialize Gemini
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment variables")
        genai.configure(api_key=api_key)
        self.gemini = genai.GenerativeModel('gemini-pro')
        
        # Initialize HuggingFace
        hf_token = os.getenv('HUGGINGFACE_API_KEY')
        if not hf_token:
            raise ValueError("HUGGINGFACE_API_KEY not found in environment variables")
        self.hf_client = InferenceClient(token=hf_token)
        self.hf_model_id = "mistralai/Mistral-7B-Instruct-v0.2"

    async def get_interactive_response(self, user_prompt: str) -> Dict[str, Any]:
        try:
            # Step 1: Get initial response from Gemini
            initial_prompt = f"Given the user question: '{user_prompt}', provide a detailed answer."
            gemini_response = await self.get_gemini_response(initial_prompt)
            
            if not gemini_response["success"]:
                return await self.get_hf_response(user_prompt)
            
            # Step 2: Have HuggingFace analyze and enhance Gemini's response
            enhancement_prompt = f"""
            User Question: {user_prompt}
            Initial Response: {gemini_response['response']}
            
            Analyze the above response and enhance it by:
            1. Adding any missing important information
            2. Correcting any inaccuracies
            3. Making it more comprehensive if needed
            
            Provide a single, unified response that incorporates both the original insights and your enhancements.
            """
            
            hf_analysis = await self.get_hf_response(enhancement_prompt)
            
            if not hf_analysis["success"]:
                return gemini_response
            
            # Step 3: Have Gemini create the final unified response
            final_prompt = f"""
            Based on:
            1. Original user question: {user_prompt}
            2. Initial analysis: {gemini_response['response']}
            3. Enhanced analysis: {hf_analysis['response']}
            
            Create a single, coherent response that combines the best insights from both analyses.
            The response should be clear, concise, and directly address the user's question.
            Do not mention that this is a combined response or reference either AI model.
            """
            
            final_response = await self.get_gemini_response(final_prompt)
            
            return {
                "response": final_response["response"] if final_response["success"] else gemini_response["response"],
                "success": True,
                "models_used": ["gemini", "huggingface"]
            }
            
        except Exception as e:
            logger.error(f"Error in interactive response generation: {str(e)}")
            return {
                "response": "An error occurred while generating the response.",
                "success": False,
                "models_used": []
            }

    async def get_gemini_response(self, prompt: str) -> Dict[str, Any]:
        try:
            response = self.gemini.generate_content(prompt)
            return {
                "response": response.text,
                "success": True
            }
        except Exception as e:
            logger.error(f"Gemini API error: {str(e)}")
            return {
                "response": str(e),
                "success": False
            }

    async def get_hf_response(self, prompt: str) -> Dict[str, Any]:
        try:
            formatted_prompt = f"""<s>[INST] {prompt} [/INST]"""
            response = self.hf_client.text_generation(
                formatted_prompt,
                model=self.hf_model_id,
                max_new_tokens=512,
                temperature=0.7,
                repetition_penalty=1.1,
                do_sample=True,
                return_full_text=False
            )
            return {
                "response": response,
                "success": True
            }
        except Exception as e:
            logger.error(f"HuggingFace API error: {str(e)}")
            return {
                "response": str(e),
                "success": False
            }