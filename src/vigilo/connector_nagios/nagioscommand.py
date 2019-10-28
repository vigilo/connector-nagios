# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2018 CS-SI
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
import shutil

from twisted.internet import threads, task, defer

from vigilo.connector.options import parseSubscriptions
from vigilo.connector.handlers import MessageHandler, QueueSubscriber

from vigilo.common.logging import get_logger, get_error_message
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


class NagiosCommandHandler(MessageHandler):
    """
    Transfère les messages pour Nagios du bus à son I{pipe} de commandes
    externes.
    """
    # Délai entre 2 tentatives de connexion au pipe de commandes Nagios
    _pipeDelay = 5.

    def __init__(self, pipe_filename, accepted_commands, group_writes,
                 nagiosconf):
        """
        Instancie un connecteur bus vers pipe.

        @param pipe_filename: le nom du fichier pipe de Nagios
        @type  pipe_filename: C{str}
        @param accepted_commands: liste des commandes Nagios autorisées
        @type  accepted_commands: C{list}
        @param group_writes: groupe les écritures de commandes Nagios dans le
            pipe, et réalise ces écritures de manière asynchrone
        @type  group_writes: C{bool}
        """
        super(NagiosCommandHandler, self).__init__()
        self.pipe_filename = pipe_filename
        self.accepted_commands = accepted_commands
        self.group_writes = group_writes
        self.nagiosconf = nagiosconf
        self._msg_group = []
        self._nagios_group = None
        self.tmpcmddir = "/dev/shm/vigilo-connector-nagios"
        self.flushGroupTask = task.LoopingCall(self.flushGroup)
        self.pipeTask = task.LoopingCall(self._connectToNagios)
        self._pipe = None

        # On attend d'être connectés au bus avant d'essayer d'envoyer
        # des messages à Nagios.
        self.pauseProducing()


    def connectionInitialized(self):
        super(NagiosCommandHandler, self).connectionInitialized()
        # Connexion à Nagios une fois connecté au bus.
        if not self.pipeTask.running:
            self.pipeTask.start(self._pipeDelay)


    def connectionLost(self, reason):
        super(NagiosCommandHandler, self).connectionLost(reason)
        self._disconnectFromNagios()


    def prepareTempDir(self):
        """
        Prépare un répertoire temporaire où écrire les fichiers à destination
        de Nagios. Règle aussi les droits pour que Nagios puisse y accéder.
        """
        assert self._nagios_group is not None
        if os.path.exists(self.tmpcmddir):
            return
        os.mkdir(self.tmpcmddir)
        os.chown(self.tmpcmddir, -1, self._nagios_group)
        os.chmod(self.tmpcmddir,
                 stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR |
                 stat.S_IRGRP | stat.S_IWGRP | stat.S_IXGRP |
                 stat.S_IROTH | stat.S_IXOTH) # 775


    def isConnected(self):
        """
        Teste la disponibilité du pipe de Nagios
        @rtype: C{boolean}
        """
        return self._pipe is not None


    def _disconnectFromNagios(self):
        self.pauseProducing()
        if self.group_writes and self.flushGroupTask.running:
            self.flushGroupTask.stop()

        if self._pipe is not None:
            try:
                # Fermer self._pipe ferme aussi le descripteur de fichier
                # sous-jacent.
                self._pipe.close()
            except:
                pass
            finally:
                self._pipe = None


    def _connectToNagios(self):
        LOGGER.info(_("Connecting to Nagios through '%s'"), self.pipe_filename)
        if not (os.path.exists(self.pipe_filename) and
            stat.S_ISFIFO(os.stat(self.pipe_filename).st_mode)):
            return

        try:
            # Lorsqu'on ouvre un pipe en écriture seule en mode non-bloquant,
            # une erreur ENXIO est retournée si le pipe n'est pas connecté.
            fd = os.open(self.pipe_filename, os.O_WRONLY | os.O_NONBLOCK)
        except OSError as e:
            LOGGER.debug("Error: %s" % get_error_message(e))
            return

        try:
            self._pipe = os.fdopen(fd, 'w')
        except OSError as e:
            LOGGER.debug("Error: %(msg)s (fd=%(fd)r)" % {
                'msg': get_error_message(e), 'fd': fd})
            os.close(fd)
            return

        if self.group_writes and not self.flushGroupTask.running:
            self.flushGroupTask.start(1)
        self.resumeProducing()
        self.pipeTask.stop()
        LOGGER.info(_("Successfully connected to Nagios through '%s'"),
                      self.pipe_filename)


    def processMessage(self, msg):
        if "host" in msg and not self.nagiosconf.has(msg["host"]):
            return # pas pour moi
        return self._processMessage(msg)

    def _processMessage(self, msg):
        self._msg_group.append(msg)
        if self.group_writes:
            return defer.succeed(None)
        else:
            return self.flushGroup()


    def flushGroup(self):
        """Traite les messages en attente à destination de Nagios"""
        msg = self.convertGroupToNagios()
        if msg is None:
            return None
        d = threads.deferToThread(self.writeToNagios, msg)
        return d


    def convertGroupToNagios(self):
        """
        Convertit les messages en attente en une commande à destination de
        Nagios. S'il y a plusieurs messages en attente, les messages Nagios
        correspondants sont écrits dans un fichier temporaire, et la commande
        retournée à destination de Nagios est un C{PROCESS_FILE}.

        @rtype: C{str}
        """
        if len(self._msg_group) == 0:
            return
        elif len(self._msg_group) == 1:
            # Envoi direct, pas de fichier temporaire
            return self.convertToNagios(self._msg_group.pop())
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
            self.prepareTempDir()
            tmpfile, tmpfilename = tempfile.mkstemp(dir=self.tmpcmddir)
            os.write(tmpfile, "\n".join(commands))
            os.write(tmpfile, '\n')
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
        if data["type"] == "nagios":
            cmd_name = data["cmdname"]
            cmd_value = data["value"]

        elif data["type"] == "state":
            if "service" in data and data["service"]:
                cmd_name = 'PROCESS_SERVICE_CHECK_RESULT'
                cmd_value = u"%(host)s;%(service)s;%(code)s;%(message)s" % data
            else:
                cmd_name = 'PROCESS_HOST_CHECK_RESULT'
                cmd_value = u"%(host)s;%(code)s;%(message)s" % data
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
        res = u"[%s] %s;%s" % (cmd_timestamp, cmd_name, cmd_value)
        return res.encode('utf-8')


    def writeToNagios(self, msg):
        """
        Écrit dans le pipe de Nagios. Cette fonction est bloquante, elle doit
        être exécutée dans un thread.

        @param msg: commande Nagios
        @type  msg: C{str}
        """
        if not self.isConnected():
            raise RuntimeError(_("Not connected to Nagios yet!"))

        LOGGER.debug("Writing to %(pipe)s: %(msg)s", {
            'pipe': self.pipe_filename,
            'msg': msg,
        })

        try:
            # Le lock + flush permet d'éviter que les données d'un autre
            # processus ne soit entrelacées avec les nôtres.
            fcntl.flock(self._pipe, fcntl.LOCK_EX)
            try:
                self._pipe.write(msg + '\n')
                self._pipe.flush()
            finally:
                fcntl.flock(self._pipe, fcntl.LOCK_UN)
        except Exception as e:
            # En général, cela signifie que la connexion est perdue.
            # On force une reconnexion.
            self._disconnectFromNagios()
            if not self.pipeTask.running:
                self.pipeTask.start(self._pipeDelay)
            raise RuntimeError(
                _("The connection to Nagios was lost (%s), reconnecting...") %
                get_error_message(e))



def nagioscmdh_factory(settings, client, nagiosconf):
    try:
        commands = settings['connector-nagios'].as_list('accepted_commands')
    except KeyError:
        commands = []
    pipe = settings['connector-nagios']['nagios_pipe']
    queue = settings["bus"]["queue"]
    queue_messages_ttl = int(settings['bus'].get('queue_messages_ttl', 0))
    prefetch_count = int(settings['bus'].get('prefetch_count', QueueSubscriber.prefetch_count))
    try:
        group_nc = settings['connector-nagios'].as_bool('group_nagios_commands')
    except KeyError:
        group_nc = False
    nch = NagiosCommandHandler(pipe, commands, group_nc, nagiosconf)
    nch.setClient(client)
    try:
        shutil.rmtree(nch.tmpcmddir)
    except OSError:
        pass
    subs = parseSubscriptions(settings)
    nch.subscribe(queue, queue_messages_ttl, subs, prefetch_count=prefetch_count)
    return nch
