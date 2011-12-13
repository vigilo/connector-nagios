# -*- coding: utf-8 -*-
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Teste l'envoi du bus vers le pipe Nagios
"""
import os
import tempfile
import shutil
import unittest

# ATTENTION: ne pas utiliser twisted.trial, car nose va ignorer les erreurs
# produites par ce module !!!
#from twisted.trial import unittest
from nose.twistedtools import reactor, deferred

from mock import Mock
from txamqp.message import Message
from txamqp.content import Content

#from twisted.words.xish import domish

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.connector_nagios.nagioscommand import NagiosCommandHandler
#from vigilo.pubsub.xml import NS_NAGIOS, NS_STATE
from vigilo.connector.test.helpers import json



class NagiosCommandTestCase(unittest.TestCase):
    """Teste la sauvegarde locale de messages en cas d'erreur."""


    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test-connector-nagios-")
        self.pipe = os.path.join(self.tmpdir, "pipe")
        open(self.pipe, "w").close() # on crée le fichier
        #os.mkfifo(self.pipe)
        accepted = ["PROCESS_SERVICE_CHECK_RESULT", "PROCESS_HOST_CHECK_RESULT"]
        self.nch = NagiosCommandHandler(self.pipe, accepted, 0)
        self.nch.registerProducer(Mock(), True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)


    @deferred(timeout=30)
    def test_send_msg(self):
        """Stockage local d'un message lorsque le bus est indisponible."""
        # Preparation du message
        msg = { "type": "nagios",
                "timestamp": "0",
                "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                "value": "test",
                }
        # Désactivation de la vérification du FIFO
        setattr(self.nch, "isConnected", lambda: True)
        # Envoi du message
        d = self.nch.write(Message(None, None, Content(json.dumps(msg))))
        def check_result(r):
            pipe = open(self.pipe, "r")
            content = pipe.read()
            pipe.close()
            print repr(content)
            self.assertEqual(content, "[0.0] PROCESS_SERVICE_CHECK_RESULT;"
                    "test\n", "Le contenu du pipe n'est pas bon")
        d.addCallback(check_result)
        return d


    def test_convertToNagios_nagios(self):
        """
        Conversion d'un message de commande en syntaxe Nagios
        """
        msg = { "type": "nagios",
                "timestamp": "0",
                "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                "value": "test",
                }
        result = self.nch.convertToNagios(msg)
        self.assertEqual(result, "[0.0] PROCESS_SERVICE_CHECK_RESULT;test",
                         "La conversion en commande Nagios n'est pas bonne")


    def _make_state_msg(self, service='', code='1', message='Test message'):
        return { "type": "state",
                 "timestamp": "1239104006",
                 "host": "server.example.com",
                 "ip": "192.168.1.1",
                 "service": service,
                 "code": str(code),
                 "statetype": "HARD",
                 "attempt": "2",
                 "message": message,
                 }


    def test_convertToNagios_state_service(self):
        """
        Conversion d'un message "state" sur un service
        """
        msg = self._make_state_msg(service='Load', code=1,
                    message='WARNING: Load average is above 4 (4.5)')
        result = self.nch.convertToNagios(msg)
        self.assertEqual(result, "[1239104006.0] PROCESS_SERVICE_CHECK_RESULT;"
                "server.example.com;Load;1;WARNING: Load average is above 4 "
                "(4.5)", "La conversion en commande Nagios n'est pas bonne")


    def test_convertToNagios_state_host(self):
        """
        Conversion d'un message "state" sur un hôte
        """
        msg = self._make_state_msg(code=2,
                message="CRITICAL: Host unreachable (192.168.1.1)")
        result = self.nch.convertToNagios(msg)
        self.assertEqual(result, "[1239104006.0] PROCESS_HOST_CHECK_RESULT;"
                "server.example.com;2;CRITICAL: Host unreachable (192.168.1.1)",
                 "La conversion en commande Nagios n'est pas bonne")


    def test_convertToNagios_state_host_unicode(self):
        """
        Conversion d'un message "state" avec caractères accentués
        """
        msg = self._make_state_msg(message=u'OK: Décalage 0.0s')
        result = self.nch.convertToNagios(msg)
        self.assertTrue(result.endswith("Décalage 0.0s"),
                "Les caractères accentués du message posent problème")


    def test_convertToNagios_state_svc_unicode(self):
        """
        Conversion d'un message "state" avec caractères accentués
        """
        msg = self._make_state_msg(service="NTP", message=u'OK: Décalage 0.0s')
        result = self.nch.convertToNagios(msg)
        self.assertTrue(result.endswith("Décalage 0.0s"),
                "Les caractères accentués du message posent problème")


    def test_convertToNagios_command_unicode(self):
        """
        Conversion d'un message "command" avec caractères accentués
        """
        msg = { "type": "nagios",
                "timestamp": "0",
                "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                "value": u"test accentué",
                }
        result = self.nch.convertToNagios(msg)
        self.assertTrue(result.endswith("accentué"),
                "Les caractères accentués du message posent problème")

