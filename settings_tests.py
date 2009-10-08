# vim: set fileencoding=utf-8 sw=4 ts=4 et :
import logging
LOGGING_PLUGINS = (
        #'vigilo.pubsub.logging',       
        )
LOGGING_SETTINGS = { 'level': logging.DEBUG, }
LOGGING_LEVELS = {}
LOGGING_SYSLOG = True
LOG_TRAFFIC = True


LOGGING_SETTINGS = {
        # 5 is the 'SUBDEBUG' level.
        'level': logging.error,
        'format': '%(levelname)s::%(name)s::%(message)s',
        }
LOGGING_LEVELS = {
        'twisted': logging.DEBUG,
        'vigilo.pubsub': logging.DEBUG,
        'vigilo.connector-nagios': logging.DEBUG,
    }



VIGILO_CONNECTOR_XMPP_SERVER_HOST = 'unknown'
VIGILO_CONNECTOR_XMPP_PUBSUB_SERVICE = 'pubsub.localhost'
# Respect the ejabberd namespacing, for now. It will be too restrictive soon.
VIGILO_CONNECTOR_JID = 'connector-nagios@localhost'
VIGILO_CONNECTOR_PASS = 'connector-nagios'

# listen on this node (écoute de ce noeud)
# pas initialisé le connector nagios n'as pas à recevoir des messages du BUS
# create this node (créer ce noeud)
VIGILO_CONNECTOR_TOPIC_OWNER = ['/home/localhost/connector-nagios/BUS']

# publish on those node (publier sur ces noeuds)
VIGILO_CONNECTOR_TOPIC_PUBLISHER = { 
        'perf': '/home/localhost/connector-nagios/BUS',
        'event': '/home/localhost/connector-nagios/BUS',
        }


VIGILO_SOCKETR = '/tmp/connector-nagios_send.sock'
VIGILO_MESSAGE_BACKUP_FILE = '/tmp/connector-nagios_backup'
VIGILO_MESSAGE_BACKUP_TABLE_TOBUS = 'connector_tobus'

