import logging, json
from pathlib import Path
from datetime import datetime, timedelta
from biscuit_auth import KeyPair, PrivateKey, PublicKey, Authorizer, Biscuit, BiscuitBuilder, BlockBuilder, Rule, DataLogError
from .sxtexceptions import SxTArgumentError, SxTFileContentError, SxTBiscuitError, SxTKeyEncodingError
from .sxtenums import SXTPermission, SXTKeyEncodings
from .sxtkeymanager import SXTKeyManager



class SXTBiscuit():
    """Definition of a single biscuit."""

    logger: logging.Logger = None 
    domain: str = 'sxt'
    name: str = 'biscuit_name'
    key_manager: SXTKeyManager = None
    GRANT = SXTPermission
    ENCODINGS = SXTKeyEncodings
    __cap:dict = {'schema.resource':['permission1', 'permission2']}
    __usr:list = ['userA','userB']
    __time:list = [ [datetime.now(), datetime.now() + timedelta(30)] ]
    __bt: str = ''
    __btchanged:bool = True
    __lastresource: str = ''
    __manualtoken:bool = False
    __parentbiscuit__:bool = False
    
    def __init__(self, name:str = '', private_key: str = None, new_keypair: bool = False, from_file: Path = None, logger:logging.Logger = None, biscuit_token:str = None) -> None:
        if logger: 
            self.logger = logger 
        else: 
            self.logger = logging.getLogger()
            self.logger.setLevel(logging.INFO)
            if len(self.logger.handlers) == 0: 
                self.logger.addHandler( logging.StreamHandler() )
        self.logger.info('-'*30 + '\nNew SXT Biscuit initiated')
        self.key_manager = SXTKeyManager(logger=self.logger, encoding=SXTKeyEncodings.BASE64)
        if new_keypair: self.key_manager.new_keypair()
        if private_key: self.private_key = private_key
        self.__cap = {}
        self.__usr = []
        self.__time = []
        if name: self.name = name 
        if from_file and Path(from_file).exists: self.load(from_file)
        if biscuit_token: 
            self.__manualtoken = True 
            self.__bt = biscuit_token
            self.logger.warning('manual biscuit token accepted as-is, not calculated or verified.')
            

    def __str__(self):
        return '\n'.join([f"{str(n).rjust(25)}: {v}" for n,v in  dict(self.to_json(True, True)).items()])
    
    def __repr__(self):
        return '\n'.join([f"{str(n).rjust(25)}: {v}" for n,v in  dict(self.to_json(False, True)).items()])

    def __len__(self):
        return 1

    @property
    def biscuit_text(self):
        bis = sorted([ f'check if {self.domain}:user("{u}");' for u in self.__usr]) 
        bis.extend( sorted( [ f'check if time($time), $time <= {t[0].strftime("%Y-%m-%dT%H:%M:%SZ")}, $time >= {t[1].strftime("%Y-%m-%dT%H:%M:%SZ")};' for t in self.__time] ))
        for resource, permissions in self.__cap.items():
            for permission in sorted([p.value for p in permissions]):
                bis.append(f'{self.domain}:capability("{permission}", "{str(resource).lower()}");')    
        return '\n'.join(bis)

        

    @property
    def biscuit_token(self) ->str:
        if self.__manualtoken: return self.__bt
        if not self.private_key or not self.biscuit_text: 
            self.__bt = ''
            return ''
        if self.__btchanged: self.__bt = self.regenerate_biscuit_token()
        return self.__bt
    
    @property
    def biscuit_json(self) -> dict:
        return self.__cap

    @property
    def private_key(self) ->str :
        return self.key_manager.private_key
    @private_key.setter
    def private_key(self, value):
        self.key_manager.private_key = value 
        self.__btchanged = True

    @property
    def public_key(self) ->str :
        return self.key_manager.public_key
    @public_key.setter
    def public_key(self, value):
        self.key_manager.public_key = value 
        self.__btchanged = True

    @property
    def encoding(self) ->str :
        return self.key_manager.encoding
    @encoding.setter
    def encoding(self, value):
        self.key_manager.encoding = value     


    def new_keypair(self) -> dict:
        return self.key_manager.new_keypair()


    def regenerate_biscuit_token(self) -> dict:
        """--------------------
        Regenerates the biscuit_token from class.biscuit_text and class.private_key. 

        For object consistency, this only leverages the class objects, so there are no arguments.  
        To build the biscuit_text, add_capability(), add_user_check(), or add_time_check, or if you want 
        to import an existing datalog file, you can load capabilities_from_text(). This function will 
        error without a valid private_key and biscuit_text.

        Args: 
            None

        Returns: 
            str: biscuit_token in base64 format. 
        """
        self.__btchanged = True

        if not self.private_key:
            raise SxTArgumentError("Private Key is required to create a biscuit", logger=self.logger)
        
        biscuit_text = self.biscuit_text 
        if not biscuit_text:
            raise SxTArgumentError('Biscuit_Text is required to create a biscuit. Try to add_capability() and inspect biscuit_text to verify.', logger=self.logger)

        try:
            private_key_obj = PrivateKey.from_hex(self.key_manager.private_key_to(SXTKeyEncodings.HEX))
            biscuit = BiscuitBuilder(self.biscuit_text).build(private_key_obj)
            self.__btchanged = False
            return biscuit.to_base64() 
        except DataLogError as ex:
            errmsg = ex
        raise SxTBiscuitError(errmsg, logger=self.logger)


    def validate_biscuit(self, biscuit_base64:str, public_key = None) -> str:
        if not public_key: public_key = self.public_key
        public_key = self.convert_key(public_key, self.get_encoding_type(public_key), SXTKeyEncodings.HEX )
        try:
            return Biscuit.from_base64( data=biscuit_base64, root=PublicKey.from_hex( public_key ))
        except Exception as ex:
            self.logger.error(ex)
        raise SxTBiscuitError('Biscuit not validated with Public Key', logger=self.logger)



    def add_time_check(self, start_datetime:datetime = None, end_datetime:datetime = None):
        """--------------------
        Uniquiely adds a valid time window to the biscuit, outside of which the biscuit is invalid.

        Args: 
            start_datetime (datetime): Beginning of valid time window. If omitted, defaults to now()
            end_datetime (datetime): End of valid time window. If omitted, defaults to 90 days in the future.

        Returns: 
            int: Number of checks added (1 or 0)

        Examples:
            >>> from datetime import datetime, timedelta
            >>> bb = SXTBiscuit()
            >>> bb.add_capability("Schema.TableA", bb.GRANT.SELECT)
            1
            >>> bb.add_time_check( datetime.now(), datetime.now() + timedelta(30) )
            1
            >>> bb.add_time_check( datetime.now(), datetime.now() + timedelta(30) )
            0
        """
        self.__btchanged = True

        if not start_datetime: start_datetime = datetime.now()
        if not end_datetime:   end_datetime = start_datetime + timedelta(90)
        
        final_times = [(start_datetime, end_datetime)]

        beginning_user_count = len(self.__time)
        final_times.extend( self.__time )
        final_times = list(set(final_times))
        ending_user_count = len(final_times)
        added_count = ending_user_count - beginning_user_count
        dup_count = 1 - added_count

        self.__time = [u for u in final_times]

        self.logger.info(f'Added {added_count} time frame{", " if added_count==1 else "s,"} from total 1 submitted ({dup_count} duplicate{"" if dup_count==1 else "s"})')
        return added_count


    def add_user_check(self, *users):
        """--------------------
        Uniquely adds a list of user checks to a biscuit, allowing only those users access.

        If a check is added, then the biscuit is only valid if all checks are satisfied.

        Args: 
            users (*): Any number of UserIDs, as strings or lists of strings, to enable for the biscuit.

        Returns: 
            int: Number of checks added (excluding duplicates)

        Examples:
            >>> bb = SXTBiscuit()
            >>> bb.add_capability("Schema.TableA", bb.GRANT.SELECT)
            1
            >>> bb.add_user_check("some_username")
            1
            >>> bb.add_user_check("some_other_username")
            1
            >>> bb.add_user_check("some_other_username")
            0
        """
        self.__btchanged = True
        
        final_users = []
        [final_users.extend(p) for p in users if type(p) == list ]
        [final_users.append(p) for p in users if type(p) == str]

        if len([p for p in users if type(p) != list and type(p) != str ]) != 0:
            msg = 'Can only add UserIDs as strings or list of strings.'
            self.logger.error(msg)
            raise KeyError(msg)

        beginning_user_count = len(self.__usr)
        submitted_count = len(final_users)
        final_users = list(set(final_users))
        unique_submitted_count = len(final_users)
        final_users.extend( self.__usr )
        final_users = list(set(final_users))
        ending_user_count = len(final_users)
        added_count = ending_user_count - beginning_user_count
        dup_count = submitted_count - added_count

        self.__usr = [u for u in final_users]

        self.logger.info(f'Added {added_count} user{", " if added_count==1 else "s,"} from total {submitted_count} submitted ({dup_count} duplicate{"" if dup_count==1 else "s"})')
        return added_count


    def add_capability(self, resource:str, *permissions):
        """--------------------
        Uniquely adds a capability to the existing biscuit structure. 

        Args:
            resource (str): Resource (Schema.Resource) to which permissions are applied.
            permission (*): Any number of SXTPermission enums to GRANT to the resource. 

        Returns:
            int: Number of items added (excluding duplicates)

        Examples:
            >>> bb = SXTBiscuit()
            >>> bb.add_capability("Schema.TableA", bb.GRANT.SELECT)
            1
            >>> bb.add_capability("Schema.TableA", bb.GRANT.INSERT)
            1
            >>> bb.add_capability("Schema.TableA", bb.GRANT.INSERT)
            0
        """
        self.__btchanged = True
        self.__lastresource = resource
        if resource not in self.__cap: self.__cap[resource] = []

        if 'ALL' in self.__cap[resource] or '*' in self.__cap[resource]:
            self.logger.warning('Cannot add other permissions to a biscuit containing ALL permissions.  Request disregarded.')
            return self.__isall__(resource)

        final_permissions = []
        [final_permissions.extend(p) for p in permissions if type(p) == list ]
        [final_permissions.append(p) for p in permissions if type(p) == SXTPermission]
        
        if len([p for p in permissions if type(p) != list and type(p) != SXTPermission ]) != 0:
            msg = 'Can only add SXTPermission (GRANT) data type to a biscuit.'
            self.logger.error(msg)
            raise KeyError(msg)
        
        beginning_resource_count = len(self.__cap[resource])
        submitted_count = len(final_permissions)
        final_permissions = list(set(final_permissions))
        unique_submitted_count = len(final_permissions)
        final_permissions.extend( self.__cap[resource] )
        final_permissions = list(set(final_permissions))
        ending_resource_count = len(final_permissions)
        added_count = ending_resource_count - beginning_resource_count
        dup_count = submitted_count - added_count

        if self.GRANT.ALL in final_permissions:
            self.__cap[resource] = [self.GRANT.ALL]
            self.logger.info(f'Added ALL permissions, replacing a total of {ending_resource_count - 1} other permissions.')
            return 1  # permissions added

        self.__cap[resource] = final_permissions

        self.logger.info(f'Added {added_count} permission{", " if added_count==1 else "s,"} from total {submitted_count} submitted ({dup_count} duplicate{"" if dup_count==1 else "s"})')
        return added_count


    def capabilities_from_text(self, biscuit_text:str) -> None:
        """--------------------
        Loads text into biscuit capabilities, for example, loading a datalog file directly.

        Args: 
            biscuit_text (str): Text to compile into capabilities.

        Results:
            str: biscuit_text that has been digested and re-processed.

        """
        self.__btchanged = True
        biscuit_lines = str(biscuit_text).strip().split('\n')
        caps = {}
        self.logger.debug(f'Translating supplied text into biscuit capabilities...')
        for line in biscuit_lines:
            if line.strip().startswith(f'{self.domain}:capability'):
                c = line.split('"')
                if len(c) <5: 
                    raise SxTArgumentError('biscuit_text capabilities must have format  domain:capability("PERMISSION", "RESOURCE");')
                p = c[1] # permission
                r = c[3] # resource
                if r not in caps: caps[r] = []
                caps[r].append(p)
        for r in list(caps.keys()):
            caps[r] = list(set(caps[r]))
        self.__cap = caps
        
        self.logger.debug(f'Successfully translated biscuit_text to biscuit capabilities objects.')
        return None


    def load_from_token(self, biscuit_token:str) -> None:
        self.__btchanged = True
        raise NotImplementedError('Not implemented yet. Please check back later.')


    def clear_biscuit(self):
        """Clears all existing capabilities from the biscuit structure"""
        self.__cap = {}
        self.__usr = []
        self.__time = []
        self.__bt = ""
        self.__btchanged = True
        self.logger.debug('Clearing all biscuit definitions')
        return None


    def to_json(self, mask_private_key:bool = True, add_tabs_to_biscuit_text:bool = False):
        """Exports content of biscuit to a json format.  WARNING, this can include private key."""
        tab = '\t' if add_tabs_to_biscuit_text else ''
        rtn = { 'private_key': getattr(self, 'private_key')[:6]+'...' if mask_private_key else getattr(self, 'private_key')
               ,'public_key' : getattr(self, 'public_key' )
               ,'biscuit_capabilities' : self.__cap
               ,'biscuit_token': self.biscuit_token
               ,'biscuit_text': f'\n{tab}' + str(self.biscuit_text).replace('\n',f'\n{tab}')
               }
        self.logger.debug(f'Translating object data to json')
        return dict(rtn)


    def save(self, filepath: Path = 'biscuits/biscuit_{resource}_{date}_{time}.json', overwrite:bool = False, resource:str = None) -> Path:
        """--------------------
        Saves biscuit information to a json file.

        The filepath will accept three different placholder texts: {resource}, {date}, and {time}.  
        This allows caller to easily create dynamically named biscuit files, reducing the likelyhood of 
        overwriting biscuit files and thus losing keys.   It is best practice to leave overwrite to False
        and use placeholders to save different files, removing older save files only after validation
        the keys are not needed anymore.  

        Args:
            filepath (Path): Full file path which to save, with placeholders allowed.
            overwrite (bool): If True, will overwrite file if exists
            resource (str): Optional resource name for placeholder in filepath.  Defaults to last resource set in add_capability().
        
        Results:
            Path: Same as filepath, if successful
        """
        # TODO: add string.replace for resource, date, time
        filepath = Path(filepath).resolve()
        # do placeholder replacements
        if not resource: resource = self.__lastresource
        date = datetime.now().strftime('%Y%m%d')
        time = datetime.now().strftime('%H%M%S')
        filepath = Path(str(filepath).replace('{resource}', resource).replace('{date}',date).replace('{time}',time))
        if filepath.exists() and not overwrite: 
            raise FileExistsError(f'{filepath} already exists.  Set overwrite = True to overwrite automatically.')

        filepath.parent.mkdir(parents=True, exist_ok=True)
        self.logger.debug(f'Opening file to write: {filepath}...')
        with open(filepath, 'w') as fh:
            fh.write( json.dumps(self.to_json(False)).replace('\t','') )
        self.logger.debug(f'Data written to file.')
        return filepath
    

    def load(self, filepath: Path, resource:str = None, date:str = None, time:str = None) -> dict:
        """--------------------
        Loads a biscuit from correctly formated JSON file.

        The filepath will accept three different placholder texts: {resource}, {date}, and {time}.  
        This allows caller to easily create (and load) dynamically named biscuit files, reducing the 
        likelyhood of overwriting biscuit files and thus losing keys.  It is best practice to leave 
        overwrite to False and use placeholders to save different files, removing older save files 
        only after validation the keys are not needed anymore.

        Args:
            filepath (Path): Full file path which to load from
            resource (str): Optional resource name for placeholder in filepath.  Defaults to last resource set in add_capability().
            date (str): Optional integer-only date (yyyymmdd) for placeholder in file path. Defaults to current date.
            time (str): Optional integer-only time (hhmmss) for placeholder in file path. Defaults to current time.

        Results:
            Path: Same as filepath, if successful
        """
        self.logger.info('Attempting to load biscuit definition from file...')
        filepath = Path(filepath).resolve()
        # do placeholder replacements
        if not resource: resource = self.__lastresource
        if not date: date = datetime.now().strftime('%Y%m%d')
        if not time: time = datetime.now().strftime('%H%M%S')
        filepath = Path(str(filepath).replace('{resource}', resource).replace('{date}',date).replace('{time}',time))
        # TODO: allow option for 'Most Recent" for date and time, which can look thru
        # the parent directory and find the file with the most recent {date} / {time}.
        # This will hopefully promote behavior of keeping history of keys, in case 
        # they're needed 
        
        if not filepath.exists: 
            raise FileNotFoundError(f'{filepath} not found.')
        try:
            self.logger.debug(f'Opening file: {filepath}...')
            with open(filepath, 'r') as fh:
                content = json.loads(fh.read())
            if 'private_key' not in content or 'biscuit_text' not in content: 
                raise SxTFileContentError 
        except (SxTFileContentError, json.JSONDecodeError):
              self.logger.error(f'File not loaded due to missing, malformed content, or simply unable to load JSON: \n{filepath}')
              return None
        try:
            self.__btchanged = True
            new_key_encoding = self.key_manager.get_encoding_type(content['private_key'])
            new_private_key =  self.key_manager.convert_key(content['private_key'], new_key_encoding, SXTKeyEncodings.BYTES)
        except SxTArgumentError: 
            return None
        
        # Assign last, after all validation.  public_key, biscuit_text, biscuit_token all recalculate automatically.
        self.logger.info(f'File opened and parsed, loading data into current object.')
        self.capabilities_from_text(content['biscuit_text'])
        self.private_key = new_private_key
        return content
            





if __name__ == '__main__':
    
    print('\n', '-=-='*10, '\n' )

    # BASIC USAGE
    bis = SXTBiscuit(name='my first biscuit', new_keypair=True)
    bis.add_capability('schema.SomeTable',    bis.GRANT.SELECT, bis.GRANT.INSERT, bis.GRANT.INSERT, bis.GRANT.UPDATE, [bis.GRANT.CREATE, bis.GRANT.DROP ])
    bis.add_capability('schema.SomeTable',    bis.GRANT.ALTER, [bis.GRANT.CREATE, bis.GRANT.DROP ])
    bis.add_capability('schema.SomeTable',    bis.GRANT.SELECT) # deduped
    bis.add_capability('schema.AnotherTable', bis.GRANT.SELECT)
    bis.add_user_check('test_userA')
    bis.add_user_check('test_userB')
    bis.add_user_check('test_userB') # deduped
    starttime = datetime.now()
    enddtime = starttime + timedelta(365)
    bis.add_time_check(starttime, enddtime)
    bis.add_time_check(starttime, enddtime) # deduped
    print( bis.biscuit_text  )
    print( bis.biscuit_token )
    # check out https://www.biscuitsec.org/ for external validation.

     
    # Permissions can be supplied as individual items, a list of items, or both
    bis.clear_biscuit()
    bis.add_capability('schema.SomeTable', bis.GRANT.SELECT, [bis.GRANT.UPDATE, bis.GRANT.INSERT, bis.GRANT.DELETE], bis.GRANT.MERGE) 
    
    # Permissions will also deduplicate themselves
    bis.add_capability('schema.SomeTable', bis.GRANT.SELECT, [bis.GRANT.CREATE, bis.GRANT.INSERT, bis.GRANT.DROP], bis.GRANT.ALTER) 
    bis.add_capability('schema.SomeTable', bis.GRANT.MERGE, bis.GRANT.DELETE, bis.GRANT.SELECT, bis.GRANT.CREATE) 
    print( bis )

    # Resources with no permissions never make it into the biscuit
    bis.clear_biscuit()
    bis.add_capability('schema.NoPermissions')
    print( f'-->{bis.biscuit_text}<--' )
    print( f'-->{bis.biscuit_token}<--' )

    # You can add ALL permissions at once
    bis.clear_biscuit()
    bis.add_capability('schema.SomeTable', bis.GRANT.ALL, bis.GRANT.SELECT )
    print( bis )

    # To build a "wildcard" biscuit (although not recommended beyond testing)
    bis.clear_biscuit()
    bis.add_capability('*', bis.GRANT.ALL)
    print( bis )

    # Note, assigning ALL to permissions will remove all other permissions
    bis.clear_biscuit()
    bis.add_capability('*', bis.GRANT.SELECT, bis.GRANT.INSERT, bis.GRANT.DELETE)
    bis.add_capability('*', bis.GRANT.ALL)
    print( bis )

    # ALL biscuits will also prevent assignment of other permissions - see WARNING
    bis.add_capability('*', bis.GRANT.SELECT)
    print( bis )


    # Printing biscuit object as string (__str__) obscures the private key.
    # to print the full private key, print the representation instead.
    print( repr( bis ) )


    # Save biscuit information to disk, so keys are not lost
    bis.clear_biscuit()
    bis.add_capability('schema.SomeTable', bis.GRANT.SELECT, [bis.GRANT.UPDATE, bis.GRANT.INSERT, bis.GRANT.DELETE], bis.GRANT.MERGE) 
    save_file = './biscuits/biscuit_{resource}_{date}.json'
    print( bis.save(save_file, overwrite = True) )

    # load new biscuit object from saved json 
    bis2 = SXTBiscuit(logger=bis.logger, from_file = './biscuits/biscuit_schema.SomeTable_{date}.json')
    print( bis2 )

    # or 
    bis3 = SXTBiscuit(logger=bis.logger)
    bis3.load( './biscuits/biscuit_{resource}_{date}.json', resource='schema.SomeTable' )
    print( bis3 )

    # Practically speaking, you'll want to guard against losing keys.
    # Using the default filename will help.
    bis3.save(resource='schema.SomeTable')


    # Return a json object with information
    print( bis.to_json() )
    pass
