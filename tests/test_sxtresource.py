import os, sys, pytest, pandas, random
from dotenv import load_dotenv
from pathlib import Path

# load local copy of libraries
sys.path.append(str( Path(Path(__file__).parents[1] / 'src').resolve() ))
from spaceandtime.spaceandtime import SpaceAndTime
from spaceandtime.spaceandtime import SXTUser
from spaceandtime.sxtkeymanager import SXTKeyManager
from spaceandtime.sxtresource import SXTResource
from spaceandtime.sxtbiscuits import SXTBiscuit

API_URL = 'https://api.spaceandtime.app'


def test_resource_methods():
    keys = SXTKeyManager(new_keypair=True)
    rs = SXTResource('Test')
    userA = SXTUser(testuser='A', user_private_key=keys.private_key)
    userB = SXTUser(testuser='B', user_private_key=keys.private_key)
    userE = SXTUser(testuser='E')
    userE.key_manager = SXTKeyManager()
    userO = object()
    userS = 'just a string, man'
    userRS = SXTUser(testuser='RS', user_private_key=keys.private_key)
    rs.user = userRS 

    assert rs.get_first_valid_user(userO, userS, userE, userA, userB) == userA
    assert rs.get_first_valid_user(userS, userB, userA, userE) == userB
    assert rs.get_first_valid_user(userA, userB, userO, userS) == userA
    assert rs.get_first_valid_user(userS, userRS, userB, userA, userO) == userRS
    assert rs.get_first_valid_user() == userRS

    assert rs.get_first_valid_user(userE, userS) == userRS
    rs.user = userO
    assert rs.get_first_valid_user(userE, userS) == userE
    assert rs.get_first_valid_user(userS, userO) == None

 

if __name__ == '__main__':
    
    test_resource_methods()
    pass 