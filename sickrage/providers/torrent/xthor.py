# -*- coding: latin-1 -*-
# Author: adaur <adaur.underground@gmail.com>
# URL: http://github.com/SiCKRAGETV/SickRage/
#
# This file is part of SickRage.
#
# SickRage is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# SickRage is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with SickRage.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import cookielib
import re
import urllib

import requests

import sickrage
from sickrage.core.helpers import bs4_parser
from sickrage.providers import TorrentProvider


class XthorProvider(TorrentProvider):
    def __init__(self):

        super(XthorProvider, self).__init__("Xthor","xthor.bz")

        self.supportsBacklog = True

        self.cj = cookielib.CookieJar()

        self.urls.update({
            'search': "{base_url}/browse.php?search=%s%s".format(base_url=self.urls['base_url'])
        })

        self.categories = "&searchin=title&incldead=0"

        self.username = None
        self.password = None
        self.ratio = None

    def _doLogin(self):
        if any(requests.utils.dict_from_cookiejar(sickrage.srCore.srWebSession.cookies).values()):
            return True

        login_params = {'username': self.username,
                        'password': self.password,
                        'submitme': 'X'}

        try:
            response = sickrage.srCore.srWebSession.post(self.urls['base_url'] + '/takelogin.php', data=login_params, timeout=30).text
        except Exception:
            sickrage.srCore.srLogger.warning("[{}]: Unable to connect to provider".format(self.name))
            return False

        if not re.search('donate.php', response):
            sickrage.srCore.srLogger.warning("[{}]: Invalid username or password. Check your settings".format(self.name))
            return False

        return True

    def search(self, search_params, search_mode='eponly', epcount=0, age=0, epObj=None):

        results = []
        items = {'Season': [], 'Episode': [], 'RSS': []}

        # check for auth
        if not self._doLogin():
            return results

        for mode in search_params.keys():
            sickrage.srCore.srLogger.debug("Search Mode: %s" % mode)
            for search_string in search_params[mode]:

                if mode != 'RSS':
                    sickrage.srCore.srLogger.debug("Search string: %s " % search_string)

                searchURL = self.urls['search'] % (urllib.quote(search_string), self.categories)
                sickrage.srCore.srLogger.debug("Search URL: %s" % searchURL)

                try:
                    data = sickrage.srCore.srWebSession.get(searchURL).text
                except Exception:
                    sickrage.srCore.srLogger.debug("No data returned from provider")
                    continue

                with bs4_parser(data) as html:
                    resultsTable = html.find("table", {"class": "table2 table-bordered2"})
                    if resultsTable:
                        rows = resultsTable.findAll("tr")
                        for row in rows:
                            link = row.find("a", href=re.compile("details.php"))
                            if link:
                                title = link.text
                                download_url = self.urls['base_url'] + '/' + \
                                               row.find("a", href=re.compile("download.php"))['href']
                                # FIXME
                                size = -1
                                seeders = 1
                                leechers = 0

                                if not all([title, download_url]):
                                    continue

                                # Filter unseeded torrent
                                # if seeders < self.minseed or leechers < self.minleech:
                                #    if mode != 'RSS':
                                #        LOGGER.debug(u"Discarding torrent because it doesn't meet the minimum seeders or leechers: {0} (S:{1} L:{2})".format(title, seeders, leechers))
                                #    continue

                                item = title, download_url, size, seeders, leechers
                                if mode != 'RSS':
                                    sickrage.srCore.srLogger.debug("Found result: %s " % title)

                                items[mode].append(item)

            # For each search mode sort all the items by seeders if available if available
            items[mode].sort(key=lambda tup: tup[3], reverse=True)

            results += items[mode]

        return results

    def seedRatio(self):
        return self.ratio
