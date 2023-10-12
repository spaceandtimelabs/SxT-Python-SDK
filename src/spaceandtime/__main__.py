# this is called when someone runs the package using the -m option, i.e., 
#   python3 -m spaceandtime <optional .env filepath>

from spaceandtime import SpaceAndTime
from pathlib import Path
import sys 

def main():
    
    # if env file path is supplied:
    if len(sys.argv) >1:
        envpath = Path(sys.argv[1]).resolve()
        sxt = SpaceAndTime(envpath)
    else:
        sxt = SpaceAndTime()

    sxt.authenticate()
    
    print( f'Authenticated UserID: {sxt.user}\nAccess Token:\n {sxt.access_token}' )


if __name__ == "__main__":
    main()