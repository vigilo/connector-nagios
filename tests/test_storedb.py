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
from socket import socket, AF_UNIX, SOCK_STREAM

from vigilo.common.conf import settings
settings.load_module(__name__)

NS_EVENT = 'http://www.projet-vigilo.org/xmlns/event1'
NS_PERF = 'http://www.projet-vigilo.org/xmlns/perf1'


class TestDBRetry(unittest.TestCase):
    """Teste la sauvegarde locale de messages en cas d'erreur."""

    def test_store_message(self):
        """Stockage local d'un message lorsque le bus est indisponible."""

        # Demarrage en tâche de fond du connector-nagios.
        commandline = ["%s/bin/vigilo-connector-nagios" % os.getcwd(), "-n", "-l", "-"]

        adr_socket = settings['connector-nagios']['listen_unix']

        # suppression du fichier socket au cas où un test précédent
        # l'aurait laissé trainer.
        if os.path.exists(adr_socket):
            remove(adr_socket)

        # Mise en tache de fond du connector nagios.
        p = Popen(commandline, bufsize=1, stdin=PIPE, stdout=PIPE, env=os.environ)

        # attente que la commande précédente s'exécute
        time.sleep(2)
        pid = p.pid

        raw_av = raw_ap = 0

        try:
            # connection à la database puis récupération du nombre d'enregistrement
            base = settings['connector']['backup_file']

            conn = sqlite3.connect(base)
            cur = conn.cursor()
            # récupération du nombre de messages dans la table avant send
            requete = 'select count(*) from ' + \
                settings['connector']['backup_table_to_bus']
            cur.execute(requete)
            raw_av = cur.fetchone()[0]

            # Connexion à la socket
            tsocket = socket(AF_UNIX, SOCK_STREAM)
            tsocket.connect(adr_socket) 
            dico = {'ns': NS_PERF}    
            b = tsocket.send("""<perf xmlns='%(ns)s'><timestamp>1165939739</timestamp><host>serveur1.example.com</host><datasource>Load</datasource><value>10</value></perf>\n""" % dico)
            time.sleep(1)

            # récupération du nombre de messages dans la table après send
            cur.execute(requete)
            raw_ap = cur.fetchone()[0]

            tsocket.close()
            cur.close()
            conn.close()

        # TODO Changer pour capturer uniquement les exceptions pertinentes.
        except:
            pass

        # On veut savoir ce qu'il sait passé dans le processus fils.
        os.kill(pid, signal.SIGTERM)    # suppression du process connector nagios
        print p.stdout.read()

        # vérification que le message a été sauvegardé
        self.assertEqual(raw_av + 1, raw_ap)      
    
if __name__ == "__main__": 
    unittest.main()

