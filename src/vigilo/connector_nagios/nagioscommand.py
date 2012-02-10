# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Tranfert des messages C{nagios} depuis le bus vers Nagios, en passant par son
I{pipe} de commandes externes.
"""
from __future__ import absolute_import

import os
import stat
import fcntl
import tempfile
import time
import stat

from twisted.internet import threads, defer

from vigilo.connector.options import parseSubscriptions
from vigilo.connector.handlers import MessageHandler

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)



class WrongNagiosPipe(Exception):
    def __str__(self):
        return _('the configured nagios command pipe is not a FIFO')



class NagiosCommandHandler(MessageHandler):
    """
    Transfère les messages pour Nagios du bus à son I{pipe} de commandes
    externes.
    """


    def __init__(self, pipe_filename, accepted_commands, group_size,
                 nagiosconf):
        """
        Instancie un connecteur XMPP vers pipe.

        @param pipe_filename: le nom du fichier pipe de Nagios
        @type  pipe_filename: C{str}
        """
        super(NagiosCommandHandler, self).__init__()
        self.pipe_filename = pipe_filename
        self.accepted_commands = accepted_commands
        self.msg_group_size = group_size
        self.nagiosconf = nagiosconf
        self._msg_group = []
        self._nagios_group = None


    def isConnected(self):
        return (os.path.exists(self.pipe_filename) and
                stat.S_ISFIFO(os.stat(self.pipe_filename).st_mode))


    def processMessage(self, msg):
        if (msg["type"] == "nagios" and "host" in msg
                and not self.nagiosconf.has(msg["host"])):
            return # pas pour moi
        return self._processMessage(msg)

    def _processMessage(self, msg):
        self._msg_group.append(msg)
        if len(self._msg_group) > self.msg_group_size:
            return self.flushGroup()
        else:
            return defer.succeed(None)


    def flushGroup(self):
        msg = self.convertGroupToNagios()
        if msg is None:
            return None
        d = threads.deferToThread(self.writeToNagios, msg)
        return d


    def convertGroupToNagios(self):
        if len(self._msg_group) == 0:
            return
        elif len(self._msg_group) == 1:
            # Envoi direct, pas de fichier temporaire
            return self.convertToNagios(self._msg_group[0])
        else:
            commands = []
            while self._msg_group:
                msg = self._msg_group.pop(0)
                cmd = self.convertToNagios(msg)
                if cmd is not None:
                    commands.append(cmd)
            if not commands:
                return
            if self._nagios_group is None:
                self._nagios_group = os.stat(self.pipe_filename).st_gid
            tmpdir = "/dev/shm/vigilo-connector-nagios"
            if not os.path.exists(tmpdir):
                os.mkdir(tmpdir)
                os.chown(tmpdir, -1, self._nagios_group)
                os.chmod(tmpdir, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                                 stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
                                 stat.S_IROTH | stat.S_IXOTH) # 775
            tmpfile, tmpfilename = tempfile.mkstemp(dir=tmpdir)
            os.write(tmpfile, "\n".join(commands))
            os.close(tmpfile)
            os.chown(tmpfilename, -1, self._nagios_group)
            os.chmod(tmpfilename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP)
            msg = "[%d] PROCESS_FILE;%s;1" % (int(time.time()), tmpfilename)
            return msg

    def convertToNagios(self, data):
        """
        Convertisseur entre un message de commande Nagios venant du bus et le
        format attendu par Nagios
        """
        cmd_timestamp = float(data["timestamp"])
        if data["type"] == "nagios" or data["type"] == "command":
            cmd_name = data["cmdname"]
            cmd_value = unicode(data["value"]).encode("utf-8")

        elif data["type"] == "state":
            if "service" in data and data["service"]:
                cmd_name = 'PROCESS_SERVICE_CHECK_RESULT'
                cmd_value = u"%(host)s;%(service)s;%(code)s;%(message)s" % data
            else:
                cmd_name = 'PROCESS_HOST_CHECK_RESULT'
                cmd_value = u"%(host)s;%(code)s;%(message)s" % data
            cmd_value = cmd_value.encode("utf-8")
        else:
            return

        LOGGER.debug('Command message to forward: %s', data)
        if cmd_name not in self.accepted_commands:
            LOGGER.error(_("Command '%(received)s' disallowed by "
                           "policy, accepted commands: %(accepted)r") % {
                            'received': cmd_name,
                            'accepted': self.accepted_commands,
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
        pipe = open(self.pipe_filename, "w")
        fcntl.flock(pipe.fileno(), fcntl.LOCK_EX)
        try:
            pipe.write(msg + '\n')
        finally:
            fcntl.flock(pipe.fileno(), fcntl.LOCK_UN)
            pipe.close()


def nagioscmdh_factory(settings, client, nagiosconf):
    try:
        commands = settings['connector-nagios'].as_list('accepted_commands')
    except KeyError:
        commands = []
    pipe = settings['connector-nagios']['nagios_pipe']
    queue = settings["bus"]["queue"]
    try:
        group_size = settings['connector-nagios'].as_int('group_size')
    except KeyError:
        group_size = 50
    nch = NagiosCommandHandler(pipe, commands, group_size, nagiosconf)
    nch.setClient(client)
    subs = parseSubscriptions(settings)
    nch.subscribe(queue, subs)
    return nch
