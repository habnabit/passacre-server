import json

from OpenSSL import SSL

from twisted.application.internet import SSLServer
from twisted.application.service import Application
from twisted.internet import ssl
from twisted.python.filepath import FilePath
from twisted.web.resource import Resource
from twisted.web.server import Site
from twisted.web.static import File

from passacre_server import GeneratorResource


fileRoot = FilePath(__file__).parent()

with fileRoot.child('configs.json').open() as infile:
    emailConfigMap = json.load(infile)

root = Resource()
root.putChild('', GeneratorResource(emailConfigMap))
root.putChild('static', File(fileRoot.child('static').path))

with fileRoot.child('server.pem').open() as infile:
    serverCert = ssl.PrivateCertificate.loadPEM(infile.read())
with fileRoot.child('ca.pem').open() as infile:
    authorityCert = ssl.Certificate.loadPEM(infile.read())

sslContextFactory = serverCert.options(authorityCert)
sslContextFactory.method = SSL.SSLv23_METHOD
site = Site(root)
application = Application('passacre-gen')
SSLServer(4443, site, sslContextFactory, interface='::').setServiceParent(application)
