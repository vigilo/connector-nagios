# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2012 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Nagios <-> Bus connector"""


from __future__ import absolute_import
import os
import sys

from twisted.application import service


def makeService(options):
    """ the service that wraps everything the connector needs. """
    from vigilo.connector.options import getSettings
    settings = getSettings(options, __name__)

    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)

    from vigilo.common.gettext import translate
    _ = translate(__name__)

    from vigilo.connector.client import client_factory
    from vigilo.connector.handlers import buspublisher_factory
    from vigilo.connector.handlers import backupprovider_factory
    from vigilo.connector.socket import socketlistener_factory
    from vigilo.connector_nagios.nagioscommand import nagioscmdh_factory
    from vigilo.connector_nagios.nagiosconf import nagiosconffile_factory

    try:
        socket_filename = settings['connector-nagios']['listen_unix']
        # Statement seems to have no effect # pylint: disable-msg=W0104
        settings['connector-nagios']['nagios_pipe']
        settings["bus"]["queue"]
    except KeyError, e:
        LOGGER.error(_("Missing configuration option: %s"), str(e))
        sys.exit(1)

    root_service = service.MultiService()

    client = client_factory(settings)
    client.setServiceParent(root_service)

    # Configuration
    nagiosconf = nagiosconffile_factory(settings)
    nagiosconf.setServiceParent(root_service)

    # Nagios vers le bus :
    # socket_listener -> backup_provider -> bus_publisher
    socket_listener = socketlistener_factory(socket_filename)

    backup_provider = backupprovider_factory(settings, socket_listener)
    backup_provider.setServiceParent(root_service)

    bus_publisher = buspublisher_factory(settings, client)
    bus_publisher.registerProducer(backup_provider, True)

    # Du bus vers Nagios
    ncmdh = nagioscmdh_factory(settings, client, nagiosconf)

    # Statistiques
    from vigilo.connector.status import statuspublisher_factory
    statuspublisher_factory(settings, client,
            providers=[bus_publisher, backup_provider, ncmdh])

    return root_service
