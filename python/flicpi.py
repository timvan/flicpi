#!/usr/bin/env python3

# Test Client application.
#
# This program attempts to connect to all previously verified Flic buttons by this server.
# Once connected, it prints Down and Up when a button is pressed or released.
# It also monitors when new buttons are verified and connects to them as well. For example, run this program and at the same time the scan_wizard.py program.
from datetime import datetime
import dateutil.parser
import fliclib
import sqlite3

client = fliclib.FlicClient("localhost")

# flicpi.db .event_log: (timestamp TEXT, bdAddr TEXT, status INTEGER)
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


def handle_single_click(bdAddr):
	
	timestamp, disturbed = get_last(bdAddr)

	print("[handle_single_click]", timestamp, disturbed)

	db.execute("INSERT INTO event_log VALUES (?, ?, ?)", (datetime.now(), bdAddr, not disturbed, ))
	db.commit()
	print("[handle_single_click]: INSERT", (datetime.now(), bdAddr, not disturbed, ))


def get_last(bdAddr):

	row = db.execute("SELECT * FROM event_log WHERE bdAddr=? ORDER BY timestamp DESC LIMIT 1", (bdAddr, )).fetchone()
	
	if row is None:
		return (datetime.now(), False)

	if bool(row[2]):
		return dateutil.parser.parse(row[0]), True
	
	return dateutil.parser.parse(row[0]),  False


client.get_info(got_info)

client.on_new_verified_button = got_button

client.handle_events()
