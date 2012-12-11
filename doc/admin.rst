**********************
Guide d'administration
**********************


Installation
============

Pré-requis logiciels
--------------------
Afin de pouvoir faire fonctionner le connecteur Nagios, l'installation
préalable des logiciels suivants est requise :

* python (>= 2.5), sur la machine où le connecteur est installé
* rabbitmq (>= 2.7.1), éventuellement sur une machine distante
* nagios (>= 3.1.0) sur la machine où le connecteur est installé


.. Installation du RPM
.. include:: ../buildenv/doc/package.rst

.. Compte sur le bus et fichier de configuration
.. include:: ../../connector/doc/admin-conf-1.rst

.. Lister ici les sections spécifiques au connecteur

connector-nagios
    Contient les options spécifiques au connecteur Nagios.

.. include:: ../../connector/doc/admin-conf-2.rst

.. Documenter ici les sections spécifiques au connecteur

Configuration spécifique au connecteur Nagios
----------------------------------------------------
Cette section décrit les options de configuration spécifiques au connecteur
Nagios. Ces options sont situées dans la section ``[connector-nagios]`` du
fichier de configuration (dans ``/etc/vigilo/connector-nagios/settings.ini``).

Commandes Nagios acceptées
^^^^^^^^^^^^^^^^^^^^^^^^^^
Le connecteur Nagios est capable d'envoyer des commandes à destination de
Nagios. Afin d'éviter des abus éventuels, l'option « accepted_commands » permet
de lister les commandes qui seront acceptées.

À minima, la commande « PROCESS_SERVICE_CHECK_RESULT » doit être acceptée si
des services de haut niveau ont été configurés au travers de VigiConf.

Socket de réception des messages
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
L'option « listen_unix » permet d'indiquer l'emplacement du socket Unix sur
lequel le connecteur attendra des messages (généralement émis directement par
Nagios).

Pipe de commandes Nagios
^^^^^^^^^^^^^^^^^^^^^^^^^^
L'option « nagios_pipe » permet de spécifier l'emplacement du « pipe » (canal
de communication) sur lequel Nagios accepte des commandes. La valeur de cette
option doit être la même que l'option portant le même nom dans le fichier de
configuration de Nagios (nagios.cfg).


.. Administration du service
.. include:: ../buildenv/doc/service.rst


Annexes
=======

.. include:: ../../connector/doc/glossaire.rst



.. vim: set tw=79 :
