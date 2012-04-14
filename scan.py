"""
filesystem data into mongodb. should be elasticsearch instead.

may need more help reading multiple users' files over nfs
"""

import os, pwd
import pymongo

def ingestOne(coll, host, full, basename):
    stat = os.stat(full)
    pw = pwd.getpwuid(stat.st_uid)
    d = dict(
        _id="%s:%s" % (host, full),
        host=host,
        path=full,
        dirs=full.split('/')[1:-1],
        base=basename,
        ext=os.path.splitext(basename)[1][1:],
        mode=stat.st_mode,
        size=stat.st_size,
        mtime=stat.st_mtime,
        uid=stat.st_uid,
        gid=stat.st_gid,
        user=pw.pw_name,
        # symlink?
        )
    coll.insert(d)
    

def ingest(host, top, coll):
    for root, dirs, files in os.walk(top):
        if root.startswith('/my/mail'):
            continue
        for basename in files:
            try:
                full = os.path.join(root, basename)
                ingestOne(coll, host, full, basename)
            except Exception, e:
                print "working on %r/%r: %s" % (root, basename, e)


coll = pymongo.Connection('bang', 27017)['fsindex']['files']

top = "/my"
host = 'nfs'

ingest(host, top, coll)
