# coding=utf-8

from vavava import sqliteutil
from datetime import datetime

SQL_CREATE_TABLES = """
-- Table:
CREATE TABLE if not exists ip (
    id        integer PRIMARY KEY ASC autoincrement,
    duration  REAL,
    ip        CHAR( 64 ),
    country   CHAR( 256 ),
    create_at DATETIME
);

-- Index
CREATE INDEX if not exists idx_ip        ON ip (ip asc);
CREATE INDEX if not exists idx_create_at ON ip (create_at asc);
"""

_now = datetime.now

class DatabaseIp:
    def __init__(self, db_file='ip.db3'):
        self.db_file = db_file
        self.db = sqliteutil.Sqlite3Helper(db_file)
        self.db.get_connection()
        self.db.conn.executescript(SQL_CREATE_TABLES)

    def insert(self, duration, ip, country):
        sql = 'insert into ip(duration,ip,country,create_at) values(?,?,?,?)'
        self.db.execute(sql, (duration, ip, country, _now()))

    def getIpRecords(self, begin=None, end=None, ip=None, order_by=None, top_n=None):
        results = self.getRecords(begin, end, ip, order_by, top_n)
        return [IP(*ip[1:]) for ip in results]

    def getRecords(self, begin=None, end=None, ip=None, order_by=None, top_n=None):
        p = []
        sql = 'select * from ip'
        if begin or end or ip:
            sql += ' where'
        if begin:
            sql += ' create_at >= ? and'
            p.append(begin)
        if end:
            sql += ' create_at >= ? and'
            p.append(end)
        if ip:
            sql += ' ip = ? '
            p.append(ip)
        if sql and sql.endswith('and'):
            sql = sql[:-3]
        if order_by:
            sql += ' order by ?'
        if top_n:
            sql += ' order by id limit ?'
            p.append(top_n)
        return self.db.fetch_all(sql, p)

    # def getIPAvarageDuration(self):
    #     sql =
    #     return self.db.fetch_all(sql, p)

    def close(self):
        self.db.close()


class IP:
    def __init__(self, *t_ip_country_time):
        """ DURATION, IP, COUNTRY"""
        self.duration, self.ip, self.country, t = t_ip_country_time
        if isinstance(t, datetime):
            self.time = t
        else:
            self.time = datetime.strptime(t[:t.find('.')], "%Y-%m-%d %H:%M:%S")
        self.duration = float(self.duration)
        self.avarage = self.duration

    @property
    def timeString(self):
        return '{}'.format(self.time)

    def __lt__(self, other):
        return self.duration < other.duration

    def __str__(self):
        return '{},{},{},{}'.format(self.duration, self.ip, self.country, self.time)


def main():
    import os
    dbfile = './tmp1.db3'
    os.remove(dbfile)
    db = DatabaseIp(dbfile)
    for pp in db.getIpRecords(top_n=3):
        print pp
    db.insert(100.1, '1.1.1.1', 'a')
    db.insert(100.2, '1.1.1.2', 'b')
    db.insert(100.3, '1.1.1.3', 'c')
    db.insert(100.4, '1.1.1.4', 'd')
    db.insert(100.5, '1.1.1.5', 'e')

    for pp in db.getIpRecords(ip='1.1.1.3'):
        print pp.timeString


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt as e:
        print 'stop by user'
        exit(0)
