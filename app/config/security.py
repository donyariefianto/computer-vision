import json
import os
import httpx
from cryptography.fernet import Fernet, InvalidToken

from app.helpers.session_manager import session_manager

key_file = 'instances/key.enc'
key_credential = 'instances/credential.enc'
key_token = 'instances/token.enc'
server_url = os.getenv("URL_SERVER")

class Security:    
    # Store access token in encrypted file
    def store_access_token(self,token):
        try:
            key = security.load_or_generate_key()
            fernet = Fernet(key)
            encrypted_token = fernet.encrypt(token.encode())

            with open(key_token, 'wb') as enc_file:
                enc_file.write(encrypted_token)
            print("Token fetched and stored securely.")
        except Exception as e:
            print(f"Error fetching Token: {e}")

    # Load access token from encrypted file
    def load_access_token(self):
        key = security.load_or_generate_key()
        fernet = Fernet(key)
        try:
            with open(key_token, 'rb') as token_file:
                encrypted_token = token_file.read()
            decrypted_token = fernet.decrypt(encrypted_token)
            return decrypted_token.decode()
        except (FileNotFoundError, InvalidToken):
            print("No access token found. Please login through the web app.")
            return None
    
    # Generate or load encryption key
    def load_or_generate_key(self):
        if os.path.exists(key_file):
            with open(key_file, 'rb') as file:
                key = file.read()
        else:
            key = Fernet.generate_key()
            with open(key_file, 'wb') as file:
                file.write(key)
        return key
    
    # Fetch configuration from server
    def fetch_and_store_config(self, api_url, token):
        headers = {'Authorization': f'Bearer {token}'}
        try:
            response = httpx.get(api_url, headers=headers)
            response.raise_for_status()
            config_data = response.json()
            key = security.load_or_generate_key()
            fernet = Fernet(key)

            encrypted_data = fernet.encrypt(json.dumps(config_data).encode())
            with open(key_credential, 'wb') as enc_file:
                enc_file.write(encrypted_data)
            print("Configuration fetched and stored securely.")
            return config_data
        except Exception as e:
            print(f"Error fetching configuration: {e}")
            return {}

    # Load and decrypt configuration
    def load_config(self):
        key = security.load_or_generate_key()
        fernet = Fernet(key)
        try:
            with open(key_credential, 'rb') as enc_file:
                encrypted_data = enc_file.read()
            decrypted_data = fernet.decrypt(encrypted_data)
            data_response = json.loads(decrypted_data.decode())
            data_response['status'] = True
            return data_response
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return {"status": False, "messages":"Error loading configuration"}
        
        
    def init(self):
        print("Init applications ...")
        token = security.load_access_token()
        if not token:
            return
        
        if os.path.exists(key_credential) == False:
            print("Fetching Configuration ...")
            url = server_url+"/v2/enygma-computer-vision/credentials/"
            security.fetch_and_store_config(url, token)
    
    async def init_fetch(self):
        print("Init applications ...")
        token = security.load_access_token()
        if not token:
            return
        print("Fetching Configuration ...")
        url = server_url+"/v2/enygma-computer-vision/credentials/"
        credentials = security.fetch_and_store_config(url, token)
        await session_manager.initialize_sessions(credentials.get('devices',[]))

security = Security()