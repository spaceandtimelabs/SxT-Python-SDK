
  
  

## python-sxt-sdk (v.0.0.1)

  

Python SDK for Space and Time Gateway (python version >= 3.6)

  

## Installation Instructions

  

_Note: Before running the code, rename `.env.sample` to `.env` and ensure that your credentials are setup in the `.env` file properly_

  

```sh
pip install -r requirements.txt
```

The code in `main.py` demonstrates how to call the SDK
  

## Features

  

-  **Sessions**

The SDK implements persistent storage in

1. _File based sessions_

  

-  **Encryption**

It supports ED25519 Public key encryption for Biscuit Authorization and securing data in the platform.

  

-  **SQL Support**

	- Support for DDL : ```creating own schema(namespace), tables, altering and deleting tables```

	- Support for DML: ```CRUD``` operation support.

	- Support for SQL: ```select``` operations support.

	- Support for SQL Views

  

-  **Platform Discovery**

	For fetching metadata and information about the database resources.

	- Namespaces
	- Tables
	- Table Columns
	- Table Indexes
	- Table Primary Keys
	- Table Relationships
	- Table Primary Key References
	- Table Foreign Key References

  
  

## Examples

  

-  **Initializing the SDK**

```python

	# Initializing the Space and Time SDK for use.
	
	from spaceandtimesdk import SpaceAndTimeSDK
	SpaceAndTimeInit =  SpaceAndTimeSDK()

```

  

-  **Authenticating with the Space and Time Platform**

  

Make sure to save your **private key** used in authentication and biscuit generation or else you will not be able to have access to the user and the tables created using the key.

  

The generated ``AccessToken`` is valid for 25 minutes and the ``RefreshToken`` for 30 minutes.

  

```python
	# Authenticate yourself using the Space and Time SDK.
	authenticate_token_data = SpaceAndTimeInit.authenticate()

	authenticate_token_response = authenticate_token_data["response"]
	authenticate_token_error = authenticate_token_data["error"]

	print("Response: ", authenticate_token_response)
	print("Error: ", authenticate_token_error)

```

-  **Generating Biscuits**

  

For the generation of biscuits for your Python SDK that is required for performing the SQL Operations to interact with the SxT Data Warehouse, please refer to the [biscuit-cli](https://www.biscuitsec.org/docs/Usage/cli/) documentation which is a CLI tool that can be used for generating biscuits.

  

-  **DDL, DML and DQL**

	**Note**:
	
	To create a new **schema**, ``ddl_create`` permission is needed.

  

```python
	# Create a Schema
	create_schema_data = SpaceAndTimeInit.CreateSchema("CREATE SCHEMA ETH")

	create_schema_response = create_schema_data["response"]
	create_schema_error = create_schema_data["error"]

	print("Response: ", create_schema_response)
	print("Error: ", create_schema_error)


	# Only for Create Table Queries
	# for ALTER and DROP, use DDL()
	ddl_create_table_data = SpaceAndTimeInit.DDLCreateTable("ETH.TESTTABLE",  "CREATE TABLE ETH.TESTTABLE (id INT PRIMARY KEY, test VARCHAR)",  "permissioned", publicKey, biscuit)

	ddl_create_table_response = ddl_create_table_data["response"]
	ddl_create_table_error = ddl_create_table_data["error"]

	print("Response: ", ddl_create_table_response)
	print("Error: ", ddl_create_table_error)


	# For ALTER and DROP
	ddl_data = SpaceAndTimeInit.DDL("ETH.TESTTABLE",  "ALTER TABLE ETH.TESTTABLE ADD TEST2 VARCHAR", biscuit)

	ddl_data_response = ddl_data["response"]
	ddl_data_error = ddl_data["error"]

	print("Response: ", ddl_data_response)
	print("Error: ", ddl_data_error)


	# DML
	# Use DML() to insert, update, delete and merge queries
	dml_data = SpaceAndTimeInit.DML("ETH.TESTTABLE",  "INSERT INTO ETH.TESTTABLE VALUES(5,'x5')", biscuit)

	dml_data_response = dml_data["response"]
	dml_data_error = dml_data["error"]

	print("Response: ", dml_data_response)
	print("Error: ", dml_data_error)


	# DQL for selecting content from the blockchain tables.
	dql_data = SpaceAndTimeInit.DQL("ETH.TESTTABLE",  "SELECT * FROM ETH.TESTTABLE", biscuit)

	dql_data_response = dql_data["response"]
	dql_data_error = dql_data["error"]

	print("Response: ", dql_data_response)
	print("Error: ", dql_data_error)

```

  

-  **DISCOVERY**

	Discovery SDK calls need a user to be logged in.

  

```python
	# List Namespaces
	namespace_data = SpaceAndTimeInit.get_namespaces()

	namespace_response = namespace_data["response"]
	namespace_error = namespace_data["error"]

	print("Response: ", namespace_response)
	print("Error: ", namespace_error)


	# List Tables in a given namespace
	# Possible scope values - ALL = all tables, PUBLIC = non-permissioned tables, PRIVATE = tables created by a requesting user
	get_tables_data = SpaceAndTimeInit.get_tables("ALL","ETH")

	get_tables_response = get_tables_data["response"]
	get_tables_error = get_tables_data["error"]

	print("Response: ", get_tables_response)
	print("Error: ", get_tables_error)

	 
	# List columns for a given table in a namespace
	get_table_column_data = SpaceAndTimeInit.get_table_columns("TESTTABLE",  "ETH")

	get_table_column_response = get_table_column_data["response"]
	get_table_column_error = get_table_column_data["error"]

	print("Response: ", get_table_column_response)
	print("Error: ", get_table_column_error)

	  
	# List table index for a given table in a namespace
	get_table_indexes_data = SpaceAndTimeInit.get_table_indexes("TESTTABLE",  "ETH")

	get_table_indexes_response = get_table_indexes_data["response"]
	get_table_indexes_error = get_table_indexes_data["error"]

	print("Response: ", get_table_indexes_response)
	print("Error: ", get_table_indexes_error)


	# List table primary key for a given table in a namespace
	get_table_primary_keys_data = SpaceAndTimeInit.get_table_primary_keys("TESTTABLE",  "ETH")

	get_table_primary_keys_response = get_table_primary_keys_data["response"]
	get_table_primary_keys_error = get_table_primary_keys_data["error"]

	print("Response: ", get_table_primary_keys_response)
	print("Error: ", get_table_primary_keys_error)

	  
	# List table relations for a namespace and scope
	get_table_relationship_data = SpaceAndTimeInit.get_table_relationships("PRIVATE",  "ETH")

	get_table_relationship_response = get_table_relationship_data["response"]
	get_table_relationship_error = get_table_relationship_data["error"]

	print("Response: ", get_table_relationship_response)
	print("Error: ", get_table_relationship_error)

	  
	# List table primary key references for a table, column and a namespace
	primary_key_reference_data = SpaceAndTimeInit.get_primary_key_references("TESTTABLE",  "TEST",  "ETH")

	primary_key_reference_response =
	primary_key_reference_data["response"]
	primary_key_reference_error = primary_key_reference_data["error"]

	print("Response: ", primary_key_reference_response)
	print("Error: ", primary_key_reference_error)

	  
	# List table foreign key references for a table, column and a namespace
	foreign_key_reference_data = SpaceAndTimeInit.get_foreign_key_references("TESTTABLE",  "TEST",  "ETH")

	foreign_key_reference_response = foreign_key_reference_data["response"]
	foreign_key_reference_error = foreign_key_reference_data["error"]

	print("Response: ", foreign_key_reference_response)
	print("Error: ", foreign_key_reference_error)

```

  

-  **Storage**

	For File Storage, the following methods are available

```python

	# File

	SpaceAndTimeInit.write_to_file(AccessToken, RefreshToken, AccessTokenExpires, RefreshTokenExpires)

	SpaceAndTimeInit.read_file_contents()

```
