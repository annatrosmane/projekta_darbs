from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from main import generate_full_outfit, get_weather
import json
import os

app = Flask(__name__)
CORS(app)

with open("product_links.json", encoding="utf-8") as f:
    product_links = json.load(f)



@app.route("/generate", methods=["POST"])
def generate():

    data = request.json

    gender = data["gender"]
    style = data["style"]
    lat = data["lat"]
    lon = data["lon"]

    try:
        result = generate_full_outfit(gender, style, lat, lon)

        if result['image_path'] is None:
            return jsonify({
                "image": None,
                "items": result["items"],
                "city": result["city"],
                "temperature": result["temperature"],
                "weather": result["weather"],
                "warning": "Outfit photo failed to generate. Please retry."
            }), 200

        return jsonify({
            "image": f"http://127.0.0.1:5000/image/{result['image_path']}",
            "items": result["items"],
            "city": result["city"],
            "temperature": result["temperature"],
            "weather": result["weather"]
        })
    
    except Exception as e:
        return jsonify({
            "error": f"Server error: {str(e)}"
        }), 500


@app.route("/image/<path:filename>")
def get_image(filename):

    return send_file(filename, mimetype='image/png')


@app.route("/get-link/<path:filename>")
def get_link(filename):

    filename = os.path.basename(filename)

    with open("product_links.json", encoding="utf-8") as f:
        product_links = json.load(f)

    link = product_links.get(filename, "#")

    response = jsonify({"link": link})

    response.headers["Cache-Control"] = "no-store"

    return response


@app.after_request
def add_header(response):

    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/weather", methods=["POST"])
def weather_route():

    data = request.json

    lat = data["lat"]
    lon = data["lon"]

    try:
        weather = get_weather(lat, lon)

        return jsonify({
            "city": weather["city"],
            "temperature": weather["temp"],
            "weather": weather["description"]
        })
    except Exception as e:
        return jsonify({
            "error": f"Failed to get weather: {str(e)}"
        }), 500


app.run(debug=True)
