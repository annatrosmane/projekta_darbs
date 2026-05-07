import requests
import os
import mimetypes
import time
import json
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from concurrent.futures import ThreadPoolExecutor


from y2k_closet import Y2K_DB as Y2K_DB
from acubi_closet import ACUBI_DB as ACUBI_DB
from classic_closet import CLASSIC_DB as CLASSIC_DB

from korean_streetwear_closet import KOREAN_STREETWEAR_DB as KOREAN_DB
from old_money_closet import OLD_MONEY_DB as OLD_MONEY_DB
from grunge_closet import GRUNGE_DB as GRUNGE_DB

MODEL_NAME = "gemini-2.5-flash-image"

STYLE_DATABASE = {
    "y2k": Y2K_DB,
    "acubi": ACUBI_DB,
    "classic": CLASSIC_DB,
    "korean streetwear": KOREAN_DB,
    "old money": OLD_MONEY_DB,
    "grunge": GRUNGE_DB
}

GEMINI_API_KEY = ""  # Šeit ir jūsu Gemini API ключ


def get_weather(lat, lon):
    token = ""  # Šeit ir jūsu token laikapstākļu iegūšanai

    data_weather = requests.get(
        f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={token}&units=metric"
    ).json()

    return {
        "city": data_weather["name"],
        "temp": data_weather["main"]["temp"],
        "feels": data_weather["main"]["feels_like"],
        "humidity": data_weather["main"]["humidity"],
        "wind": data_weather["wind"]["speed"],
        "description": data_weather["weather"][0]["description"]
    }



def get_outfit_from_ai(weather, gender, style, fashion_db):
    client = genai.Client(api_key=GEMINI_API_KEY)

    prompt = f"""
    You are a professional fashion stylist.

    Your task is to create a REALISTIC and COHESIVE outfit.

    Weather conditions:

    city: {weather["city"]}
    temperature: {weather["temp"]}
    feels_like: {weather["feels"]}
    humidity: {weather["humidity"]}
    wind_speed: {weather["wind"]}
    description: {weather["description"]}

    Person:

    gender: {gender}
    style: {style}

    Clothing database:

    {fashion_db}

    IMPORTANT RULE:

    Clothing names MUST be copied EXACTLY from the database.
    Do NOT modify names.
    Do NOT shorten names.
    Copy the exact text.

    TASK:

    Create ONE complete outfit.
    The outfit MUST look like a real fashion look that someone would actually wear.
    The outfit MUST strictly follow the requested style: {style}

    STYLING RULES:

    1. Items must match the requested style.
    2. Do NOT choose random items.
    3. All pieces must visually work together.
    4. The outfit must look intentional and styled.

    Example for Y2K style:

    - oversized silhouettes
    - baggy jeans
    - cargo pants
    - cropped tops
    - chunky sneakers
    - metallic accessories
    - sporty sunglasses
    - beanies
    - mini bags

    WEATHER RULES:

    - Clothes must be comfortable in {weather["temp"]}°C
    - Consider feels_like, humidity and wind

    RULES:

    - All items MUST come from the database
    - Return as many items as needed for a complete outfit
    - Maximum 2 layers on the top
    - A realistic outfit usually contains 5-6 items
    - Return JSON only

    Example output:

    {{
    "top": "cropped baby tee",
    "bottom": "baggy jeans",
    "shoes": "chunky sneakers",
    "outerwear": "oversized bomber jacket",
    "hat": "y2k beanie hat",
    "bag": "mini shoulder bag",
    "sunglasses": "sport sunglasses",
    "socks": "white crew socks",
    "jewelry": "silver chain necklace"
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    import re
    match = re.search(r"\{.*\}", response.text, re.S)
    return json.loads(match.group())



def get_products(search_text):
    params = (
        ('token', ''),  # Šeit ir jūsu token AliExpress produktu atlasīšanai
        ('scraper', 'aliexpress-serp'),
        ('format', 'json'),
        ('country', 'US'),
        ('url', f'https://www.aliexpress.com/wholesale?SearchText={search_text}')
    )
    response = requests.get('https://api.crawlbase.com/', params=params)
    data = response.json()
    return data["body"]["products"]


def clear_items_folder():
    folder = "items"
    if os.path.exists(folder):
        for filename in os.listdir(folder):
            file_path = os.path.join(folder, filename)
            try:
                os.remove(file_path)
            except Exception as e:
                print("Error deleting", file_path, e)



def download_image(url, save_path, label=None):
    headers = {"User-Agent": "Mozilla/5.0"}
    for _ in range(3):
        try:
            img = requests.get(url, headers=headers, timeout=20)
            if img.status_code == 200:
                with open(save_path, "wb") as f:
                    f.write(img.content)
                
                im = Image.open(save_path).convert("RGB").resize((1024,1024))
                if label:
                    draw = ImageDraw.Draw(im)
                    font = ImageFont.load_default()
                    draw.text((10,10), label, fill=(255,0,0), font=font)
                im.save(save_path)
                return
        except:
            time.sleep(2)


def save_product_links(outfit_links, filename="product_links.json"):
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(outfit_links, f, indent=4, ensure_ascii=False)

    except Exception as e:
        print("Error saving product links:", e)


def build_tryon_prompt(outfit):

    prompt_lines = [
        "Virtual fashion try-on.",
        "Dress the model from the first image using the clothing items from the reference images.\n",
        "Create a realistic fashion outfit.\n",
        "Keep the result clean and natural.\n\n",
        "\nRules:\n",
        "- Keep proportions realistic\n",
        "- White background\n"
        "- Use the following clothing items:\n"
    ]

    if "dress" in outfit:
        prompt_lines.append(f"- use the {outfit['dress']}\n")
        if "shoes" in outfit:
            prompt_lines.append(f"- use the {outfit['shoes']}\n")
    else:
        for key, value in outfit.items():
            if any(x in key.lower() for x in ["top", "bottom", "shoes"]):
                prompt_lines.append(f"- use the {value}\n")



    return "".join(prompt_lines)



def load_image_part(path):
    with open(path, "rb") as f:
        data = f.read()
    mime_type, _ = mimetypes.guess_type(path)
    return types.Part(inline_data=types.Blob(data=data, mime_type=mime_type))




def generate_outfit(image_paths, outfit):
    client = genai.Client(api_key=GEMINI_API_KEY)
    contents = [load_image_part(p) for p in image_paths]
    prompt = build_tryon_prompt(outfit)
    contents.append(types.Part.from_text(text=prompt))
    config = types.GenerateContentConfig(response_modalities=["IMAGE"], temperature=0.1)

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=contents, config=config)
    except Exception as e:
        print("Error calling Gemini API:", e)
        return None

    if (not response.candidates 
        or not response.candidates[0].content 
        or not response.candidates[0].content.parts):
        print("Gemini API returned empty response")
        return None

    os.makedirs("output", exist_ok=True)
    for part in response.candidates[0].content.parts:
        if part.inline_data:
            filename = f"output/outfit_{int(time.time())}.png"
            with open(filename, "wb") as f:
                f.write(part.inline_data.data)
            print("Saved:", filename)
            return filename

    return None  




def generate_full_outfit(gender, style, lat, lon):

    clear_items_folder()

    weather = get_weather(lat, lon)

    FASHION_DB = STYLE_DATABASE.get(style.lower())
    outfit = get_outfit_from_ai(weather, gender, style, FASHION_DB)
    os.makedirs("items", exist_ok=True)

    if gender.lower() == "man":
        model_image = "man.jpg"
    else:
        model_image = "woman.png"

    generation_items = ["top", "bottom", "dress", "shoes"]
    image_paths_for_generation = [model_image]

    def process_item(category, item):
        try:
            products = get_products(item)
            if not products:
                return None

            img_url = products[0]["image"]
            product_url = products[0]["url"]
            path = f"items/{category}.jpg"
            download_image(img_url, path)

            return {
            "category": category,
            "path": path,
            "product_url": product_url,
            "item_name": item
            }

        except Exception as e:
            print("Error in", category, e)
            return None

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(
            lambda x: process_item(x[0], x[1]),
            [(c, i) for c, i in outfit.items()]  
        ))

    item_images = []
    product_links = {}
    image_paths_for_generation = [model_image]

    for result in results:
        if result:
            path = result["path"]
            category = result["category"]
            product_url = result["product_url"]

            item_images.append({
                "category": category,
                "path": path,
                "url": product_url
            })

            filename = f"{category}.jpg"
            product_links[filename] = product_url

            if category in generation_items:
                image_paths_for_generation.append(path)

    save_product_links(product_links)
    image_path = generate_outfit(image_paths_for_generation, outfit)

    if image_path is None:
        print("Warning: outfit image was not generated")
        return {
            "outfit": outfit,
            "image_path": None,
            "items": item_images,
            "city": weather["city"],
            "temperature": weather["temp"],
            "weather": weather["description"]
        }
    else:
        return {
            "outfit": outfit,
            "image_path": image_path,
            "items": item_images,
            "city": weather["city"],
            "temperature": weather["temp"],
            "weather": weather["description"]
        }
