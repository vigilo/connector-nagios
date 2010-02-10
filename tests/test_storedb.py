# -*- coding: utf-8 -*-
'''
Created on 30 sept. 2009

@author: smoignar
'''
# Teste la sauvegarde d'un message nagios dans la database 
# Cas ou le bus n'est pas actif 
from __future__ import absolute_import
import unittest
from subprocess import Popen, PIPE
from os import kill, remove, putenv, system, getcwd
import time
from socket import socket, AF_UNIX, SOCK_STREAM
from vigilo.common.conf import settings
import sqlite3

NS_EVENT = 'http://www.projet-vigilo.org/xmlns/event1'
NS_PERF = 'http://www.projet-vigilo.org/xmlns/perf1'


class TestSauveDB(unittest.TestCase):
    # Message from Socket impossible to forward(XMPP BUS not connected)
    # Vérification que le message est sauvegardé dans la database 
    def test_startconnector(self):
        # Demarrage en tâche de fond du connector nagiosnom_connector 
        # Mise en place d'une variable environnement de test TESTNAGIOS
       
        commandline = "%(WD)s/bin/connector-nagios" % {'WD': getcwd()}
        
        # Mise en tache de fond du connector nagios, mise place de la variable d'environnement 
        # pour TEST fonctionnel avec un serveur inexistant
        p = Popen(commandline, bufsize=1, stdin=PIPE, stdout=PIPE, env={
            'VIGILO_SETTINGS': getcwd() + "/settings_tests.ini",
            })
        # attente que la commande précédente s'exécute
        time.sleep(2)
        pid = p.pid
        
        # connection à la database puis récupération du nombre d'enregistrement
        base = settings['connector']['backup_file']
        conn = sqlite3.connect(base)
        cur = conn.cursor()
        # récupération du nomnbre de message dans la table avant send
        requete = 'select count(*) from ' + settings['connector']['backup_table_to_bus']
        cur.execute(requete)
        raw_av = cur.fetchone()[0]

        # Création de la socket
        tsocket = socket(AF_UNIX, SOCK_STREAM)
        adr_socket = settings['connector-nagios']['listen_unix']
        tsocket.connect(adr_socket) 
        dico = {'ns': NS_PERF}    
        b = tsocket.send("""<perf xmlns='%(ns)s'><timestamp>1165939739</timestamp><host>serveur1.example.com</host><datasource>Load</datasource><value>10</value></perf>\n""" % dico)
        time.sleep(1)      
    
        # récupération du nombre de message dans la table après send
        cur.execute(requete)
        raw_ap = cur.fetchone()[0]
             
        tsocket.close()
        cur.close()
        conn.close()
        kill(pid, 1)    # suppression du process connector nagios
        # suppression du fichier socket
        remove (adr_socket)
        
        # vérification que le message a été sauvegardé
        self.assertEqual(raw_av +1 ,raw_ap)      

    
if __name__ == "__main__": 
    unittest.main()
