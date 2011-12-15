# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Nagios <-> Bus connector"""


from __future__ import absolute_import
import os
import sys

from twisted.application import service


def makeService(options):
    """ the service that wraps everything the connector needs. """
    from vigilo.connector import getSettings
    settings = getSettings(options)

    from vigilo.common.logging import get_logger
    LOGGER = get_logger(__name__)

    from vigilo.common.gettext import translate
    _ = translate(__name__)

    from vigilo.connector.client import client_factory
    from vigilo.connector.handlers import buspublisher_factory
    from vigilo.connector.handlers import backupprovider_factory
    from vigilo.connector.socket import socketlistener_factory
    from vigilo.connector.status import statuspublisher_factory
    from vigilo.connector_nagios.nagioscommand import nagioscmdh_factory

    try:
        socket_filename = settings['connector-nagios']['listen_unix']
        settings['connector-nagios']['nagios_pipe']
        settings["bus"]["queue"]
    except KeyError, e:
        LOGGER.error(_("Missing configuration option: %s"), str(e))
        sys.exit(1)

    root_service = service.MultiService()

    client = client_factory(settings)
    client.setServiceParent(root_service)

    bus_publisher = buspublisher_factory(settings, client)
    socket_listener = socketlistener_factory(socket_filename)

    backup_provider = backupprovider_factory(settings, socket_listener)
    backup_provider.stat_names["queue"] = "queue-from-nagios"
    backup_provider.setServiceParent(root_service)

    bus_publisher.registerProducer(backup_provider, True)

    # Du bus vers Nagios
    ncmdh = nagioscmdh_factory(settings, client)

    # Statistiques
    servicename = options["name"]
    if servicename is None:
        servicename = "vigilo-connector-nagios"
    status_publisher = statuspublisher_factory(settings, servicename, client,
            providers=[bus_publisher, backup_provider])

    ## Du bus vers Nagios
    #if os.path.exists(pw) and not os.access(pw, os.W_OK):
    #    msg = _("Can't write to the Nagios command pipe: '%s'") % pw
    #    LOGGER.error(msg)
    #    raise OSError(msg)
    #if not os.access(os.path.dirname(pw), os.X_OK):
    #    msg = _("Can't traverse directory: '%(dir)s'") % \
    #            {'dir': os.path.dirname(pw)}
    #    LOGGER.error(msg)
    #    raise OSError(msg)
    #message_consumer = XMPPToPipeForwarder(
    #        pw,
    #        bkpfile,
    #        settings['connector']['backup_table_from_bus'])
    #message_consumer.setHandlerParent(xmpp_client)
    ## pour les stats: gestion de la file d'attente du consommateur
    #message_publisher.from_bus = message_consumer

    return root_service
