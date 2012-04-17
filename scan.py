"""
filesystem data into elasticsearch

may need more help reading multiple users' files over nfs
"""

import os, pwd, json
import pyes

def ingestOne(db, host, full, basename):
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
    db.insert(d)
    

def ingest(host, top, db):
    for root, dirs, files in os.walk(top):
        if root.startswith('/my/mail'):
            continue
        for basename in files:
            # if filenames in the same dir differ only by a number, it
            # would be nice to collapse that so it doesn't flood the
            # results, but i still need to be able to search '9999' to
            # find 'IMG_9999.JPG'. Maybe the answer is to give a very
            # low boost to the followup files after the first one in a
            # big sequence.
            try:
                full = os.path.join(root, basename)
                ingestOne(db, host, full, basename)
            except Exception, e:
                print "working on %r/%r: %s" % (root, basename, e)

def resetIndex(db):
    try:
        db.delete_index("fsindex")
    except pyes.exceptions.IndexMissingException:
        pass
    db.create_index("fsindex", settings={
        'index':{
            'refresh_interval':'-1',
            },
        'analysis':{
            'analyzer':{
                'path':{
                    'type':'custom',
                    'tokenizer':'keyword',
                    'filter':['lowercase', 'pathNgram'],
                    },
                },
            'filter':{
                'pathNgram':{
                    'type':'ngram',
                    'min_gram':3,
                    # 2-30, 26GB index
                    # 2-10, 8GB ? index
                    # 3-8, 
                    'max_gram':8
                    }
                }
            }
        })

    db.put_mapping(
        "files",
        {
            'properties':dict(
                host=dict(type='string', store='no', index='not_analyzed'),
                path=dict(type='string', store='no', index='analyzed', analyzer='path'),
                base=dict(type='string', store='no', index='not_analyzed'),
                ext=dict(type='string', store='no', index='not_analyzed'),
                mode=dict(type='integer', store='no', index='not_analyzed'),
                size=dict(type='long', store='no', index='not_analyzed'),
                mtime=dict(type='float', store='no', index='not_analyzed'),
                uid=dict(type='integer', store='no', index='not_analyzed'),
                gid=dict(type='integer', store='no', index='not_analyzed'),
                user=dict(type='string', store='no', index='not_analyzed'),
            )
            },
        ["fsindex"])

db =  pyes.ES('localhost:9200')
resetIndex(db)
for num, line in enumerate(open("/tmp/files.json")):
    try:
        d = json.loads(line)
        del d['_id']
        if 'dirs' in d:
            del d['dirs']
        db.index(doc=d, index="fsindex", doc_type="files", bulk=True)
    except Exception, e:
        print line, e
    if num == 1000:
        db.refresh('fsindex') # for testing
db.force_bulk()
db.update_settings('fsindex', {
    'index':{
        'refresh_interval':'30s',
        }
    })
"""
this should do a real scan of all the volumes when there's an index schema change,
and the rest of the time it should do a nightly refresh of the volatile areas. it would
be cool if we could get notifications of all file changes, but that's hard on solaris nfs.
"""
top = "/my"
host = 'nfs'
#ingest(host, top, db)
