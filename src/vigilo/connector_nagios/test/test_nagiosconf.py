# -*- coding: utf-8 -*-
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Teste la lecture des hôtes depuis la conf Nagios
"""

import os
import tempfile
import unittest

from vigilo.connector_nagios.nagiosconf import NagiosConfFile


class NagiosConfFileTestCase(unittest.TestCase):


    def setUp(self):
        tmpfd, self.tmppath = tempfile.mkstemp(prefix="test-conn-nagios")
        self.tmpfile = os.fdopen(tmpfd, "w")

    def tearDown(self):
        try:
            self.tmpfile.close()
        except OSError:
            pass # Déjà fermé
        os.remove(self.tmppath)


    def test_regexp_1(self):
        self.tmpfile.write("""
define host{
    use                     generic-active-host
    host_name               testhost-1
    alias                   Test Host 1
    address                 localhost
    check_command           check-host-alive
    hostgroups              /Tests
}

define service{
    use                     generic-active-service
    host_name               testhost-1
    service_description     Test Service
    check_command           check_test
    process_perf_data       1
}
""")
        self.tmpfile.close()
        n = NagiosConfFile(self.tmppath)
        n.reload()
        self.assertEqual(n.hosts, set(["testhost-1"]))


    def test_regexp_host_with_spaces(self):
        self.tmpfile.write("""
define host{
  host_name             Test Host Avec Espaces
  service_description   Test Service
}
""")
        self.tmpfile.close()
        print self.tmppath
        n = NagiosConfFile(self.tmppath)
        n.reload()
        self.assertEqual(n.hosts, set(["Test Host Avec Espaces"]))
