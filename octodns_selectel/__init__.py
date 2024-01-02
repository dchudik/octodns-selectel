#
#
#

from logging import getLogger

from octodns.provider.base import BaseProvider
from octodns.record import Record, Update

from .dns_client import DNSClient
from .exceptions import ApiException
from .mappings import to_octodns_record_data, to_selectel_rrset

# TODO: remove __VERSION__ with the next major version release
__version__ = '0.0.4'


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
        self._zones = self.group_existing_zones_by_name()
        self._zone_rrsets = {}

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
        if not self._is_zone_already_created(zone_name):
            self.create_zone(zone_name)
        zone_id = self._get_zone_id_by_name(zone_name)
        for change in changes:
            action = change.__class__.__name__.lower()
            if action == 'create':
                self._apply_create(zone_id, change)
            if action == 'update':
                self._apply_update(zone_id, change)
            if action == 'delete':
                self._apply_delete(zone_id, change)

    def _is_zone_already_created(self, zone_name):
        return zone_name in self._zones.keys()

    def _get_rrset_id(self, zone_name, rrset_type, rrset_name):
        return next(
            filter(
                lambda rrset: rrset["type"] == rrset_type
                and rrset["name"] == rrset_name,
                self._zone_rrsets[zone_name],
            )
        )["uuid"]

    def _apply_create(self, zone_id, change):
        new_record = change.new
        rrset = to_selectel_rrset(new_record)
        self.create_rrset(zone_id, rrset)

    def _apply_update(self, zone_id, change):
        existing = change.existing
        rrset_id = self._get_rrset_id(
            existing.zone.name, existing._type, existing.fqdn
        )
        data_for_update = to_selectel_rrset(change.new)
        self.update_rrset(zone_id, rrset_id, data_for_update)

    def _apply_delete(self, zone_id, change):
        existing = change.existing
        rrset_id = self._get_rrset_id(
            existing.zone.name, existing._type, existing.fqdn
        )
        self.delete_rrset(zone_id, rrset_id)

    def populate(self, zone, target=False, lenient=False):
        self.log.debug(
            'populate: name=%s, target=%s, lenient=%s',
            zone.name,
            target,
            lenient,
        )
        before = len(zone.records)
        rrsets = []
        if self._is_zone_already_created(zone.name):
            rrsets = self.list_rrsets(zone)
        for rrset in rrsets:
            rrset_type = rrset['type']
            if rrset_type in self.SUPPORTS:
                record_data = to_octodns_record_data(rrset)
                rrset_hostname = zone.hostname_from_fqdn(rrset['name'])
                record = Record.new(
                    zone,
                    rrset_hostname,
                    record_data,
                    source=self,
                    lenient=lenient,
                )
                zone.add_record(record)
        self.log.info('populate: found %s records', len(zone.records) - before)

    def _get_zone_id_by_name(self, zone_name):
        return self._zones.get(zone_name, False)["uuid"]

    def create_zone(self, name):
        self.log.debug('Create zone: %s', name)
        zone = self._client.create_zone(name)
        self._zones[zone["name"]] = zone
        return zone

    def group_existing_zones_by_name(self):
        self.log.debug('View zones')
        return {zone['name']: zone for zone in self._client.list_zones()}

    def list_rrsets(self, zone):
        self.log.debug('View rrsets. Zone: %s', zone.name)
        zone_id = self._get_zone_id_by_name(zone.name)
        zone_rrsets = self._client.list_rrsets(zone_id)
        self._zone_rrsets[zone.name] = zone_rrsets
        return zone_rrsets

    def create_rrset(self, zone_id, data):
        self.log.debug('Create rrset. Zone id: %s, data %s', zone_id, data)
        return self._client.create_rrset(zone_id, data)

    def update_rrset(self, zone_id, rrset_id, data):
        self.log.debug(
            f'Update rrsets. Zone id: {zone_id}, rrset id: {rrset_id}'
        )
        try:
            self._client.update_rrset(zone_id, rrset_id, data)
        except ApiException as api_exception:
            self.log.warning(
                f'Failed to update rrset {rrset_id}. {str(api_exception)}'
            )

    def delete_rrset(self, zone_id, rrset_id):
        self.log.debug(
            f'Delete rrsets. Zone id: {zone_id}, rrset id: {rrset_id}'
        )
        try:
            self._client.delete_rrset(zone_id, rrset_id)
        except ApiException as api_exception:
            self.log.warning(
                f'Failed to delete rrset {rrset_id}. {str(api_exception)}'
            )
