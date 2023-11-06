import logging, random, time, json
from datetime import datetime
from pathlib import Path
from .sxtuser import SXTUser
from .sxtresource import SXTTable, SXTView
from .sxtkeymanager import SXTKeyManager
from .sxtenums import *
from .sxtexceptions import *

class SpaceAndTime:

    user: SXTUser = None 
    application_name: str = 'SxT-SDK'
    network_calls_enabled:bool = True
    discovery = None
    default_local_folder:str = None
    envfile_filepath:str = None
    start_time: datetime = None
    key_manager: SXTKeyManager = None
    GRANT = SXTPermission
    ENCODINGS = SXTKeyEncodings
    SQLTYPE = SXTSqlType
    OUTPUT_FORMAT = SXTOutputFormat
    TABLE_ACCESS = SXTTableAccessType
    DISCOVERY_SCOPE = SXTDiscoveryScope


    def __init__(self, envfile_filepath=None, api_url=None, 
                user_id=None, user_private_key=None, 
                default_local_folder:str = None,
                application_name='SxT-SDK', 
                logger: logging.Logger = None):
        """Create new instance of Space and Time SDK for Python"""
        if logger: 
            self.logger = logger 
        else: 
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
            if len(self.logger.handlers) == 0: 
                self.logger.addHandler( logging.StreamHandler() )

        self.start_time = datetime.now()
        self.logger.info('-'*30 + f'\nSpace and Time SDK initiated for {self.application_name} at {self.start_time.strftime("%Y-%m-%d %H:%M:%S")}')

        if application_name: self.application_name = application_name
        self.default_local_folder = default_local_folder if default_local_folder else Path('.').resolve()
        self.envfile_filepath = envfile_filepath if envfile_filepath else self.default_local_folder

        self.user = SXTUser(dotenv_file=envfile_filepath, api_url=api_url, user_id=user_id, user_private_key=user_private_key, logger=self.logger)
        self.key_manager = self.user.key_manager
        return None 
    
    @property
    def access_token(self) -> str:
        return self.user.access_token

    @property
    def refresh_token(self) -> str:
        return self.user.refresh_token
    

    def authenticate(self, user:SXTUser = None):
        """--------------------
        Authenticate user to Space and Time.  Uses the default dotenv file to create a default user, if no other is supplied.
        
        Args:
            user (SXTUser): (optional) SXTUser object used to authenticate, and set as default user.  Creates new from default dotenv file if omitted.

        Returns: 
            bool: Success indicator
            str: Access Token returned from Space and Time network

        Examples:
            >>> sxt = spaceandtime()
            >>> success, access_token = sxt.authenticate()
            >>> print( success )
            True
            >>> print( len(access_token) >= 64 )
            True

        """
        if not user: user = self.user
        if self.network_calls_enabled: 
            success, rtn = user.authenticate()
        else:
            user.access_token = 'eyJ0eXBlI_this_is_a_pretend_access_token_it_will_not_really_work_4lXUgI5gIdk8T5Rb4Zlx8-Z1rlY-0y4pu5b4lIjh60wQY_g0vkteuQE0Or0cPDbstDnLg8uRpz5dM4GNg7QHYQ'
            user.refresh_token = 'eyJ0eXBlI_this_is_a_pretend_refresh_token_it_will_not_really_work_4lXUgI5gIdk8T5Rb4Zlx8-Z1rlY-0y4pu5b4lIjh60wQY_g0vkteuQE0Or0cPDbstDnLg8uRpz5dM4GNg7QHYQ'
            success, rtn = (True, user.access_token)
        user.base_api.access_token = self.user.access_token
        self.logger.info(f'Authentcation Success: {success}')
        if not success: self.logger.error(f'Authentication error: {str(rtn)}')
        return success, rtn
    

    def execute_query(self, sql_text:str, sql_type:SXTSqlType = SXTSqlType.DQL, 
                      resources:list = None, user:SXTUser = None, 
                      biscuits:list  = None, output_format:SXTOutputFormat = SXTOutputFormat.JSON) -> tuple:
        """--------------------
        Execute a query using an authenticated user.  If not specified, uses the default user.  
        
        Args: 
            sql_text (str): SQL query text to execute. Allowed two placeholders: {public_key} which will be replaced with the user.public_key, and {resource} which is replaced with the first element in resource list (resource[0]). 
            resources (list): (optional) List of Resources ("schema.table_name") in the sql_text. Supplying will optimize performance. If only 1 value, can optionally supply a str.
            sql_type (SXTSqlType): (optional) Type of query, DML, DDL, DQL. Supplying will optimize performance.
            user (SXTUser): (optional) Authenticated user to use to execute the query. Defaults to default user.
            biscuits (list): (optional) List of biscuit tokens for permissioned tables.  If only querying public tables, this is not needed.
            output_format (SXTOutputFormat): (optional) Output format enum, either JSON or CSV. Defaults to SXTOutputFormat.JSON.

        Returns:
            bool: True if success, False if in Error. 
            list: Rows, either in JSON or CSV format. 

        Examples:
            >>> from spacenadtime import SpaceAndTime
            >>> sxt = SpaceAndTime()
            >>> sxt.authenticate()
            >>> execute_query('Select 1 as A from SXTDEMO.Singularity')
            1

        """
        if not user: user = self.user
        if not resources: resources = []
        if not biscuits: biscuits = []
        rtn = []

        try: 
            resources = resources if type(resources)==list else [str(resources)]
            sql_text = self.__replaceall(mainstr=sql_text, replacemap={'resource':resources[0] if resources else [] ,'public_key':user.public_key })
            self.logger.info(f'Executing query: \n{sql_text}')

            if self.network_calls_enabled: 
                if  sql_type == SXTSqlType.DDL :
                    success, rtn = user.base_api.sql_ddl(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name)

                elif sql_type == SXTSqlType.DML and resources:
                    success, rtn = user.base_api.sql_dml(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name, resources=resources)

                elif sql_type == SXTSqlType.DQL and resources:
                    success, rtn = user.base_api.sql_dql(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name, resources=resources)

                else:
                    success, rtn = user.base_api.sql_exec(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name)
            else:
                success, rtn = (True, [{'col1':'data', 'col2':'data'},{'col1':'data', 'col2':'data'},{'col1':'data', 'col2':'data'}] )

            if not success: raise SxTQueryError(f'Query Failed: {str(rtn)}', logger=self.logger)

        except SxTQueryError as ex:
            self.logger.error(f'Error in query execution: {ex}')
            return False, {'error':f'Error in query execution: {ex}'}

        if output_format == SXTOutputFormat.JSON: return True, rtn
        if output_format == SXTOutputFormat.CSV: return True, self.json_to_csv(rtn)
        return True, rtn
        
    @staticmethod
    def json_to_csv(list_of_dicts:list) -> list:
        """--------------------
        Takes a list of dictionaries (default return from DQL query) and transforms to a list of CSV rows, preceded with a header row.

        Args:
            list_of_dicts (list): A list of dictionary items, i.e., rows of JSON columns.

        Returns: 
            list: A list of CSV strings, i.e., rows of CSV values plus a header row (len(list) will always be N+1)

        Examples:
            >>> success, rows = SpaceAndTime.json_to_csv([{"id":1, "val":"A"}, {"id":2, "val":"B"}, {"id":3, "val":"C"}])
            >>> len(rows)
            4
            >>> rows[1] == '"1","A"'
            True

        """
        if list_of_dicts == []: return False, []
        rows = [','.join( list(list_of_dicts[0].keys()) )] # headers
        for row in list_of_dicts:
            rows.append( ','.join([f'"{str(val).replace(chr(34),chr(34)+chr(34))}"' for val in list(row.values())]) )
        return True, rows 
            

    def __replaceall(self, mainstr:str, replacemap:dict) -> str:
        if 'date' not in replacemap.keys(): replacemap['date'] = datetime.now().strftime('%Y%m%d')
        if 'time' not in replacemap.keys(): replacemap['time'] = datetime.now().strftime('%H%M%S')
        for findname, replaceval in replacemap.items():
            mainstr = mainstr.replace('{'+str(findname)+'}', str(replaceval))                    
        return mainstr

    
    def discovery_get_schemas(self, scope:SXTDiscoveryScope = SXTDiscoveryScope.ALL, 
                              user:SXTUser = None, 
                              return_as:type = list) -> tuple:
        """--------------------
        Connects to the Space and Time network and returns all available schemas.

        Args:
            scope (SXTDiscoveryScope): (optional) Scope of objects to return: All, Public, Subscription, or Private. Defaults to SXTDiscoveryScope.ALL.
            user (SXTUser): (optional) Authenticated User object. Uses default user if omitted.
            return_as (type): (optional) Python type to return. Currently supports n, dict, list, str.

        Returns: 
            object: Return type defined with the return_as feature.
        """
        if not user: user = self.user
        if not scope: scope = SXTDiscoveryScope.ALL
        success, response = user.base_api.discovery_get_schemas(scope=scope.name)  
        if success and return_as in [list, str]: response = sorted([tbl['schema'] for tbl in response])
        if success and return_as == str: response = ', '.join(response)
        if success and return_as not in [json, dict, list, str]:
            self.logger.warning('Supplied an unsupported return type, only [json, list, str] currently supported. Defaulting to dict.')
        return success, response

        
    def discovery_get_tables(self, schema:str, 
                             scope:SXTDiscoveryScope = SXTDiscoveryScope.ALL, 
                             user:SXTUser = None, 
                             search_pattern:str = None, 
                             return_as:type = json) -> tuple:
        """--------------------
        Connects to the Space and Time network and returns all available tables within a schema.

        Args:
            schema (str): Schema name to search for tables.
            scope (SXTDiscoveryScope): (optional) Scope of objects to return: All, Public, Subscription, or Private. Defaults to SXTDiscoveryScope.ALL.
            user (SXTUser): (optional) Authenticated User object. Uses default user if omitted.
            search_pattern (str): (optional) Tablename pattern to match for inclusion into result set. Defaults to None / all tables.
            return_as (type): (optional) Python type to return. Currently supports n, dict, list, str.

        Returns: 
            object: Return type defined with the return_as feature.
        """        
        if not user: user = self.user
        if not scope: scope = SXTDiscoveryScope.ALL
        success, response = user.base_api.discovery_get_tables(scope=scope.name, schema=schema, search_pattern=search_pattern)  
        if success and return_as in [list, str]: response = sorted([ f"{r['schema']}.{r['table']}" for r in response])
        if success and return_as == str: response = ', '.join(response)
        if success and return_as == json: response = {f"{r['schema']}.{r['table']}":r for r in response}
        if success and return_as not in [json, dict, list, str]:
            self.logger.warning('Supplied an unsupported return type, only [json, list, str] currently supported. Defaulting to dict.')
        return success, response

        
        


    

if __name__ == '__main__':
    from pprint import pprint
    def randpad(i=6): return str(random.randint(0,999999)).rjust(6,'0')

    if True:

        # BASIC USAGE 
        sxt = SpaceAndTime()
        sxt.authenticate()

        success, rows = sxt.execute_query(
            'select * from POLYGON.BLOCKS limit 5')
        pprint( rows )


        # bit more complicated:
        success, rows = sxt.execute_query("""
            SELECT 
            substr(time_stamp,1,7) AS YrMth
            ,count(*) AS block_count
            FROM polygon.blocks 
            GROUP BY YrMth
            ORDER BY 1 desc """ )
        pprint( sxt.json_to_csv(rows) )

        print( sxt.user )
        

        # discovery calls provide network information
        success, schemas = sxt.discovery_get_schemas()
        pprint(f'There are {len(schemas)} schemas currently on the network.')
        pprint(schemas)


        for t in [list, json, str]:
            success, tables = sxt.discovery_get_tables('SXTDEMO', return_as=t)
            if success: pprint( tables )

        # Create a table (with random name)
        tableA = SXTTable(name = f"SXTTEMP.MyTestTable_{randpad()}", 
                        new_keypair=True, default_user=sxt.user, logger=sxt.logger,
                        access_type=SXTTableAccessType.PERMISSSIONED)
        tableA.create_ddl = """
        CREATE TABLE {table_name} 
        ( MyID         int
        , MyName       varchar
        , MyDate       date
        , Primary Key(MyID) 
        ) {with_statement}
        """ 
        tableA.add_biscuit('read',  tableA.PERMISSION.SELECT )
        tableA.add_biscuit('write', tableA.PERMISSION.SELECT, tableA.PERMISSION.INSERT, 
                                    tableA.PERMISSION.UPDATE, tableA.PERMISSION.DELETE,
                                    tableA.PERMISSION.MERGE )
        tableA.add_biscuit('admin', tableA.PERMISSION.ALL )
        
        tableA.save() # <-- Important!  Don't lose your keys, or you lose control of your table
        success, results = tableA.create()

        if success:  # load some records

            # generate some dummy data
            cols = ['MyID','MyName','MyDate']
            data = [[i, chr(64+i), f'2023-09-0{i}'] for i in list(range(1,10))]

            # insert 
            tableA.insert(columns=cols, data=data)

            # select rows, just for fun
            success, rows = tableA.select()
            pprint( rows )

            success, results = tableA.delete(where='MyID=6')

            # should be one less than last time
            success, rows = tableA.select()
            pprint( rows )
            


        # emulate starting over, loading from save file
        user_selection = tableA.recommended_filename
        tableA = None
        sxt = None 

        # reload from save file:
        sxt = SpaceAndTime()
        sxt.authenticate()

        tableA = SXTTable(from_file = user_selection, default_user=sxt.user)
        pprint( tableA )
        pprint( tableA.select() )


        # create a view 
        viewB = SXTView('SXTTEMP.MyTest_Odds', default_user=tableA.user, 
                        private_key=tableA.private_key, logger=tableA.logger)
        viewB.add_biscuit('read', viewB.PERMISSION.SELECT)
        viewB.add_biscuit('admin', viewB.PERMISSION.ALL) 
        viewB.table_biscuit = tableA.get_biscuit('admin')
        viewB.create_ddl = """
            CREATE VIEW {view_name} 
            {with_statement} 
            AS
            SELECT *
            FROM """ + tableA.table_name + """
            WHERE MyID in (1,3,5,7,9) """
        
        viewB.save() # <-- Important! don't lose keys!
        viewB.create()

        # the view will be created immediately, but there may be a small delay in seeing data
        # until end of 2023.
        
        input("""
            Now is your time to pause and play around... 
            after pressing enter, the script will drop objects 
            in order to clean up.
              
            Note, if you wait too long (>25min) the access_token will time-out
            and you'll need to tableA.user.authenticate() again. 
              """)

        viewB.drop()
        tableA.drop()

    print( tableA.recommended_filename )
    print( viewB.recommended_filename )
    print( sxt.user.recommended_filename )

    # Multiple Users, Multiple Tables
    suzy = SXTUser('.env', authenticate=True)

    bill = SXTUser()
    bill.load('.env')
    bill.authenticate()

    print('\nDifferent Logins? ', suzy.access_token != bill.access_token)

    # new user
    pat = SXTUser(user_id=f'pat_{randpad()}')
    pat.new_keypair()
    pat.api_url = suzy.api_url
    pat.save() # <-- Important! don't lose keys!
    pat.authenticate()

    # suzy to invite pat:
    if suzy.user_type in ['owner','admin']: 
        joincode = suzy.generate_joincode()
        success, results = pat.join_subscription(joincode=joincode)
        pprint( results )


    # emulate starting over
    pats_file = pat.recommended_filename
    pat = SXTUser(dotenv_file=pats_file)
    pat.authenticate()

    pass 
    
