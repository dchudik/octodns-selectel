import uuid
from unittest import TestCase

import requests_mock

from octodns.record import Delete, Record, Update
from octodns.zone import Zone

from octodns_selectel import DNSClient, SelectelProvider
from octodns_selectel.mappings import to_octodns_record_data


class TestSelectelProvider(TestCase):
    _zone_uuid = str(uuid.uuid4())
    _zone_name = 'unit.tests.'
    _ttl = 3600
    rrsets = []
    octodns_zone = Zone(_zone_name, [])
    expected_records = set()
    selectel_zones = [dict(uuid=_zone_uuid, name=_zone_name)]
    _version = '0.0.1'
    _openstack_token = 'some-openstack-token'

    def _a_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='A',
            ttl=self._ttl,
            records=[dict(content='1.2.3.4'), dict(content='5.6.7.8')],
        )

    def _aaaa_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='AAAA',
            ttl=self._ttl,
            records=[
                dict(content="4ad4:a6c4:f856:18be:5a5f:7f16:cc3a:fab9"),
                dict(content="da78:f69b:8e5a:6221:d0c9:64b8:c6c0:2eab"),
            ],
        )

    def _cname_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='CNAME',
            ttl=self._ttl,
            records=[dict(content=self._zone_name)],
        )

    def _mx_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='MX',
            ttl=self._ttl,
            records=[dict(content=f'10 mx.{self._zone_name}')],
        )

    def _ns_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='NS',
            ttl=self._ttl,
            records=[
                dict(content=f'ns1.{self._zone_name}'),
                dict(content=f'ns2.{self._zone_name}'),
                dict(content=f'ns3.{self._zone_name}'),
            ],
        )

    def _srv_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='SRV',
            ttl=self._ttl,
            records=[
                dict(content=f'40 50 5050 foo-1.{self._zone_name}'),
                dict(content=f'50 60 6060 foo-2.{self._zone_name}'),
            ],
        )

    def _txt_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='TXT',
            ttl=self._ttl,
            records=[dict(content='"Foo1"'), dict(content='"Foo2"')],
        )

    def _sshfp_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}'
            if hostname
            else self._zone_name,
            type='SSHFP',
            ttl=self._ttl,
            records=[dict(content='1 1 123456789abcdef')],
        )

    def setUp(self):
        # A, subdomain=''
        a_uuid = str(uuid.uuid4())
        self.rrsets.append(self._a_rrset(a_uuid, ''))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                '',
                data=to_octodns_record_data(self._a_rrset(a_uuid, '')),
            )
        )
        # A, subdomain='sub'
        a_sub_uuid = str(uuid.uuid4())
        self.rrsets.append(self._a_rrset(a_sub_uuid, 'sub'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'sub',
                data=to_octodns_record_data(self._a_rrset(a_sub_uuid, 'sub')),
            )
        )

        # CNAME, subdomain='www2'
        cname_uuid = str(uuid.uuid4())
        self.rrsets.append(self._cname_rrset(cname_uuid, 'www2'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'www2',
                data=to_octodns_record_data(
                    self._cname_rrset(cname_uuid, 'www2')
                ),
            )
        )
        # CNAME, subdomain='wwwdot'
        cname_sub_uuid = str(uuid.uuid4())
        self.rrsets.append(self._cname_rrset(cname_sub_uuid, 'wwwdot'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'wwwdot',
                data=to_octodns_record_data(
                    self._cname_rrset(cname_sub_uuid, 'wwwdot')
                ),
            )
        )
        # MX, subdomain=''
        mx_uuid = str(uuid.uuid4())
        self.rrsets.append(self._mx_rrset(mx_uuid, ''))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                '',
                data=to_octodns_record_data(self._mx_rrset(mx_uuid, '')),
            )
        )
        # root NS record not supported for unit.tests.; ignoring it
        # NS, subdomain=''
        # ns_uuid = str(uuid.uuid4())
        # self.rrsets.append(self._ns_rrset(ns_uuid, ''))
        # self.expected_records.add(
        #     Record.new(
        #         self.octodns_zone,
        #         '',
        #         data=to_octodns_record_data(self._ns_rrset(ns_uuid, '')),
        #     )
        # )
        # NS, subdomain='www3'
        ns_sub_uuid = str(uuid.uuid4())
        self.rrsets.append(self._ns_rrset(ns_sub_uuid, 'www3'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'www3',
                data=to_octodns_record_data(
                    self._ns_rrset(ns_sub_uuid, 'www3')
                ),
            )
        )
        # AAAA, subdomain=''
        aaaa_uuid = str(uuid.uuid4())
        self.rrsets.append(self._aaaa_rrset(aaaa_uuid, ''))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                '',
                data=to_octodns_record_data(self._aaaa_rrset(aaaa_uuid, '')),
            )
        )
        # SRV, subdomain='_srv._tcp'
        srv_uuid = str(uuid.uuid4())
        self.rrsets.append(self._srv_rrset(srv_uuid, '_srv._tcp'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                '_srv._tcp',
                data=to_octodns_record_data(
                    self._srv_rrset(srv_uuid, '_srv._tcp')
                ),
            )
        )
        # TXT, subdomain='txt'
        txt_uuid = str(uuid.uuid4())
        self.rrsets.append(self._txt_rrset(txt_uuid, 'txt'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'txt',
                data=to_octodns_record_data(self._txt_rrset(srv_uuid, 'txt')),
            )
        )
        # SSHFP, subdomain='sshfp'
        sshfp_uuid = str(uuid.uuid4())
        self.rrsets.append(self._sshfp_rrset(sshfp_uuid, 'sshfp'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'sshfp',
                data=to_octodns_record_data(
                    self._sshfp_rrset(srv_uuid, 'sshfp')
                ),
            )
        )

    def tearDown(self):
        self.rrsets.clear()
        self.expected_records.clear()
        self.octodns_zone = Zone(self._zone_name, [])

    @requests_mock.Mocker()
    def test_populate(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(
                result=self.rrsets, limit=len(self.rrsets), next_offset=0
            ),
        )
        zone = Zone(self._zone_name, [])

        provider = SelectelProvider(self._version, self._openstack_token)
        provider.populate(zone)

        self.assertEqual(len(self.rrsets), len(zone.records))
        self.assertEqual(self.expected_records, zone.records)

    @requests_mock.Mocker()
    def test_apply(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(result=list(), limit=0, next_offset=0),
        )
        fake_http.post(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/rrset', json=dict()
        )

        provider = SelectelProvider(
            self._version, self._openstack_token, strict_supports=False
        )

        zone = Zone(self._zone_name, [])
        for record in self.expected_records:
            zone.add_record(record)

        plan = provider.plan(zone)
        self.assertEqual(len(self.expected_records), len(plan.changes))
        self.assertEqual(len(self.expected_records), provider.apply(plan))

    @requests_mock.Mocker()
    def test_apply_with_create_zone(self, fake_http):
        zone_name_for_created = 'octodns-zone.test.'
        zone_uuid = "bdd902e7-7270-44c8-8d18-120fa5e1e5d4"
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(result=list(), limit=0, next_offset=0),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(result=list(), limit=0, next_offset=0),
        )
        fake_http.post(
            f'{DNSClient.API_URL}/zones',
            json=dict(uuid=zone_uuid, name=zone_name_for_created),
        )
        fake_http.post(f'{DNSClient.API_URL}/zones/{zone_uuid}/rrset')
        zone = Zone(zone_name_for_created, [])
        provider = SelectelProvider(
            self._version, self._openstack_token, strict_supports=False
        )
        provider.populate(zone)

        zone.add_record(
            Record.new(
                zone, '', data=dict(ttl=self._ttl, type="A", values=["1.2.3.4"])
            )
        )

        plan = provider.plan(zone)
        apply_len = provider.apply(plan)
        self.assertEqual(1, apply_len)

    @requests_mock.Mocker()
    def test_populate_with_not_supporting_type(self, fake_http):
        print("populate_soa")
        rrsets_with_not_supporting_type = self.rrsets
        rrsets_with_not_supporting_type.append(
            dict(
                name=self._zone_name,
                ttl=self._ttl,
                type="SOA",
                records=[
                    dict(
                        content="a.ns.selectel.ru. support.selectel.ru. "
                        "2023122202 10800 3600 604800 60"
                    )
                ],
            )
        )

        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(
                result=rrsets_with_not_supporting_type,
                limit=len(self.rrsets),
                next_offset=0,
            ),
        )

        zone = Zone(self._zone_name, [])
        print(zone)
        provider = SelectelProvider(self._version, self._openstack_token)
        print(provider)
        provider.populate(zone)

        self.assertNotEqual(
            len(rrsets_with_not_supporting_type), len(zone.records)
        )
        self.assertNotEqual(rrsets_with_not_supporting_type, zone.records)

    @requests_mock.Mocker()
    def test_apply_update(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )

        updated_rrset = self.rrsets[0]
        updated_record = Record.new(
            zone=self.octodns_zone,
            name=self.octodns_zone.hostname_from_fqdn(updated_rrset["name"]),
            data=to_octodns_record_data(updated_rrset),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(
                result=[self._a_rrset(updated_rrset["uuid"], '')],
                limit=len(self.rrsets),
                next_offset=0,
            ),
        )

        fake_http.delete(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/rrset/{updated_rrset["uuid"]}'
        )

        fake_http.post(f'{DNSClient.API_URL}/zones/{self._zone_uuid}/rrset')

        zone = Zone(self._zone_name, [])
        provider = SelectelProvider(self._version, self._openstack_token)
        provider.populate(zone)

        zone.remove_record(updated_record)
        updated_record.ttl *= 2
        zone.add_record(updated_record)

        plan = provider.plan(zone)
        apply_len = provider.apply(plan)

        self.assertEqual(1, apply_len)

    @requests_mock.Mocker()
    def test_apply_delete(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )

        deleted_rrset = self.rrsets[0]
        deleted_record = Record.new(
            zone=self.octodns_zone,
            name=self.octodns_zone.hostname_from_fqdn(deleted_rrset["name"]),
            data=to_octodns_record_data(deleted_rrset),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(
                result=[self._a_rrset(deleted_rrset["uuid"], '')],
                limit=len(self.rrsets),
                next_offset=0,
            ),
        )

        fake_http.delete(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/rrset/{deleted_rrset["uuid"]}'
        )

        zone = Zone(self._zone_name, [])
        provider = SelectelProvider(self._version, self._openstack_token)
        provider.populate(zone)

        zone.remove_record(deleted_record)

        plan = provider.plan(zone)
        apply_len = provider.apply(plan)

        self.assertEqual(1, apply_len)

    @requests_mock.Mocker()
    def test_apply_delete_with_error(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )
        fake_http.get(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/'
            f'rrset?limit={DNSClient._PAGINATION_LIMIT}&offset=0',
            json=dict(
                result=self.rrsets, limit=len(self.rrsets), next_offset=0
            ),
        )
        deleted_rrset = self.rrsets[0]
        deleted_record = Record.new(
            zone=self.octodns_zone,
            name=self.octodns_zone.hostname_from_fqdn(deleted_rrset["name"]),
            data=to_octodns_record_data(deleted_rrset),
        )

        fake_http.delete(
            f'{DNSClient.API_URL}/zones/{self._zone_uuid}/rrset/{deleted_rrset["uuid"]}',
            status_code=500,
        )

        zone = Zone(self._zone_name, [])
        provider = SelectelProvider(self._version, self._openstack_token)
        provider.populate(zone)
        change = Delete(deleted_record)
        provider._apply_delete(self._zone_uuid, change)

    @requests_mock.Mocker()
    def test_include_change_returns_false(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )

        provider = SelectelProvider(self._version, self._openstack_token)
        zone = Zone(self._zone_name, [])

        exist_record = Record.new(
            zone, '', dict(ttl=60, type="A", values=["1.2.3.4"])
        )
        new = Record.new(zone, '', dict(ttl=10, type="A", values=["1.2.3.4"]))
        change = Update(exist_record, new)
        include_change = provider._include_change(change)

        self.assertFalse(include_change)

    @requests_mock.Mocker()
    def test_include_change_returns_true(self, fake_http):
        fake_http.get(
            f'{DNSClient.API_URL}/zones',
            json=dict(
                result=self.selectel_zones,
                limit=len(self.selectel_zones),
                next_offset=0,
            ),
        )

        provider = SelectelProvider(self._version, self._openstack_token)
        zone = Zone(self._zone_name, [])

        exist_record = Record.new(
            zone, '', dict(ttl=60, type="A", values=["1.2.3.4"])
        )
        new = Record.new(zone, '', dict(ttl=70, type="A", values=["1.2.3.4"]))
        change = Update(exist_record, new)
        include_change = provider._include_change(change)

        self.assertTrue(include_change)

    # @requests_mock.Mocker()
    # def test_domain_list(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )

    #     expected = {'unit.tests': self.domain[0]}
    #     provider = SelectelProvider(123, 'test_token')

    #     result = provider.domain_list()
    #     self.assertEqual(result, expected)

    # @requests_mock.Mocker()
    # def test_authentication_fail(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/', status_code=401)
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )

    #     with self.assertRaises(Exception) as ctx:
    #         SelectelProvider(123, 'fail_token')
    #     self.assertEqual(
    #         str(ctx.exception), 'Authorization failed. Invalid or empty token.'
    #     )

    # @requests_mock.Mocker()
    # def test_not_exist_domain(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/', status_code=404, json='')
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )

    #     fake_http.post(
    #         f'{self.API_URL}/',
    #         json={
    #             "name": "unit.tests",
    #             "create_date": 1507154178,
    #             "id": 100000,
    #         },
    #     )
    #     fake_http.get(f'{self.API_URL}/unit.tests/records/', json=list())
    #     fake_http.head(
    #         f'{self.API_URL}/unit.tests/records/',
    #         headers={'X-Total-Count': str(len(self.api_record))},
    #     )
    #     fake_http.post(f'{self.API_URL}/100000/records/', json=list())

    #     provider = SelectelProvider(123, 'test_token', strict_supports=False)

    #     zone = Zone('unit.tests.', [])

    #     for record in self.expected:
    #         zone.add_record(record)

    #     plan = provider.plan(zone)
    #     self.assertEqual(10, len(plan.changes))
    #     self.assertEqual(10, provider.apply(plan))

    # @requests_mock.Mocker()
    # def test_change_record(self, fake_http):
    #     exist_record = [
    #         self.aaaa_record,
    #         {
    #             "content": "6.6.5.7",
    #             "ttl": 100,
    #             "type": "A",
    #             "id": 100001,
    #             "name": "delete.unit.tests",
    #         },
    #         {
    #             "content": "9.8.2.1",
    #             "ttl": 100,
    #             "type": "A",
    #             "id": 100002,
    #             "name": "unit.tests",
    #         },
    #     ]  # exist
    #     fake_http.get(f'{self.API_URL}/unit.tests/records/', json=exist_record)
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     fake_http.get(f'{self.API_URL}/100000/records/', json=exist_record)
    #     fake_http.head(
    #         f'{self.API_URL}/unit.tests/records/',
    #         headers={'X-Total-Count': str(len(exist_record))},
    #     )
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )
    #     fake_http.head(
    #         f'{self.API_URL}/100000/records/',
    #         headers={'X-Total-Count': str(len(exist_record))},
    #     )
    #     fake_http.post(f'{self.API_URL}/100000/records/', json=list())
    #     fake_http.delete(f'{self.API_URL}/100000/records/100001', text="")
    #     fake_http.delete(f'{self.API_URL}/100000/records/100002', text="")

    #     provider = SelectelProvider(123, 'test_token', strict_supports=False)

    #     zone = Zone('unit.tests.', [])

    #     for record in self.expected:
    #         zone.add_record(record)

    #     plan = provider.plan(zone)
    #     self.assertEqual(10, len(plan.changes))
    #     self.assertEqual(10, provider.apply(plan))

    # @requests_mock.Mocker()
    # def test_fail_record_deletion(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     record = dict(id=1, type="NS", name="unit.tests")
    #     fake_http.get(f'{self.API_URL}/100000/records/', json=[record])
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )
    #     fake_http.head(
    #         f'{self.API_URL}/unit.tests/records/',
    #         headers={'X-Total-Count': '1'},
    #     )
    #     fake_http.delete(f'{self.API_URL}/100000/records/1', exc=HTTPError)
    #     provider = SelectelProvider(123, 'test_token')

    #     provider.delete_record('unit.tests', 'NS', None)
