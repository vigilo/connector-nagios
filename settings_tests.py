import logging
LOGGING_PLUGINS = ()
LOGGING_SETTINGS = { 'level': logging.DEBUG, }
LOGGING_LEVELS = {}
LOGGING_SYSLOG = False



VIGILO_CONNECTOR_DAEMONIZE = True
VIGILO_CONNECTOR_PIDFILE = '/home/smoignar/var/vigilo/connector-nagios/connector-nagios.pid'
VIGILO_CONNECTOR_XMPP_SERVER_HOST = 'localhost'
VIGILO_CONNECTOR_XMPP_PUBSUB_SERVICE = 'pubsub.localhost'
# Respect the ejabberd namespacing, for now. It will be too restrictive soon.
VIGILO_CONNECTOR_JID = 'user-nagios@localhost'
VIGILO_CONNECTOR_PASS = 'user-nagios'

#VIGILO_CONNECTOR_TOPIC = '/home/tburguie3/connectorx/BUS'
VIGILO_SOCKETR = '/var/lib/vigilo/connector-nagios/send.sock'
VIGILO_MESSAGE_BACKUP_FILE = '/var/lib/vigilo/connector-nagios/backup'
VIGILO_MESSAGE_BACKUP_TABLE_TOBUS = 'connector_tobus'
VIGILO_CONNECTOR_VPYTHON = 'bin/python'
VIGILO_CONNECTOR_MAIN = '/home/smoignar/workspace/connector-nagios/src/vigilo/connector_nagios/main.py'
