# -*- coding: utf-8 -*-
# Copyright (C) 2006-2016 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Teste l'envoi du bus vers le pipe Nagios
"""
from __future__ import print_function
import os
import tempfile
import shutil
import unittest
import re

# ATTENTION: ne pas utiliser twisted.trial, car nose va ignorer les erreurs
# produites par ce module !!!
#from twisted.trial import unittest
from nose.twistedtools import reactor, deferred # pylint:disable-msg=W0611

from mock import Mock
from txamqp.message import Message
from txamqp.content import Content

from vigilo.connector import json
from vigilo.connector_nagios.nagioscommand import NagiosCommandHandler



class NagiosCommandTestCase(unittest.TestCase):
    """Teste la sauvegarde locale de messages en cas d'erreur."""


    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test-connector-nagios-")
        self.pipe = os.path.join(self.tmpdir, "pipe")
        open(self.pipe, "w").close() # on crée le fichier
        #os.mkfifo(self.pipe)
        accepted = ["PROCESS_SERVICE_CHECK_RESULT", "PROCESS_HOST_CHECK_RESULT"]
        self.nagiosconf = Mock()
        self.nagiosconf.has.return_value = True
        self.nch = NagiosCommandHandler(self.pipe, accepted, False,
                                        self.nagiosconf)
        self.nch.registerProducer(Mock(), False)

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
        def check_result(_r):
            pipe = open(self.pipe, "r")
            content = pipe.read()
            pipe.close()
            print(repr(content))
            self.assertEqual(content, "[0.0] PROCESS_SERVICE_CHECK_RESULT;"
                    "test\n", "Le contenu du pipe n'est pas bon")
        d.addCallback(check_result)
        return d


    def test_convertToNagios_nagios(self):
        """
        Conversion d'un message de commande en syntaxe Nagios
        """
        msg = { "type": "nagios",
                "timestamp": 0,
                "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                "value": "test",
                }
        result = self.nch.convertToNagios(msg)
        self.assertEqual(result, "[0.0] PROCESS_SERVICE_CHECK_RESULT;test",
             "La conversion en commande Nagios n'est pas bonne")


    def test_convertToNagios_nagios_unicode(self):
        """
        Conversion d'un message de commande Unicode en syntaxe Nagios
        """
        msg = { "type": u"nagios",
                "timestamp": 0,
                "cmdname": u"PROCESS_SERVICE_CHECK_RESULT",
                "value": u"test éçà",
                }
        result = self.nch.convertToNagios(msg)
        self.assertEqual(result,
            # Les octets exprimés en hexadécimal correspondent à la suite
            # de séquences UTF-8 pour les caractères "é", "ç" et "à".
            "[0.0] PROCESS_SERVICE_CHECK_RESULT;test \xC3\xA9\xC3\xA7\xC3\xA0",
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


    @deferred(timeout=30)
    def test_is_local(self):
        """Envoi d'un message sur un hôte local"""
        # Preparation du message
        msg = { "type": "nagios",
                "timestamp": "0",
                "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                "value": "test",
                "host": "testhost",
                }
        self.nagiosconf.has.return_value = True
        self.nch.writeToNagios = Mock()
        # Envoi du message
        d = self.nch.write(Message(None, None, Content(json.dumps(msg))))
        def check(_r):
            self.assertTrue(self.nch.writeToNagios.called)
        d.addCallback(check)
        return d


    @deferred(timeout=30)
    def test_is_not_local(self):
        """Ignorer les messages sur un hôte non local"""
        # Preparation des message
        msg_n = { "type": "nagios",
                  "timestamp": "0",
                  "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                  "value": "test",
                  "host": "testhost",
                  }
        msg_n = Message(None, None, Content(json.dumps(msg_n)))
        msg_s = self._make_state_msg(service="test state",
                                     message=u'test state')
        msg_s = Message(None, None, Content(json.dumps(msg_s)))
        self.nagiosconf.has.return_value = False
        self.nch.writeToNagios = Mock()
        # Envoi des message
        d = self.nch.write(msg_n)
        d.addCallback(lambda _x: self.nch.write(msg_s))
        def check(_r):
            print(self.nch.writeToNagios.call_args_list)
            self.assertFalse(self.nch.writeToNagios.called,
                             "Un message à ignorer à été traité")
        d.addCallback(check)
        return d


    @deferred(timeout=30)
    def test_message_group(self):
        """Envoi d'un groupe de messages à Nagios"""
        # Preparation des messages
        msgs = []
        for i in range(10):
            msgs.append({ "type": "nagios",
                          "timestamp": "0",
                          "cmdname": "PROCESS_SERVICE_CHECK_RESULT",
                          "value": "test %d" % i,
                          })
        self.nch.group_writes = True
        # Désactivation de la vérification du FIFO
        setattr(self.nch, "isConnected", lambda: True)
        # Envoi des message
        for msg in msgs:
            self.nch.write(Message(None, None, Content(json.dumps(msg))))
        d = self.nch.flushGroup()
        def check_result(_r):
            pipe = open(self.pipe, "r")
            maincmd = pipe.read()
            pipe.close()
            print(repr(maincmd))
            maincmd_mo = re.match("\[\d+\] PROCESS_FILE;([^;]+);1\n", maincmd)
            self.assertTrue(maincmd_mo is not None,
                            "Le contenu du pipe n'est pas bon")
            self.assertTrue(os.path.exists(maincmd_mo.group(1)))
            tmpfile = open(maincmd_mo.group(1), "r")
            subcmds = tmpfile.read()
            tmpfile.close()
            print(repr(subcmds))
            expected = "".join([
                    "[0.0] PROCESS_SERVICE_CHECK_RESULT;test %d\n" % i
                    for i in range(10) ])
            self.assertEqual(subcmds, expected,
                    "Le contenu du fichier temporaire n'est pas bon")
        d.addCallback(check_result)
        return d
