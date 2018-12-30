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


def load_tables(name):
    df = pd.read_sql(f'select * from `{name}`', connection).to_dict(orient='record')
    for r in df:
        pk = list(r.keys())[0]
        if isinstance(r[pk], float):
            return {str(r.pop(pk)) if r[pk] % 1 else str(int(r.pop(pk))): r for r in df}
        else:
            return {r.pop(pk): r for r in df}


def make_tree(db):
    for table in db:
        if 'name' in db[table]:
            name = db[table]['name'].lower().replace(' ', '_')
        else:
            return
        if name in globals():
            make_tree(eval(name))
            db[table]['contents'] = eval(name)


connection = pymysql.connect(**connection_config)

main_record = load_tables('main record')

# main record
observer_on_timeless_temple = load_tables('observer on timeless temple')
# epic_of_remnant = load_tables('epic of remnant')
# cosmos_in_the_lostbelt = load_tables('cosmos in the lostbelt')

# Observer on Timeless Temple
fuyuki = load_tables('fuyuki')
# orleans = load_tables('orleans')
# septem = load_tables('septem')
# okeanos = load_tables('okeanos')
# london = load_tables('london')
# e_pluribus_unam = load_tables('e_pluribus_unam')
# camelot = load_tables('camelot')
# babyronia = load_tables('babyronia')
# solomon = load_tables('solomon')

# Fuyuki
prologue = load_tables('prologue')
# burning_city = load_tables('burning_city')
# to_the_spirit_meridian = load_tables('to_the_spirit_meridian')
# investigate_the_bridge = load_tables('investigate_the_bridge')
# investigate_the_port_ruin = load_tables('investgate_the_port_ruin')
# investigate_the_church_ruin = load_tables('investigate_the_church_ruin')
# shadow_servant = load_tables('shadow_servant')
# mash's_training = load_tables('mash's_training')
# the_dark_cave = load_tables('the_dark_cave')
# facing_the_greater_grail = load_tables('facing_the_greater_grail')
# grand_order = load_tables('grand_order')

# Others
option_list = load_tables('option_list')
mash_talk_list = load_tables('mash_talk')
tables = pd.read_sql('show tables', connection).values
table_list = tables.reshape(len(tables))

connection.close()

make_tree(main_record)

if __name__ == '__main__':

    print('main_record')
    pprint(main_record)
    print()

    print('option_list')
    pprint(option_list)
    print()

    print('mash_talk')
    pprint(mash_talk)
    print()

    print('table_list')
    pprint(table_list)
    print()
