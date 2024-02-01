import hashlib
import os
import requests
import time
from flask import Flask, request, jsonify

app = Flask(__name__)

# Marvel API base URL
API_URL = 'https://gateway.marvel.com:443/v1/public/'

# Endpoint for searching characters and comics
@app.route('/searchComics', methods=['GET'])
def search_comics():
    # Get request parameters
    search_term = request.args.get('search_term', '')
    filter_type = request.args.get('filter_type', '')

    # Validate that a search term is provided
    if not search_term:
        return jsonify({'error': 'You must provide a search term'}), 400

    # Get Marvel API keys
    public_key, ts, hash = get_api_auth()

    # Perform search based on filter type (character or comic)
    if filter_type.lower() == 'character':
        results = search_character(public_key, ts, hash, search_term)
    elif filter_type.lower() == 'comic':
        results = search_comic(public_key, ts, hash, search_term)
    else:
        return jsonify({'error': 'Invalid filter type'}), 400

    # Return results in JSON format
    return jsonify({'results': results})

# Function to search for characters in the Marvel API
def search_character(public_key, ts, hash, name):
    response = requests.get(
        f'{API_URL}characters?nameStartsWith={name}&ts={ts}&apikey={public_key}&hash={hash}')

    # Handle Marvel API response
    if response.status_code != 200:
        return []

    # Extract relevant data from the response
    characters = response.json().get('data', {}).get('results', [])

    # Format the results according to the desired structure
    return [
        {"id": character['id'],
         "name": character['name'],
         "image": character['thumbnail']['path']+'.jpg',
         "appearances": character['comics']['available']} for character in characters
    ]

# Function to search for comics in the Marvel API
def search_comic(public_key, ts, hash, title):
    response = requests.get(
        f'{API_URL}comics?titleStartsWith={title}&ts={ts}&apikey={public_key}&hash={hash}')

    # Handle Marvel API response
    if response.status_code != 200:
        return []

    # Extract relevant data from the response
    comics = response.json().get('data', {}).get('results', [])

    # Format the results according to the desired structure
    return [
        {"id": comic['id'],
         "title": comic['title'],
         "image": comic['thumbnail']['path']+'.jpg',
         "onsaleDate": comic['dates'][0]['date']} for comic in comics
    ]

# Function to get Marvel API keys
def get_api_auth():
    # Get the public key
    public_key = os.getenv('MARVEL_PUBLIC_KEY')

    # Validate that the public key is configured
    if not public_key:
        raise Exception("Public key not found.")

    # Get the current timestamp
    ts = str(time.time())

    # Get the private key
    private_key = os.getenv('MARVEL_PRIVATE_KEY')

    # Validate that the private key is configured
    if not private_key:
        raise Exception("Private key not found.")

    # Calculate MD5 hash from the concatenation of timestamp, private key, and public key
    str_encoded = (ts + private_key + public_key).encode()
    api_key = hashlib.md5(str_encoded).hexdigest()

    # Return the keys
    return public_key, ts, api_key

# Run the Flask application
if __name__ == '__main__':
    app.run(debug=True)
