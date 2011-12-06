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
from nose.twistedtools import deferred

from twisted.words.xish import domish

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.connector_nagios.xmpptopipefw import XMPPToPipeForwarder
from vigilo.pubsub.xml import NS_NAGIOS, NS_STATE


class TestForwarder(unittest.TestCase):
    """Teste la sauvegarde locale de messages en cas d'erreur."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test-connector-nagios-")
        self.pipe = os.path.join(self.tmpdir, "pipe")
        open(self.pipe, "w").close() # on crée le fichier
        #os.mkfifo(self.pipe)
        self.fwd = XMPPToPipeForwarder(self.pipe, None, None)

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    @deferred(timeout=30)
    def test_send_msg(self):
        """Stockage local d'un message lorsque le bus est indisponible."""
        # Preparation du message
        msg = domish.Element((NS_NAGIOS, 'command'))
        msg.addElement('timestamp', content="0")
        msg.addElement('cmdname', content="PROCESS_SERVICE_CHECK_RESULT")
        msg.addElement('value', content="test")
        # Désactivation de la vérification du FIFO
        setattr(self.fwd, "isConnected", lambda: True)
        # Envoi du message
        d = self.fwd.processMessage([msg])
        def check_result(r):
            self.failUnless(os.path.exists(self.pipe),
                            "Rien n'a été écrit dans le pipe")
            pipe = open(self.pipe, "r")
            content = pipe.read()
            self.assertEqual(content, "[0.0] PROCESS_SERVICE_CHECK_RESULT;"
                    "test\n", "Le contenu du pipe n'est pas bon")
            pipe.close()
        d.addCallback(check_result)
        return d

    def test_convertToNagios_command(self):
        """
        Message "command"
        """
        msg = domish.Element((NS_NAGIOS, 'command'))
        msg.addElement('timestamp', content="0")
        msg.addElement('cmdname', content="PROCESS_SERVICE_CHECK_RESULT")
        msg.addElement('value', content="test")
        result = self.fwd.convertXmlToNagios(msg)
        self.assertEqual(result, "[0.0] PROCESS_SERVICE_CHECK_RESULT;test",
                         "La conversion en commande Nagios n'est pas bonne")

    def _make_state_msg(self, service=None, code='1', message='Test message'):
        msg = domish.Element((NS_STATE, 'state'))
        msg.addElement('timestamp', content='1239104006')
        msg.addElement('host', content='server.example.com')
        msg.addElement('ip', content='192.168.1.1')
        if service is not None:
            msg.addElement('service', content=service)
        msg.addElement('code', content=str(code))
        msg.addElement('type', content='HARD')
        msg.addElement('attempt', content='2')
        msg.addElement('message', content=message)
        return msg

    def test_convertToNagios_state_service(self):
        """
        Message "state" sur un service
        """
        msg = self._make_state_msg(service='Load', code=1,
                    message='WARNING: Load average is above 4 (4.5)')
        result = self.fwd.convertXmlToNagios(msg)
        self.assertEqual(result, "[1239104006.0] PROCESS_SERVICE_CHECK_RESULT;"
                "server.example.com;Load;1;WARNING: Load average is above 4 "
                "(4.5)", "La conversion en commande Nagios n'est pas bonne")

    def test_convertToNagios_state_host(self):
        """
        Message "state" sur un hôte
        """
        msg = self._make_state_msg(code=2,
                message="CRITICAL: Host unreachable (192.168.1.1)")
        result = self.fwd.convertXmlToNagios(msg)
        self.assertEqual(result, "[1239104006.0] PROCESS_HOST_CHECK_RESULT;"
                "server.example.com;2;CRITICAL: Host unreachable (192.168.1.1)",
                 "La conversion en commande Nagios n'est pas bonne")

    def test_convertToNagios_state_host_unicode(self):
        """
        Message "state" avec caractères accentués
        """
        msg = self._make_state_msg(message=u'OK: Décalage 0.0s')
        result = self.fwd.convertXmlToNagios(msg)
        self.assertTrue(result.endswith("Décalage 0.0s"),
                "Les caractères accentués du message posent problème")

    def test_convertToNagios_state_svc_unicode(self):
        """
        Message "state" avec caractères accentués
        """
        msg = self._make_state_msg(service="NTP", message=u'OK: Décalage 0.0s')
        result = self.fwd.convertXmlToNagios(msg)
        self.assertTrue(result.endswith("Décalage 0.0s"),
                "Les caractères accentués du message posent problème")

    def test_convertToNagios_command_unicode(self):
        """
        Message "command" avec caractères accentués
        """
        msg = domish.Element((NS_NAGIOS, 'command'))
        msg.addElement('timestamp', content="0")
        msg.addElement('cmdname', content="PROCESS_SERVICE_CHECK_RESULT")
        msg.addElement('value', content=u"test accentué")
        result = self.fwd.convertXmlToNagios(msg)
        self.assertTrue(result.endswith("accentué"),
                "Les caractères accentués du message posent problème")

