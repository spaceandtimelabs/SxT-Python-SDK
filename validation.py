import re
import base64
import binascii
from Cryptodome.Cipher import AES

def validate_number(number_val):
    if not isinstance(number_val, int):
        raise TypeError("Expected Integer but got {}".format(type(number_val).__name__))


def validate_string(input_string):
    if not isinstance(input_string, str):
        raise TypeError("Expected string, but got {}".format(type(input_string).__name__))
    
def validate_boolean(input_bool):
    if not isinstance(input_bool, bool):
        raise TypeError("Expected boolean, but got {}".format(type(input_bool).__name__))

# Checking if the given string is Base64 URL Safe Encoded or not.
def is_base64(s):
    try:
        # Replace '-' with '+' and '_' with '/' to convert URL-safe base64 to standard base64
        s = s.replace('-', '+').replace('_', '/')
        # Pad the string with '=' characters
        s += '=' * (-len(s) % 4)

        # Attempt to decrypt using a dummy key and IV
        cipher = AES.new(b'A' * 32, AES.MODE_CBC, iv=b'B' * 16)
        cipher.decrypt(base64.b64decode(s))
        return True
    except (binascii.Error, ValueError) as error:
        raise binascii.Error("The Input String is not URL-safe base64 encoded.")
    
def check_prefix_and_joincode(prefix, join_code):
    if not isinstance(prefix, str) or not isinstance(join_code, str):
        error_prefix = '' if isinstance(prefix, str) else f"Unexpected type of {type(prefix)} for prefix"
        error_joincode = '' if isinstance(join_code, str) else f"{' and' if not isinstance(prefix, str) else ''} Unexpected type of {type(join_code)} for joincode"
        raise ValueError(f"{error_prefix}{error_joincode}")
    
VALID_DB_RESOURCE_IDENTIFIER = "^[A-Z_][A-Z0-9_]+$"
INVALID_RESOURCEID = "Invalid resourceId"
DEFAULT_SCHEMA = "PUBLIC"

def is_valid_database_identifier(input):
    return re.match(VALID_DB_RESOURCE_IDENTIFIER, input) is not None

def try_parse_identifier(resource_id):
    parts = resource_id.upper().split(".")
    if len(parts) == 0 or len(parts) > 2:
        raise ValueError(INVALID_RESOURCEID + ": Provided table identifier format is invalid")
    elif len(parts) == 1:
        schema_name = DEFAULT_SCHEMA
        table_name = parts[0]
    else:
        schema_name = parts[0]
        table_name = parts[1]
    if not is_valid_database_identifier(schema_name) or not is_valid_database_identifier(table_name):
        raise ValueError(INVALID_RESOURCEID + ": Either schema or table identifier is invalid")
    return (schema_name, table_name)

