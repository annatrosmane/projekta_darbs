import os
import json
import re
import random
from google import genai


from y2k_closet import Y2K_DB as Y2K_DB
from acubi_closet import ACUBI_DB as ACUBI_DB
from classic_closet import CLASSIC_DB as CLASSIC_DB

from korean_streetwear_closet import KOREAN_STREETWEAR_DB as KOREAN_DB
from old_money_closet import OLD_MONEY_DB as OLD_MONEY_DB
from grunge_closet import GRUNGE_DB as GRUNGE_DB

FASHION_DB = {
    "y2k": Y2K_DB,
    "acubi": ACUBI_DB,
    "classic": CLASSIC_DB,
    "korean streetwear": KOREAN_DB,
    "old money": OLD_MONEY_DB,
    "grunge": GRUNGE_DB
}
MODEL_NAME = "gemini-2.5-flash"


def tester(outfit, genders_styles, weather):
    client = genai.Client(api_key=os.environ.get(""))

    prompt = f"""
    You are a strict fashion critic.

    You will evaluate 10 outfits.

    INPUT:

    Outfits:
    {outfit}

    People:
    {genders_styles}

    Weather:
    {weather}

    Each outfit corresponds to the same index:
    - outfit[0] → person[0] + weather[0]
    - outfit[1] → person[1] + weather[1]
    ...

    TASK:

    Evaluate EACH outfit separately.

    CRITERIA:

    - style accuracy
    - weather suitability
    - outfit coherence
    - realism

    Each score: 1–10

    Return JSON ONLY as a LIST:

    [
    {{
        "style_score": int,
        "weather_score": int,
        "coherence_score": int,
        "realism_score": int,
        "total": int,
        "comment": "short explanation"
    }}
    ]
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    match = re.search(r"\[.*?\]", response.text, re.S)
    return json.loads(match.group())




def get_outfit_from_ai(weather, genders_styles, fashion_db):
    client = genai.Client(api_key=os.environ.get(""))

    prompt = f"""
    You are a professional fashion stylist.

    Your task is to create 10 REALISTIC and COHESIVE outfits.

    You are given 10 weather conditions and 10 persons.
    Each outfit must correspond to the matching index.

    INPUT:

    Weather list:
    {weather}

    People list:
    {genders_styles}

    Clothing database:
    {fashion_db}

    IMPORTANT RULE:

    - Clothing names MUST be copied EXACTLY from the database
    - Do NOT modify names
    - Do NOT shorten names

    TASK:

    Generate 10 outfits:
    - Outfit 0 → for weather[0] and person[0]
    - Outfit 1 → for weather[1] and person[1]
    - ...
    - Outfit 9 → for weather[9] and person[9]

    STYLING RULES:

    1. Each outfit must match its style
    2. Items must not be random
    3. All pieces must visually work together
    4. Outfit must look intentional and realistic

    WEATHER RULES:

    - Clothes must match temperature
    - Consider feels_like, humidity, wind

    RULES:

    - All items MUST come from the database
    - Maximum 2 layers on top
    - Each outfit should have 5–6 items

    Return JSON ONLY as a LIST:

    [
    {{
        "top": "...",
        "bottom": "...",
        "shoes": "...",
        "outerwear": "...",
        "bag": "...",
        "sunglasses": "...",
        "socks": "...",
        "jewelry": "..."
    }}
    ]
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    match = re.search(r"\[.*?\]", response.text, re.S)
    return json.loads(match.group())


def weather_generator():
    client = genai.Client(api_key=os.environ.get(""))

    prompt = """
    Your task is to generate 10 plausible current weather conditions for your 10 preffered city

    Example:
    weather = {
        "city": "Riga",
        "temp": 30,
        "feels": 30,
        "humidity": 50,
        "wind": 0,
        "description": "sunny"
    }

    IMPORTANT:

    - The weather MUST be realistic
    - Do NOT generate extreme or impossible values
    - Values must be believable in real life

    
    GENERATE:

    - temperature (in Celsius)
    - feels_like (close to temperature, but can differ slightly)
    - humidity (0–100)
    - wind_speed (m/s)
    - description (short realistic phrase, e.g. "clear sky", "light rain", "cloudy")

    
    Please create 10 different conditions with 10 different cities from all over the world

    Return JSON ONLY:

Return JSON ONLY as a LIST:

[
  {
    "city": "string",
    "temp": number,
    "feels": number,
    "humidity": number,
    "wind": number,
    "description": "string"
  },
  {
    "city": "string",
    "temp": number,
    "feels": number,
    "humidity": number,
    "wind": number,
    "description": "string"
  },
  ...
]

    
    
    """


    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    match = re.search(r"\[.*?\]", response.text, re.S)
    return json.loads(match.group())



if __name__ == "__main__":
    weather = weather_generator()
    print(json.dumps(weather, indent=2, ensure_ascii=False))
    print()

    genders = ["woman", "man"]
    styles_man = ["old money", "grunge", "korean streetwear"]
    styles_woman = ["y2k", "acubi", "classic"]

    genders_styles = []

    for i in range(10):
        gender = genders[random.randint(0,1)]
        if (gender == "woman"):
            style = styles_woman[random.randint(0,2)]
        else:
            style = styles_man[random.randint(0,2)]

        gender_style = {
           "gender": gender,
           "style": style 
        }

        genders_styles += [gender_style]

    print(json.dumps(genders_styles, indent=2, ensure_ascii=False))  
    print()

    outfit = get_outfit_from_ai(weather, genders_styles, FASHION_DB)
    print(json.dumps(outfit, indent=2, ensure_ascii=False))

    print()

    score = tester(outfit, genders_styles, weather)
    print(json.dumps(score, indent=2, ensure_ascii=False))
