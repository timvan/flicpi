from datetime import datetime
import dateutil
import sqlite3
db = sqlite3.connect('flicpi.db')
print(db)
bdAddr = "80:80:80:80"

# c = db.cursor()

# c.execute("SELECT * FROM event_log WHERE bdAddr=?", bdAddr)


def handle_single_click(bdAddr):
	
	timestamp, disturbed = get_last(bdAddr)

	print("[handle_single_click]", timestamp, disturbed)

	db.execute("INSERT INTO event_log VALUES (?, ?, ?)", (datetime.now(), bdAddr, not disturbed, ))
	db.commit()
	print((datetime.now(), bdAddr, not disturbed, ))


def get_last(bdAddr):

	row = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()
	print(row)
	if row is None:
		return (datetime.now(), False)

	if bool(row[2]):
		return dateutil.parser.parse(row[0]), True

	return dateutil.parser.parse(row[0]),  False



handle_single_click(bdAddr)


for row in db.execute("SELECT * FROM event_log WHERE bdAddr=?", (bdAddr, )):
	print("ROW:", row)


# print("[get_status]:", timestamp, status)