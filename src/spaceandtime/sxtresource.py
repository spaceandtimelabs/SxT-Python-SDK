import logging, datetime, json, random
from pathlib import Path
from .sxtenums import SXTResourceType, SXTPermission, SXTKeyEncodings, SXTTableAccessType
from .sxtexceptions import SxTArgumentError, SxTFileContentError
from .sxtbiscuits import SXTBiscuit
from .sxtkeymanager import SXTKeyManager
from .sxtuser import SXTUser

class SXTResource():
    # child objects should override: self.__with__, has_with_statement(), self.resource_type

    logger: logging.Logger
    resource_type:SXTResourceType = SXTResourceType.UNDEFINED
    PERMISSION = SXTPermission
    create_ddl:str = ''
    user: SXTUser = None
    filepath: Path = ''
    application_name:str = ''
    biscuits = []
    start_time: datetime.datetime = None
    __rcn:str = ''
    __ddlt__:str = ''
    __allprops__: list = []
    __with__:str 


    def __init__(self, name:str=None, from_file:Path=None, default_user:SXTUser = None, 
                 private_key:str = None, new_keypair:bool = False, key_manager:SXTKeyManager = None,
                 application_name:str = None, logger:logging.Logger = None) -> None:
        if logger: 
            self.logger = logger 
        else: 
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
            if len(self.logger.handlers) == 0: 
                self.logger.addHandler( logging.StreamHandler() )
        if from_file: 
            self.load(from_file)
        else: 
            if name: self.resource_name = name
            if key_manager and type(key_manager)==SXTKeyManager:
                self.key_manager = key_manager
            else:
                self.key_manager = SXTKeyManager(private_key=private_key, new_keypair=new_keypair, logger=logger, encoding=SXTKeyEncodings.BASE64 )
            self.start_time = datetime.datetime.now()    
            self.biscuits = []    
        if default_user: self.user = default_user
        self.application_name = application_name
        self.__with__ = 'WITH "public_key={public_key}"'
        self.__allprops__ = [self.resource_type.value, 'start_time','resource_name','resource_type','resource_name_template',
                             'resource_private_key','resource_public_key','biscuits',
                             'with_statement', 'create_ddl_template','create_ddl']


    def __str__(self) -> str:
        line_formatter = lambda n,v: f"{str(n).rjust(20)} = {v}"
        biscuit_formatter = lambda n,v: f"\n{str(n)}: \n{v}"
        sql_formatter = lambda n,v: f"{'- '*30}\n{str(n)}: \n{v}\n"
        lines = list(self.to_list(True, 
                                  func_line_formatter=line_formatter, 
                                  func_biscuit_formatter=biscuit_formatter, 
                                  func_sql_formatter=sql_formatter))
        lines.insert(0,f"\n {'-'*11}{'='*10} {self.resource_name} {'='*10}{'-'*11}" )
        return '\n'.join(lines)

    def __repr__(self) -> str:
        line_formatter = lambda n,v: f"{str(n).rjust(20)} = {v}"
        biscuit_formatter = lambda n,v: f"{str(n)}: \n{v}\n"
        sql_formatter = lambda n,v: f"{'- '*30}\n{str(n)}: \n{v}\n"
        lines = list(self.to_list(False, 
                                  func_line_formatter=line_formatter, 
                                  func_biscuit_formatter=biscuit_formatter, 
                                  func_sql_formatter=sql_formatter))
        lines.insert(0,f"\n {'-'*10}{'='*10} {self.resource_name} {'='*10}{'-'*10}" )
        return '\n'.join(lines)


    @property
    def private_key(self) ->str :
        return self.key_manager.private_key
    @private_key.setter
    def private_key(self, value):
        self.key_manager.private_key = value 
        self.__bt = ''

    @property
    def public_key(self) ->str :
        return self.key_manager.public_key
    @public_key.setter
    def public_key(self, value):
        self.key_manager.public_key = value 

    @property
    def encoding(self) ->str :
        return self.key_manager.encoding
    @encoding.setter
    def encoding(self, value):
        self.key_manager.encoding = value     

    @property
    def resource_name_template(self) -> str:
        return self.__rcn
    @resource_name_template.setter
    def resource_name_template(self, value):
        self.__rcn = value 

    @property
    def resource_name(self) -> str:
        tmpprops = [k for k in self.__allprops__ if k not in ['resource_name','biscuits','create_ddl',self.resource_type.value, 'with','with_statement']]
        return self.replace_all(self.__rcn, self.to_dict(False, tmpprops) )
    @resource_name.setter
    def resource_name(self, value):
        self.__rcn = value 

    @property
    def recommended_filename(self) -> Path:
        filename = f'./resources/{str(self.resource_type.name).lower()}--{self.resource_name}' 
        filename = f"{filename}--v{self.start_time.strftime('%Y%m%d%H%M%S')}.sql"
        return Path(filename)

    @property
    def create_ddl(self) -> str:
        tmpprops = [k for k in self.__allprops__ if k not in ['biscuits','create_ddl']]
        ddl = self.replace_all( mainstr= self.create_ddl_template, replace_map = self.to_dict(False, tmpprops) ).rstrip()
        if self.has_with_statement(ddl): return ddl 
        if ddl[-1:] == ';': ddl = ddl[:-1]
        return f'{ddl} \n{self.with_statement}'
    @create_ddl.setter
    def create_ddl(self, value):
        self.__ddlt__ = str(value)
    
    @property
    def create_ddl_template(self) -> str:
        return str(self.__ddlt__)
    @create_ddl_template.setter
    def create_ddl_template(self, value):
        self.__ddlt__ = str(value)
        
    @property
    def with_statement(self) -> str:
        tmpprops = [k for k in self.__allprops__ if k not in ['biscuits','create_ddl','create_ddl_template','with','with_statement']]
        tmpencoding = self.key_manager.encoding
        if tmpencoding != SXTKeyEncodings.HEX: self.key_manager.encoding = SXTKeyEncodings.HEX
        rtn = self.replace_all(self.__with__, self.to_dict(False, tmpprops) )
        if tmpencoding != SXTKeyEncodings.HEX: self.key_manager.encoding = tmpencoding
        return rtn 
    
    @property
    def create_ddl_sample(self) -> str:
        return """
        CREATE TABLE {table_name} 
        ( MyID         int
        , MyName       varchar
        , MyDate       date
        , Primary Key  (MyID) 
        ) {with_statement} """


    def new_keypair(self) -> dict:
        """--------------------
        Generate a new ED25519 keypair, set class variables and return dictionary of values.

        Returns: 
            dict: New keypair values

        Examples: 
            >>> resourceA.new_keypair()
            >>> len( resourceA.private_key )
            44
            >>> resourceA.key_manager.encoding = SXTKeyEncodings.HEX
            >>> len( resourceA.private_key )
            64
         """
        return self.key_manager.new_keypair()


    def add_biscuit_object(self, biscuit_object:SXTBiscuit) -> SXTBiscuit:
        self.biscuits.append(biscuit_object)
        return biscuit_object


    def add_biscuit(self, name:str = '', *permissions) -> SXTBiscuit:
        if not self.private_key:
            raise SxTArgumentError('Resource requires a private key to be set before making new biscuits.', logger=self.logger)
        biscuit = SXTBiscuit(name=name, private_key=self.private_key, logger=self.logger )
        biscuit.add_capability(self.resource_name, *permissions)
        self.biscuits.append(biscuit)
        return biscuit
    

    def get_biscuit(self, by_name:str) -> list:
        return  [b for b in self.biscuits if b.name == by_name]

            
    def clear_biscuits(self):
        self.biscuits = []        


    def replace_all(self, mainstr:str, replace_map:dict = None) -> str:
        if not replace_map: replace_map = {}
        if 'date' not in replace_map.keys(): replace_map['date'] = int(self.start_time.strftime('%Y%m%d'))
        if 'time' not in replace_map.keys(): replace_map['time'] = int(self.start_time.strftime('%H%M%S'))
        if 'resource_public_key'  in replace_map.keys(): replace_map['public_key']  = replace_map['resource_public_key']
        if 'resource_private_key' in replace_map.keys(): replace_map['private_key'] = replace_map['resource_private_key']
        # if 'with_statement' in replace_map.keys(): replace_map['with'] = replace_map['with_statement']
        for findname, replaceval in replace_map.items():
            mainstr = str(mainstr).replace('{'+str(findname)+'}', str(replaceval))                    
        return mainstr


    def to_json(self, obscure_private_key:bool = True, omit_keys:list = []) -> json:
        """--------------------
        Returns a json document containing relevent information from the Resource object.

        Args:
            obscure_private_key (bool): If True will only display first 6 characters of private keys.
            omit_keys (list): List of key names to exclude from the return. 
            
        Returns:
            json: JSON representation of the class.
        """
        return json.dumps(self.to_dict(obscure_private_key=obscure_private_key, omit_keys=omit_keys))
    

    def to_dict(self, obscure_private_key:bool = True, include_keys:list = []) -> dict:
        """--------------------
        Returns a dictionary object containing relevent information from the Resource object.

        Args:
            obscure_private_key (bool): If True will only display first 6 characters of private keys.
            include_keys (list): List of key names to include in the return.  Defaults to all keys.
            
        Returns:
            dict: Curated dictionary of relevent values in the class.
        """
        if include_keys ==[]: include_keys = self.__allprops__
        rtn = {}
        for prop in include_keys:
            match prop:
                case 'resource_type':  rtn[prop] = self.resource_type.name
                case self.resource_type.value: rtn[prop] = self.resource_name
                case 'resource_private_key': rtn[prop] = self.private_key[:6]+'...' if obscure_private_key else self.private_key
                case 'resource_public_key': rtn[prop] = self.public_key
                case 'with_statement': 
                    rtn[prop] = self.with_statement
                    rtn['with'] = self.with_statement
                case 'start_time': 
                    rtn[prop] = self.start_time.strftime('%Y-%m-%d %H:%M:%S')
                    rtn['date'] = int(self.start_time.strftime('%Y%m%d'))
                    rtn['time'] = int(self.start_time.strftime('%H%M%S'))
                case 'biscuits': 
                    rtn[prop] = {}
                    for bis in self.biscuits:
                        if bis and type(bis) == SXTBiscuit:
                            rtn[prop][bis.name] = bis.biscuit_token
                case _:
                    rtn[prop] = getattr(self, prop, str('')) 
                    if type(rtn[prop]) == SXTTableAccessType: rtn[prop] = rtn[prop].value
        return  rtn
    

    def to_list(self, obscure_private_key:bool = True, 
                include_keys:list = [],
                func_line_formatter = lambda n,v: f'{n}={v}', 
                func_biscuit_formatter = lambda n,v: f'{n}_biscuit_token={v}',
                func_sql_formatter = lambda n,v: f'{n}\n:{v}') -> list:
        """------------------
        Returns a list object containing relevent information from the Resource object, with name/value formatted to one line.

        Args:
            obscure_private_key (bool): If True will only display first 6 characters of private keys
            omit_keys (list): List of key names to exclude from the return
            func_line_formatter (function): Function that accepts two parameters (name, value) and returns a single string. Defaults to lambda n,v: f'{n}={v}' 
            func_biscuit_formatter (function): Same as line_formatter, but used specifically for any biscuit nested objects found
            func_sql_formatter (function): Same as line_formatter, but used specifically for any names containing 'ddl' or 'sql'
            
        Returns:
            list: List representation of the class.
        """
        rtn = []
        for n,v in self.to_dict(obscure_private_key=obscure_private_key, include_keys=include_keys).items():
            if n=='biscuits':
                for bname, token in dict(v).items():
                    rtn.append(func_biscuit_formatter(bname, token))
            elif 'ddl' in n or 'sql' in n:
                rtn.append(func_sql_formatter(n,v))
            else:
                rtn.append(func_line_formatter(n,v))
        return rtn


    def get_first_valid_user(self, *users) -> SXTUser:
        users = [user for user in list(users) + [self.user] if type(user) == SXTUser and not user.access_expired]
        if users == []:
            raise SxTArgumentError('SXT authenticated User must be provided as an argument to create the resource.', logger=self.logger)
        return users[0]
    

    def create(self, sql_text:str = None, user:SXTUser = None, biscuits:list = None):
        """--------------------
        Issues the supplied (parameterized) CREATE statement to the Space and Time network, and report back success and details.

        Args:
            sql_text (str): Parameterized CREATE statement.  If omitted, will use the resource.create_ddl class property.  Both will replace {placeholders} with real values before submission.
            user (SXTUser): Authenticated user who will issue the command.  If omitted, will use the default user, resource.user
            biscuits (list): List of biscuits to include with the request, either as string biscuit tokens or as SXTBiscuit objects.  If omitted, will use the class.biscuits list.  Must contain CREATE permissions. 

        Returns: 
            bool: Success flag, True if the object was created.
            object: other details supplied during the request, including API messaging. Typically a dict.
        """
        user = self.get_first_valid_user(user)
        if not sql_text: 
            if self.create_ddl_template == '':
                raise SxTArgumentError('Must set the create_ddl before trying to create the table.', logger=self.logger)
            sql_text = self.create_ddl
        if self.private_key == '': 
            raise SxTArgumentError('Must create or set a keypair before trying to create the table.  Try running new_keypair().', logger=self.logger)
        if not biscuits: biscuits = self.biscuits if type(self.biscuits)==list else [self.biscuits]
        if biscuits == []: 
            self.logger.warning('No biscuits found. While this may be OK, it can also cause errors.', logger=self.logger)
        success, result = user.base_api.sql_ddl(sql_text=sql_text.strip(), biscuits=biscuits, app_name=self.application_name)
        if success: 
            self.logger.info(f'{self.resource_type.name} Created: {self.resource_name}:\n{sql_text}')
        else:
            self.logger.error(f'{self.resource_type.name} FAILED TO CREATE with user {user.user_id}:\n{result}\n{sql_text}\n\nBiscuits: {biscuits}')
        return success, result


    def drop(self, user:SXTUser = None, biscuits:list = None):
        """--------------------
        Issues the supplied (parameterized) DROP statement to the Space and Time network, and report back success and details.

        Args:
            user (SXTUser): Authenticated user who will issue the command.  If omitted, will use the default user, resource.user
            biscuits (list): List of biscuits to include with the request, either as string biscuit tokens or as SXTBiscuit objects.  If omitted, will use the class.biscuits list.  Must contain DROP permissions. 

        Returns: 
            bool: Success flag, True if the object was dropped.
            object: other details supplied during the request, including API messaging. Typically a dict.
        """
        self.logger.info(f'{"-"*15}\nDROPPING {self.resource_type.name}: {self.resource_name}...')
        user = self.get_first_valid_user(user)
        if not biscuits: biscuits = list(self.biscuits) 
        if biscuits == []: 
            raise SxTArgumentError('A biscuit with DROP must be included.', logger=self.logger)
        sql_text = f'DROP {self.resource_type.name} {self.resource_name}' 
        success, result = user.base_api.sql_ddl(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name)
        if success: 
            self.logger.info(f'       DROPPED: {self.resource_name}')
        else:
            self.logger.error(f'{self.resource_type.name} FAILED TO DROP with user {user.user_id}:\n{result}\n{sql_text}')
        return success, result
        

    def select(self, sql_text:str = '', columns:list = ['*'], user:SXTUser = None, biscuits:list = None, row_limit:int = 20) -> json:
        """--------------------
        Issues a SELECT statement to the Space and Time network, and report back success and rows (or failure details).

        This is intended as a convenience feature, to quickly verify data structures or recently loaded data.  While it can 
        run more sophisticated SQL, it is recommended to use the SXTUser object for more flexibility.

        Args:
            sql_text (str): Sql text to execute.  If omitted, will defaults to "SELECT [columns] FROM [resource_name] LIMIT [row_limit]".
            columns (list): List of columns to build the SELECT statement.  Defaults to "*".  If sql_text is supplied, this is ignored.
            user (SXTUser): Authenticated user who will issue the command.  If omitted, will use the default user, resource.user
            biscuits (list): List of biscuits to include with the request, either as string biscuit tokens or as SXTBiscuit objects.  If omitted, will use the class.biscuits list.  
            row_limit (int): Limits the number of rows returned. 

        Returns: 
            bool: Success flag, True if the object was dropped.
            object: Row output of the SQL request, in JSON format, or if error, details returned from the request.

        Examples: 
            >>> suzy = SXTUser('.env', authenticate=True)
            >>> ethblocks = SXTTable(name='ETHEREUM.Blocks', default_user=suzy)
            >>> success, rows = ethblocks.select (columns = 'BLOCK_NUMBER', row_limit = 10)
            >>> len( rows )
            10
            >>> len(rows[0].keys())
            11
        """
        self.logger.info(f'{"-"*15}\nSELECTing {self.resource_type.name} {self.resource_name}...')
        user = self.get_first_valid_user(user)
        if not biscuits: biscuits = list(self.biscuits) 
        if biscuits == []: 
            self.logger.warning('No biscuits found. While this may be OK, it can also cause errors.')
        if sql_text == '': sql_text = f"SELECT { ','.join( columns ) } FROM {self.resource_name} LIMIT {row_limit}"
        self.logger.info(f'{self.resource_type.name} Query Started: {self.resource_name}:\n{sql_text}')
        success, result = user.base_api.sql_dql(sql_text=sql_text, biscuits=biscuits, resources=self.resource_name, app_name=self.application_name)
        if success: 
            self.logger.info(f'{self.resource_type.name} {self.resource_name} Finished: {len(result)} Rows Returned')
        else:
            self.logger.error(f'{self.resource_type.name} QUERY FAILED with user {user.user_id}:\n{result}\n{sql_text}')
        return success, result

    
    def clear_all(self) -> None:
        """Clears all content from the object. It is HIGHLY RECOMMENDED you save() before a clear_all(), to prevent key loss. No arguments and None returned."""
        self.clear_biscuits()
        props = [p for p in self.__allprops__ if p not in ['resource_type','with_statement']]
        for prop in props:
            setattr(self, prop, '')
        self.start_time = datetime.datetime.now()
        self.key_manager = SXTKeyManager(logger=self.logger, encoding=SXTKeyEncodings.BASE64)
        # TODO: add a 'dirty' flag, and warn if not saved
        self.logger.info(f'{self.resource_type.name} resource has been cleared.')
        return None 
        

    def __filestarts__(self, folderfilepath:Path) -> Path:
        if Path(folderfilepath).exists(): return Path(folderfilepath)
        folderfilepath = Path(folderfilepath).resolve()
        files = sorted([str(file) for file in list(Path(folderfilepath.parent).iterdir()) if str(Path(file).name).startswith(folderfilepath.name)])
        return Path(files[-1:][0]) if len(files) > 0 else None         


    def load(self, filepath:Path, find_latest:bool = False ):
        """--------------------
        Loads Resource file *WITH PRIVATE KEYS* to the current object, overwriting all current values.

        The load is expecting a plain-text file in a shell-loadable format, meaning you can run the input file in a 
        terminal /shell, and it will load into environment variables.  This is the same file that the save() function
        produces.  Any NAME=Value format is translated into object variables, including heredocs using the EOM marker.
        For examples, look at the save() file produced.  To prevent losing keys, it is recommended you always
        save() before you load().
        
        Args:
            filepath (Path): File to load into object.
            find_latest (bool): If True, will accept incomplete filename and search the parent folder for the last matching. This works well in tandum with the recommended_filename to load the most recent file. Defaults to False (off).

        Returns: 
            bool: True if load was successful, False if not. 

        """
        self.clear_all()
        filepath = self.__filestarts__(filepath) if find_latest else Path(filepath)
        if not filepath or not filepath.exists():
            raise FileNotFoundError(f'Resource file not found: {filepath}')

        try:    
            # load and clean file content
            with open(Path(filepath).resolve()) as fh: 
                lines = fh.read().replace('\nEOM\n)\n','\n::E::').replace('$(cat << EOM','::S::').split('\n')
                lines = [l for l in lines if not (l.strip()=='' 
                                            or l.startswith('#') 
                                            or l.startswith('DATE=') 
                                            or l.startswith('TIME=') 
                                            or l.startswith('WITH=')
                                            or l.startswith('WITH_STATEMENT=')
                                            or l.startswith('RESOURCE_TYPE=') 
                                            or l.startswith('RESOURCE_PUBLIC_KEY=')  )]
                
            # loop thru and build dict to control load
            loadmap = {}
            multiline = None
            lines = iter(lines) # so we can do next()
            for line in lines:
                eq = line.find('=')
                name  = line[:eq]
                value = line[eq+1:]
                if value[:1]=='"' and value[-1:]=='"': value = value[1:-1]
                if  '::S::' in value: 
                    multiline = []
                    mline = ''
                    while True:
                        mline = next(lines, '')
                        if '::E::' in mline: break
                        multiline.append( mline )
                    value = '\n'.join(multiline)
                loadmap[name.lower()] = value
                
            # with loadmap, load into object (sorted, to prevent create_ddl / _template overwriting)
            loadmap = {k:loadmap[k] for k in sorted(list(loadmap.keys()))} 
            for name, value in loadmap.items():
                if name == 'start_time':
                    setattr(self, name, datetime.datetime.strptime(value, '%Y-%m-%d %H:%M:%S') )
                elif name == 'resource_private_key':
                    self.key_manager = SXTKeyManager(private_key=value, encoding=SXTKeyEncodings.BASE64, logger=self.logger)
                elif name.endswith( '_biscuit_token'):
                    if type(self.biscuits) != list:  self.biscuits = []
                    self.biscuits.append(SXTBiscuit(name=name.replace('_biscuit_token',''), logger=self.logger, 
                                                    private_key=self.private_key,
                                                    biscuit_token= value))
                else:
                    setattr(self, name, value)
            return True
        except Exception as ex:
            err = ex
        raise SxTFileContentError(f'Failed to load file {filepath}: {err}')
                

    def save(self, filepath:Path = None):
        """--------------------
        Saves Resource file *WITH PRIVATE KEYS* to the specified filepath.  Will not overwrite.

        The format saved is a plain-text file in a shell-loadable format, meaning you can run the output file in a 
        terminal /shell, and it will load into environment variables.  This format can also be loaded into the python 
        SDK using the load() command. To prevent lost keys, this process will specifically NOT OVERWRITE files. It is 
        best practice to version files as needed and keep history.
        
        Args:
            filepath (Path): Where to save the file. If filepath is None, it will use the object's recommended_filename.

        Returns: 
            bool: True if save was successful, False if not. 

        """
        filepath = Path(filepath) if filepath else Path(self.recommended_filename)
        line_formatter = lambda n,v: f'{str(n).upper()}="{v}"'
        biscuit_formatter = lambda n,v: f'{str(n).upper()}_BISCUIT_TOKEN="{v}"'
        sql_formatter = lambda n,v: f'{str(n).upper()}=$(cat << EOM\n{v}\nEOM\n)\n'
        lines = list(self.to_list(obscure_private_key=False,
                                  func_line_formatter=line_formatter, 
                                  func_biscuit_formatter=biscuit_formatter, 
                                  func_sql_formatter=sql_formatter,
                                  include_keys=[p for p in self.__allprops__ if p not in ['with','with_statement']]))
        lines.insert(0, f'# -- Resource File for  {self.resource_name}')
        lines.insert(1, f'# -- this file can be executed as a shell script to set environment variables')
        for i, line in enumerate(lines):
            if str(line).startswith('CREATE_DDL'): 
                lines.insert(i, '# -- SQL:')
                break
        for i, line in enumerate(lines):
            if 'BISCUIT_TOKEN' in line:
                lines.insert(i, '# -- BISCUITS:')
                break
        fp = Path(self.replace_all(str(filepath), self.to_dict(False))).resolve()
        self.logger.info(f'Saving Resource File: {fp}')
        if fp.exists():
            self.logger.error(f'File Exists: {fp.resolve()}\nTo minimize lost keys, file over-writes are not allowed.')
            raise FileExistsError('To minimize lost keys, file over-writes are not allowed.')
        else:
            if not fp.parent.exists(): fp.parent.mkdir(parents=True, exist_ok=True)
            try:
                with open(fp.resolve(), 'w') as fh:
                    fh.write( '\n'.join(lines) )
            except Exception as ex:
                self.logger.error(f'Error while saving Resource File: {ex}')
                return False 
        return True


    def has_with_statement(self, create_ddl:str) ->bool:
        """-------------------
        Returns True/False as to whether supplied Create Resource SQL has a WITH statement.
        
        Args:
            create_ddl (str): The Create Resource DDL / SQL to analyze for a WITH statement.

        Returns: 
            bool: True if the WITH statement was found, FALSE if not. 
        """
        create_ddl = create_ddl.replace('{with_statement}','').replace('{with}','')
        if 'with' not in create_ddl.lower(): return False
        r6 = '' # rolling 6 chars
        for i in range(len(create_ddl)-6, 0, -1):
            r6 = create_ddl[i:i+6]
            if r6[1:5].lower() == 'with' and not r6[0:1].isalnum() and not r6[5:6].isalnum(): return True
            if r6[0:1] == ')': return False
        return False




class SXTTable(SXTResource):
    access_type: SXTTableAccessType 

    def __init__(self, name:str='', from_file:Path=None, default_user:SXTUser = None, 
                 private_key:str = '', new_keypair:bool = False, key_manager:SXTKeyManager = None,
                 access_type:SXTTableAccessType = SXTTableAccessType.PERMISSSIONED,
                 application_name:str = None, logger:logging.Logger = None) -> None:
        self.resource_type = SXTResourceType.TABLE    
        super().__init__(name, from_file, default_user, private_key, new_keypair, key_manager, application_name, logger)
        self.access_type = access_type
        self.__allprops__.insert(2, 'access_type')
        self.__with__= 'WITH "public_key={public_key}, access_type={access_type}"'
        
    @property
    def table_name(self) ->str:
        return self.resource_name
    @table_name.setter
    def table_name(self, value):
        self.resource_name = value


    def get_column_names(self) -> dict:
        """Returns a dictonary of column_name : data_type as defined in the create_ddl.
        
        Useful when an iterable list of columns (and types) is required, such as building 
        INSERT statements or view SELECT lists.  Order should be preserved, although as a dict 
        object type, this is technically not gauranteed.
        """
        rtn = {}

        # prep ddl to isolate columns 
        ddl = str(self.create_ddl).replace('\t',' ').replace('\n',' ').strip()
        while '  ' in ddl: ddl = ddl.replace('  ',' ')
        first_paren = ddl.find('(')+1
        for i in range(len(ddl), 1, -1):
            if ddl[i:i+1] == ')': 
                last_paren = i 
                break
        
        # process columns
        cols = [c.strip() for c in ddl[first_paren:last_paren].split(',') ]
        for col in cols:
            if col.lower().startswith('primary key'): continue
            colname = col.split(' ')[0]
            coltype = col.split(' ')[1]
            rtn[colname] = coltype

        return rtn 


    def insert(self, sql_text:str = None, columns:list = None, data:list = None, user:SXTUser = None, biscuits:list = None):
        """-----------------
        Inserts records into the table, in one DML request per 1000 rows.

        The process uses a column list and data list (rather than a single dictionary) because the multi-row 
        insert syntax requires a single column definition, with all data rows expected to follow that same 
        order and completeness. This also adheres better to common high-volumn analytic formats like CSV, 
        where repeating column definitions becomes onerous.  NOTE: this submits in 1000 row transactions, 
        so it is possible to have partially successful loads (in 1000 row chunks). Once any part insert fails
        the holistic process stops and reports an error, and reports Success = False.

        Args:
            sql_text (str): If set, columns and data are ignored and this SQL text is simply passed thru to the network directly as a DML request.
            columns (list): List of columns to build the INSERT statement. Order must match the data list.
            data (list): List of data that matches the columns order.  
            user (SXTUser): User who will execute the request. Defaults to the default user.
            biscuits (list): List of biscuits required to authorize this request. 

        Returns: 
            bool: Success flag, True if the data was fully inserted, False if any of the records failed.
            object: Row output of the SQL request, in JSON format, or if error, details returned from the request.
        """
        user = self.get_first_valid_user(user)
        if not biscuits: biscuits = list(self.biscuits) 
        if biscuits == []: 
            raise SxTArgumentError('A biscuit with INSERT permissions must be included.', logger=self.logger)
        if not sql_text:
            while data !=[]:
                sql_text_prefix = f"INSERT INTO {self.table_name} ({ ', '.join(columns) }) VALUES \n"
                sql_text_rows = []
                for row in data[:999]:
                    sql_text_rows.append( "('" + str("', '").join([str(val) for val in row]) + "')" )
                sql_text = sql_text_prefix + ',\n'.join(sql_text_rows)
                success, response = user.base_api.sql_dml(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name,resources=[self.table_name])
                data = data[999:]
            if not success: 
                msg = 'NOTE: data may have been left in a partially inserted state.'
                response['warning'] = msg
                self.logger.error(msg)
                return success, response
        else: # manual sql_text
            success, response = user.base_api.sql_exec(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name)
        return success, response


    def delete(self, sql_text:str = None, where:str = '0=1', user:SXTUser = None, biscuits:list = None):
        """--------------------
        Deletes records from the table, with a required WHERE statement.

        Note, some tables in the space and time network are immutable and cannot be changed.

        Args: 
            sql_text (str): If set, the sql_text is simply passed thru to the network directly as a DML request.
            where (str): A WHERE statement to limit rows deleted. This defaults to a zero-delete statement, so must be overriden to execute a meaningful delete. 
            user (SXTUser): User who will execute the request. Defaults to the default user.
            biscuits (list): List of biscuits required to authorize this request. 

        Returns: 
            bool: Success flag, True if the data was fully inserted, False if any of the records failed.
            object: Row output of the SQL request, in JSON format, or if error, details returned from the request.
        """
        user = self.get_first_valid_user(user)
        if not biscuits: biscuits = list(self.biscuits) 
        if biscuits == []: 
            raise SxTArgumentError('A biscuit with DELETE permissions must be included.', logger=self.logger)
        if len(where) >0 and not str(where).strip().startswith('where'): where = f' WHERE {where} '
        if not sql_text: sql_text = f"DELETE FROM {self.table_name} {where}"
        return user.base_api.sql_dml(sql_text=sql_text, biscuits=biscuits, app_name=self.application_name, resources=[self.table_name])

    



class SXTView(SXTResource):
    def __init__(self, name:str='', from_file:Path=None, default_user:SXTUser = None, 
                 private_key:str = '', new_keypair:bool = False, key_manager:SXTKeyManager = None,
                 application_name:str = None, logger:logging.Logger = None) -> None:
        self.resource_type = SXTResourceType.VIEW
        super().__init__(name, from_file, default_user, private_key, new_keypair, key_manager, application_name, logger)
        self.__with__= ' WITH "public_key={public_key}" '
        
    @property
    def view_name(self) -> str:
        return self.resource_name
    @view_name.setter
    def view_name(self, value):
        self.resource_name = value

    @property
    def table_biscuit(self) -> SXTBiscuit:
        rtn = [b for b in self.biscuits if b.__parentbiscuit__]
        if len(rtn) >0: 
            return rtn[0]
        else: 
            return None
    @table_biscuit.setter
    def table_biscuit(self, value):
        if type(value) == list and len(value) >0: value = value[0]
        if len(value)==0: return None
        if not type(value) == SXTBiscuit: 
            raise SxTArgumentError('Table_biscuit must be of type SXTBiscuit or a list of SXTBiscuits.')
        for biscuit in self.biscuits:
            if biscuit.__parentbiscuit__: biscuit=None 
        self.biscuits = [b for b in self.biscuits if b]
        value.__parentbiscuit__ = True
        self.biscuits.append(value) 

    @property
    def create_ddl_sample(self) -> str:
        return """
        CREATE VIEW {view_name} 
        {with_statement} 
        AS
        SELECT *
        FROM MySchema.MyTable """
    
    def has_with_statement(self, create_ddl:str) ->bool:
        """-------------------
        Returns True/False as to whether supplied Create Resource SQL has a WITH statement.
        
        Args:
            create_ddl (str): The Create Resource DDL / SQL to analyze for a WITH statement.

        Returns: 
            bool: True if the WITH statement was found, FALSE if not. 
        """
        create_ddl = create_ddl.lower().strip().replace('\n',' ').replace('\t',' ').replace('   ',' ').replace('  ',' ').replace('  ',' ')
        if '{with_statement}' in create_ddl or '{with}' in create_ddl: return True
        if 'with' not in create_ddl.lower(): return False
        pass 
        r6 = '' # rolling 6 chars
        for i in range(0, len(create_ddl)-6, 1):
            r6 = create_ddl[i:i+6]
            if r6[1:5].lower() == 'with' and not r6[0:1].isalnum() and not r6[5:6].isalnum(): return True
            if r6[1:5].lower() == ' as ': return False
        return False
    



class SXTMaterializedView(SXTResource):
    __ri__: int 

    def __init__(self, name:str='', from_file:Path=None, default_user:SXTUser = None, 
                 private_key:str = '', new_keypair:bool = False, key_manager:SXTKeyManager = None,
                 application_name:str = None, logger:logging.Logger = None) -> None:
        self.resource_type = SXTResourceType.MATERIALIZED_VIEW
        super().__init__(name, from_file, default_user, private_key, new_keypair, key_manager, application_name, logger)
        self.__ri__ = 1440
        self.__allprops__.insert(2, 'refresh_interval')
        self.__with__= ' WITH "public_key={public_key} , refresh_interval={refresh_interval}" '
        
    @property
    def matview_name(self) ->str:
        return self.resource_name
    @matview_name.setter
    def matview_name(self, value):
        self.resource_name = value

    @property
    def refresh_interval(self) -> int:
        return self.__ri__
    @refresh_interval.setter
    def refresh_interval(self, value):
        if value >= 1440: 
            self.__ri__ = value 
        else:
            raise SxTArgumentError('Current limit to a Materialized View refresh is once every 24 hours // 1440 minutes', logger=self.logger)

    @property
    def create_ddl_sample(self) -> str:
        return """
        CREATE MATERIALIZED VIEW {view_name} 
        {with_statement} 
        AS
        SELECT *
        FROM MySchema.MyTable """
    
    def has_with_statement(self, create_ddl:str) ->bool:
        """-------------------
        Returns True/False as to whether supplied Create Resource SQL has a WITH statement.
        
        Args:
            create_ddl (str): The Create Resource DDL / SQL to analyze for a WITH statement.

        Returns: 
            bool: True if the WITH statement was found, FALSE if not. 
        """
        create_ddl = create_ddl.lower().strip().replace('\n',' ').replace('\t',' ').replace('   ',' ').replace('  ',' ').replace('  ',' ')
        if '{with_statement}' in create_ddl or '{with}' in create_ddl: return True
        if 'with' not in create_ddl.lower(): return False
        pass 
        r6 = '' # rolling 6 chars
        for i in range(0, len(create_ddl)-6, 1):
            r6 = create_ddl[i:i+6]
            if r6[1:5].lower() == 'with' and not r6[0:1].isalnum() and not r6[5:6].isalnum(): return True
            if r6[1:5].lower() == ' as ': return False
        return False
    




if __name__ == '__main__':
    from pprint import pprint
    print('\n', '-=-='*10, '\n' )

    # Create a user and authenticate:
    suzy = SXTUser('.env', authenticate=True)


    # Create a table, using a new keypair
    tableA = SXTTable(name='SXTTEMP.New_TableName', new_keypair=True, default_user=suzy)
    tableA.add_biscuit('Read', tableA.PERMISSION.SELECT)
    tableA.add_biscuit('Load', tableA.PERMISSION.SELECT, tableA.PERMISSION.INSERT, tableA.PERMISSION.UPDATE, tableA.PERMISSION.DELETE, tableA.PERMISSION.MERGE)
    tableA.add_biscuit('Admin', tableA.PERMISSION.ALL)
    tableA.create_ddl = """
        CREATE TABLE {table_name} 
        ( MyID         int
        , MyName       varchar
        , MyDate       date
        , Primary Key  (MyID) 
        )  
    """
    print( tableA.get_column_names() )

    tableA.save()  # save to local file, to prevent lost keys
    success, results = tableA.create()  # Create table on Space and Time network
    

    if success:

        # generate some dummy data
        cols = ['MyID','MyName','MyDate']
        data = [[i, chr(64+i), f'2023-09-0{i}'] for i in list(range(1,10))]

        # perform insert
        tableA.insert(columns=cols, data=data)
        tableA.insert(sql_text= f"Insert into {tableA.table_name} values (20, 'manual test', '2023-01-01')" )

        # select records back, just to verify
        success, results = tableA.select()
        pprint(results if success else f'Error! {results}')


        # create a view based on the above table, with the same keys
        viewA = SXTView(name="SXTTEMP.New_ViewName", default_user=suzy, private_key=tableA.private_key)
        viewA.add_biscuit('Admin', viewA.PERMISSION.ALL)
        viewA.table_biscuit = tableA.get_biscuit('Admin')
        viewA.create_ddl = "CREATE VIEW {view_name} {with_statement} AS SELECT * from " + tableA.table_name
        
        success, results = viewA.create()
        pprint(f'Success! {results}' if success else f'Error! {results}')

        if success:
            success, results = viewA.select()
            pprint(results if success else f'Error! {results}')
        
        # drop the view
        success, results = viewA.drop() 
        pprint(f'Success! {results}' if success else f'Error! {results}')

    # drop the table
    success, results = tableA.drop()
    print( f'success?  {success}\nData: {results}' )




    # find the latest save file, load it, and perform a drop (in cases it was interrupted above):
    if False: 
        tableA = SXTTable(default_user=suzy)
        tableA.load(filepath = './resources/table--SXTTEMP.New_TableName--v202309271907',  find_latest = True)
        viewA = SXTView(name='SXTTEMP.New_ViewName', private_key=tableA.private_key, default_user=suzy)
        viewA.add_biscuit('admin', viewA.PERMISSION.ALL)
        viewA.table_biscuit = tableA.get_biscuit('admin')
        success, result = viewA.drop()
        success, result = tableA.drop()

    pass 