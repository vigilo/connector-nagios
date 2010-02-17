#!/usr/bin/env python
# vim: set fileencoding=utf-8 sw=4 ts=4 et :
import os
from setuptools import setup

sysconfdir = os.getenv("SYSCONFDIR", "/etc")
localstatedir = os.getenv("LOCALSTATEDIR", "/var")

tests_require = [
    'coverage',
    'nose',
    'pylint',
]

setup(name='vigilo-connector-nagios',
        version='0.1',
        author='Vigilo Team',
        author_email='contact@projet-vigilo.org',
        url='http://www.projet-vigilo.org/',
        description='vigilo nagios connector component',
        license='http://www.gnu.org/licenses/gpl-2.0.html',
        long_description='The vigilo nagios connector component is a connector between:\n'
        +'   - XMPP/PubSub BUS of message\n'
        +'   - nagios\n',
        install_requires=[
            # dashes become underscores
            # order is important (wokkel before Twisted)
            'setuptools',
            'vigilo-common',
            'vigilo-pubsub',
            'vigilo-connector',
            'python-daemon',
            'wokkel',
            'Twisted',
            ],
        namespace_packages = [
            'vigilo',
            ],
        packages=[
            'vigilo',
            'vigilo.connector_nagios',
            ],
        extras_require={
            'tests': tests_require,
        },
        entry_points={
            'console_scripts': [
                'vigilo-connector-nagios = vigilo.connector_nagios.main:main',
                ],
            },
        package_dir={'': 'src'},
        data_files=[
                    (os.path.join(sysconfdir, "vigilo/connector-nagios"),
                        ["settings.ini"]),
                    (os.path.join(localstatedir, "lib/vigilo/connector-nagios"), []),
                    (os.path.join(localstatedir, "run/vigilo-connector-nagios"), []),
                   ],
        )

