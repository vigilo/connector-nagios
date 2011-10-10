**********************
Guide d'administration
**********************

Ce document a pour objectif de présenter le fonctionnement du module
connector-nagios aux administrateurs.


Installation
============

Pré-requis logiciels
--------------------
Afin de pouvoir faire fonctionner le connecteur Nagios, l'installation
préalable des logiciels suivants est requise :

* python (>= 2.5), sur la machine où le connecteur est installé
* nagios (>= 3.1.0) sur la machine où le connecteur est installé
* ejabberd (>= 2.1), éventuellement sur une machine distante

Reportez-vous aux manuels de ces différents logiciels pour savoir comment
procéder à leur installation sur votre machine.

Le connecteur Nagios requiert également la présence de plusieurs dépendances
Python. Ces dépendances seront automatiquement installées en même temps que le
paquet du connecteur.

Installation du paquet RPM
--------------------------
L'installation du connecteur se fait en installant simplement le paquet RPM
« vigilo-connector-nagios ». La procédure exacte d'installation dépend du
gestionnaire de paquets utilisé. Les instructions suivantes décrivent la
procédure pour les gestionnaires de paquets RPM les plus fréquemment
rencontrés.

Installation à l'aide de urpmi::

    urpmi vigilo-connector-nagios

Installation à l'aide de yum::

    yum install vigilo-connector-nagios

Création du compte XMPP
-----------------------
Le connector-nagios nécessite qu'un compte soit créé sur la machine hébergeant
le bus XMPP pour le composant.

Les comptes doivent être créés sur la machine qui héberge le serveur ejabberd,
à l'aide de la commande::

    $ su -c 'ejabberdctl register connector-nagios localhost connector-nagios' ejabberd

**Note :** si plusieurs instances du connecteur s'exécutent simultanément sur
le parc, chaque instance doit disposer de son propre compte (JID). Dans le cas
contraire, des conflits risquent de survenir qui peuvent perturber le bon
fonctionnement de la solution.



Configuration
=============

Le module connector-nagios est fourni avec un fichier de configuration situé
par défaut dans ``/etc/vigilo/connector-nagios/settings.ini``.

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



Administration du service
=========================

Le connecteur est fourni avec un script de démarrage standard pour Linux,
facilitant les opérations d'administration du connecteur. Ce chapitre décrit
les différentes opérations d'administration disponibles.

Démarrage
---------
Pour démarrer le module en mode démon, lancez la commande suivante en tant que
super-utilisateur::

    service vigilo-connector-nagios start

Si le service parvient à démarrer correctement, le message « OK » apparaît dans
le terminal.

Vérification de l'état du service
---------------------------------
L'état du service peut être vérifié à tout moment, grâce à la commande::

    service vigilo-connector-nagios status

S'il est bien en cours d'exécution, le module connector-nagios est maintenant
apte à traiter les messages issus de Nagios. Dans le cas contraire, analysez
les logs système consignés dans ``/var/log/syslog``.

Arrêt
-----
Pour arrêter le module connector-nagios, lancez la commande suivante en tant
que super-utilisateur::

    service vigilo-connector-nagios stop



Annexes
=======

.. include:: ../../connector/doc/glossaire.rst



.. vim: set tw=79 :
