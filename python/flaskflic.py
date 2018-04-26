from flask import Flask, render_template
from flask_socketio import SocketIO
from datetime import datetime, timedelta
import dateutil.parser
import fliclib
import sqlite3


app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
app.debug = True
app.port = 5000
app.host = '0.0.0.0'

socketio = SocketIO(app)

client = fliclib.FlicClient("0.0.0.0")
# flicpi.db .event_log: (timestamp TEXT, bdAddr TEXT, status INTEGER)
# flicpi.db .disturbances: (timestamp TEXT, bdADdr TEXT, disturbance INTEGER)
db = sqlite3.connect('flicpi.db')


@app.route('/')
def index():
	return render_template('index.html')


@socketio.on('my event')
def handle_my_event(json):
	print('received json:', str(json))


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


client.get_info(got_info)
client.on_new_verified_button = got_button
client.handle_events()	


if __name__ == '__main__':

    socketio.run(app, debug = True, port = 5000, host = '0.0.0.0')


    
