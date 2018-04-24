from datetime import datetime
import sqlite3
db = sqlite3.connect('flicpi.db')
print(db)
bdAddr = ("80:80:80:80",)

# c = db.cursor()

# c.execute("SELECT * FROM event_log WHERE bdAddr=?", bdAddr)


def get_last(bdAddr):

	row = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", bdAddr).fetchone()

	if row is None:
		return (datetime.now(), False)

	return (datetime.now(), False)

timestamp, status = get_last(bdAddr)




print("[get_status]:", timestamp, status)