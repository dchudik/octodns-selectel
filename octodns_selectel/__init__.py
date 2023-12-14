#
#
#

from logging import getLogger
from requests.exceptions import HTTPError

from octodns.provider.base import BaseProvider
from octodns.record import Record, Update

from .dns_client import DNSClient

# TODO: remove __VERSION__ with the next major version release
__version__  = '0.0.4'

def require_root_domain(fqdn):
    if fqdn.endswith('.'):
        return fqdn

    return f'{fqdn}.'


class SelectelProvider(BaseProvider):
    SUPPORTS_GEO = False
    SUPPORTS = set(
        ('A', 'AAAA', 'ALIAS', 'CNAME', 'MX', 'NS', 'TXT', 'SRV', 'SSHFP')
    )
    MIN_TTL = 60

    def __init__(self, id, token, *args, **kwargs):
        self.log = getLogger(f'SelectelProvider[{id}]')
        self.log.debug('__init__: id=%s', id)
        super().__init__(id, *args, **kwargs)
        self._client = DNSClient(__version__, token)
        self._zones = self.zones()
        self._zone_rrsets = {}

    # TODO: check when using this function
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
        zone_name = desired.name
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
        self.log.debug("change=%s", change)
        self._apply_delete(zone_name, change)
        self._apply_create(zone_name, change)

    def _apply_delete(self, zone_name, change):
        existing = change.existing
        self.delete_rrset(zone_name, existing._type, existing.name)

    def _base_rrset_info_from_record(self, record):
        return {
            'name': record.fqdn,
            'ttl': max(self.MIN_TTL, record.ttl),
            'type': record._type,
        }

    def _params_for_multiple(self, record):
        rrset = self._base_rrset_info_from_record(record)
        rrset["records"] = list(map(lambda value: {'content':value, 
                                                   'disabled':False}, record.values))
        yield rrset

    def _params_for_multiple_TXT(self, record):
        rrset = self._base_rrset_info_from_record(record)
        rrset["records"] = list(map(lambda value: {'content':'"%s"'%value, 
                                                   'disabled':False}, record.values))
        yield rrset

    def _params_for_single(self, record):
        rrset = self._base_rrset_info_from_record(record)
        rrset["records"] = [{'content':record.value, 'disabled':False}]
        yield rrset

    def _params_for_MX(self, record):
        rrset = self._base_rrset_info_from_record(record)
        rrset["records"] = list(map(lambda value: {'content':
            f'{value.preference} {value.exchange}', 'disabled':False}, record.values))
        yield rrset

    def _params_for_SRV(self, record):
        rrset = self._base_rrset_info_from_record(record)
        rrset["records"] = list(map(lambda value: 
                                    {'content':f'{value.priority} {value.weight} {value.port} {value.target}', 
                                     'disabled':False}, record.values))
        yield rrset

    def _params_for_SSHFP(self, record):
        rrset = self._base_rrset_info_from_record(record)
        rrset["records"] = list(map(lambda value: 
                                    {'content':f'{value.algorithm} {value.fingerprint_type} {value.fingerprint}', 
                                     'disabled':False}, record.values))
        yield rrset

    _params_for_A = _params_for_multiple
    _params_for_AAAA = _params_for_multiple
    _params_for_NS = _params_for_multiple
    _params_for_TXT = _params_for_multiple_TXT

    _params_for_CNAME = _params_for_single
    _params_for_ALIAS = _params_for_single

    def _data_with_content(self, _type, rrset):
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'values': [r['content'] for r in rrset["records"]],
        }
    
    _data_for_A = _data_with_content
    _data_for_AAAA = _data_with_content
    _data_for_TXT = _data_with_content 

    def _data_for_NS(self, _type, rrset):
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'values': [require_root_domain(r["content"]) for r in rrset["records"]],
        }

    def _data_for_MX(self, _type, rrset):
        values = list(map(lambda record: {
                    'preference': record.split(" ")[0],
                    'exchange': require_root_domain(record.split(" ")[1]),
                }, rrset["records"]))
        return {'ttl': rrset['ttl'], 'type': _type, 'values': values}

    def _data_for_CNAME(self, _type, rrset):
        value = rrset["records"][0]["content"]
        return {
            'ttl': rrset['ttl'],
            'type': _type,
            'value': require_root_domain(value),
        }

    _data_for_ALIAS = _data_for_CNAME

    def _parse_record_SRV(record):
        priority, weight, port, target = record["content"].split(" ")
        return {
            'priority': priority,
            'weight': weight,
            'port': port,
            'target': require_root_domain(target),
        }

    def _data_for_SRV(self, _type, rrset):
        values = list(map(lambda record: self._parse_record_SRV(record), rrset["records"]))
        return {'type': _type, 'ttl': rrset['ttl'], 'values': values}
    
    def _parse_record_SSHFP(record):
        algorithm, fingerprint_type, fingerprint = record["content"].split(" ")
        return {
            'algorithm': algorithm,
            'fingerprint_type': fingerprint_type,
            'fingerprint': fingerprint,
        }
    
    def _data_for_SSHFP(self, _type, rrset):
        values = list(map(lambda record: self._parse_record_SSHFP(record), rrset["records"]))
        return {'type': _type, 'ttl': rrset['ttl'], 'values': values}

    def populate(self, zone, target=False, lenient=False):
        self.log.debug(
            'populate: name=%s, target=%s, lenient=%s', zone.name, target, lenient)
        before = len(zone.records)
        rrsets = self.zone_rrsets(zone)
        for rrset in rrsets:
            rrset_name = zone.hostname_from_fqdn(rrset['name'])
            rrset_type = rrset['type']
            if rrset_type in self.SUPPORTS:
                data_for = getattr(self, f'_data_for_{rrset_type}')
                data = data_for(rrset_type, rrset)
                record = Record.new(
                    zone, rrset_name, data, source=self, lenient=lenient
                )
                zone.add_record(record)
        self.log.info(
            'populate: found %s records', len(zone.records) - before
        )

    def _get_zone_id_by_name(self, zone_name):
        zone = self._zones.get(zone_name,False)
        return zone["uuid"] if zone else ""

    def create_zone(self, name):
        self.log.debug('Create zone: %s', name)
        zone = self._client.create_zone(require_root_domain(name))
        self._zones[zone["name"]] = zone
        return zone

    def zones(self):
        self.log.debug('View zones')
        zones = self._client.list_zones()
        zones_dict = {}
        for zone in zones:
            zones_dict[zone['name']] = zone
        return zones_dict

    def zone_rrsets(self, zone):
        self.log.debug('View rrsets. Zone: %s', zone.name)
        zone_id = self._get_zone_id_by_name(zone.name)
        zone_rrsets = []
        if zone_id:
            zone_rrsets = self._client.list_rrsets(zone_id)
            self._zone_rrsets[zone.name] = zone_rrsets
        return zone_rrsets

    def _is_zone_already_created(self, zone_name):
        return zone_name in self._zones.keys()
    
    def create_rrset(self, zone_name, data):
        self.log.debug('Create rrset. Zone: %s, data %s', zone_name, data)
        if self._is_zone_already_created(zone_name):
            zone_id = self._get_zone_id_by_name(zone_name)
        else:
            zone_id = self.create_zone(zone_name)['uuid']
        
        return self._client.create_rrset(zone_id, data)

    def delete_rrset(self, zone_name, rrset_type, rrset_name):
        self.log.debug('Delete rrsets. Zone name: %s, rrset type: %s, rrset name: %s', 
                       zone_name, rrset_type, rrset_name)
        zone_id = self._get_zone_id_by_name(zone_name)
        rrsets = self._zone_rrsets.get(zone_name)
        fqdn = f'{rrset_name}.{zone_name}' if rrset_name else zone_name
        delete_count, skip_count = 0, 0
        for rrset in rrsets:
            if rrset['type'] == rrset_type and rrset['name'] == fqdn:
                try:
                    self._client.delete_rrset(zone_id, rrset["uuid"])
                    delete_count += 1
                except HTTPError:
                    skip_count += 1
                    self.log.warning(f'Failed to delete rrset {rrset["uuid"]}')
        self.log.debug(
            f'Deleted {delete_count} rrsets. Skipped {skip_count} rrsets'
        )