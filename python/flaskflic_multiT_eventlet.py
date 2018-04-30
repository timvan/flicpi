from flask import Flask, render_template
from flask_socketio import SocketIO
from datetime import datetime, timedelta
import dateutil.parser
import fliclib
import sqlite3
import threading
from threading import Lock
import json

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
	render_template('index.html')
	update_state_tabe()
	return


@socketio.on('connect new button')
def connect_new_button():
	pass

def get_last_time_and_state(bdAddr):
	""" 
	Get the last entry of this bdAddr in event_log. 
	Return the status and the time of log.
	If does not exist return False and datetime.now().
	"""

	row = db_flicpi.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()			
	print('1[get_state]', row)

	if row is not None:
		return dateutil.parser.parse(row[0]), bool(row[2])

	return datetime.now(), False



def update_state_tabe():

	table = []

	devs = db_flicdeamon.execute("SELECT bdaddr, color FROM buttons").fetchall()

	for i, device in enumerate(devs):
		timestamp, state = get_state(device[0])
		row = {
			'bdAddr': device[0],
			'color': device[1],
			'user': i,
			'state': state,
			'disruption_start': timestamp if state else None,
		}
		table.append(row)

	print(json.dumps(table))
	
	socketio.emit('update state table', table)


def start_counter(bdAddr):
	socketio.emit('start counter', bdAddr)

# def socket_handle_single_click(bdAddr):
# 	print('socket_handle_single_click', bdAddr)
# 	socketio.emit('single click', bdAddr)

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

		# socketio.emit('single click', bdAddr)
		# socket_handle_single_click(bdAddr)
		

		timestamp, disturbed = get_last(bdAddr)

		

		if disturbed:
			distrubance = datetime.now() - timestamp
			print(bdAddr + " was disturbed for " + str(distrubance) + '.')
			db.execute("INSERT INTO disturbances VALUES (?, ?, ?)", (timestamp, bdAddr, distrubance.total_seconds()))
			print("2.2[handle_single_click] - inserted into disturbances", bdAddr)
			db.commit()
			stop_counter(bdAddr)

		else:
			print(bdAddr, "is now disturbed...")
			start_count(bdAddr)

		db.execute("INSERT INTO event_log VALUES (?, ?, ?)", (datetime.now(), bdAddr, not disturbed, ))
		print("2.3[handle_single_click] - inserted into event_log", bdAddr)
		db.commit()

		update_state_tabe()
		

	def get_last(bdAddr):
		""" 
		Get the last entry of this bdAddr in event_log. 
		Return the status and the time of log.
		If does not exist return False and datetime.now().
		"""

		row = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()			
		print("2.1[get_last]", row)

		if row is not None:
			return dateutil.parser.parse(row[0]), bool(row[2])

		return (datetime.now(), False)


	def get_total_disturbance(bdAddr):
		"""
		Sum total disturbances for this bdAddr in disturbances.
		Return rounded total.
		"""
		total = db.execute("SELECT SUM(disturbance) FROM disturbances WHERE bdAddr=?", (bdAddr,)).fetchone()
		return round(total[0], 0)


	client.get_info(got_info)
	client.on_new_verified_button = got_button
	client.handle_events()



# --------------------- RUN TIME ---------------------

eventlet.spawn(background_thread)
# init_devices()

if __name__ == '__main__':

    
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)


    
