from collections import defaultdict
from logging import getLogger
from requests import Session
from requests.exceptions import HTTPError

from octodns import __VERSION__ as octodns_version
from octodns.provider import ProviderException

class SelectelAuthenticationRequired(ProviderException):
    def __init__(self, msg):
        message = 'Authorization failed. Invalid or empty token.'
        super().__init__(message)

class SelectelClient(object):
    API_URL = 'https://api.selectel.ru/domains/v2'
    PAGINATION_LIMIT = 50

    def __init__(self, library_version:str, token:str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._sess = Session()
        self._sess.headers.update(
            {
                'X-Auth-Token': token,
                'Content-Type': 'application/json',
                'User-Agent': f'octodns/{octodns_version} octodns-selectel/{library_version}',
            }
        )

    def _request(self, method, path, params=None, data=None):
        url = f'{self.API_URL}{path}'
        resp = self._sess.request(method, url, params=params, json=data)
        if resp.status_code == 401:
            raise SelectelAuthenticationRequired(resp.text)
        elif resp.status_code == 404:
            return {}
        resp.raise_for_status()
        if method == "DELETE":
            return {}
        return resp.json()
    
    def _request_with_offset(self, path, offset=0):
        result = self._request(
            'GET',
            path,
            params={'limit': self.PAGINATION_LIMIT, 'offset': offset},
        )
        return result
    
    def _request_all_entities(self, path):
        result = []
        resp = self._request_with_offset(path)
        result += resp["result"]
        offset = resp["next_offset"]
        while offset != 0:
            resp = self._request_with_offset(path, offset)
            result += resp["result"]
            offset = resp["next_offset"]
        return result
    
    def create_zone(self, name):
        path = '/zones'
        data = {'name': name}
        resp = self._request('POST', path, data=data)
        return resp

    def zones(self):
        path = '/zones'
        zones = self._request_all_entities(path)
        return zones

    def zone_rrsets(self, zone_id):
        path = f'/zones/{zone_id}/rrset'
        zone_rrsets = self._request_all_entities(path)
        return zone_rrsets

    def create_rrset(self, zone_id, data):
        path = f'/zones/{zone_id}/rrset'
        return self._request('POST', path, data=data)
    
    def delete_rrset(self, zone_id, rrset_id):
        path = f'/zones/{zone_id}/rrset/{rrset_id}'
        self._request('DELETE', path)
        return {}
