# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Teste les particularités de NagiosSender
"""

import unittest

# ATTENTION: ne pas utiliser twisted.trial, car nose va ignorer les erreurs
# produites par ce module !!!
#from twisted.trial import unittest
from nose.twistedtools import deferred

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.connector_nagios.nagiossender import NagiosSender

class FakeForwarder(object):
    queue = []

class NagiosSenderTestCase(unittest.TestCase):

    def setUp(self):
        self.ns = NagiosSender("", None, None)

    @deferred(timeout=30)
    def test_replace_queue_stat(self):
        """La stat de file d'attente doit venir de queue_source"""
        ff = FakeForwarder()
        ff.queue = range(42)
        self.ns.from_bus = ff
        d = self.ns.getStats()
        def check(stats):
            print stats
            self.assertTrue("queue-from-bus" in stats)
            self.assertTrue("queue-from-nagios" in stats)
            self.assertFalse("queue" in stats)
            self.assertEqual(stats["queue-from-bus"], 42)
        d.addCallback(check)
        return d

