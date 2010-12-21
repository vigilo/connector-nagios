# -*- coding: utf-8 -*-
'''
Created on 30 sept. 2009

@author: smoignar
'''
# Teste la sauvegarde d'un message nagios dans la database 
# Cas ou le bus n'est pas actif 
import signal
import unittest
import time
import sqlite3
from subprocess import Popen, PIPE
import os, os.path
import tempfile
import shutil
from socket import socket, AF_UNIX, SOCK_STREAM

from twisted.words.xish import domish

from vigilo.common.conf import settings
settings.load_module(__name__)

from vigilo.connector.sockettonodefw import SocketToNodeForwarder
from vigilo.connector.converttoxml import NS_EVENT, NS_PERF


class TestDBRetry(unittest.TestCase):
    """Teste la sauvegarde locale de messages en cas d'erreur."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="test-conn-nagios-dbretry-")

    def tearDown(self):
        shutil.rmtree(self.tmpdir)

    def test_store_message(self):
        """Stockage local d'un message lorsque le bus est indisponible."""

        base = os.path.join(self.tmpdir, "backup.sqlite")
        tobus_table = "tobus"
        publisher = SocketToNodeForwarder(
                os.path.join(self.tmpdir, "read.sock"),
                base, tobus_table)

        # récupération du nombre de messages dans la table avant envoi
        conn = sqlite3.connect(base)
        cur = conn.cursor()
        request = 'SELECT COUNT(*) FROM ' + tobus_table
        cur.execute(request)
        before = cur.fetchone()[0]

        # Preparation du message
        msg = domish.Element((NS_PERF, 'perf'))
        msg.addElement('test', content="this is a test")

        # Envoi du message
        publisher.publishXml(msg)

        # récupération du nombre de messages dans la table apres envoi
        cur.execute(request)
        after = cur.fetchone()[0]
        cur.close()
        conn.close()

        self.assertEqual(after, before + 1)


if __name__ == "__main__": 
    unittest.main()

