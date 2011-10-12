# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""Nagios <-> XMPP connector"""
from __future__ import absolute_import
import os
import sys

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.application import service
from twisted.words.protocols.jabber.jid import JID

from vigilo.common.gettext import translate
from vigilo.connector import client
from vigilo.connector import options as base_options

_ = translate('vigilo.connector_nagios')

class NagiosConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector needs.
    """
    implements(service.IServiceMaker, IPlugin)
    tapname = "vigilo-nagios"
    description = "Vigilo connector for Nagios"
    options = base_options.Options

    def makeService(self, options):
        """ the service that wraps everything the connector needs. """
        from vigilo.common.conf import settings
        if options["config"] is not None:
            settings.load_file(options["config"])
        else:
            settings.load_module('vigilo.connector_nagios')

        from vigilo.common.logging import get_logger
        LOGGER = get_logger('vigilo.connector_nagios')

        from vigilo.connector_nagios.xmpptopipefw import XMPPToPipeForwarder
        from vigilo.connector_nagios.nagiossender import NagiosSender

        xmpp_client = client.client_factory(settings)

        nodetopublish = settings.get('publications', {})
        _service = JID(settings['bus'].get('service', None))

        bkpfile = settings['connector'].get('backup_file', ":memory:")
        try:
            pw = settings['connector-nagios']['nagios_pipe']
            sr = settings['connector-nagios']['listen_unix']
        except KeyError, e:
            LOGGER.error(_("Missing configuration option: %s"), str(e))
            sys.exit(1)

        if bkpfile != ':memory:':
            if not os.path.exists(os.path.dirname(bkpfile)):
                msg = _("Directory not found: '%(dir)s'") % \
                        {'dir': os.path.dirname(bkpfile)}
                LOGGER.error(msg)
                raise OSError(msg)
            if not os.access(os.path.dirname(bkpfile), os.R_OK | os.W_OK | os.X_OK):
                msg = _("Wrong permissions on directory: '%(dir)s'") % \
                        {'dir': os.path.dirname(bkpfile)}
                LOGGER.error(msg)
                raise OSError(msg)

        # De Nagios vers le bus
        if not os.path.exists(os.path.dirname(sr)):
            msg = _("Directory not found: '%(dir)s'") % \
                    {'dir': os.path.dirname(sr)}
            LOGGER.error(msg)
            raise OSError(msg)
        if not os.access(os.path.dirname(sr), os.R_OK | os.W_OK | os.X_OK):
            msg = _("Wrong permissions on directory: '%(dir)s'") % \
                    {'dir': os.path.dirname(sr)}
            LOGGER.error(msg)
            raise OSError(msg)
        message_publisher = NagiosSender(
                sr, bkpfile,
                settings['connector']['backup_table_to_bus'])
        message_publisher.setHandlerParent(xmpp_client)

        # Du bus vers Nagios
        if os.path.exists(pw) and not os.access(pw, os.W_OK):
            msg = _("Can't write to the Nagios command pipe: '%s'") % pw
            LOGGER.error(msg)
            raise OSError(msg)
        if not os.access(os.path.dirname(pw), os.X_OK):
            msg = _("Can't traverse directory: '%(dir)s'") % \
                    {'dir': os.path.dirname(pw)}
            LOGGER.error(msg)
            raise OSError(msg)
        message_consumer = XMPPToPipeForwarder(
                pw,
                bkpfile,
                settings['connector']['backup_table_from_bus'])
        message_consumer.setHandlerParent(xmpp_client)
        # pour les stats: la file d'attente est celle du consommateur
        message_publisher.queue_source = message_consumer

        # Présence
        from vigilo.connector.presence import PresenceManager
        presence_manager = PresenceManager()
        presence_manager.setHandlerParent(xmpp_client)
        message_consumer.registerProducer(presence_manager, True)

        # Statistiques
        from vigilo.connector.status import StatusPublisher
        servicename = options["name"]
        if servicename is None:
            servicename = "vigilo-connector-nagios"
        stats_publisher = StatusPublisher(message_publisher,
                        settings["connector"].get("hostname", None),
                        servicename=servicename,
                        node=settings["connector"].get("status_node", None))
        stats_publisher.setHandlerParent(xmpp_client)
        presence_manager.registerStatusPublisher(stats_publisher)

        root_service = service.MultiService()
        xmpp_client.setServiceParent(root_service)
        return root_service

nagios_connector = NagiosConnectorServiceMaker()
