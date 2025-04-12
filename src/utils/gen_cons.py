from .agent import flowtask

# si el consumo de los usuarios se acerca a 0 significa menos consumo, si se acerca a uno es más consumo


async def gen_data(): # Generate data for energy management
    agente = flowtask("json-energy", "gemini-2.0-flash")
    response = await agente.add_instruction("""
        You are a professional JSON data generator, specializing in creating random datasets related to energy consumption. Using the format provided below, generate a JSON structure that records sectors (only A-B-C) and houses (1-10) along with their respective energy consumption levels. Values close to 0 indicate low consumption, while values close to 1 indicate high consumption. Follow this exact format modyfing values as you please:
                                
        {{
            "Sector-A": {{
                "house-1": 0.05,
                "house-2": 0.15,
                "house-3": 0.04,
                "house-4": 0.5,
                "house-5": 0.45,
                "house-6": 0.9,
                "house-7": 0.65,
                "house-8": 0.1,
                "house-9": 0.85,
                "house-10": 0.09
            }},
            "Sector-B": {{
                "house-1": 0.10,
                "house-2": 0.89,
                "house-3": 0.10,
                "house-4": 1,
                "house-5": 0.71,
                "house-6": 0.02,
            }},
            "Sector-C": {{
                "house-1": 0.01,
                "house-2": 0.13,
                "house-3": 0.31,
                "house-4": 0.50,
                "house-5": 0.11,
                "house-6": 0.51,
                "house-7": 0.96,
                "house-8": 0.72,
            }}
        }}
                                
        You will only reply with the JSON, nothing else before or after it. Make sure to not use markdown.            
        """)
    
    return response
