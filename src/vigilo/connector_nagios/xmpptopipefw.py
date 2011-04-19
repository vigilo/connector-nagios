# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Extends pubsub clients to compute code message.
"""
from __future__ import absolute_import

import os
import stat
import fcntl
from twisted.internet import threads
from twisted.words.xish import domish
from vigilo.pubsub import xml

from vigilo.common.conf import settings

from vigilo.common.logging import get_logger
from vigilo.connector.forwarder import PubSubListener
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


class WrongNagiosPipe(Exception):
    def __str__(self):
        return _('the configured nagios command pipe is not a FIFO')


class XMPPToPipeForwarder(PubSubListener):
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
        self.max_send_simult = 1

    def isConnected(self):
        return stat.S_ISFIFO(os.stat(self.pipe_filename).st_mode)

    def processMessage(self, msg):
        if isinstance(msg, domish.Element):
            msg = self.convertXmlToNagios(msg)
        if msg is None:
            return None
        d = threads.deferToThread(self.writeToNagios, msg)
        d.addErrback(self._send_failed, msg)
        return d

    def convertXmlToNagios(self, data):
        """
        Convertisseur entre un message de commande Nagios en XML et le format
        attendu par Nagios
        """
        qualified_name = xml.namespaced_tag(data.uri, data.name)

        if qualified_name in [xml.namespaced_tag(xml.NS_NAGIOS, 'command'),
                              xml.namespaced_tag(xml.NS_COMMAND, 'command')]:

            cmd_timestamp = float(str(data.timestamp))
            cmd_name = str(data.cmdname)
            cmd_value = str(data.value)

        elif qualified_name == xml.namespaced_tag(xml.NS_STATE, 'state'):
            cmd_timestamp = float(str(data.timestamp))
            if str(data.service):
                cmd_name = 'PROCESS_SERVICE_CHECK_RESULT'
                cmd_value = "%s;%s;%s;%s" % (str(data.host), str(data.service),
                                             str(data.code), str(data.message))
            else:
                cmd_name = 'PROCESS_HOST_CHECK_RESULT'
                cmd_value = "%s;%s;%s" % (str(data.host), str(data.code),
                                          str(data.message))
        else:
            return

        LOGGER.debug('Command message to forward: %s', data.toXml())
        if cmd_name not in settings['connector-nagios']['accepted_commands']:
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
        if not self.isConnected():
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

