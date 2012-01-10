# vim: set fileencoding=utf-8 sw=4 ts=4 et :
# Copyright (C) 2006-2011 CS-SI
# License: GNU GPL v2 <http://www.gnu.org/licenses/gpl-2.0.html>

"""
Chargement d'une base sqlite de configuration générée par Vigiconf pour le
connector-nagios.
"""

from __future__ import absolute_import

from twisted.internet import defer

from vigilo.connector.confdb import ConfDB



class NagiosConfDB(ConfDB):
    """
    Accès à la configuration du connector-nagios fournie par VigiConf (dans une
        base SQLite)
    """


    def _rebuild_cache(self):
        """
        Format du cache : {
            "host1": ("groupe-de-ventilation", "est-local"),
            "host2": ("groupe-de-ventilation", "est-local"),
            "host3": ("groupe-de-ventilation", "est-local"),
        }
        """
        self._cache = {}
        self.get_hosts()


    def get_hosts(self):
        if self._db is None:
            return defer.succeed([])
        result = self._db.runQuery("SELECT hostname, ventilation, local FROM "
                                   "hosts")
        def cache_hosts(results):
            self._cache = dict( (r[0], (r[1], bool(r[2]))) for r in results )
            return hosts
        result.addCallback(cache_hosts)
        return result


    def is_local(self, hostname):
        if self._db is None:
            return defer.succeed(False)
        if self._cache:
            return defer.succeed(hostname in self._cache
                                 and self._cache[hostname][1])
        result = self._db.runQuery("SELECT local FROM hosts "
                                   "WHERE hostname = ?", (hostname,) )
        result.addCallback(lambda results: results and bool(results[0][0]))
        return result


    def get_ventilation(self, hostname):
        if self._db is None:
            return defer.succeed(None)
        if self._cache:
            if hostname not in self._cache:
                return defer.succeed(None)
            return defer.succeed(self._cache[hostname][0])
        result = self._db.runQuery("SELECT ventilation FROM hosts "
                                   "WHERE hostname = ?", (hostname,) )
        def parse_result(results):
            if not results:
                return None
            return results[0][0]
        result.addCallback(parse_results)
        return result
