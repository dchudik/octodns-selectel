from requests import Session

from octodns import __VERSION__ as octodns_version

from .exceptions import ApiException, SelectelException


class DNSClient:
    API_URL = 'https://api.selectel.ru/domains/v2'
    _PAGINATION_LIMIT = 50

    __zone_path = "/zones"
    __zone_path_specific = "/zones/{}"
    __rrsets_path = "/zones/{}/rrset"
    __rrsets_path_specific = "/zones/{}/rrset/{}"

    def __init__(self, library_version: str, openstack_token: str):
        self._sess = Session()
        self._sess.headers.update(
            {
                'X-Auth-Token': openstack_token,
                'Content-Type': 'application/json',
                'User-Agent': f'octodns/{octodns_version} octodns-selectel/{library_version}',
            }
        )

    @classmethod
    def _zone_path(cls):
        return cls.__zone_path

    @classmethod
    def _zone_path_specific(cls, zone_uuid):
        return cls.__zone_path_specific.format(zone_uuid)

    @classmethod
    def _rrset_path(cls, zone_uuid):
        return cls.__rrsets_path.format(zone_uuid)

    @classmethod
    def _rrset_path_specific(cls, zone_uuid, rrset_uuid):
        return cls.__rrsets_path_specific.format(zone_uuid, rrset_uuid)

    def _request(self, method, path, params=None, data=None):
        url = f'{self.API_URL}{path}'
        resp = self._sess.request(method, url, params, json=data)
        match resp.status_code:
            case 400:
                raise ApiException(
                    f'Bad request. Description: {resp.json()["description"]}'
                )
            case 401:
                raise ApiException(
                    'Authorization failed. Invalid or empty token.'
                )
            case 404:
                raise ApiException('Resource not found.')
            case 409:
                raise ApiException('Resource already created.')
            case _ if resp.status_code >= 500:
                raise ApiException('Internal server error.')
        try:
            return resp.json()
        except ValueError:
            return {}
        except Exception as e:
            raise SelectelException(e)

    def _request_all_entities(self, path, records=[], offset=0):
        resp = self._request(
            "GET", path, dict(limit=self._PAGINATION_LIMIT, offset=offset)
        )
        next_offset = resp["next_offset"]
        if next_offset == 0:
            return records + resp["result"]
        return self._request_all_entities(
            path, records + resp["result"], next_offset
        )

    def list_zones(self):
        path = self._zone_path()
        zones = self._request_all_entities(path)
        return zones

    def create_zone(self, name):
        path = self._zone_path()
        data = dict(name=name)
        resp = self._request('POST', path, data=data)
        return resp

    def list_rrsets(self, zone_uuid):
        path = self._rrset_path(zone_uuid)
        zone_rrsets = self._request_all_entities(path)
        return zone_rrsets

    def create_rrset(self, zone_uuid, data):
        path = self._rrset_path(zone_uuid)
        return self._request('POST', path, data=data)

    def delete_rrset(self, zone_uuid, rrset_uuid):
        path = self._rrset_path_specific(zone_uuid, rrset_uuid)
        self._request('DELETE', path)
        return {}
