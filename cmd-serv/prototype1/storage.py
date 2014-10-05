import sqlite3

conn = sqlite3.connect('test.db')
print "Opened database successfully";
conn.row_factory = sqlite3.Row

c = conn.execute("SELECT rowid, firstname, lastname FROM person")
r = c.fetchone()
print r
print r.keys()

print "Operation done successfully";
conn.close()