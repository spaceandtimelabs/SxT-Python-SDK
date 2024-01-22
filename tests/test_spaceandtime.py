import os, sys, pytest, pandas, random
from dotenv import load_dotenv
from pathlib import Path

# load local copy of libraries
sys.path.append(str( Path(Path(__file__).parents[1] / 'src').resolve() ))
from spaceandtime.spaceandtime import SpaceAndTime
from spaceandtime.sxtkeymanager import SXTKeyManager
from spaceandtime.sxtbiscuits import SXTBiscuit


# authenticate once for all subsequent tests
envfile = Path(Path(__file__).parent / '.env').resolve() # ./tests/.env
sxt = SpaceAndTime(envfile_filepath=envfile, application_name='pytest_SDKTesting')
sxt.logger_addFileHandler( Path(envfile.parent / 'latest_test_log.txt') )
sxt.authenticate()


def test_access_token_created():
    # designed to test the root-level authentication
    assert sxt.access_token != ''
    assert sxt.user.user_id == 'pySDK_tester'
    assert sxt.user.public_key == "Lu8fefHsAYxKfj7oaCx+Rtz7eNiPln6xbOxJJo0aIZQ="
    assert sxt.user.private_key[:6] == 'MeaW6J'
    assert sxt.access_token[:4] == 'eyJ0' 

 
def test_execute_query():
    success, data = sxt.execute_query('Select * from SXTLabs.Singularity limit 1')
    assert success
    assert data[0]['NAME'] == 'Singularity'
    assert type(data) == list
    assert type(data[0]) == dict

    success, data = sxt.execute_query('Select * from SXTLabs.Singularity limit 1', 
                                      sql_type=sxt.SQLTYPE.DQL, resources=['SXTLabs.Singularity'],
                                      output_format = sxt.OUTPUT_FORMAT.PARQUET )
    assert success
    assert type(data) == bytes
 
    success, data = sxt.execute_query('Select * from SXTLabs.Singularity limit 1', 
                                      sql_type=sxt.SQLTYPE.DQL, resources=['SXTLabs.Singularity'],
                                      output_format = sxt.OUTPUT_FORMAT.DATAFRAME )
    assert success
    assert type(data) == pandas.DataFrame

    success, data = sxt.execute_query('Select * from SXTLabs.Singularity limit 1', 
                                      sql_type=sxt.SQLTYPE.DQL, resources=['SXTLabs.Singularity'],
                                      output_format = sxt.OUTPUT_FORMAT.CSV )
    assert success
    assert type(data) == list
    assert type(data[0]) == str # header
    assert type(data[1]) == str # data
    assert len(data) == 2 # header + 1 data row
    assert data[1].count(',') > 3




def test_discovery():
    # Schemas
    success, schemas = sxt.discovery_get_schemas(return_as=list)
    assert success
    assert type(schemas) == list 
    assert 'ETHEREUM' in schemas
    assert 'SXTDEMO' in schemas
    assert 'SXTLABS' in schemas

    success, schemas = sxt.discovery_get_schemas(return_as=dict)
    assert success
    assert type(schemas) == list
    assert type(schemas[0]) == dict
    assert [s for s in schemas if s['schema']=='SXTDEMO'][0]['isPublic']

    success, schemas = sxt.discovery_get_schemas(return_as=str)
    assert success
    assert type(schemas) == str
    assert 'POLYGON,' in schemas
    assert schemas.count(',') >= 10

    success, schemas = sxt.discovery_get_schemas(scope = sxt.DISCOVERY_SCOPE.PRIVATE)
    assert success
    assert schemas.count(',') == 0  # no such thing right now

    # Tables
    success, tables = sxt.discovery_get_tables('SXTLabs', scope = sxt.DISCOVERY_SCOPE.PRIVATE, return_as=list)
    assert success
    assert 'SXTLABS.CRM_ACCOUNTS' in tables
    assert len(tables) >=10

    success, tables = sxt.discovery_get_tables('SXTLabs', search_pattern='CRM_Cosell', scope = sxt.DISCOVERY_SCOPE.PRIVATE, return_as=list)
    assert success
    assert 'SXTLABS.CRM_COSELL_AGREEMENTS' in tables
    assert len(tables) <=10

    # Columns
    success, columns = sxt.discovery_get_table_columns('POLYGON', 'BLOCKS', return_as=list)
    assert success
    assert 'TIME_STAMP' in columns
    assert len(columns) > 5
    
    success, columns = sxt.discovery_get_table_columns('POLYGON', 'BLOCKS', search_pattern='BLOCK', return_as=dict)
    assert success
    assert 'BLOCK_NUMBER' in [c['column'] for c in columns]
    assert len(columns) < 5
    

    pass 

if __name__ == '__main__':
    
    
    pass 