import requests
import ed25519
import base64
import binascii
import validation
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
            validation.check_prefix_and_joincode(prefix, join_code)
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
    def generate_tokens(self, user_id, auth_code, private_key, public_key, scheme="ed25519"): 

        try:
            validation.is_base64(private_key)
            validation.is_base64(public_key)

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
            return self.authenticate(priv_key, pub_key)

        #2) If user_id already exists, then authenticate 
        else:
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


    #Logout or end an authenticated session.
    def logout(self):
        try:
            tokens = self.read_file_contents()
            refresh_token = tokens["refreshToken"]

            api_endpoint = f'{self.base_url}/auth/logout'
            headers = {
                "accept": "application/json",
                "Authorization" : f'Bearer {refresh_token}'
            }

            response = requests.post(api_endpoint, headers=headers)
            response.raise_for_status()
            if response.status_code == 200: print('User has been logged out.')
            return {"response" : response.text, "error" : None}
            
        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    """ Resource Discovery APIs """

    # Fetch the namespace metadata
    def get_namespaces(self):
        try:
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]

            api_endpoint = f"{self.base_url}/discover/namespace"

            headers = {
                "accept": "application/json",
                "Authorization" : f'Bearer {access_token}'
            }

            response = requests.get(api_endpoint, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    # Fetch table metadata
    def get_tables(self, scope, namespace):
        try:
            validation.validate_string(scope)
            validation.try_parse_identifier(namespace)
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]

            api_endpoint = f"{self.base_url}/discover/table?scope={scope}&namespace={namespace}"

            headers = {
                "accept": "application/json",
                "Authorization":f'Bearer {access_token}'
            }

            response = requests.get(api_endpoint, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}
        
        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    def discovery_API_Request(self, namespace, table_name, api_endpoint):
         try:
           validation.try_parse_identifier(namespace)
           validation.try_parse_identifier(table_name)
           tokens = self.read_file_contents()
           access_token = tokens["accessToken"]

           validation.validate_string(namespace)

           headers = {
               "accept": "application/json",
               "Authorization":f'Bearer {access_token}'
           }

           response = requests.get(api_endpoint, headers=headers)
           response.raise_for_status()
           return {"response" : response.text, "error" : None}
         
         except requests.exceptions.RequestException as error:
             return {"response" : None, "error" : str(error)}
 

    # Fetch table column metadata
    def get_table_columns(self, table_name, namespace):
        api_endpoint = f"{self.base_url}/discover/table/column?namespace={namespace}&table={table_name}"
        return self.discovery_API_Request(namespace, table_name, api_endpoint)

    # Fetch table indexes metadata
    def get_table_indexes(self, table_name, namespace):
        api_endpoint = f"{self.base_url}/discover/table/index?namespace={namespace}&table={table_name}"
        return self.discovery_API_Request(namespace, table_name, api_endpoint)

    # Fetch table primary key metadata
    def get_table_primary_keys(self, table_name, namespace):
        api_endpoint = f"{self.base_url}/discover/table/primaryKey?namespace={namespace}&table={table_name}"
        return self.discovery_API_Request(namespace, table_name, api_endpoint)

    # Fetch table relationship metadata for tables in a namespace
    def get_table_relationships(self, scope, namespace):
        try:
           validation.validate_string(scope)
           validation.try_parse_identifier(namespace)

           tokens = self.read_file_contents()
           access_token = tokens["accessToken"]

           api_endpoint = f"{self.base_url}/discover/table/relations?namespace={namespace}&scope={scope}"

           headers = {
               "accept": "application/json",
               "Authorization":f'Bearer {access_token}'
           }

           response = requests.get(api_endpoint, headers=headers)
           response.raise_for_status()
           return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    def discovery_API_Request_References(self, namespace, table_name, column, api_endpoint):
        try:
           validation.try_parse_identifier(namespace)
           validation.try_parse_identifier(table_name)
           validation.validate_string(column)

           tokens = self.read_file_contents()
           access_token = tokens["accessToken"]

           headers = {
               "accept": "application/json",
               "Authorization":f'Bearer {access_token}'
           }

           response = requests.get(api_endpoint, headers=headers)
           response.raise_for_status()
           return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}


    #Fetch all primary keys referenced by a provided foreign key
    def get_primary_key_references(self, table_name, column, namespace):
        api_endpoint = f"{self.base_url}/discover/refs/primarykey?table={table_name}&namespace={namespace}&column={column}"
        return self.discovery_API_Request_References(namespace, table_name, column, api_endpoint)

    # Fetch all foreign key referencing the provided primary key
    def get_foreign_key_references(self, table_name, column, namespace):
        api_endpoint = f"{self.base_url}/discover/refs/foreignkey?table={table_name}&namespace={namespace}&column={column}"
        return self.discovery_API_Request_References(namespace, table_name, column, api_endpoint)
        
    """ CoreSQL """

    @staticmethod
    def convert_SQL_Text(sql_text, public_key, access_type):
        return f'{str(sql_text)} WITH \"public_key={str(public_key)},access_type={access_type}\"'

    # Create a Schema
    def CreateSchema(self, sql_text, biscuit_tokens=[], origin_app=""):
        try:
            validation.validate_string(sql_text)

            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]
            sql_text = sql_text.upper()

            api_endpoint = f"{self.base_url}/sql/ddl"

            payload = {
                'biscuits':biscuit_tokens,
                'sqlText': sql_text
            }

            headers = {
               "Authorization":f'Bearer {access_token}',
               "Content-Type": "application/json",
               "Accept": "application/json",
               "originApp":origin_app
            }

            response = requests.post(api_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}


    # DDL
    # Create a table with the given ResourceId
    def DDLCreateTable(self, sql_text, access_type, public_key, biscuit, biscuit_tokens=[], origin_app=""):
        try:
           validation.validate_string(sql_text)
           validation.validate_string(access_type)

           tokens = self.read_file_contents()
           access_token = tokens["accessToken"]

           sql_text = sql_text.upper()

           api_endpoint = f"{self.base_url}/sql/ddl"
           sql_text_payload = self.convert_SQL_Text(sql_text, public_key, access_type)

           payload = {
               'biscuits':biscuit_tokens,
               'sqlText': sql_text_payload
           }

           headers = {
               "Authorization":f'Bearer {access_token}',
               "content-type": "application/json",
               "Accept": "application/json",
               "Biscuit": biscuit,
               "originApp":origin_app
           }

           response = requests.post(api_endpoint, json=payload, headers=headers)
           response.raise_for_status()
           return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    # Alter and drop a table with the given ResourceId
    def DDL(self, sql_text, biscuit, biscuit_tokens=[], origin_app=""):
        try:
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]
            validation.validate_string(sql_text)

            api_endpoint = f"{self.base_url}/sql/ddl"

            payload = {
                "biscuits":biscuit_tokens,
                "sqlText":sql_text
            }

            headers = {
               "accept": "application/json",
               "content-type": "application/json",
               "Authorization":f'Bearer {access_token}',
               "Biscuit": biscuit,
               "originApp":origin_app
           }
                        
            response = requests.post(api_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}

    # DML
    # Perform insert, update, merge and delete with the given resourceId

    def DML(self, resource_id, sql_text, biscuit, biscuit_tokens=[], origin_app=""):
        try:
            validation.try_parse_identifier(resource_id)
            validation.validate_string(sql_text)
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]

            api_endpoint = f"{self.base_url}/sql/dml"

            payload = {
                "biscuits":biscuit_tokens,
                "resourceId":resource_id.upper(),
                "sqlText":sql_text
            }

            headers = {
               "accept": "application/json",
               "content-type": "application/json",
               "Authorization":f'Bearer {access_token}',
               "Biscuit": biscuit,
               "originApp":origin_app
            }
            
            response = requests.post(api_endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None} 

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}
    
    # DQL
    # Perform selection with the given resourceId
    # If rowCount is 0, then the query will fetch all of the data

    def DQL(self, resource_id, sql_text, biscuit, biscuit_tokens=[], origin_app="", row_count=0):
        try:
            validation.try_parse_identifier(resource_id)
            validation.validate_string(sql_text)
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]
            validation.validate_number(row_count)

            api_endpoint = f"{self.base_url}/sql/dql"

            if(row_count > 0):
                payload = {
                "biscuits":biscuit_tokens,
                "resourceId":resource_id.upper(),
                "sqlText":sql_text,
                "rowCount":row_count
            }
            else:
                payload = {
                "biscuits":biscuit_tokens,
                "resourceId":resource_id.upper(),
                "sqlText":sql_text.upper(),
            }

            headers = {
               "accept": "application/json",
               "content-type": "application/json",
               "Authorization":f'Bearer {access_token}',
               "Biscuit": biscuit,
               "originApp":origin_app
           }

            response = requests.post(api_endpoint, json=payload,headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}


    """ Views """        
    
    # Execute a view 
    def execute_view(self, view_name, parameters_request={}):
        try:
            validation.validate_string(view_name)
            tokens = self.read_file_contents()
            access_token = tokens["accessToken"]

            param_endpoint = ""
            param_string = ""
            api_endpoint = f"{self.base_url}/sql/views/{view_name}"

            if(len(parameters_request) > 0):
                for parameter_request_value in parameters_request:
                    param_name = parameter_request_value["name"]
                    param_type = parameter_request_value["type"]

                    param_string += f"{param_name}={param_type}&"

                param_string = param_string[:-1]
                param_endpoint += f"?params={param_string}"


            api_endpoint += f"{param_endpoint}"

            headers = {
                "accept": "application/json",
                "Authorization":f'Bearer {access_token}',
            }

            response = requests.get(api_endpoint, headers=headers)
            response.raise_for_status()
            return {"response" : response.text, "error" : None}

        except requests.exceptions.RequestException as error:
            return {"response" : None, "error" : str(error)}
   