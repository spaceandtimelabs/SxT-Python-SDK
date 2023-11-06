import setup, teardown, pytest

from pprint import pprint 
from spaceandtime import SpaceAndTime, SXTTable, SXTTableAccessType, SXTKeyEncodings, SXTPermission

# connect and authenticate
sxt = SpaceAndTime(default_local_folder='./tests')
sxt.authenticate()

# query public tables:
print( '\nQUERY PUBLIC TABLE:' )
success, data = sxt.execute_query('select * from SXTLabs.Singularity')
pprint( data )


# query a permissioned table:
print( '\nQUERY PERMISSIONED TABLE:' )
read_biscuit = "EqsBCkEKDnN4dDpjYXBhYmlsaXR5CgpkcWxfc2VsZWN0ChBzeHRkZW1vLmRhcmtzdGFyGAMiDwoNCIAIEgMYgQgSAxiCCBIkCAASIF1eifHhHMXwzwmyAucLBhd3wwRCquCEHoy6B3YG_qknGkADvxnWxpLNPvE7zMZmVBOVbCJTNRrYH_yYswxkyKC54fPjevRDYkAtC3AAn-RF472-_EkJhxNnWTwrP5sTphMHIiIKIJgsh47eT423Is5I3BJEmD3mPFKU5qWtlX6mzTMX1sDy"
success, data = sxt.execute_query('select * from SXTDemo.Darkstar', biscuits=[read_biscuit])
pprint( data )


# return as CSV
print( '\nQUERY AND RETURN CSV:' )
success, data = sxt.execute_query('select * from SXTDemo.Darkstar', output_format = sxt.OUTPUT_FORMAT.CSV, biscuits=[read_biscuit])
pprint( data )


# fully optimized: 
print( '\nFULLY QUALIFIED (OPTIMIZED) QUERY:' )
success, data = sxt.execute_query('select * from SXTLabs.Singularity', sql_type = sxt.SQLTYPE.DQL, resources=['SXTLabs.Singularity'])
pprint( data )