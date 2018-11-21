import os
import pymysql.cursors
import pandas as pd
from pprint import pprint

connection_config = {
    'user': os.environ['DB_USER'],
    'password': os.environ['DB_PASS'],
    'host': os.environ['DB_HOST'],
    'database': os.environ['DB_NAME'],
    'cursorclass': pymysql.cursors.DictCursor
}
connection = pymysql.connect(**connection_config)
main_record = pd.read_sql('select * from `main record`', connection)
observer_on_timeless_temple = pd.read_sql('select * from `Observer on Timeless Temple`', connection)
fuyuki = pd.read_sql('select * from fuyuki', connection)
prologue = pd.read_sql('select * from prologue', connection)
option_list = pd.read_sql('select * from option_list', connection)
mash = pd.read_sql('select * from mash_talk', connection)
tables = pd.read_sql('show tables', connection).values
table_list = tables.reshape(len(tables))
connection.close()

if __name__ == '__main__':
    pprint(main_record)
    pprint(observer_on_timeless_temple)
    pprint(fuyuki)
    pprint(prologue)
    pprint(option_list)
    pprint(mash)
    pprint(table_list)
