**********************
Guide de développement
**********************

Ce document a pour objectif de présenter le fonctionnement du connector-nagios
aux développeurs désireux d'étendre les fonctionnalités du connecteur.


Installation
============

Pré-requis logiciels
--------------------
Ce document suppose que vous disposez déjà d'une installation fonctionnelle du connector-nagios, dont vous souhaitez étendre les fonctionnalités.

Reportez-vous au manuel administrateur du connector-nagios et à la procédure
d'installation générale de Vigilo pour plus d'information sur la manière
d'installer le connector-nagios.


.. _formats:

Format des messages transmis au connecteur
==========================================

Le chapitre qui suit détaille le format des différents messages que le
composant « connector-nagios » est capable de traiter. Bien que ces messages
soient principalement envoyés au connecteur par l'outil de supervision Nagios,
le format utilisé est très simple ce qui permet par exemple de générer des
alertes depuis n'importe quel autre programme.

Les messages sont composés de plusieurs champs, séparés par des barres
verticales (« | », soit la combinaison de touches AltGr+6).

Messages de changement d'état
-----------------------------
Les messages de changement d'état contiennent les informations nécessaires pour
connaître le nouvel état d'un élément supervisé du parc.

Chacun de ces messages est de la forme::

    event|<horodatage>|<hôte>|<service>|<état>|<message>

Le premier champ est fixe et permet d'identifier le type de message. Pour un
changement d'état, le code associé est « event ».

Le second champ contient un horodatage de l'événement (timestamp), sous la
forme d'un horodatage UNIX (le nombre de secondes écoulées depuis le 1er
Janvier 1970).

Le troisième champ contient le nom de l'hôte (serveur, routeur, etc.) concerné
par le changement d'état.

Le quatrième champ contient le nom du service concerné par le changement d'état
sur l'hôte précité. Si le changement d'état concerne directement l'hôte,
utilisez une chaîne vide ou utilisez le mot clé « HOST » en guise de nom de
service impacté.

Le cinquième champ contient le nom du nouvel état Nagios dans lequel se trouve
l'élément (en majuscules). Les états valides dépendent du type d'élément (hôte
ou service). Les différents états possibles sont les suivants :

UP (hôte) / OK (service)

    L'hôte ou le service se trouve dans son état nominal.

UNREACHABLE (hôte) / UNKNOWN (service)

    L'état de l'hôte ou du service ne peut pas être déterminé.

WARNING (service uniquement)

    Le service est dans un état d'alerte mais continue de fonctionner.

DOWN (hôte) / CRITICAL (service)

    L'hôte ne répond plus ou le service est dans un état critique dans lequel
    il risque de ne plus pouvoir remplir ses fonctions.

Le sixième champ contient un message décrivant la raison du changement d'état.
Le message ne doit contenir que des caractères imprimables (en particulier, il
ne doit pas contenir de retour à la ligne) et ne peut pas contenir le caractère
utilisé comme séparateur de champs (« | »).

Exemple d'un changement d'état indiquant un retour à la normale du la charge
sur 5 minutes (service « Load 05 ») sur le serveur « host1.example.com »::

    event|1290420699|host1.example.com|Load 05|OK|OK: Load at 37%

Il est usuel de reprendre le nom de l'état Nagios (ici, « OK ») dans le message
d'état (dans cet exemple, « OK: Load at 37% »), mais il ne s'agit en rien d'une
obligation.

Messages de métrologie
----------------------
Les messages de métrologie contiennent des indications sur les performances
d'un élément du parc.

Chacun de ces messages est de la forme::

    perf|<horodatage>|<hôte>|<service>|<valeur>

Le premier champ est fixe et permet d'identifier le type de message. Pour une
donnée de métrologie, le code associé est « perf ».

Le second champ contient un horodatage de l'événement (timestamp), sous la
forme d'un horodatage UNIX (le nombre de secondes écoulées depuis le 1er
Janvier 1970).

Le troisième champ contient le nom de l'hôte (serveur, routeur, etc.) concerné
par le changement d'état.

Le quatrième champ contient le nom du service concerné par le changement d'état
sur l'hôte précité. Si le changement d'état concerne directement l'hôte,
utilisez une chaîne vide ou utilisez le mot clé « HOST » en guise de nom de
service impacté.

Le cinquième champ contient la nouvelle valeur associée à cet indicateur de
métrologie. Il s'agit d'un entier ou d'une nombre flottant, en fonction du type
d'indicateur.

Exemple d'un message contenant une donnée de métrologie sur le service « TCP
Connections » (le nombre de connexions TCP ouvertes sur un serveur) de l'hôte
« host1.example.com »::

    perf|1290421397|host1.example.com|TCP Connections|10



Simulation de pannes
====================

Afin de simuler des scénarios de pannes ou la réception de données de
métrologie, vous pouvez utiliser l'outil « socat » de Linux et les indications
sur le format des différents messages acceptés par le connecteur (voir chapitre
:ref:`formats`).

Exemple d'utilisation de la commande « socat » pour envoyer une alerte sur
l'état de l'hôte « host1.example.com »::

    echo "event|`date +%s`|host1.example.com||DOWN|DOWN: Machine indisponible" | socat - UNIX-CONNECT:/var/ib/vigilo/connector-nagios/send.sock

Notez l'utilisation d'une pipe UNIX (« | ») pour passer le message formaté par
la commande « echo » à la commande « socat ».

La commande « date » est exécuté grâce à des apostrophes inversées (« ` ») afin
de récupérer un horodatage dans le format attendu.

Le socket UNIX « /var/ib/vigilo/connector-nagios/send.sock » est passé en
argument à la méthode « UNIX-CONNECT » de socat. Cette valeur correspond à
l'option « listen_unix » de la configuration du connector-nagios. Elle doit
être adaptée en fonction de votre installation.



.. vim: set tw=79 :

