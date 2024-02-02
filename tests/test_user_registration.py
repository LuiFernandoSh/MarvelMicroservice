import os
import pytest
import requests


# Asumiendo que estás usando un archivo .env para las configuraciones
from dotenv import load_dotenv

# Cargar configuraciones desde el archivo .env
load_dotenv()

# Establecer el MONGO_URI para pruebas
os.environ['MONGO_URI'] = 'mongodb+srv://LuisF:2904@cluster0.ncqa5wy.mongodb.net/MC?retryWrites=true&w=majority'

# Asegurar que Flask se ejecute en modo de prueba
os.environ['FLASK_ENV'] = 'testing'

# Importar la aplicación Flask después de cargar la configuración
from app import app, mongo

# Función para realizar la prueba de registro de usuario
def test_register_user():
    # Datos de usuario para la prueba
    user_data = {
        "name": "luis",
        "email": "luisfe.sh1@hotmail.com",
        "password": "2904"
    }

    # Realizar una solicitud POST para registrar al usuario
    response = requests.post('http://127.0.0.1:5000/user_api/users/register', json=user_data)

    # Verificar si la respuesta es exitosa (código de estado 201)
    assert response.status_code == 201

    # Verificar si la respuesta contiene el mensaje esperado
    assert response.json()['message'] == 'Usuario registrado exitosamente'

    # Verificar si el usuario se ha registrado en la base de datos
    registered_user = mongo.db.users.find_one({'name': user_data['name']})
    assert registered_user is not None

    # Limpiar la base de datos después de la prueba
    mongo.db.users.delete_one({'name': user_data['name']})

# Si estás ejecutando las pruebas manualmente, puedes agregar este bloque
if __name__ == "__main__":
    pytest.main()
