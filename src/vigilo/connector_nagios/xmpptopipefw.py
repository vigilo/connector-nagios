# vim: set fileencoding=utf-8 sw=4 ts=4 et :

"""
Extends pubsub clients to compute Node message.
"""
from __future__ import absolute_import


from vigilo.common.logging import get_logger
from vigilo.connector.store import DbRetry
import os
import stat
from wokkel.subprotocols import XMPPHandler
from wokkel import xmppim

LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)

class XMPPToPipeForwarder(XMPPHandler):
    """
    Receives messages from xmpp, and passes them to the pipe.
    Forward XMPP to pipe.
    """
    def connectionInitialized(self):
        """
        redefinition in order to add :
            - new observer for message type=chat;
            - sending presence.

        """
        # Called when we are connected and authenticated
        XMPPHandler.connectionInitialized(self)
        # add an observer to deal with chat message (oneToOne message)
        self.xmlstream.addObserver("/message[@type='chat']", self.chatReceived)

        
        # There's probably a way to configure it (on_sub vs on_sub_and_presence)
        # but the spec defaults to not sending subscriptions without presence.
        self.send(xmppim.AvailablePresence())
        LOGGER.info(_('ConnectionInitialized'))



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
        XMPPHandler.__init__(self)
        self.retry = DbRetry(dbfilename, dbtable)
        self.__backuptoempty = os.path.exists(dbfilename)
        self.pipe_filename = pipe_filename

    def sendQueuedMessages(self):
        """
        Called to send Message previously stored
        """
        if self.__backuptoempty:
            self.__backuptoempty = False
            # XXX Ce code peut potentiellement boucler indéfiniment...
            while True:
                msg = self.retry.unstore()
                if msg is None:
                    break
                else:
                    if self.messageForward(msg) is not True:
                        # we loose the ability to send message again
                        self.__backuptoempty = True
                        break
            self.retry.vacuum()


    def connectionMade(self):
        """Called when a connection is made.

        This may be considered the initializer of the protocol, because
        it is called when the connection is completed.  For clients,
        this is called once the connection to the server has been
        established; for servers, this is called after an accept() call
        stops blocking and a socket has been received.  If you need to
        send any greeting or initial message, do it here.
        """
        self.sendQueuedMessages()
    
    def messageForward(self, msg):
        """
        function to forward the message to the pipe
        @param msg: message to forward
        @type msg: C{str}
        """

        if self.__backuptoempty and not self.__emptyingbackup:
            self.sendQueuedMessages()
        try:
            # testing there is a pipe (FIFO) which exist.
            if not stat.S_ISFIFO(os.stat(self.pipe_filename).st_mode):
                self.retry.store(msg)
                self.__backuptoempty = True
                return
            # XXX il serait possible d'aggréger les écritures si on flush
            #  après chaque écriture (pour ne pas ouvrir/fermer le pipe à
            # chaque fois
            # (texte suivant issue du code de nsca)
# /* if we don't fflush() then we're writing in 4k non-CR-terminated blocks, and
#  * anything else (eg. pscwatch) which writes to the file will be writing into
#  * the middle of our commands.
#  */
            pipe = open(self.pipe_filename, 'w')
            pipe.write(msg + '\n')
            pipe.close()
            return True
        except OSError, e:
            LOGGER.error(_('Message impossible to forward %(error_message)s' +
                           ', the message is stored for later reemission') % \
                            {'error_message': str(e)})
            self.retry.store(msg)
            self.__backuptoempty = True


    def chatReceived(self, msg):
        """ 
        function to treat a received chat message 
        
        @param msg: msg to treat
        @type  msg: Xml object

        """
        # It should only be one body
        # Il ne devrait y avoir qu'un seul corps de message (body)
        bodys = [element for element in msg.elements()
                         if element.name in ('body',)]

        for b in bodys:
            for data in b.elements():
                # the data we need is just underneath
                # les données dont on a besoin sont juste en dessous
                if data.name != 'command' and data['type'] not in \
                    settings['connector-nagios']['vigilo_connector_accepted_command_types']:
                    LOGGER.error(_("Command type (type: '%s') " 
                        "unrecognized or disallowed by policy") % data['type'])
                    continue
                for raw in data.children:
                    LOGGER.debug(_('Chat message to forward: %s') % raw)
                    self.messageForward(raw)

