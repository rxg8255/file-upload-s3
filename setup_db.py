import sqlite3

conn = sqlite3.connect('6632808')
cur = conn.cursor()

cur.execute('''
          CREATE TABLE IF NOT EXISTS users(
          [email] TEXT PRIMARY KEY, 
          [password] TEXT NOT NULL,
          [firstname] TEXT NOT NULL,
          [lastname] TEXT NOT NULL
          )
          ''')

conn.commit()