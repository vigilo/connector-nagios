# -*- coding: utf-8 -*-
'''
Created on 29 sept. 2009
@author: smoignar

'''
from __future__ import absolute_import

import unittest

from vigilo.connector.converttoxml import text2xml

NS_EVENT = 'http://www.projet-vigilo.org/xmlns/event1'
NS_PERF = 'http://www.projet-vigilo.org/xmlns/perf1'

class TestSequenceFunctions(unittest.TestCase):
    """ Test the connector nagios functions """
    
    def test_event2xml(self):
        """ Test the connector function event2xml """
        dico = {'ns': NS_EVENT}
        # subfunction event2xml 
        self.assertEqual("""<event xmlns='%(ns)s'><timestamp>1165939739</timestamp><host>serveur1.example.com</host><ip>192.168.0.1</ip><service>Load</service><state>CRITICAL</state><message>CRITICAL: load avg: 12 10 10</message></event>""" % dico, text2xml("""event|1165939739|serveur1.example.com|192.168.0.1|Load|CRITICAL|CRITICAL: load avg: 12 10 10""").toXml())
    
    def test_perft2xml(self):
        """ Test the connector function perf2xml """
        dico = {'ns': NS_PERF}
        # subfunction perf2xml 
        self.assertEqual("""<perf xmlns='%(ns)s'><timestamp>1165939739</timestamp><host>serveur1.example.com</host><datasource>Load</datasource><value>10</value></perf>""" % dico, text2xml("""perf|1165939739|serveur1.example.com|Load|10""").toXml())   
    
if __name__ == "__main__": 
    unittest.main()
