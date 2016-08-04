Connector Nagios
===============

Connector Nagios est le composant de Vigilo_ qui permet à Nagios_ d'envoyer
les changements d'état et les données de performance collectées sur le bus.

Il permet aussi de transférer à Nagios, par l'intermédiaire de son *pipe*, les
commandes qui auraient été émises sur le bus à son intention.

Pour les détails du fonctionnement du Connector Nagios, se reporter à la
`documentation officielle`_.


Dépendances
-----------
Vigilo nécessite une version de Python supérieure ou égale à 2.5. Le chemin de
l'exécutable python peut être passé en paramètre du ``make install`` de la
façon suivante::

    make install PYTHON=/usr/bin/python2.6

Le Connector Nagios a besoin de Nagios_ et des modules Python suivants :

- setuptools (ou distribute)
- vigilo-common
- vigilo-connector


Installation
------------
L'installation se fait par la commande ``make install`` (à exécuter en
``root``).


License
-------
Connector Nagios est sous licence `GPL v2`_.


.. _documentation officielle: Vigilo_
.. _Vigilo: http://www.projet-vigilo.org
.. _Nagios: http://nagios.org
.. _GPL v2: http://www.gnu.org/licenses/gpl-2.0.html

.. vim: set syntax=rst fileencoding=utf-8 tw=78 :
