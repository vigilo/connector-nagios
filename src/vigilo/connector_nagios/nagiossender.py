# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Relai des messages Nagios vers le bus
"""

from __future__ import absolute_import

import os
import stat
import fcntl
from twisted.internet import threads
from twisted.words.xish import domish
from vigilo.pubsub import xml

from vigilo.common.conf import settings

from vigilo.connector.sockettonodefw import SocketToNodeForwarder

from vigilo.common.logging import get_logger
LOGGER = get_logger(__name__)

from vigilo.common.gettext import translate
_ = translate(__name__)


class NagiosSender(SocketToNodeForwarder):
    """
    Quasiment comme L{SocketToNodeForwarder}, mais remplace les stats de file
    d'attente par celle du Forwarder spécifié dans la variable L{queue_source}.
    """

    def __init__(self, *args, **kwargs):
        super(NagiosSender, self).__init__(*args, **kwargs)
        self.from_bus = None

    def getStats(self):
        d = super(NagiosSender, self).getStats()
        def split_queues(stats):
            if self.from_bus is not None:
                stats["queue-from-nagios"] = stats["queue"]
                del stats["queue"]
                stats["queue-from-bus"] = len(self.from_bus.queue)
            return stats
        d.addCallback(split_queues)
        return d
