# -*- coding: utf-8 -*-

project = u'Vigilo connector-nagios'

pdf_documents = [
        ('admin', "admin-connector-nagios", "Connector-nagios : Guide d'administration", u'Vigilo'),
        ('dev', "dev-connector-nagios", "Connector-nagios : Guide de développement", u'Vigilo'),
]

latex_documents = [
        ('admin', 'admin-connector-nagios.tex', u"Connector-nagios : Guide d'administration",
         'AA100004-2/ADM00002', 'vigilo'),
        ('dev', 'dev-connector-nagios.tex', u"Connector-nagios : Guide de développement",
         'AA100004-2/DEV00006', 'vigilo'),
]

execfile("../buildenv/doc/conf.py")
