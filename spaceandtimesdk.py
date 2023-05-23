import requests
import ed25519
import base64
import binascii
import json
from datetime import datetime
import os
from nacl.signing import SigningKey, VerifyKey
from nacl.exceptions import BadSignatureError
from dotenv import load_dotenv, set_key, get_key

from keygen import exported_keys

class SpaceAndTimeSDK:
    def __init__(self):
        self.base_url = os.getenv('BASEURL')

    """ Authentication APIs """
    # Check if a User is using the ID
    def check_user_identifier(self, user_id):
        try:

            api_endpoint = f"{self.base_url}/auth/idexists/{user_id}"
            headers = {"accept": "application/json"}
            response = requests.get(api_endpoint,headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    # Generates an AuthCode given an userId, prefix and joinCode
    def generate_auth_code(self, user_id, prefix, join_code):
        try:
            
            api_endpoint = f"{self.base_url}/auth/code"
            payload = {
                'userId': user_id,
                'prefix': prefix,
                'joinCode': join_code,
            }

            headers = {
                "accept": "application/json",
                "content-type": "application/json"
            }     

            response = requests.post(api_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}
    
        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    # Generate a signature using an authcode and privatekey
    def signature_generation(self, auth_code, priv_key_arg, public_key_arg):
        
        
        message = bytes(auth_code, 'utf-8')
        private_key = self.signing_keys_convert(priv_key_arg)

        signature = private_key.sign(message)

        hex_signature = binascii.hexlify(signature).decode()[:128]
        keys_content_object = {
            'b64_private_key':priv_key_arg,
            'b64_public_key':public_key_arg,
            'hex_signature':hex_signature
        }

        return keys_content_object

    # Generates access and refresh tokens
    def generate_tokens(self, user_id, auth_code, private_key, public_key, scheme="ed25519"):  #(user_id, auth_code, private_key, public_key, scheme)        

        try:

            api_endpoint = f"{self.base_url}/auth/token"
            signature_contents = self.signature_generation(auth_code, private_key, public_key)
            b64_private_key, b64_public_key, hex_signature = signature_contents.values()

            payload = {
                    'userId': user_id,
                    'authCode': auth_code,
                    'signature': hex_signature,
                    'key': b64_public_key,
                    'scheme': scheme
                }
            
            headers = {
                    "accept": "application/json",
                    "content-type": "application/json"
            }     

            response = requests.post(api_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}
        
        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    def signing_keys_convert(self, private_key_arg):

        # Decoding the Base64 Key.
        decoded_private_key = base64.b64decode(private_key_arg)

        # Converting the decoded Base64 Key to a Signing Key.
        private_signing_key = SigningKey(decoded_private_key)

        return private_signing_key

    def read_file_contents(self):
        with open("session.txt") as file:
            access_token = file.readline().strip()
            refresh_token = file.readline().strip()
            access_token_expires = file.readline().strip()
            refresh_token_expires = file.readline().strip()

        token_obj = {
            "accessToken": access_token,
            "refreshToken": refresh_token,
            "accessTokenExpires": access_token_expires,
            "refreshTokenExpires":refresh_token_expires
        }

        return token_obj

    def write_to_file(self, accessToken, refreshToken, accessTokenExpires, refreshTokenExpires):
        with open("session.txt", "w") as file:
            file.write(accessToken + "\n")
            file.write(refreshToken + "\n")
            file.write(str(accessTokenExpires) + "\n")
            file.write(str(refreshTokenExpires) + "\n")

    def user_id_exists(self):
        user_id = os.getenv('USERID')
        user_id_response = self.check_user_identifier(user_id)["response"]
        
        final_result = True if (user_id_response == 'true') else False
        return final_result
    
    def authenticate_user(self, private_key_arg="", public_key_arg=""):

        main_public_key = exported_keys["b64_public_key"] if public_key_arg == "" else public_key_arg
        main_private_key = exported_keys["b64_private_key"] if private_key_arg == "" else private_key_arg

        pub_key = main_public_key if os.getenv('PUBLICKEY') is None else os.getenv('PUBLICKEY')
        priv_key = main_private_key if os.getenv('PRIVATEKEY') is None else os.getenv('PRIVATEKEY')

        if not self.user_id_exists():
            print('Lets create your user ID!')
            return self.authenticate(priv_key, pub_key)

        #2) If user_id already exists, then authenticate 
        else:
            print('Time to authenticate!')
            return self.authenticate(priv_key, pub_key)


    #Creates Access and Refresh Tokens for Users
    def authenticate(self, priv_key, pub_key, prefix=""):

        user_id = os.getenv('USERID')
        join_code = os.getenv('JOINCODE')
        scheme = os.getenv('SCHEME')

        auth_code_data = self.generate_auth_code(user_id, prefix, join_code)
        auth_code_response, auth_code_error = auth_code_data["response"], auth_code_data["error"]
        if auth_code_error: raise Exception(auth_code_error)

        auth_code = json.loads(auth_code_response)["authCode"]

        required_private_key = priv_key 
        required_public_key = pub_key 

        tokens_data = self.generate_tokens(user_id, auth_code, required_private_key, required_public_key, scheme)        
        tokens_response, tokens_error = tokens_data["response"], tokens_data["error"]
        if tokens_error: raise Exception(tokens_error)

        jsonResponse = json.loads(tokens_response)

        # Writing Token response to file
        self.write_to_file(jsonResponse["accessToken"], jsonResponse["refreshToken"], jsonResponse["accessTokenExpires"], jsonResponse["refreshTokenExpires"])
        
        # Writing key values to ENV
        
        set_key(".env", "PUBLICKEY", required_public_key)
        set_key(".env", "PRIVATEKEY", required_private_key)

        return {"response" : jsonResponse, "error" : tokens_error}

    # Allows the user to generate new tokens if time left is less than or equal to 2 minutes OR gives them back their unexpired tokens.
    def rotate_tokens(self):
        MINIMUM_TOKEN_SECONDS = 120

        tokens = self.read_file_contents()
        access_token, refresh_token = tokens['accessToken'], tokens['refreshToken']
        access_token_expires, refresh_token_expires = int(tokens['accessTokenExpires']), int(tokens['refreshTokenExpires'])

        authentication_tokens = [access_token, refresh_token]

        current_milliseconds = int(datetime.timestamp(datetime.now()) * 1000)

        access_token_expiry_datetime = datetime.fromtimestamp((current_milliseconds + access_token_expires) / 1000)
        refresh_token_expiry_datetime = datetime.fromtimestamp((current_milliseconds + refresh_token_expires) / 1000)

        access_token_expiry_duration = round((access_token_expiry_datetime - datetime.now()).total_seconds())
        refresh_token_expiry_duration = round((refresh_token_expiry_datetime - datetime.now()).total_seconds())

        should_refresh_token = access_token_expiry_duration <= MINIMUM_TOKEN_SECONDS
        should_authenticate_user = refresh_token_expiry_duration <= MINIMUM_TOKEN_SECONDS

        if should_refresh_token: 
            if should_authenticate_user:
                token_response, token_error = self.authenticate_user()
                return token_response, token_error
            
            refresh_token_response, refresh_token_error = self.refresh_token()
            return refresh_token_response, refresh_token_error

        return authentication_tokens, None

    # Checks if your accessToken value is valid and gives you the UserID on success.
    def validate_token(self):
        try:
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]

            api_endpoint = f"{self.base_url}/auth/validtoken"

            headers = {
                "accept": "application/json",
                "content-type": "application/json",
                "Authorization" : f'Bearer {access_token}'
            }    

            response = requests.get(api_endpoint, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}
        
        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    #Refresh your Access and Refresh Tokens by providing a valid RefreshToken
    def refresh_token(self):
        try:
            tokens = self.read_file_contents()
            refresh_token = tokens["refreshToken"]

            api_endpoint = f"{self.base_url}/auth/refresh"
            headers = {
                "accept": "application/json",
                "Authorization" : f'Bearer {refresh_token}'
            }    
            
            response = requests.post(api_endpoint, headers=headers)
            response.raise_for_status()
            jsonResponse = response.json()

            # Writing Token response to file
            self.write_to_file(jsonResponse["accessToken"], jsonResponse["refreshToken"], jsonResponse["accessTokenExpires"], jsonResponse["refreshTokenExpires"])
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

   