# vim: set fileencoding=utf-8 sw=4 ts=4 et :
""" Nagios connector Pubsub client. """
from __future__ import absolute_import, with_statement
import os

from zope.interface import implements
from twisted.plugin import IPlugin
from twisted.application import service
from twisted.words.protocols.jabber.jid import JID

from vigilo.common.gettext import translate
from vigilo.connector import client, options

_ = translate('vigilo.connector_metro')

class NagiosConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector needs.
    """
    implements(service.IServiceMaker, IPlugin)
    tapname = "vigilo-nagios"
    description = "Vigilo connector (for Nagios)"
    options = options.Options

    def makeService(self, options):
        """ the service that wraps everything the connector needs. """
        from vigilo.common.conf import settings
        settings.load_module('vigilo.connector_metro')

        from vigilo.common.logging import get_logger
        LOGGER = get_logger('vigilo.connector_metro')

        from vigilo.connector_nagios.xmpptopipefw import XMPPToPipeForwarder
        from vigilo.connector.sockettonodefw import SocketToNodeForwarder
        from vigilo.connector.presence import PresenceManager
        from vigilo.connector.status import StatusPublisher

        xmpp_client = client.client_factory(settings)

        nodetopublish = settings.get('publications', {})
        _service = JID(settings['bus'].get('service', None))

        bkpfile = settings['connector'].get('backup_file', ":memory:")
        pw = settings['connector-nagios'].get('nagios_pipe', None)
        sr = settings['connector-nagios'].get('listen_unix', None)

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

        if sr:
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

        if pw:
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


        if sr is not None:
            message_publisher = SocketToNodeForwarder(
                    sr, bkpfile,
                    settings['connector']['backup_table_to_bus'])
            message_publisher.setHandlerParent(xmpp_client)

        # Présence
        presence_manager = PresenceManager()
        presence_manager.setHandlerParent(xmpp_client)

        # Statistiques
        stats_publisher = StatusPublisher(message_publisher,
                            settings["connector"].get("hostname", None))
        stats_publisher.setHandlerParent(xmpp_client)

        root_service = service.MultiService()
        xmpp_client.setServiceParent(root_service)
        return root_service

nagios_connector = NagiosConnectorServiceMaker()
