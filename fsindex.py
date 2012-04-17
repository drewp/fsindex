"""
webserver of mongodb fsindex.files data
"""
from __future__ import division

import cyclone.web, json, re, sys, restkit
from twisted.internet import reactor
import httplib, cgi

class PrettyErrorHandler(object):
    """
    mix-in to improve cyclone.web.RequestHandler
    """
    def get_error_html(self, status_code, **kwargs):
        try:
            tb = kwargs['exception'].getTraceback()
        except AttributeError:
            tb = ""
        return "<html><title>%(code)d: %(message)s</title>" \
               "<body>%(code)d: %(message)s<pre>%(tb)s</pre></body></html>" % {
            "code": status_code,
            "message": httplib.responses[status_code],
            "tb" : cgi.escape(tb),
        }

class Index(cyclone.web.RequestHandler):
    def get(self):
        self.set_header("Content-Type", "application/xhtml+xml")
        self.write(open("index.html").read())

class Query(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self):
        # the client may abort this, and it would be great to forward
        # that abort into
        # ES. http://stackoverflow.com/questions/7348736/how-to-check-if-connection-was-aborted-in-node-js-server
        # talks about handling it for nodejs. The server may have to
        # send occasional no-op bytes over the link to know if it's
        # been closed. Or can my client be nice and send something
        # from its end just before closing?
        
        jsonRet = db.post("files/_search", payload=self.get_argument("q"),
                          headers={'content-type':'application/json'}).body_string()
        self.set_header("Content-Type", "application/json")
        self.write(jsonRet)

class Status(PrettyErrorHandler, cyclone.web.RequestHandler):
    def get(self):
        jsonRet = db.get("_status").body_string()
        self.set_header("Content-Type", "application/json")
        self.write(jsonRet)


class Static(cyclone.web.RequestHandler):
    def get(self, f):
        self.write(open(f).read())

if __name__ == '__main__':

    from twisted.python import log as twlog
    #twlog.startLogging(sys.stdout)

    db = restkit.Resource("http://localhost:9200/fsindex/")
    reactor.listenTCP(9089, cyclone.web.Application([
        (r"^/", Index),
        (r"^/query", Query),
        (r"^/status", Status),
        (r"^/static/(knockout-2\.0\.0\.js|jquery\.min\.js)$", Static),
        ], db=db))
    reactor.run()
