import logging

def log_if_logger(*args, **kwargs) -> None:

    # use supplied logger if supplied, or root if it has been setup, otherwise no logger, just exit
    if 'logger' in kwargs and type(kwargs['logger']) in [logging.RootLogger, logging.Logger]: 
        errlogger = kwargs['logger']
    else: 
        try:
            if logging.getLogger().hasHandlers():  
                errlogger = logging.getLogger()
            else: 
                return None
        except:
            return None 

    # use message if supplied in kwargs, or as pos0 in args
    if 'message' in kwargs: 
        msg = kwargs['message']  
    else: 
        msg = 'No message supplied' if len(args) == 0 else str(args[0])    

    # log message
    errlogger.error(msg)
    return None


class SxTBiscuitError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)

class SxTKeyEncodingError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)

class SxTArgumentError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)
    
class SxTFileContentError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)
    
class SxTQueryError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)

class SxTAuthenticationError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)

class SxTAPINotDefinedError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)


class SxTAPINotSuccessfulError(Exception):
    def __init__(self, *args: object, **kwargs) -> None:
        log_if_logger(*args, **kwargs)
        super().__init__(*args)


class SxTExceptions():
    SxTAuthenticationError = SxTAuthenticationError
    SxTQueryError = SxTQueryError
    SxTFileContentError = SxTFileContentError
    SxTArgumentError = SxTArgumentError
    SxTKeyEncodingError = SxTKeyEncodingError
    SxTBiscuitError = SxTBiscuitError
    SxTAPINotDefinedError = SxTAPINotDefinedError
    SxTAPINotSuccessfulError = SxTAPINotSuccessfulError