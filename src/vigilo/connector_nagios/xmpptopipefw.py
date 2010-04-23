# vim: set fileencoding=utf-8 sw=4 ts=4 et :

"""
Extends pubsub clients to compute Node message.
"""
from __future__ import absolute_import


from vigilo.common.logging import get_logger
from vigilo.connector.store import DbRetry
import os
import stat
import fcntl
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
        LOGGER.debug(_('Connection initialized'))



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
    
    def messageForward(self, cmd_timestamp, cmd_name, cmd_value):
        """
        function to forward the message to the pipe
        @param msg: message to forward
        @type msg: C{str}
        """

        # TODO: ajouter des tests unitaires
        msg = "[%s] %s;%s" % (cmd_timestamp, cmd_name, cmd_value)
        if self.__backuptoempty and not self.__emptyingbackup:
            self.sendQueuedMessages()
        try:
            # testing there is a pipe (FIFO) which exist.
            if not stat.S_ISFIFO(os.stat(self.pipe_filename).st_mode):
                LOGGER.error(_('The configured nagios command pipe is not '
                        'a FIFO. Storing message for later.'))
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
            LOGGER.debug(_("Writing to %s: %s") % (self.pipe_filename, msg))
            # cannot open in append mode, since that causes a seek
            pipe = os.open(self.pipe_filename, os.O_WRONLY)
            fcntl.flock(pipe, fcntl.LOCK_EX)
            os.write(pipe, msg + '\n')
            fcntl.flock(pipe, fcntl.LOCK_UN)
            os.close(pipe)
            return True
        except OSError, e:
            LOGGER.error(_('Unable to forward message %(error_message)s, '
                           'this message is stored for later reemission.') % \
                            {'error_message': str(e)})
            self.retry.store(msg)
            self.__backuptoempty = True


    def chatReceived(self, msg):
        """ 
        function to treat a received chat message 
        
        @param msg: msg to treat
        @type  msg: Xml object

        """
        # TODO: ajouter des tests unitaires
        from vigilo.common.conf import settings
        settings.load_module(__name__)

        # It should only be one body
        # Il ne devrait y avoir qu'un seul corps de message (body)
        bodys = [element for element in msg.elements()
                         if element.name in ('body',)]

        for b in bodys:
            for data in b.elements():
                # the data we need is just underneath
                # les données dont on a besoin sont juste en dessous
                if data.name != 'command':
                    LOGGER.error(_("Unrecognized message type: '%s'")
                                    % data.cmdname)
                    continue
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
                    continue
                LOGGER.debug(_('Command message to forward: '
                                'ts=%s name=%s val=%s') % (
                                    cmd_timestamp,
                                    cmd_name,
                                    cmd_value,
                                ))
                self.messageForward(cmd_timestamp, cmd_name, cmd_value)

