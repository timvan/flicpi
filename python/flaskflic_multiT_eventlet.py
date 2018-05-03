from flask import Flask, render_template
from flask_socketio import SocketIO
from datetime import date, datetime, timedelta
import dateutil.parser
import fliclib
import sqlite3
import threading
from threading import Lock
import json
import math

# thread_lock = Lock()

import eventlet
eventlet.monkey_patch()

global DEVICES
DEVICES = []

class Device():
	def __init__(self, bdAddr, user, colour):
		self.bdAddr = bdAddr
		self.user = user
		self.colour = colour
		# self.status = False #<< is this going to lead to conflicting sources of truth

	# def status_change(self):



# --------------------- FLASK APP  ---------------------

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

socketio = SocketIO(app)

db_flicdeamon = sqlite3.connect('../bin/armv6l/flicd.sqlite.db')
db_flicpi =  sqlite3.connect('flicpi.db')

@app.route('/')
def index():

	history = []
	rows = db_flicpi.execute("SELECT * FROM disturbances ORDER BY timestamp DESC").fetchall()

	for row in rows:
		history.append({
			'timestamp': row[0],
			'bdAddr': row[1],
			'user': row[2],
			'disturbance': secs_to_string(row[3]),
			})

	get_graph_history()
	return render_template('index.html', history = history)


@socketio.on('page loaded')
def update_state_tabe():

	table = []

	c = db_flicdeamon.cursor()
	c.execute("SELECT bdAddr, color FROM buttons")
	devs = c.fetchall()


	for i, device in enumerate(devs):
		timestamp, state = get_last_time_and_state(device[0])
		daily_total = get_daily_total(device[0])
		row = {
			'bdAddr': device[0],
			'color': device[1],
			'user': db_flicpi.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (device[0],)).fetchone(),
			'state': state,
			'disturbance_start': timestamp.ctime() if state else None,
			'daily_total': daily_total if daily_total else 0,
		}
		table.append(row)

	# print(json.dumps(table))
	
	socketio.emit('update state table', table)


def get_last_time_and_state(bdAddr):
	""" 
	Get the last entry of this bdAddr in event_log. 
	Return the status and the time of log.
	If does not exist return False and datetime.now().
	"""
	row = db_flicpi.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()
	# print('1[get_last_time_and_state]', row)

	if row is not None:
		return dateutil.parser.parse(row[0]), bool(row[2])

	return datetime.now(), False


def get_daily_total(bdAddr):

	user = db_flicpi.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (bdAddr,)).fetchone()
	if user is not None:
		user = user[0]

	total =  db_flicpi.execute("SELECT SUM(disturbance) FROM disturbances WHERE user=? AND timestamp > datetime('now', 'localtime', 'start of day')", (user,)).fetchone()

	return total[0]


@socketio.on('start new scan wizard')
def start_new_scan_wizard():
	print('start new scan wizard, spanning new thread..')
	eventlet.spawn(new_scan_wizard_thread)


@socketio.on('get connected devices')
def get_connected_devices():
	print('getting connected devices..')
	table = []

	c = db_flicdeamon.cursor()
	c.execute("SELECT bdaddr, color FROM buttons")
	devs = c.fetchall()

	for i, device in enumerate(devs):
		row = {
			'bdAddr': device[0],
			'color': device[1],
			'user': db_flicpi.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (device[0],)).fetchone(),
			'slackhandle': db_flicpi.execute("SELECT slackhandle FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (device[0],)).fetchone(),
		}
		table.append(row)

	socketio.emit('got connected devices', table)



def get_graph_history():
	days_to_graph = 10
	devs = db_flicdeamon.execute("SELECT bdaddr, color FROM buttons").fetchall()
	rows = []

	n = 0

	for i in range(days_to_graph):
		n += i

		if (date.today() - timedelta(days = n)).weekday() in [5,6]:
			n += 2

		day_str = str(date.today() - timedelta(days = n))

		row =[day_str]

		for i, device in enumerate(devs):
			user = get_user(device[0])
			row.append(math.floor(get_day_disturbance_by_user(user, -n) / 60.0))
				
		rows.append(row)

	print(rows)
	socketio.emit('graph', rows)

def get_day_disturbance_by_user(user, day):

	total =  db_flicpi.execute("SELECT SUM(disturbance) FROM disturbances WHERE user=? AND timestamp > datetime('now', 'localtime', 'start of day', '? day') AND timestamp <= datetime('now', 'localtime', 'start of day', '? day') ", (user, day, day + 1)).fetchone()

	return total[0]



def get_user(bdAddr):

	user = db_flicpi.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (bdAddr,)).fetchone()
	if user is not None:
		user = user[0]
	return user



@socketio.on('scan wizard insert')
def scan_wizard_succes(new_user):


	# db.execute("INSERT INTO users VALUES (?, ?, ?)", (bdAddr, username, slackhandle))
	# db.commit()
	print('scan wizard insert', new_user)
	rowid = db_flicpi.execute("SELECT ROWID FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (new_user['bdAddr'], )).fetchone()

	c = db_flicpi.cursor()
	c.execute("UPDATE users SET user = ?, slackhandle = ? WHERE ROWID = ?", (new_user['username'], new_user['slackhandle'], rowid[0]))
	db_flicpi.commit()
	update_state_tabe()


@socketio.on('connected devices change')
def connected_devies_change(data):

	print("Making changes to connected devices... ", data)

	for change in data:
		db_flicpi.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (datetime.now(), change['bdAddr'], change['user'], change['slackhandle']))
		db_flicpi.commit()

	update_state_tabe()


def secs_to_string(secs):

	secs = math.floor(float(secs))

	if secs < 60:
		return (str(secs) + "s")

	days = secs // (60 * 60 * 8)
	hours = (secs // (60 * 60)) % 8
	minutes = (secs // 60) % 60

	units = ['d', 'h', 'm']

	lst = []
	values = [days, hours, minutes]

	for index, val in enumerate(values):
		if val > 0:
			lst.append(str(val) + units[index])

	rendered_time = " ".join(lst)

	return rendered_time

# --------------------- FLIC THREAD ---------------------


def background_thread():

	print("Running T...")

	client = fliclib.FlicClient("localhost")

	# flicpi.db .event_log: (timestamp TEXT, bdAddr TEXT, status INTEGER)
	# flicpi.db .disturbances: (timestamp TEXT, bdADdr TEXT, disturbance INTEGER)
	db = sqlite3.connect('flicpi.db')


	def got_button(bd_addr):
		cc = fliclib.ButtonConnectionChannel(bd_addr)
		cc.on_button_single_or_double_click_or_hold = \
			lambda channel, click_type, was_queued, time_diff: \
				handle_click_type(channel.bd_addr, click_type)

		cc.on_connection_status_changed = \
			lambda channel, connection_status, disconnect_reason: \
				print(channel.bd_addr + " " + str(connection_status) + (" " + str(disconnect_reason) if connection_status == fliclib.ConnectionStatus.Disconnected else ""))
		client.add_connection_channel(cc)


	def got_info(items):
		print(items)
		for bd_addr in items["bd_addr_of_verified_buttons"]:
			got_button(bd_addr)


	def handle_click_type(bdAddr, click_type):

		if click_type is fliclib.ClickType.ButtonSingleClick:
			handle_single_click(bdAddr)
		else:
			print("No process to handle click type:",  str(fliclib.ClickType))


	def handle_single_click(bdAddr):


		timestamp, disturbed = get_last(bdAddr)

		
		if disturbed:
			disturbance = (datetime.now() - timestamp).total_seconds()
			print(bdAddr + " was disturbed for " + str(disturbance) + '.')
			user = db.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (bdAddr,)).fetchone()
			
			if user is not None:
				user = user[0]

			new_entry = {
				'timestamp': str(timestamp),
				'bdAddr': bdAddr,
				'user': user,
				'disturbance': disturbance,
			}

			db.execute("INSERT INTO disturbances VALUES (?, ?, ?, ?)", (new_entry['timestamp'], new_entry['bdAddr'], new_entry['user'], new_entry['disturbance']))
			db.commit()

			new_entry['disturbance'] = secs_to_string(disturbance)

			socketio.emit('new disturbance', new_entry)

		else:
			print(bdAddr, "is now disturbed...")

		db.execute("INSERT INTO event_log VALUES (?, ?, ?)", (datetime.now(), bdAddr, not disturbed, ))
		# print("2.3[handle_single_click] - inserted into event_log", bdAddr)
		db.commit()

		update_state_tabe()
		

	def get_last(bdAddr):
		""" 
		Get the last entry of this bdAddr in event_log. 
		Return the status and the time of log.
		If does not exist return False and datetime.now().
		"""

		row = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()		
		# print("2.1[get_last]", row)

		if row is not None:
			return dateutil.parser.parse(row[0]), bool(row[2])

		return (datetime.now(), False)


	def get_total_disturbance(bdAddr):
		"""
		Sum total disturbances for this bdAddr in disturbances.
		Return rounded total.
		"""

		user = db.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (bdAddr,)).fetchone()

		if user is not None:
			user = user[0]

		total = db.execute("SELECT SUM(disturbance) FROM disturbances WHERE uesr=?", (user,)).fetchone()
		return round(total[0], 0)


	client.get_info(got_info)
	client.on_new_verified_button = got_button
	client.handle_events()


# --------------------- NEW SCAN WIZARD THREAD ---------------------


def new_scan_wizard_thread():

	msg = ("New scan wizard thread..")
	print(msg)
	socketio.emit('scan wizard', msg)

	wizard_client = fliclib.FlicClient("localhost")

	# db_sw_deamon = sqlite3.connect('../bin/armv6l/flicd.sqlite.db')
	# db_sw_flicpi =  sqlite3.connect('flicpi.db')

	def on_found_private_button(scan_wizard):
		msg = ("Found a private button. Please hold it down for 7 seconds to make it public.")
		print(msg)
		socketio.emit('scan wizard', msg)

	def on_found_public_button(scan_wizard, bd_addr, name):
		msg = ("Found public button " + bd_addr + " (" + name + "), now connecting...")
		print(msg)
		socketio.emit('scan wizard', msg)

	def on_button_connected(scan_wizard, bd_addr, name):
		msg = ("The button was connected, now verifying...")
		print(msg)
		socketio.emit('scan wizard', msg)

	def on_completed(scan_wizard, result, bd_addr, name):
		msg = ("Scan wizard completed with result " + str(result) + ".")
		print(msg)
		socketio.emit('scan wizard', msg)



		if result == fliclib.ScanWizardResult.WizardSuccess:
			
			c = db_flicpi.cursor()
			c.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (datetime.now(), bd_addr, None, None))
			db_flicpi.commit()

			msg = ("Your button is now ready. The bd addr is " + bd_addr + ".")
			print(msg)
			socketio.emit('scan wizard', msg)
			
			c = db_flicdeamon.cursor()
			c.execute("SELECT color FROM buttons WHERE bdAddr = ?", (bd_addr, ))
			color = c.fetchone()
			
			data = {
			 'bdAddr': bd_addr,
			 'color': color
			}
			socketio.emit('scan wizard succes', data)

		wizard_client.close()

	wizard = fliclib.ScanWizard()
	wizard.on_found_private_button = on_found_private_button
	wizard.on_found_public_button = on_found_public_button
	wizard.on_button_connected = on_button_connected
	wizard.on_completed = on_completed
	wizard_client.add_scan_wizard(wizard)

	msg = ("Welcome to Scan Wizard. Please press your Flic button.")
	print(msg)
	socketio.emit('scan wizard', msg)

	wizard_client.handle_events()


# --------------------- RUN TIME ---------------------

eventlet.spawn(background_thread)
# init_devices()

if __name__ == '__main__':

    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)


    
