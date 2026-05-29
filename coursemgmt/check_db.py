from django.db import connection
import pprint
pprint.pprint(connection.settings_dict)
cur=connection.cursor()
cur.execute('SELECT DATABASE()')
print('current_db:', cur.fetchone()[0])
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = DATABASE() AND table_name = 'courses_tcm'")
print('courses_tcm_exists:', cur.fetchone()[0])
