import sqlite3

conn = sqlite3.connect('queue.db')
print "Opened database successfully";
conn.row_factory = sqlite3.Row

c = conn.execute("SELECT max (rowid) from commands")
r = c.fetchone()
print r
print r.keys()

c = conn.execute("SELECT rowid, * from commands")
r = c.fetchall()
print r

conn.close()