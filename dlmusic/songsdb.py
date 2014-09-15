#! /usr/bin/env python
# -*- coding: utf-8 -*-

from vavava import sqliteutil

SQL_CREATE_TABLES = """
-- Table: songs
CREATE TABLE IF NOT EXISTS songs (
    id      INTEGER PRIMARY KEY,
    code    TEXT    UNIQUE,
    title   TEXT,
    offline INTEGER
);

-- Index: idx_songs_code
-- CREATE INDEX idx_songs_code ON songs (
--     code COLLATE NOCASE DESC
-- );
"""

class Songs:
    def __init__(self, db_file):
        self.db_file = db_file
        self.db = sqliteutil.Sqlite3Helper(db_file)
        self.db.get_connection()
        self.db.conn.executescript(SQL_CREATE_TABLES)

    def exists(self, code):
        sql = r'select count(id) from song where code=%s'%code
        return self.db.fetch_one(sql)[0] > 0

    def insert(self, code, title):
        sql = r'insert into songs(code, title, offline) values("%s", "%s", 0)' % (code, title)
        self.db.conn.execute(sql)

    def set_offline(self, code, offline):
        sql = r'update songs set offline=%s where code=%s' % (offline, code)
        self.db.conn.execute(sql)

    def get_need_offline_list(self):
        """return [(id,code,title,offline)]"""
        sql = r'select * from songs where offline=0'
        return self.db.fetch_all(sql)


    def getinfo_by_code(self, code):
        """return (id,code,title,offline)"""
        sql = r'select * from songs where code="%s"' % (code)
        return self.db.fetch_one(sql)


###### for test #####

def test_set_offline(songs):
    code = '158465'
    print r'===> %d,%s,%s,%d' % songs.getinfo_by_code(code)
    songs.set_offline(code, 1)
    print r'===> %d,%s,%s,%d' % songs.getinfo_by_code(code)
    songs.set_offline(code, 0)
    print r'===> %d,%s,%s,%d' % songs.getinfo_by_code(code)

def test_syn_song_list_to_db(songs):
    for song in open('song_list.txt', 'r').readlines():
        try:
            info = song.split("#")
            code, title = info[0], info[1]
            songs.insert(code, title)
            print '===> insert:', code, "#", title
        except Exception as e:
            print e.message

def test_get_need_offline_list(songs):
    for info in songs.get_need_offline_list():
        print r'%d,%s,%s,%d'%info

def test_set_all(songs):
    for code in [x[1] for x in songs.get_need_offline_list()]:
        songs.set_offline(code, 1)

if __name__ == "__main__":
    songs = Songs('songs.db3')
    # test_syn_song_list_to_db(songs)
    # test_set_offline(songs)
    test_get_need_offline_list(songs)
    # test_set_all(songs)
