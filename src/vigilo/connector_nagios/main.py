# vim: set fileencoding=utf-8 sw=4 ts=4 et :

""" Metrology connector nagios Pubsub client. """
from __future__ import absolute_import, with_statement

import sys
from twisted.application import app, service
from twisted.internet import reactor
from twisted.words.protocols.jabber.jid import JID
from vigilo.common.gettext import translate
from vigilo.connector.main import daemonize
from wokkel import client
from vigilo.pubsub.checknode import VerificationNode

_ = translate(__name__)



class ConnectorServiceMaker(object):
    """
    Creates a service that wraps everything the connector nagios needs.
    """


    def makeService(self):
        """ the service that wraps everything the connector nagios needs. """ 
        #from vigilo.connector_nagios.sockettonodefw import SocketToNodeForwarder
        from vigilo.connector.sockettonodefw import SocketToNodeForwarder
        from vigilo.pubsub import NodeOwner
        from vigilo.common.conf import settings
        xmpp_client = client.XMPPClient(
                JID(settings['VIGILO_CONNECTOR_JID']),
                settings['VIGILO_CONNECTOR_PASS'],
                settings['VIGILO_CONNECTOR_XMPP_SERVER_HOST'])
        xmpp_client.logTraffic = True
        xmpp_client.setName('xmpp_client')
        
        node_owner = NodeOwner()
        node_owner.setHandlerParent(xmpp_client)
        
        list_nodeOwner = settings.get('VIGILO_CONNECTOR_TOPIC_OWNER', [])
        # liste_nodeSubsciber pas initialisé le service n'as pas besoin de recevoir
        # des éléments 'VIGILO_CONNECTOR_NAGIOS_TOPIC' liste vide
        list_nodeSubscriber = settings.get('VIGILO_CONNECTOR_NAGIOS_TOPIC',[])
        verifyNode = VerificationNode(list_nodeOwner, list_nodeSubscriber, doThings=True)
        verifyNode.setHandlerParent(xmpp_client)
        nodetopublish = settings.get('VIGILO_CONNECTOR_TOPIC_PUBLISHER', None)
        _service = JID(settings.get('VIGILO_CONNECTOR_XMPP_PUBSUB_SERVICE', None))

        #Initialise un Socket récupération des messages en provenance de nagios 
        sr = settings.get('VIGILO_SOCKETR', None)
        if sr is not None:
            message_publisher = SocketToNodeForwarder(
                    sr,settings['VIGILO_MESSAGE_BACKUP_FILE'],
                    settings['VIGILO_MESSAGE_BACKUP_TABLE_TOBUS'],
                    nodetopublish,_service)
            message_publisher.setHandlerParent(xmpp_client)
        
        root_service = service.MultiService()
        xmpp_client.setServiceParent(root_service)
        return root_service
    
def main():
    """ main function designed to launch the program """
    from vigilo.common.conf import settings
    if settings.get('VIGILO_CONNECTOR_DAEMONIZE', False) == True:
        with daemonize(settings.get('VIGILO_CONNECTOR_PIDFILE', None)):
            pass

    application = service.Application('Twisted PubSub component')
    conn_service = ConnectorServiceMaker().makeService()
    conn_service.setServiceParent(application)
    app.startApplication(application, False)
    reactor.run()


if __name__ == '__main__':
    result = main()
    sys.exit(result)

