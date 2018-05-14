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

	c = db.cursor()
	c.execute("SELECT timestamp, bdAddr FROM event_log")
	rows = c.fetchone()
	c.close()

	print(rows)
	# for row in rows:

	# 	print(row[0], row[1])

def get_users2():

	c = db.cursor()
	rows = c.execute("SELECT timestamp, bdAddr FROM event_log LIMIT 1").fetchone()


	print('2', rows[0])
	# for row in rows:

	# 	print(row[0], row[1])



get_users()
get_users2()
get_users()
get_users2()
get_users()




devices = []

class Device():
	def __init__(self, bdAddr, user, colour):
		self.bdAddr = bdAddr
		self.user = user
		self.colour = colour
		self.status = False #<< is this going to lead to conflicting sources of truth


db_flicdeamon = sqlite3.connect('../bin/armv6l/flicd.sqlite.db')
def init_devices():	
	rows = db_flicdeamon.execute("SELECT * FROM buttons").fetchall()
	for i, row in enumerate(rows):
		devices.append(Device(bdAddr = row['bdAddr'], user = i, colour = row['color']))

# init_devices()
# print(devices)

# for row in db.execute("SELECT * FROM event_log WHERE bdAddr=?", (bdAddr, )):
# 	print("ROW:", row)


# print("[get_status]:", timestamp, status)