# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2021 CS GROUP - France
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Chargement d'une base sqlite de configuration générée par Vigiconf pour le
connector-nagios.
"""

from __future__ import absolute_import
from __future__ import with_statement

import re

from vigilo.connector.conffile import ConfFile



class NagiosConfFile(ConfFile):
    """
    Accès à la configuration de Nagios fournie par VigiConf
    """


    def __init__(self, path):
        super(NagiosConfFile, self).__init__(path)
        self.hosts = set()
        self.regexp = re.compile(r"^\s*host_name\s+([^#]+?)\s*(#.*)?$", re.MULTILINE)


    def _read_conf(self):
        hosts = set()
        with open(self.path) as conffile:
            content = conffile.read()
            # attention, ça peut être long. deferToThread ?
            for host, comment_ in self.regexp.findall(content):
                hosts.add(host)
        self.hosts = hosts


    def has(self, hostname):
        return hostname in self.hosts


def nagiosconffile_factory(settings):
    try:
        conffile = settings['connector-nagios']['nagios_config']
    except KeyError:
        conffile = "/etc/vigilo/vigiconf/prod/nagios/nagios.cfg"
    return NagiosConfFile(conffile)
