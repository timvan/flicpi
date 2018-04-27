from datetime import datetime
import dateutil.parser
import sqlite3
db = sqlite3.connect('flicpi.db')
bdAddr = "80:80:80:80"

# c = db.cursor()

# c.execute("SELECT * FROM event_log WHERE bdAddr=?", bdAddr)


def handle_single_click(bdAddr):
	
	timestamp, disturbed = get_last(bdAddr)

	print("[handle_single_click] get_last returned", timestamp, disturbed)

	if disturbed:
		distrubance = datetime.now() - timestamp
		print("[handle_single_click]", bdAddr, "was disturbed for", str(distrubance))
		db.execute("INSERT INTO disturbances VALUES (?, ?, ?)", (timestamp, bdAddr, distrubance.total_seconds()))

		print("[handle_single_click] Total disturbed: " + str(get_total_disturbance(bdAddr)) + "s")
	else:
		print("[handle_single_click]", bdAddr, "is now disturbed")

	
	print("[handle_single_click] INSERTING", (datetime.now(), bdAddr, not disturbed, ))
	db.execute("INSERT INTO event_log VALUES (?, ?, ?)", (datetime.now(), bdAddr, not disturbed, ))
	db.commit()
	



def get_last(bdAddr):

	row = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()
	
	if row is None:
		return (datetime.now(), False)

	if bool(row[2]):
		return dateutil.parser.parse(row[0]), True

	return dateutil.parser.parse(row[0]),  False


def get_total_disturbance(bdAddr):

	total = db.execute("SELECT SUM(disturbance) FROM disturbances WHERE bdAddr=?", (bdAddr,)).fetchone()
	return round(total[0], 0)



# handle_single_click(bdAddr)

def get_users():

	rows = db.execute("SELECT * FROM event_log").fetchall()

	for row in rows:

		print(row[0])


get_users()


# for row in db.execute("SELECT * FROM event_log WHERE bdAddr=?", (bdAddr, )):
# 	print("ROW:", row)


# print("[get_status]:", timestamp, status)