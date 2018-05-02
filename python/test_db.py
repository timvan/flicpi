import sqlite3

db_flicpi =  sqlite3.connect('flicpi.db')


device = ['80:e4:da:73:d6:8c', '']
new_user = {
	'bdAddr': '80:e4:da:73:d6:8c',
}

# bdAddr = '80:e4:da:73:d6:8c'
bdAddr = '80:e4:da:73:d5:a5'

x = db_flicpi.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (device[0],)).fetchone()

rowid = db_flicpi.execute("SELECT ROWID FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (new_user['bdAddr'], )).fetchone()

user = db_flicpi.execute("SELECT user FROM users WHERE bdAddr = ? ORDER BY ROWID DESC LIMIT 1", (bdAddr,)).fetchone()

print(type(user))
print(user)