"""
webserver of mongodb fsindex.files data
"""
from __future__ import division

import cyclone.web, pymongo, json, re, sys
from twisted.internet import reactor

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/xhtml+xml")
        self.write(open("index.html").read())

class Query(cyclone.web.RequestHandler):
    def get(self):
        # the client may abort this, and it would be great to forward
        # that abort into a mongodb
        # killOp. http://stackoverflow.com/questions/7348736/how-to-check-if-connection-was-aborted-in-node-js-server
        # talks about handling it for nodejs. The server may have to
        # send occasional no-op bytes over the link to know if it's
        # been closed. Or can my client be nice and send something
        # from its end just before closing?
        
        self.set_header("Content-Type", "application/json")
        spec = {}

        args = self.request.arguments
        if args.get('basePrefix', []):
            spec['base'] = re.compile("^"+re.escape(args['basePrefix'][0]))
        if args.get('baseSubstr', []):
            # join this with the prefix one
            spec['base'] = re.compile(re.escape(args['baseSubstr'][0]))

        if args.get('user', []):
            spec['user'] = args['user'][0]

        if args.get('pathPrefix', []):
            spec['path'] = re.compile("^"+re.escape(args['pathPrefix'][0]))

        docs = list(self.settings.db['files'].find(spec).limit(101))
        self.write(json.dumps({'docs':docs}))

class Static(cyclone.web.RequestHandler):
    def get(self, f):
        self.write(open(f).read())

if __name__ == '__main__':

    from twisted.python import log as twlog
    twlog.startLogging(sys.stdout)

    db = pymongo.Connection("bang", 27017)['fsindex']
    reactor.listenTCP(9089, cyclone.web.Application([
        (r"^/", Index),
        (r"^/query", Query),
        (r"^/static/(knockout-2\.0\.0\.js|jquery\.min\.js)$", Static),
        ], db=db))
    reactor.run()
