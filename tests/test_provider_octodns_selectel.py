import uuid
from unittest import TestCase

import requests_mock

# from octodns.record import Record, Update
from octodns.record import Record
from octodns.zone import Zone

from octodns_selectel import DNSClient, SelectelProvider
from octodns_selectel.mappings import to_octodns_record_data

# from requests.exceptions import HTTPError


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
            name=f'{hostname}.{self._zone_name}',
            type='A',
            ttl=self._ttl,
            records=[dict(content='1.2.3.4'), dict(content='5.6.7.8')],
        )

    def _aaaa_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}',
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
            name=f'{hostname}.{self._zone_name}',
            type='CNAME',
            ttl=self._ttl,
            records=[dict(content=self._zone_name)],
        )

    def _mx_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}',
            type='MX',
            ttl=self._ttl,
            records=[dict(content=f'10 mx.{self._zone_name}')],
        )

    def _ns_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}',
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
            name=f'{hostname}.{self._zone_name}',
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
            name=f'{hostname}.{self._zone_name}',
            type='TXT',
            ttl=self._ttl,
            records=[dict(content='"Foo1"'), dict(content='"Foo2"')],
        )

    def _sshfp_rrset(self, uuid, hostname):
        return dict(
            uuid=uuid,
            name=f'{hostname}.{self._zone_name}',
            type='SSHFP',
            ttl=self._ttl,
            records=[dict(content='1 1 123456789abcdef')],
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
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
        # NS, subdomain=''
        ns_uuid = str(uuid.uuid4())
        self.rrsets.append(self._ns_rrset(ns_uuid, ''))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                '',
                data=to_octodns_record_data(self._ns_rrset(ns_uuid, '')),
            )
        )
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
        print("Excpected", self.expected_records)
        print("Zone", zone.records)
        self.assertEqual(self.expected_records, zone.records)

    # @requests_mock.Mocker()
    # def test_populate_invalid_record(self, fake_http):
    #     more_record = self.api_record
    #     more_record.append(
    #         {
    #             "name": "unit.tests",
    #             "id": 100001,
    #             "content": "support.unit.tests.",
    #             "ttl": 300,
    #             "ns": "ns1.unit.tests",
    #             "type": "SOA",
    #             "email": "support@unit.tests",
    #         }
    #     )

    #     zone = Zone('unit.tests.', [])
    #     fake_http.get(f'{self.API_URL}/unit.tests/records/', json=more_record)
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     fake_http.head(
    #         f'{self.API_URL}/unit.tests/records/',
    #         headers={'X-Total-Count': str(len(self.api_record))},
    #     )
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )

    #     zone.add_record(
    #         Record.new(
    #             self.zone,
    #             'unsup',
    #             {
    #                 'ttl': 200,
    #                 'type': 'NAPTR',
    #                 'value': {
    #                     'order': 40,
    #                     'preference': 70,
    #                     'flags': 'U',
    #                     'service': 'SIP+D2U',
    #                     'regexp': '!^.*$!sip:info@bar.example.com!',
    #                     'replacement': '.',
    #                 },
    #             },
    #         )
    #     )

    #     provider = SelectelProvider(123, 'secret_token')
    #     provider.populate(zone)

    #     self.assertNotEqual(self.expected, zone.records)

    # @requests_mock.Mocker()
    # def test_apply(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/unit.tests/records/', json=list())
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     fake_http.head(
    #         f'{self.API_URL}/unit.tests/records/',
    #         headers={'X-Total-Count': '0'},
    #     )
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
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
    # def test_delete_no_exist_record(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     fake_http.get(f'{self.API_URL}/100000/records/', json=list())
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )
    #     fake_http.head(
    #         f'{self.API_URL}/unit.tests/records/',
    #         headers={'X-Total-Count': '0'},
    #     )

    #     provider = SelectelProvider(123, 'test_token')

    #     zone = Zone('unit.tests.', [])

    #     provider.delete_record('unit.tests', 'NS', zone)

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
    # def test_include_change_returns_false(self, fake_http):
    #     fake_http.get(f'{self.API_URL}/', json=self.domain)
    #     fake_http.head(
    #         f'{self.API_URL}/', headers={'X-Total-Count': str(len(self.domain))}
    #     )
    #     provider = SelectelProvider(123, 'test_token')
    #     zone = Zone('unit.tests.', [])

    #     exist_record = Record.new(
    #         zone, '', {'ttl': 60, 'type': 'A', 'values': ['1.1.1.1', '2.2.2.2']}
    #     )
    #     new = Record.new(
    #         zone, '', {'ttl': 10, 'type': 'A', 'values': ['1.1.1.1', '2.2.2.2']}
    #     )
    #     change = Update(exist_record, new)

    #     include_change = provider._include_change(change)

    #     self.assertFalse(include_change)

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
