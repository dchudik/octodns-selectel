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

    def _a_rrset(self, hostname):
        return dict(
            uuid=str(uuid.uuid4()),
            name=f'{hostname}.{self._zone_name}',
            type='A',
            ttl=self._ttl,
            records=[dict(content='1.2.3.4'), dict(content='5.6.7.8')],
        )

    def _cname_rrset(self, hostname):
        return dict(
            uuid=str(uuid.uuid4()),
            name=f'{hostname}.{self._zone_name}',
            type='CNAME',
            ttl=self._ttl,
            records=[dict(content=self._zone_name)],
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # A, subdomain=''
        self.rrsets.append(self._a_rrset(hostname=''))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                '',
                data=to_octodns_record_data(self._a_rrset(hostname='')),
            )
        )
        # A, subdomain='sub'
        self.rrsets.append(self._a_rrset(hostname='sub'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'sub',
                data=to_octodns_record_data(self._a_rrset(hostname='sub')),
            )
        )

        # CNAME, subdomain='www2'
        self.rrsets.append(self._cname_rrset(hostname='www2'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'www2',
                data=to_octodns_record_data(self._cname_rrset(hostname='www2')),
            )
        )
        # CNAME, subdomain='wwwdot'
        self.rrsets.append(self._cname_rrset(hostname='wwwdot'))
        self.expected_records.add(
            Record.new(
                self.octodns_zone,
                'wwwdot',
                data=to_octodns_record_data(
                    self._cname_rrset(hostname='wwwdot')
                ),
            )
        )

    # # MX
    # api_record.append(
    #     {
    #         'type': 'MX',
    #         'ttl': 400,
    #         'content': 'mx1.unit.tests',
    #         'priority': 10,
    #         'name': 'unit.tests',
    #         'id': 4,
    #     }
    # )
    # expected.add(
    #     Record.new(
    #         zone,
    #         '',
    #         {
    #             'ttl': 400,
    #             'type': 'MX',
    #             'values': [{'preference': 10, 'exchange': 'mx1.unit.tests.'}],
    #         },
    #     )
    # )

    # # NS
    # api_record.append(
    #     {
    #         'type': 'NS',
    #         'ttl': 600,
    #         'content': 'ns1.unit.tests',
    #         'name': 'unit.tests.',
    #         'id': 6,
    #     }
    # )
    # api_record.append(
    #     {
    #         'type': 'NS',
    #         'ttl': 600,
    #         'content': 'ns2.unit.tests',
    #         'name': 'unit.tests',
    #         'id': 7,
    #     }
    # )
    # api_record.append(
    #     {
    #         'type': 'NS',
    #         'ttl': 600,
    #         'content': 'ns3.unit.tests.',
    #         'name': 'unit.tests',
    #         'id': 7,
    #     }
    # )
    # expected.add(
    #     Record.new(
    #         zone,
    #         '',
    #         {
    #             'ttl': 600,
    #             'type': 'NS',
    #             'values': [
    #                 'ns1.unit.tests.',
    #                 'ns2.unit.tests.',
    #                 'ns3.unit.tests.',
    #             ],
    #         },
    #     )
    # )

    # # NS with sub
    # api_record.append(
    #     {
    #         'type': 'NS',
    #         'ttl': 700,
    #         'content': 'ns3.unit.tests',
    #         'name': 'www3.unit.tests',
    #         'id': 8,
    #     }
    # )
    # api_record.append(
    #     {
    #         'type': 'NS',
    #         'ttl': 700,
    #         'content': 'ns4.unit.tests',
    #         'name': 'www3.unit.tests',
    #         'id': 9,
    #     }
    # )
    # expected.add(
    #     Record.new(
    #         zone,
    #         'www3',
    #         {
    #             'ttl': 700,
    #             'type': 'NS',
    #             'values': ['ns3.unit.tests.', 'ns4.unit.tests.'],
    #         },
    #     )
    # )

    # # SRV
    # api_record.append(
    #     {
    #         'type': 'SRV',
    #         'ttl': 800,
    #         'target': 'foo-1.unit.tests',
    #         'weight': 20,
    #         'priority': 10,
    #         'port': 30,
    #         'id': 10,
    #         'name': '_srv._tcp.unit.tests',
    #     }
    # )
    # api_record.append(
    #     {
    #         'type': 'SRV',
    #         'ttl': 800,
    #         'target': 'foo-2.unit.tests',
    #         'name': '_srv._tcp.unit.tests',
    #         'weight': 50,
    #         'priority': 40,
    #         'port': 60,
    #         'id': 11,
    #     }
    # )
    # expected.add(
    #     Record.new(
    #         zone,
    #         '_srv._tcp',
    #         {
    #             'ttl': 800,
    #             'type': 'SRV',
    #             'values': [
    #                 {
    #                     'priority': 10,
    #                     'weight': 20,
    #                     'port': 30,
    #                     'target': 'foo-1.unit.tests.',
    #                 },
    #                 {
    #                     'priority': 40,
    #                     'weight': 50,
    #                     'port': 60,
    #                     'target': 'foo-2.unit.tests.',
    #                 },
    #             ],
    #         },
    #     )
    # )

    # # AAAA
    # aaaa_record = {
    #     'type': 'AAAA',
    #     'ttl': 200,
    #     'content': '1:1ec:1::1',
    #     'name': 'unit.tests',
    #     'id': 15,
    # }
    # api_record.append(aaaa_record)
    # expected.add(
    #     Record.new(
    #         zone, '', {'ttl': 200, 'type': 'AAAA', 'value': '1:1ec:1::1'}
    #     )
    # )

    # # TXT
    # api_record.append(
    #     {
    #         'type': 'TXT',
    #         'ttl': 300,
    #         'content': 'little text',
    #         'name': 'text.unit.tests',
    #         'id': 16,
    #     }
    # )
    # expected.add(
    #     Record.new(
    #         zone, 'text', {'ttl': 200, 'type': 'TXT', 'value': 'little text'}
    #     )
    # )

    # # SSHFP
    # api_record.append(
    #     {
    #         'type': 'SSHFP',
    #         'ttl': 800,
    #         'algorithm': 1,
    #         'fingerprint_type': 1,
    #         'fingerprint': "123456789abcdef",
    #         'id': 17,
    #         'name': 'sshfp.unit.tests',
    #     }
    # )
    # expected.add(
    #     Record.new(
    #         zone,
    #         'sshfp',
    #         {
    #             'ttl': 800,
    #             'type': 'SSHFP',
    #             'value': {
    #                 'algorithm': 1,
    #                 'fingerprint_type': 1,
    #                 'fingerprint': "123456789abcdef",
    #             },
    #         },
    #     )
    # )

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
