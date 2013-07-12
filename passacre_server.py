import os

from twisted.python import log
from twisted.web.resource import Resource
from twisted.web.template import tags, renderElement

from passacre.application import Passacre


selectJS = 'this.selectionStart = 0; this.selectionEnd = this.value.length;'
htmlHead = tags.head(
    tags.link(rel='apple-touch-icon', href='/static/passacre.png'),
    tags.link(rel='stylesheet', type='text/css', href='/static/style.css'),
    tags.meta(
        name='viewport',
        content='user-scalable=no, width=device-width, initial-scale=1.0, maximum-scale=1.0'),
    tags.meta(name='apple-mobile-web-app-capable', content='yes'),
    tags.meta(name='format-detection', content='telephone=no'),
)


class GeneratorResource(Resource):
    isLeaf = True

    def __init__(self, emailConfigMap):
        Resource.__init__(self)
        self.emailConfigMap = emailConfigMap
        self._applications = {}

    def getRequestEmail(self, request):
        cert = request.transport.getPeerCertificate()
        components = dict(cert.get_subject().get_components())
        return components['emailAddress']

    def getApplication(self, request):
        email = self.getRequestEmail(request)
        configFile = self.emailConfigMap[email]
        mtime, app = self._applications.get(email, (0, None))
        currentModificationTime = os.path.getmtime(configFile)
        if mtime < currentModificationTime:
            app = Passacre()
            log.msg('loading config file %r' % (configFile,))
            app.load_config(open(configFile, 'rb'))
            self._applications[email] = currentModificationTime, app
        return app

    def render_GET(self, request):
        email = self.getRequestEmail(request)
        request.setHeader('content-type', 'text/html; charset=utf-8')
        element = tags.html(
            htmlHead,
            tags.body(tags.form(
                tags.fieldset(
                    tags.div(
                        tags.label('Cert e-mail'),
                        tags.label('Username', for_='username'),
                        tags.label('Password', for_='password'),
                        tags.label('Site', for_='site', class_='last'),
                        id='names',
                    ),
                    tags.div(
                        tags.input(disabled='true', value=email),
                        tags.input(name='username', type='text'),
                        tags.input(name='password', type='password'),
                        tags.input(name='site', type='url', class_='last'),
                        id='fields',
                    ),
                ),
                tags.button('Generate', type='submit'),
                action='', method='POST',
            )),
        )
        return renderElement(request, element)

    def render_POST(self, request):
        request.setHeader('content-type', 'text/html; charset=utf-8')
        app = self.getApplication(request)
        password = app.config.generate_for_site(
            request.args['username'][0],
            request.args['password'][0],
            request.args['site'][0])
        element = tags.html(
            htmlHead,
            tags.body(tags.div(
                tags.input(
                    size='1', value=password, onFocus=selectJS, onMouseUp='return false',
                ),
            ), class_='center'),
        ),
        return renderElement(request, element)
