# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Nagios <-> bus connector"""
from __future__ import absolute_import

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.application import service

from vigilo.connector import options as base_options

class NagiosConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector needs.
    """
    implements(service.IServiceMaker, IPlugin)
    tapname = "vigilo-nagios"
    description = "Vigilo connector for Nagios"
    options = base_options.make_options('vigilo.connector_nagios')

    def makeService(self, options):
        """ the service that wraps everything the connector needs. """
        from vigilo.connector_nagios import makeService
        return makeService(options)

nagios_connector = NagiosConnectorServiceMaker()
