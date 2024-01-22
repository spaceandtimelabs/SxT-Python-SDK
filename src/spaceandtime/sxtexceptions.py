import logging

def log_if_logger(*args, **kwargs) -> None:
    msg = ''
    if 'logger' in kwargs: 
        if 'message' in kwargs: 
            msg = kwargs['message']  
        else: 
            if len(args) >=1: msg = str(args[0])    
        logging.Logger(kwargs['logger']).error(msg)
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


class SxTExceptions():
    SxTAuthenticationError = SxTAuthenticationError
    SxTQueryError = SxTQueryError
    SxTFileContentError = SxTFileContentError
    SxTArgumentError = SxTArgumentError
    SxTKeyEncodingError = SxTKeyEncodingError
    SxTBiscuitError = SxTBiscuitError
    SxTAPINotDefinedError = SxTAPINotDefinedError