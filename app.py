# Importamos las librerías necesarias
import hashlib
import os
import urllib.parse
import time
import requests
from flask import Flask, request, jsonify, Blueprint
from flask_pymongo import PyMongo
from flask_bcrypt import Bcrypt
from flask_jwt_extended import JWTManager, jwt_required, get_jwt_identity, create_access_token  # Corregido a create_access_token
from dotenv import load_dotenv
import secrets
from collections.abc import Mapping  # Importado desde collections.abc

# Creamos la aplicación Flask
app = Flask(__name__)

# Cargamos las variables de entorno desde el archivo .env
load_dotenv()

# Configuraciones de la aplicación
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY') or secrets.token_hex(24)
app.config['MONGO_URI'] = os.getenv('MONGO_URI')

# Creamos las instancias de las extensiones de Flask
mongo = PyMongo(app)
bcrypt = Bcrypt(app)
jwt = JWTManager(app)

# Configuración de la API de Marvel
API_URL = 'https://gateway.marvel.com:443/v1/public/'

# Funciones para la API de Marvel

# Función para buscar personajes
def search_character(name):
    public_key, ts, hash_value = get_api_auth()

    response = requests.get(
        f'{API_URL}characters?nameStartsWith={urllib.parse.quote(name)}&ts={ts}&apikey={public_key}&hash={hash_value}')

    return handle_response(response)

# Función para buscar cómics
def search_comic(title):
    public_key, ts, hash_value = get_api_auth()

    response = requests.get(
        f'{API_URL}comics?titleStartsWith={urllib.parse.quote(title)}&ts={ts}&apikey={public_key}&hash={hash_value}')

    return handle_response(response)

# Función para manejar la respuesta de la API de Marvel
def handle_response(response):
    if response.status_code != 200:
        return jsonify({'error': 'Error al consultar la API de Marvel'}), 500

    results = response.json().get('data', {}).get('results', [])

    formatted_results = [
        {
            "id": result['id'],
            "name" if 'name' in result else "title": result['name'] if 'name' in result else result['title'],
            "image": result['thumbnail']['path']+'.jpg',
            "appearances" if 'comics' in result else "onsaleDate": result['comics']['available'] if 'comics' in result else result['dates'][0]['date']
        } for result in results
    ]

    return jsonify({'results': formatted_results})

# Función para obtener las claves de la API de Marvel
def get_api_auth():
    public_key = os.getenv('MARVEL_PUBLIC_KEY')
    ts = str(time.time())
    private_key = os.getenv('MARVEL_PRIVATE_KEY')
    str_encoded = (ts + private_key + public_key).encode()
    hash_value = hashlib.md5(str_encoded).hexdigest()
    return public_key, ts, hash_value

# Blueprint para la API de Marvel
marvel_api_blueprint = Blueprint('marvel_api', __name__)

# Ruta para la búsqueda de cómics y personajes
@marvel_api_blueprint.route('/searchComics', methods=['GET'])
def search_comics():
    """
    Esta ruta permite buscar cómics y personajes en la API de Marvel.

    Parámetros:
        search_term: Término de búsqueda para cómics y personajes.

    Retorna:
        Resultados de la búsqueda en formato JSON.
    """
    # Obtener el término de búsqueda de los parámetros de la solicitud
    search_term = request.args.get('search_term')

    # Verificar si se proporciona un término de búsqueda
    if not search_term:
        return jsonify({'error': 'Se requiere un término de búsqueda'}), 400

    # Llamar a la función correspondiente según el tipo de búsqueda
    if search_term.isdigit():
        # Si el término de búsqueda es un número, buscar cómics por título
        return search_comic(search_term)
    else:
        # Si el término de búsqueda no es un número, buscar personajes por nombre
        return search_character(search_term)

# Blueprint para la API de usuarios
user_api_blueprint = Blueprint('user_api', __name__)

# Ruta para registrar usuarios
@user_api_blueprint.route('/users/register', methods=['POST'])
def register_user():
    """
    Esta ruta permite registrar un nuevo usuario.

    Parámetros:
        name: El nombre del usuario.
        email: El correo electrónico del usuario.
        password: La contraseña del usuario.

    Retorno:
        Un diccionario con un mensaje de éxito o error.
    """
    data = request.get_json()

    name = data.get('name')
    email = data.get('email')
    password = data.get('password')

    if not name or not email or not password:
        return jsonify({'error': 'Por favor, proporciona todos los datos'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')

    # Utiliza create_access_token para generar el token JWT
    token = create_access_token(identity={'name': name, 'email': email})

    mongo.db.users.insert_one({
        'name': name,
        'email': email,
        'password': hashed_password,
        'token': token
    })

    return jsonify({'message': 'Usuario registrado exitosamente', 'token': token}), 201

# Ruta para iniciar sesión
@user_api_blueprint.route('/users/login', methods=['POST'])
def login_user():
    """
    Esta ruta permite iniciar sesión a un usuario.

    Parámetros:
        name: El nombre del usuario.
        password: La contraseña del usuario.

    Retorno:
        Un diccionario con un mensaje de éxito o error y el token de acceso.
    """
    data = request.get_json()

    name = data.get('name')
    password = data.get('password')

    if not name or not password:
        return jsonify({'error': 'Por favor, proporciona todos los datos'}), 400

    user = mongo.db.users.find_one({'name': name})

    if user and bcrypt.check_password_hash(user['password'], password):
        token = create_access_token(identity={'name': name, 'email': user['email']})
        return jsonify({'message': 'Inicio de sesión exitoso', 'token': token}), 200

    return jsonify({'error': 'Credenciales incorrectas'}), 401

# Registrar los blueprints
app.register_blueprint(marvel_api_blueprint, url_prefix='/marvel_api')
app.register_blueprint(user_api_blueprint, url_prefix='/user_api')

if __name__ == '__main__':
    app.run(debug=True)

