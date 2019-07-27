import sqlite3
import logging

class DbHandler:
    def __init__(self):
        self.conn = sqlite3.connect("favs.db", check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS favs(
        userId integer,
        station integer,
        name text,
        PRIMARY KEY(userId, station)
        );""")

        self.cursor.execute("""CREATE TABLE IF NOT EXISTS users(
            userId integer,
            PRIMARY KEY(userId)
        );""")

    def addUserFav(self, user, station, name):
        self.cursor.execute("""INSERT INTO favs
        VALUES (?,?,?);
        """, (user, station, name))
        self.conn.commit()

    def addUser(self, user):
        self.cursor.execute("""INSERT INTO users
        VALUES (?);
        """, (user,))
        self.conn.commit()

    def deleteUserFav(self, user, station):
        self.cursor.execute("""DELETE FROM favs
        WHERE userId=? AND station=?;""", (user,station))
        self.conn.commit()

    def getUserFavs(self, user):
        self.cursor.execute("""SELECT * FROM favs
        WHERE userId=?;""",(user,))

        rows = self.cursor.fetchall()

        stations = []
        for row in rows:
            _, station, name = tuple(row)
            stations.append((str(station), name))
        return stations

    def getAllUsers(self):
        self.cursor.execute("""SELECT * FROM users;""")

        rows = self.cursor.fetchall()

        users = []
        for row in rows:
            user = row[0]
            users.append(user)
        return users

    def check_duplicate(self, user, station):
        self.cursor.execute("""SELECT * FROM favs
        WHERE userId=? AND station=?;""",(user, station))

        return len(self.cursor.fetchall()) > 0

    def check_duplicate_user(self, user):
        self.cursor.execute("""SELECT * FROM users
        WHERE userId=?;""",(user,))

        return len(self.cursor.fetchall()) > 0

    def save(self):
        self.conn.commit()
        self.conn.close()
        logging.info(msg="Saving database")

