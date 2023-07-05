# File containing Examples to run the SDK.

from spaceandtimesdk import SpaceAndTimeSDK
import os
from dotenv import load_dotenv
import re
import base64
import binascii
from Cryptodome.Cipher import AES

load_dotenv()

from keygen import exported_keys

SpaceAndTimeInit = SpaceAndTimeSDK()

join_code = os.getenv('JOINCODE')
prefix = os.getenv('PREFIX')
user_id = os.getenv('USERID')
scheme = os.getenv('SCHEME')

tokens = SpaceAndTimeInit.read_file_contents()
access_token, refresh_token = tokens['accessToken'], tokens['refreshToken']

"""
AUTHENTICATION BLOCK
"""

if access_token: 
    validate_token_data = SpaceAndTimeInit.validate_token()
    validate_token_response, validate_token_error = validate_token_data["response"], validate_token_data["error"]
    if validate_token_response:
        print('Valid access token provided.')
        print('Valid User ID: ', validate_token_response)
    else:
        refresh_token_data = SpaceAndTimeInit.refresh_token()
        refresh_token_response, refresh_token_error = refresh_token_data["response"], refresh_token_data["error"]
        print('Refreshed Tokens: ', refresh_token_response)

        if not refresh_token_response: 
            authenticate_token_data = SpaceAndTimeInit.authenticate_user()
            authenticate_token_response, authenticate_token_error = authenticate_token_data["response"], authenticate_token_data["error"]
            if not authenticate_token_error: 
                print(authenticate_token_response)
            else: 
                print('Invalid user tokens provided.')
                print(authenticate_token_error)
    
else:
    authenticate_token_data = SpaceAndTimeInit.authenticate_user()
    authenticate_token_response, authenticate_token_error = authenticate_token_data["response"], authenticate_token_data["error"]

    if not authenticate_token_error:
        print(authenticate_token_response)
    else:
        print('Invalid user tokens provided.')
        print(authenticate_token_error)

# Authentication APIs

# Check if a UserId is already in use
check_user_identifier_data = SpaceAndTimeInit.check_user_identifier(user_id)
print(check_user_identifier_data)

# Authenticate yourself with Space And Time using the SDK
authenticate_token_data = SpaceAndTimeInit.authenticate_user()
print(authenticate_token_data)

# Refresh Your Tokens
refresh_tokens_data = SpaceAndTimeInit.refresh_token()
print(refresh_tokens_data)

# Rotate Tokens 
rotate_token_data = SpaceAndTimeInit.rotate_tokens()
print(rotate_token_data)

# Validate your AccessToken by getting back the UserId
validate_token_data = SpaceAndTimeInit.validate_token()
print(validate_token_data)

# Logout or end your authenticated session by using a RefreshToken
logout_data = SpaceAndTimeInit.logout()
print(logout_data)


scope = "ALL"
namespace = "ETHEREUM"
owned = True
column = "BLOCK_NUMBER"
table_name = "FUNGIBLETOKEN_WALLET"
foreign_key_table_name = "BLOCKS"

# Resource Discovery APIs

# List the namespaces
namespace_data = SpaceAndTimeInit.get_namespaces()
print(namespace_data)

# List the table of a given namespace
# Scope value options - ALL = all tables, PUBLIC = non-permissioned tables, PRIVATE = tables created by a requesting user
get_tables_data = SpaceAndTimeInit.get_tables(scope, namespace)
print(get_tables_data)

# List table column metadata
get_table_column_data = SpaceAndTimeInit.get_table_columns(table_name, namespace)
print(get_table_column_data)

# List table Index metadata
get_table_indexes_data = SpaceAndTimeInit.get_table_indexes(table_name, namespace)
print(get_table_indexes_data)

# List table primarykey metadata
get_table_primary_keys_data = SpaceAndTimeInit.get_table_primary_keys(table_name, namespace)
print(get_table_primary_keys_data)

# List table relationship metadata including table, column and primary key references for all tables of a namespace
get_table_relationship_data = SpaceAndTimeInit.get_table_relationships(scope, namespace)
print(get_table_relationship_data)

# List all primary key references by the provided foreign key reference
primary_key_reference_data = SpaceAndTimeInit.get_primary_key_references(table_name, column, namespace)
print(primary_key_reference_data)

# List all foreign key references referencing the provided primary key
foreign_key_references_data = SpaceAndTimeInit.get_foreign_key_references(foreign_key_table_name, column, namespace)
print(foreign_key_references_data)

# Core SQL APIs

namespace = "ETH"
table_name = "PYTHTEST1"
# table_name = "PYTHSXT2"

biscuit_array = ["EpABCiYKD..."]
resource_id = f"{namespace}.{table_name}"

create_sql_text = "CREATE TABLE ETH.PYTHTEST1 (ID INT PRIMARY KEY, TEST VARCHAR)"
select_sql_text = "SELECT * FROM ETH.PYTHTEST1"
drop_sql_text = "DROP TABLE ETH.PYTHTEST1"
insert_sql_text = "INSERT INTO ETH.PYTHTEST1 VALUES(1, 'X1')"


main_public_key = exported_keys["hex_public_key"]
main_private_key = exported_keys["hex_private_key"]
access_type = "public_append"
biscuit_token = ""

# Create a Schema 
create_schema_sql_text = "CREATE SCHEMA ETH"
create_schema_data = SpaceAndTimeInit.CreateSchema(create_schema_sql_text)
print(create_schema_data)

# DDL
# Create a table
ddl_create_table_data = SpaceAndTimeInit.DDLCreateTable(create_sql_text, access_type, main_public_key, biscuit_token, biscuit_array)
print(ddl_create_table_data)

# Drop a table
ddl_data = SpaceAndTimeInit.DDL(resource_id, drop_sql_text, biscuit_token, biscuit_array)
print(ddl_data)

# DML
# Insert, update, merge and delete contents of a table
dml_data = SpaceAndTimeInit.DML(insert_sql_text, biscuit_token, biscuit_array)
print(dml_data)

# DQL
# Select query and selects all if row_count = 0
dql_data = SpaceAndTimeInit.DQL(resource_id, select_sql_text, biscuit, biscuit_array)
print(dql_data)

# Views API

parameters_request = [
    {
        "name":"BLOCK_NUMBER",
        "type":"Integer"
    }
]

namespace = "ETH"
table_name = "BLOCK"
resource_id = f"{namespace}.{table_name}"
view_text = "SELECT * FROM ETH.BLOCK WHERE BLOCK_NUMBER={{BLOCK_NUMBER}}"
view_name = "block-view-pyth3"
description = "display the blocks by BLOCK NUMBER"
update_description = "block view update 3"
publish = True


# Execute a view
print(SpaceAndTimeInit.execute_view(view_name, parameters_request))
