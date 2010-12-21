# vim: set fileencoding=utf-8 sw=4 ts=4 et :

"""
Extends pubsub clients to compute Node message.
"""
from __future__ import absolute_import

import os
import stat
import fcntl
from twisted.internet import defer, threads
from twisted.words.xish import domish
from wokkel.pubsub import PubSubClient
from wokkel import xmppim
from vigilo.pubsub import xml

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.common.logging import get_logger
from vigilo.connector.forwarder import PubSubForwarder, NotConnectedError
from vigilo.connector.store import DbRetry
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


class WrongNagiosPipe(NotConnectedError):
    def __str__(self):
        return _('the configured nagios command pipe is not a FIFO')

class XMPPToPipeForwarder(PubSubForwarder):
    """
    Receives messages from xmpp, and passes them to the pipe.
    Forward XMPP to pipe.
    """

    def __init__(self, pipe_filename, dbfilename, dbtable):
        """
        Instancie un connecteur XMPP vers pipe.

        @param pipe_filename: le nom du fichier pipe qui accueillra les
        messages XMPP
        @type pipe_filename: C{str}
        @param dbfilename: le nom du fichier permettant la sauvegarde des
        messages en cas de problème d'éciture sur le pipe
        @type dbfilename: C{str}
        @param dbtable: Le nom de la table SQL dans ce fichier.
        @type dbtable: C{str}
        """
        super(XMPPToPipeForwarder, self).__init__(dbfilename, dbtable)
        self.pipe_filename = pipe_filename

    def connectionInitialized(self):
        """
        Redefinition in order to add a new observer for message type=chat
        """
        # Called when we are connected and authenticated
        super(XMPPToPipeForwarder, self).connectionInitialized()
        # add an observer to deal with chat message (oneToOne message)
        self.xmlstream.addObserver("/message[@type='chat']", self.chatReceived)

    def forwardMessage(self, msg, source="bus"):
        if isinstance(msg, domish.Element):
            msg = self.convertXmlToNagios(msg)
        if msg is None:
            return defer.succeed(None) # on ignore
        if source != "backup" and \
                (self._sendingbackup or self._waitingforreplies):
            self.storeMessage(msg)
            return
        d = threads.deferToThread(self.writeToNagios, msg)
        d.addErrback(self._send_failed, msg)
        return d

    def convertXmlToNagios(self, data):
        """
        Convertisseur entre un message de commande Nagios en XML et le format
        attendu par Nagios
        """
        LOGGER.debug(_('Command message to forward: %s') % data.toXml())
        qualified_name = xml.namespaced_tag(data.uri, data.name)
        if qualified_name not in [xml.namespaced_tag(xml.NS_NAGIOS, 'command'),
                                 xml.namespaced_tag(xml.NS_COMMAND, 'command')]:
            return
        cmd_timestamp = int(str(data.timestamp))
        cmd_name = str(data.cmdname)
        cmd_value = str(data.value)
        if cmd_name not in \
            settings['connector-nagios']['accepted_commands']:
            LOGGER.error(_("Command '%(received)s' disallowed by "
                        "policy, accepted commands: %(accepted)r") % {
                            'received': data.cmdname,
                            'accepted': settings['connector-nagios']
                                                ['accepted_commands'],
                         })
            return
        return "[%s] %s;%s" % (cmd_timestamp, cmd_name, cmd_value)

    def writeToNagios(self, msg):
        # testing there is a pipe (FIFO) which exist.
        if not stat.S_ISFIFO(os.stat(self.pipe_filename).st_mode):
            raise WrongNagiosPipe()
        # XXX il serait possible d'aggréger les écritures si on flush
        #  après chaque écriture (pour ne pas ouvrir/fermer le pipe à
        # chaque fois
        # (texte suivant issue du code de nsca)
# /* if we don't fflush() then we're writing in 4k non-CR-terminated blocks, and
#  * anything else (eg. pscwatch) which writes to the file will be writing into
#  * the middle of our commands.
#  */
        LOGGER.debug("Writing to %(pipe)s: %(msg)s", {
            'pipe': self.pipe_filename,
            'msg': msg,
        })
        # cannot open in append mode, since that causes a seek
        pipe = os.open(self.pipe_filename, os.O_WRONLY)
        fcntl.flock(pipe, fcntl.LOCK_EX)
        os.write(pipe, msg + '\n')
        fcntl.flock(pipe, fcntl.LOCK_UN)
        os.close(pipe)
        return True

    def chatReceived(self, msg):
        """
        function to treat a received chat message

        @param msg: msg to treat
        @type  msg: Xml object

        """
        # Il ne devrait y avoir qu'un seul corps de message (body)
        # TODO: ajouter des tests unitaires
        bodys = [element for element in msg.elements()
                         if element.name in ('body',)]
        for b in bodys:
            for data in b.elements():
                # les données dont on a besoin sont juste en dessous
                self.forwardMessage(data, source="bus")

    def itemsReceived(self, event):
        """
        Méthode de traitement des messages arrivant
        sur un nœud de publication auquel le connecteur
        Nagios est abonné.
        """
        for item in event.items:
            # Item is a domish.IElement and a domish.Element
            # Serialize as XML before queueing,
            # or we get harmless stderr pollution  × 5 lines:
            # Exception RuntimeError: 'maximum recursion depth exceeded in
            # __subclasscheck__' in <type 'exceptions.AttributeError'> ignored
            #
            # stderr pollution caused by http://bugs.python.org/issue5508
            # and some touchiness on domish attribute access.
            xmlstr = item.toXml()
            LOGGER.debug(u'Got item: %s', xmlstr)

            if item.name != 'item':
                # The alternative is 'retract', which we silently ignore
                # We receive retractations in FIFO order,
                # ejabberd keeps 10 items before retracting old items.
                LOGGER.debug(u'Skipping unrecognized item (%s)', item.name)
                continue

            data = item.firstChildElement()
            self.forwardMessage(data, source="bus")
