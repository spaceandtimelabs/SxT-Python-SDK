import sys,random, time
from pathlib import Path
from datetime import datetime

# load local copy of libraries
sys.path.append(str( Path(Path(__file__).parents[1] / 'src').resolve() ))
from spaceandtime.spaceandtime import SpaceAndTime
from spaceandtime.sxtkeymanager import SXTKeyManager
from spaceandtime.sxtbiscuits import SXTBiscuit
from spaceandtime.sxtresource import SXTTable, SXTView, SXTMaterializedView


# authenticate once for all subsequent tests
envfile = Path(Path(__file__).parent / '.env').resolve() # ./tests/.env
sxt = SpaceAndTime(envfile_filepath=envfile, application_name='pytest_SDKTesting')
sxt.logger_addFileHandler( Path(envfile.parent / 'latest_test_log.txt') )
sxt.authenticate()


def test_all():
    num = '{num:06d}'.format(num=random.randint(0,999999))
    biscuit_file = Path(Path(__file__).parent / 'backup_biscuits' / f"{datetime.now().strftime('%Y%m%d.%h%m%s')}_biscuits_from_tests.json")

    try:
        # create one keypair / biscuit for all use-cases and objects 
        biscuit = SXTBiscuit('all_uses', new_keypair=True)
        biscuit.add_capability('*', sxt.GRANT.ALL)
        biscuit.save(biscuit_file) # in case something goes wrong... we can rm at the end

        # Create table
        table = SXTTable(f'SXTTest.MyTestTable_{num}', key_manager=biscuit.key_manager, access_type=sxt.TABLE_ACCESS.PUBLIC_READ, SpaceAndTime_parent=sxt)
        table.add_biscuit_object(biscuit)
        table.create_ddl = table.create_ddl_sample
        table_success, resopnse = table.create()
        assert table_success
        assert table.exists

        # load some made-up data
        data = [{'MyID':n, 'MyName':chr(n), 'MyDate':'2024-01-01'} for n in range(65,65+26)]
        insert_success, response = table.insert.with_list_of_dicts(data)
        assert insert_success

        # Select, using built-in function
        select_success, data = table.select() 
        assert select_success
        assert len(data) == 26
        assert data[0]['MYDATE'][:10] == '2024-01-01'
        assert 64 < data[0]['MYID'] < 90
        assert sorted([d['MYID'] for d in data])[0] == 65 # sorted here, in python

        # Select, using custom SQL
        select_success, data = table.select(f'Select * from {table.table_name} order by MyID')
        assert select_success
        assert len(data) == 26
        assert data[0]['MYID'] == 65 # sorted in the SQL

        # create view on table
        view = SXTView(f'SXTTest.MyTestView_{num}_Evens', key_manager=biscuit.key_manager, SpaceAndTime_parent=sxt)
        view.add_biscuit_object(biscuit)
        view.create_ddl = f"""
            CREATE VIEW {view.view_name} 
            {view.with_statement} AS
            SELECT * FROM {table.table_name} WHERE MyID % 2 = 0 """
        view_success, response = view.create()
        assert view_success
        assert view.exists
        
        # views can take a moment for network to sync sometimes, let's check a few times
        for i in range(1,30):
            select_success, data = view.select()
            if select_success and len(data) == 13: break
            time.sleep(10) 

        # select from the EVENS view (only even numbers)
        assert select_success
        assert len(data) == 13
        assert sorted([d['MYID'] for d in data])[0] == 66

        # create materialized view
        matview = SXTMaterializedView(f'SXTTest.MyTestMatView_{num}_Odds', key_manager=biscuit.key_manager, SpaceAndTime_parent=sxt)
        matview.add_biscuit_object(biscuit)
        matview.create_ddl_template = f"""
            CREATE VIEW {matview.matview_name} 
            {matview.with_statement} AS
            SELECT * FROM {table.table_name} 
            WHERE MyID not in ( Select MyID from {view.view_name} ) """
        view_success, response = matview.create()
        assert view_success
        assert matview.exists

        for i in range(1,30):
            select_success, data = matview.select()
            if select_success and len(data) == 13: break
            time.sleep(10) 

        # select from the ODDS materialized view (only odd numbers)
        assert select_success
        assert len(data) == 13
        assert sorted([d['MYID'] for d in data])[0] == 65

    
    except Exception as ex:
        # for any error, just try to drop everything
        pass 

    # make sure to drop in reverse order of dependencies
    dropmatview_success = dropview_success = droptable_success = True
    if 'matview' in locals(): dropmatview_success, response = matview.drop()
    if 'view' in locals(): dropview_success, response = view.drop()
    if 'table' in locals(): droptable_success, response = table.drop()
    
    # if anything created fails to drop, hang onto the biscuit (or if )
    if (dropmatview_success and dropview_success and droptable_success):
        Path(biscuit_file).unlink(True)



if __name__ == '__main__':
    test_all()
    pass