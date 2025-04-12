import requests
import asyncio
import aiohttp
import json
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="config.env")

### Este script envía un texto a la API de Google Gemini y recibe un análisis literario del mismo.

''' 
LISTA DE MODELOS GRATIS:

# GOOGLE
gemini-2.0-flash
gemma-3-27b-it
gemini-2.5-pro-exp-03-25

# QWEN
qwen/qwen2.5-vl-72b-instruct:free

# DeepSeek
deepseek/deepseek-r1:free         EL MEJOR
deepseek/deepseek-chat-v3-0324:free  SEGUNDO MEJOR pero a veces la información es imprecisa
deepseek-r1-zero     Es bueno pero a veces la información es imprecisa

# Quasar Alpha (1 M de tokens)
openrouter/quasar-alpha 

'''

class instructions:
    def __init__(self):
        self.countinstructions = 0
        self.storeinstructions = {}
        self.instruction = "" # para devolver la misma instrucción dada
    
    def new(self, instruction):
        self.countinstructions += 1
        self.storeinstructions[self.countinstructions] = instruction # almacenar instrucción
        self.instruction = instruction # para devolver la misma instrucción dada
        return instruction
    
    def __str__(self): 
        return self.instruction
        

class flowtask:
    def __init__(self, agentname, aimodel):
        self.agentname = agentname # #nombre del agente especializado para un conjunto de tareas específico
        self.aimodel = aimodel
        self.apikey = os.environ.get("GOOGLE_API_KEY") #Google Api
        if not self.apikey:
            raise ValueError("GOOGLE_API_KEY no está definida. Asegúrate de que la variable de entorno esté configurada correctamente.")
        self.urltorequest = f"https://generativelanguage.googleapis.com/v1beta/models/{self.aimodel}:generateContent"
        self.countinstructions = 0
        self.storeinstructions = {}

    async def add_instruction(self, instruction):
        self.countinstructions += 1 
        self.storeinstructions[self.countinstructions] = instruction 

        return await self.request(instruction)
        
    async def request(self, input_text):
        input_data = {
            "contents": [{
                "parts": [{
                    "text": input_text
                }]
            }]
        }

        if not self.apikey:
            raise ValueError("GOOGLE_API_KEY no está definida")

        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": self.apikey
        }

        # Google Models
        if self.aimodel == "gemini-2.0-flash" or self.aimodel == "gemma-3-27b-it" or self.aimodel == "gemini-2.5-pro-exp-03-25":
            # print("Usando Google Model")
            async with aiohttp.ClientSession() as session:
                async with session.post(self.urltorequest, headers=headers, json=input_data) as response:
                    if response.status == 200:
                        output_data = await response.json()
                        output_text = output_data["candidates"][0]["content"]["parts"][0]["text"]
                        return output_text
                    else:
                        print(f"Error: {response.status}")
                        print(await response.text())
                        return await response.text(), response.status
                    
        # Qwen Model
        elif(self.aimodel == "qwen1"):
           # print("Usando Qwen Model")
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            qwen_model = os.environ.get("QWEN_MODEL")

            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY no está definida")
            if not qwen_model:
                raise ValueError("QWEN_MODEL no está definida")

            openrouter_headers = {
                "Authorization": f"Bearer {openrouter_api_key}",
                "Content-Type": "application/json"
            }
            openrouter_data = json.dumps({
                "model": qwen_model,
                "messages": [
                {
                    "role": "user",
                    "content": input_text
                }
                ],
            })

            async with aiohttp.ClientSession() as session:
                async with session.post(openrouter_url, headers=openrouter_headers, data=openrouter_data) as response:
                    if response.status == 200:
                        output_data = await response.json()
                        output_text = output_data["choices"][0]["message"]["content"]
                        return output_text
                    else:
                        print(f"Error: {response.status}")
                        print(await response.text())
                        return await response.text(), response.status
                    
        # DeepSeek R1 Model
        elif(self.aimodel == "deepseek-r1"):
            # print("Usando DeepSeek R1 Model")
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            deepseek_r1_model = os.environ.get("DEEPSEEK_R1_MODEL")

            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY no está definida")
            if not deepseek_r1_model:
                raise ValueError("DEEPSEEK_R1_MODEL no está definida")
            
            openrouter_headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }
            openrouter_data = json.dumps({
                    "model": deepseek_r1_model,
                    "messages": [
                    {
                        "role": "user",
                        "content": input_text
                    }
                    ],
                })
            async with aiohttp.ClientSession() as session:
                async with session.post(openrouter_url, headers=openrouter_headers, data=openrouter_data) as response:
                    if response.status == 200:
                        output_data = await response.json()
                        output_text = output_data["choices"][0]["message"]["content"]
                        return output_text
                    else:
                        print(f"Error: {response.status}")
                        print(await response.text())
                        return await response.text(), response.status
                    
        # DeepSeek R1 Zero Model (Aprendizaje autónomo)
        elif(self.aimodel == "deepseek-r1-zero"):
            # print("Usando DeepSeek R1 Zero Model (También pensamiento profundo, pero con aprendizaje autónomo)")
            
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            deepseek_r1_zero_model = os.environ.get("DEEPSEEK_R1_ZERO_MODEL")

            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY no está definida")
            if not deepseek_r1_zero_model:
                raise ValueError("DEEPSEEK_R1_ZERO_MODEL no está definida")
            
            openrouter_headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }
            openrouter_data = json.dumps({
                    "model": deepseek_r1_zero_model,
                    "messages": [
                    {
                        "role": "user",
                        "content": input_text
                    }
                    ],
                })
            async with aiohttp.ClientSession() as session:
                async with session.post(openrouter_url, headers=openrouter_headers, data=openrouter_data) as response:
                    if response.status == 200:
                        output_data = await response.json()
                        output_text = output_data["choices"][0]["message"]["content"]
                        return output_text
                    else:
                        print(f"Error: {response.status}")
                        print(await response.text())
                        return await response.text(), response.status
                    
        # DeepSeek Chat V3 0324 Model (Sin pensamiento profundo)
        elif(self.aimodel == "deepseek-cv3"):
            # print("Usando Chat V3 0324 Model (Sin pensamiento profundo)")
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            deepseek_cv3_model = os.environ.get("DEEPSEEK_CV3_MODEL")

            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY no está definida")
            if not deepseek_cv3_model:
                raise ValueError("DEEPSEEK_CV3_MODEL no está definida")
            
            openrouter_headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }
            openrouter_data = json.dumps({
                    "model": deepseek_cv3_model,
                    "messages": [
                    {
                        "role": "user",
                        "content": input_text
                    }
                    ],
                })
            async with aiohttp.ClientSession() as session:
                async with session.post(openrouter_url, headers=openrouter_headers, data=openrouter_data) as response:
                    if response.status == 200:
                        output_data = await response.json()
                        output_text = output_data["choices"][0]["message"]["content"]
                        return output_text
                    else:
                        print(f"Error: {response.status}")
                        print(await response.text())
                        return await response.text(), response.status
                    
        #  Quasar Alpha (1 M de tokens) Model
        elif(self.aimodel == "quasar-alpha"):
            # print("Usando Quasar Alpha Model")
            openrouter_url = "https://openrouter.ai/api/v1/chat/completions"
            openrouter_api_key = os.environ.get("OPENROUTER_API_KEY")
            quasarmodel = os.environ.get("QUASAR_ALPHA_MODEL")

            if not openrouter_api_key:
                raise ValueError("OPENROUTER_API_KEY no está definida")
            if not quasarmodel:
                raise ValueError("QUASAR_ALPHA_MODEL no está definido")
            
            openrouter_headers = {
                    "Authorization": f"Bearer {openrouter_api_key}",
                    "Content-Type": "application/json"
                }
            openrouter_data = json.dumps({
                    "model": quasarmodel,
                    "messages": [
                    {
                        "role": "user",
                        "content": input_text
                    }
                    ],
                })
            async with aiohttp.ClientSession() as session:
                async with session.post(openrouter_url, headers=openrouter_headers, data=openrouter_data) as response:
                    if response.status == 200:
                        output_data = await response.json()
                        print(output_data)
                        output_text = output_data["choices"][0]["message"]["content"]
                        return output_text
                    else:
                        print(f"Error: {response.status}")
                        print(await response.text())
                        return await response.text(), response.status
