import sqlite3
db = sqlite3.connect('flicpi.db')
print(db)
bdAddr = ("80:80:80:80",)

# c = db.cursor()

# c.execute("SELECT * FROM event_log WHERE bdAddr=?", bdAddr)

for row in db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", bdAddr):
	print("row:", row)

cur = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", bdAddr)
print(cur.fetchone())

if None:
	return False


print("[get_status]:")