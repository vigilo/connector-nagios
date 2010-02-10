# vim: set fileencoding=utf-8 sw=4 ts=4 et :
""" Nagios connector Pubsub client. """
from __future__ import absolute_import, with_statement

from twisted.application import app, service
from twisted.internet import reactor
from twisted.words.protocols.jabber.jid import JID


from wokkel import client
from vigilo.common.gettext import translate
_ = translate(__name__)

class ConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector needs.
    """

    #implements(service.IServiceMaker, IPlugin)

    def makeService(self):
        """ the service that wraps everything the connector needs. """ 
        from vigilo.connector_nagios.xmpptopipefw import XMPPToPipeForwarder
        from vigilo.connector.sockettonodefw import SocketToNodeForwarder
        from vigilo.pubsub.checknode import VerificationNode
        from vigilo.common.conf import settings
        from vigilo.common.logging import get_logger
        import os
        LOGGER = get_logger(__name__)

        xmpp_client = client.XMPPClient(
                JID(settings['connector-nagios']['vigilo_connector_jid']),
                settings['connector-nagios']['vigilo_connector_pass'],
                settings['connector-nagios']['vigilo_connector_xmpp_server_host'])
        xmpp_client.logTraffic = True
        xmpp_client.setName('xmpp_client')

        list_nodeOwner = settings['connector-nagios'].get('vigilo_connector_topic_owner', [])
        list_nodeSubscriber = settings['connector-nagios'].get('vigilo_connector_topic', [])
        verifyNode = VerificationNode(list_nodeOwner, list_nodeSubscriber, 
                                      doThings=True)
        verifyNode.setHandlerParent(xmpp_client)
        nodetopublish = settings.get('vigilo_connector_topic_publisher', {})
        _service = JID(settings['connector-nagios'].get('vigilo_connector_xmpp_pubsub_service',
                                    None))

        bkpfile = settings['connector-nagios'].get('vigilo_message_backup_file', ":memory:")
        pw = settings['connector-nagios'].get('vigilo_pipew', None)
        sr = settings['connector-nagios'].get('vigilo_socketr', None)

        for i in bkpfile, pw, sr:
            if i != ':memory:' and i is not None:
                if not os.access(os.path.dirname(i), os.F_OK):
                    msg = _("Directory not found: '%(dir)s'") % \
                            {'dir': os.path.dirname(i)}
                    LOGGER.error(msg)
                    raise OSError(msg)
                if not os.access(os.path.dirname(i), os.R_OK):
                    msg = _("Directory not readable: '%(dir)s'") % \
                            {'dir': os.path.dirname(i)}
                    LOGGER.error(msg)
                    raise OSError(msg)
                if not os.access(os.path.dirname(i), os.W_OK):
                    msg = _("Directory not writable: '%(dir)s'") % \
                            {'dir': os.path.dirname(i)}
                    LOGGER.error(msg)
                    raise OSError(msg)
                if not os.access(os.path.dirname(i), os.X_OK):
                    msg = _("Directory not executable: '%(dir)s'") % \
                            {'dir': os.path.dirname(i)}
                    LOGGER.error(msg)
                    raise OSError(msg)

        if pw is not None:
            message_consumer = XMPPToPipeForwarder(
                    pw,
                    bkpfile,
                    settings['connector-nagios']['vigilo_message_backup_table_frombus'])
            message_consumer.setHandlerParent(xmpp_client)


        if sr is not None:
            message_publisher = SocketToNodeForwarder(
                    sr,
                    bkpfile,
                    settings['connector-nagios']['vigilo_message_backup_table_tobus'],
                    nodetopublish,
                    _service)
            message_publisher.setHandlerParent(xmpp_client)

        root_service = service.MultiService()
        xmpp_client.setServiceParent(root_service)
        return root_service

def do_main_programm():
    """ main function designed to launch the program """
    application = service.Application('Twisted PubSub component')
    conn_service = ConnectorServiceMaker().makeService()
    conn_service.setServiceParent(application)
    app.startApplication(application, False)
    reactor.run()

def main():
    """ main function designed to launch the program """

    from vigilo.common.daemonize import daemonize
    context = daemonize()
    with context:
        do_main_programm()


if __name__ == '__main__':
    main()

