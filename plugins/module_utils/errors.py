# -*- coding: utf-8 -*-
# Copyright: (c) 2021, XLAB Steampunk <steampunk@xlab.si>
#
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

class TMDBException(Exception):
    pass

class TMDBAuthException(TMDBException):
    pass

class TMDBResponseException(TMDBException):
    def __init__(self, status, data):
        self.message = f"Unexpected response from TMDB API - {status} {data}"
        super(TMDBResponseException, self).__init__(self.message)