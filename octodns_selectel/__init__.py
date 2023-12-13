#
#
#

from collections import defaultdict
from logging import getLogger

from requests import Session
from requests.exceptions import HTTPError

from octodns import __VERSION__ as octodns_version
from octodns.provider import ProviderException
from octodns.provider.base import BaseProvider
from octodns.record import Record, Update

# TODO: remove __VERSION__ with the next major version release
__version__ = __VERSION__ = '1.0.0'


def require_root_domain(fqdn):
    if fqdn.endswith('.'):
        return fqdn

    return f'{fqdn}.'


class SelectelAuthenticationRequired(ProviderException):
    def __init__(self, msg):
        message = 'Authorization failed. Invalid or empty token.'
        super().__init__(message)


class SelectelProvider(BaseProvider):
    SUPPORTS_GEO = False

    SUPPORTS = set(
        ('A', 'AAAA', 'ALIAS', 'CNAME', 'MX', 'NS', 'TXT', 'SRV', 'SSHFP')
    )

    MIN_TTL = 60

    PAGINATION_LIMIT = 50

    API_URL = 'https://api.selectel.ru/domains/v2'

    def __init__(self, id, token, *args, **kwargs):
        self.log = getLogger(f'SelectelProvider[{id}]')
        self.log.debug('__init__: id=%s', id)
        super().__init__(id, *args, **kwargs)

        self._sess = Session()
        self._sess.headers.update(
            {
                'X-Auth-Token': token,
                'Content-Type': 'application/json',
                'User-Agent': f'octodns/{octodns_version} octodns-selectel/{__VERSION__}',
            }
        )
        self._zone_rrsets = {}
        self._zone_list = self.zone_list()

    def _request(self, method, path, params=None, data=None):
        self.log.debug('_request: method=%s, path=%s, data=%s', method, path, data)
        url = f'{self.API_URL}{path}'
        resp = self._sess.request(method, url, params=params, json=data)
        self.log.debug('_request: status=%s', resp.status_code)
        if resp.status_code == 401:
            raise SelectelAuthenticationRequired(resp.text)
        elif resp.status_code == 404:
            return {}
        # TODO: delete it. It for debug only
        # if resp.json():
        #     self.log.debug('_request: response=%s', resp.json())
        resp.raise_for_status()
        if method == 'DELETE':
            return {}
        return resp.json()

    def _request_with_pagination(self, path):
        result = []
        resp = self._request_for_pagination(path)
        result += resp["result"]
        offset = resp["next_offset"]
        while offset != 0:
            resp = self._request_for_pagination(path, offset)
            result += resp["result"]
            offset = resp["next_offset"]
        return result

    def _request_for_pagination(self, path, offset=0):
        result = self._request(
            'GET',
            path,
            params={'limit': self.PAGINATION_LIMIT, 'offset': offset},
        )
        return result

    def _include_change(self, change):
        if isinstance(change, Update):
            existing = change.existing.data
            new = change.new.data
            new['ttl'] = max(self.MIN_TTL, new['ttl'])
            if new == existing:
                self.log.debug(
                    '_include_changes: new=%s, found existing=%s', new, existing
                )
                return False
        return True

    def _apply(self, plan):
        desired = plan.desired
        changes = plan.changes
        self.log.debug(
            '_apply: zone=%s, len(changes)=%d', desired.name, len(changes)
        )
        zone_name = desired.name[:-1]
        for change in changes:
            class_name = change.__class__.__name__
            getattr(self, f'_apply_{class_name}'.lower())(zone_name, change)

    def _apply_create(self, zone_name, change):
        new = change.new
        params_for = getattr(self, f'_params_for_{new._type}')
        for params in params_for(new):
            self.log.debug("params: %s", params_for(new))
            self.create_rrset(zone_name, params)

    def _apply_update(self, zone_name, change):
        self._apply_delete(zone_name, change)
        self._apply_create(zone_name, change)

    def _apply_delete(self, zone_name, change):
        existing = change.existing
        self.delete_rrset(zone_name, existing._type, existing.name)

    def _params_for_multiple(self, record):
        yield {
            'records': list(map(lambda value: {'content':value, 'disabled':False}, record.values)),
            'name': record.fqdn,
            'ttl': max(self.MIN_TTL, record.ttl),
            'type': record._type,
        }

    def _params_for_multiple_TXT(self, record):
        yield {
            'records': list(map(lambda value: {'content':'"%s"'%value, 'disabled':False}, record.values)),
            'name': record.fqdn,
            'ttl': max(self.MIN_TTL, record.ttl),
            'type': record._type,
        }

    def _params_for_single(self, record):
        yield {
            'records': [{'content':record.value, 'disabled':False}],
            'name': record.fqdn,
            'ttl': max(self.MIN_TTL, record.ttl),
            'type': record._type,
        }

    def _params_for_MX(self, record):
        yield {
            'records': list(map(lambda value: {'content':f'{value.preference} {value.exchange}', 'disabled':False}, record.values)),
            'name': record.fqdn,
            'ttl': max(self.MIN_TTL, record.ttl),
            'type': record._type,
        }

    def _params_for_SRV(self, record):
        yield {
                'name': record.fqdn,
                'ttl': max(self.MIN_TTL, record.ttl),
                'type': record._type,
                'records': list(map(lambda value: 
                                    {'content':f'{value.priority} {value.weight} {value.port} {value.target}', 
                                     'disabled':False}, record.values)),
            }

    def _params_for_SSHFP(self, record):
        yield {
                'name': record.fqdn,
                'ttl': max(self.MIN_TTL, record.ttl),
                'type': record._type,
                'records': list(map(lambda value: {'content':f'{value.algorithm} {value.fingerprint_type} {value.fingerprint}', 'disabled':False}, record.values)),
            }

    _params_for_A = _params_for_multiple
    _params_for_AAAA = _params_for_multiple
    _params_for_NS = _params_for_multiple
    _params_for_TXT = _params_for_multiple_TXT
    _params_for_MX = _params_for_MX

    _params_for_CNAME = _params_for_single
    _params_for_ALIAS = _params_for_single

    def _data_for_A(self, _type, rrset):
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'values': [r['content'] for r in rrset["records"]],
        }

    _data_for_AAAA = _data_for_A

    def _data_for_NS(self, _type, rrset):
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'values': [require_root_domain(r["content"]) for r in rrset["records"]],
        }

    def _data_for_MX(self, _type, rrset):
        values = []
        if rrset["records"]:
            for record in rrset["records"]:
                priority,exchange = record["content"].split(" ")
                values.append(
                    {
                        'preference': priority,
                        'exchange': require_root_domain(exchange),
                    }
                )
        return {'ttl': rrset['ttl'], 'type': _type, 'values': values}

    def _data_for_CNAME(self, _type, rrset):
        value = rrset["records"][0]["content"]
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'value': require_root_domain(value),
        }

    _data_for_ALIAS = _data_for_CNAME

    def _data_for_TXT(self, _type, rrset):
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'values': [r['content'] for r in rrset["records"]],
        }

    def _data_for_SRV(self, _type, rrset):
        values = []
        for record in rrset["records"]:
            priority, weight, port, target = record["content"].split(" ")
            values.append(
                {
                    'priority': priority,
                    'weight': weight,
                    'port': port,
                    'target': require_root_domain(target),
                }
            )
        return {'type': _type, 'ttl': rrset['ttl'], 'values': values}
    
    def _data_for_SSHFP(self, _type, rrset):
        values = []
        for record in rrset["records"]:
            algorithm, fingerprint_type, fingerprint = record["content"].split(" ")
            values.append(
                {
                    'algorithm': algorithm,
                    'fingerprint_type': fingerprint_type,
                    'fingerprint': fingerprint,
                }
            )
        return {'type': _type, 'ttl': rrset['ttl'], 'values': values}

    # TODO: refactor it
    def populate(self, zone, target=False, lenient=False):
        self.log.debug(
            'populate: name=%s, target=%s, lenient=%s',
            zone.name,
            target,
            lenient,
        )
        before = len(zone.records)
        records = self.zone_rrsets(zone)
        if records:
            values = defaultdict(lambda: defaultdict(list))
            for record in records:
                name = zone.hostname_from_fqdn(record['name'])
                _type = record['type']
                if _type in self.SUPPORTS:
                    values[name][record['type']].append(record)
            for name, types in values.items():
                for _type, rrset in types.items():
                    data_for = getattr(self, f'_data_for_{_type}')
                    if rrset:
                        data = data_for(_type, rrset[0])
                        record = Record.new(
                            zone, name, data, source=self, lenient=lenient
                        )
                        zone.add_record(record)
        self.log.info(
            'populate:   found %s records', len(zone.records) - before
        )

    def create_zone(self, name):
        self.log.debug('Create zone: %s', name)
        path = '/zones'
        data = {'name': name}
        resp = self._request('POST', path, data=data)
        self._zone_list[require_root_domain(name)] = resp
        return resp

    def zone_list(self):
        path = '/zones'
        zones = {}
        zones_list = self._request_with_pagination(path)
        for zone in zones_list:
            zones[zone['name']] = zone
        return zones

    def zone_rrsets(self, zone):
        self.log.debug('View rrset. Zone: %s', zone)
        zone_rrsets = []
        zone_by_name = self._zone_list.get(require_root_domain(zone.name))
        zone_id = zone_by_name.get("uuid") if zone_by_name else None
        if zone_id:
            path = f'/zones/{zone_id}/rrset'
            zone_rrsets = self._request_with_pagination(path)
        self._zone_rrsets[require_root_domain(zone.name)] = zone_rrsets
        return self._zone_rrsets[require_root_domain(zone.name)]

    def create_rrset(self, zone_name, data):
        self.log.debug('Create rrset. Zone: %s, data %s', zone_name, data)
        if require_root_domain(zone_name) in self._zone_list.keys():
            zone_id = self._zone_list[require_root_domain(zone_name)]['uuid']
        else:
            zone_id = self.create_zone(zone_name)['uuid']
        path = f'/zones/{zone_id}/rrset'

        return self._request('POST', path, data=data)

    # TODO: refactor it
    def delete_rrset(self, zone, _type, rrset_name):
        self.log.debug('Delete rrsets. Zone: %s, Type: %s, Rrset Name: %s', zone, _type, rrset_name)
        zone_id = self._zone_list[require_root_domain(zone)]['uuid']
        rrsets = self._zone_rrsets.get(require_root_domain(zone), False)
        if not rrsets:
            path = f'/zones/{zone_id}/rrset'
            rrsets = self._request('GET', path)
        full_domain = f'{rrset_name}.{require_root_domain(zone)}'
        delete_count, skip_count = 0, 0
        for rrset in rrsets:
            if rrset['type'] == _type and rrset['name'] == full_domain:
                rrset_id = rrset["uuid"]
                path = f'/zones/{zone_id}/rrset/{rrset_id}'
                try:
                    self._request('DELETE', path)
                    delete_count += 1
                except HTTPError:
                    skip_count += 1
                    self.log.warning(f'Failed to delete rrset {rrset_id}')
        self.log.debug(
            f'Deleted {delete_count} rrsets. Skipped {skip_count} rrsets'
        )