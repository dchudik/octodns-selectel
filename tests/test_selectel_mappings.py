import ipaddress
from unittest import TestCase

from octodns.record import AaaaRecord, ARecord, MxRecord, SrvRecord
from octodns.zone import Zone

from octodns_selectel.exceptions import SelectelException
from octodns_selectel.mappings import to_octodns_record, to_selectel_rrset


class TestSelectelMappings(TestCase):
    zone = Zone("test-octodns.ru.", [])

    _a_values = ["10.20.30.42", "50.60.70.73"]
    _a_record = ARecord(zone, "a", dict(type="A", ttl=3600, values=_a_values))
    _a_rrset = {
        "name": f'a.{zone.name}',
        "ttl": 3600,
        "type": "A",
        "records": [{"content": _a_values[0]}, {"content": _a_values[1]}],
    }

    def test_to_octodns_record_a(self):
        record = to_octodns_record(self._a_rrset)
        self.assertEqual(
            self._a_record._type, record["type"], "Types must equals"
        )
        self.assertEqual(self._a_record.ttl, record["ttl"], "TTL must equals")
        self.assertListEqual(
            self._a_record.values,
            record["values"],
            "Values from rrset must equals values in record",
        )

    def test_to_selectel_rrset_a(self):
        rrset = to_selectel_rrset(self._a_record)
        self.assertEqual(
            self._a_record._type, rrset["type"], "Types must equals"
        )
        self.assertEqual(self._a_record.ttl, rrset["ttl"], "TTL must equals")
        self.assertEqual(
            rrset,
            self._a_rrset,
            "Values from record must equals values in expected rrset",
        )

    _aaaa_values = [
        str(ipaddress.IPv6Address("4ad4:a6c4:f856:08be:5a5f:7f16:cc3a:fab9")),
        # With ipv6: 16e6:deb4:ab53:ebea:2f27:3c17:7937:1c6b not pass
        str(ipaddress.IPv6Address("da78:f69b:8e5a:6221:d0c9:64b8:c6c0:2eab")),
    ]
    _aaaa_record = AaaaRecord(
        zone, "aaaa", dict(type="AAAA", ttl=3600, values=_aaaa_values)
    )
    _aaaa_rrset = {
        "name": f'aaaa.{zone.name}',
        "ttl": 3600,
        "type": "AAAA",
        "records": [{"content": _aaaa_values[0]}, {"content": _aaaa_values[1]}],
    }

    def test_to_octodns_record_aaaa(self):
        record = to_octodns_record(self._aaaa_rrset)
        self.assertEqual(
            self._aaaa_record._type, record["type"], "Types must equals"
        )
        self.assertEqual(
            self._aaaa_record.ttl, record["ttl"], "TTL must equals"
        )
        self.assertListEqual(
            self._aaaa_record.values,
            record["values"],
            "Values from rrset must equals values in record",
        )

    def test_to_selectel_rrset_aaaa(self):
        rrset = to_selectel_rrset(self._aaaa_record)
        self.assertEqual(
            self._aaaa_record._type, rrset["type"], "Types must equals"
        )
        self.assertEqual(self._aaaa_record.ttl, rrset["ttl"], "TTL must equals")
        self.assertEqual(
            rrset,
            self._aaaa_rrset,
            "Values from record must equals values in expected rrset",
        )

    _invalid_type_rrset = {
        "uuid": "ecc390cf-3d6f-48fb-8ef8-a982f6c2b3fc",
        "name": f'bad.{zone.name}',
        "ttl": 3600,
        "type": "INCORRECT",
    }

    def test_to_octodns_record_type_invalid(self):
        with self.assertRaises(SelectelException) as selectel_exception:
            _ = to_octodns_record(self._invalid_type_rrset)
            self.assertEquals(
                selectel_exception.exception,
                'DNS Record with type: INCORRECT not supported',
            )

    _mx_values = [
        dict(preference=10, exchange="mail1.octodns-test.ru."),
        dict(preference=20, exchange="mail2.octodns-test.ru."),
    ]
    _mx_record = MxRecord(
        zone, "mx", dict(type="MX", ttl=3600, values=_mx_values)
    )
    _mx_rrset = {
        "name": f"mx.{zone.name}",
        "ttl": 3600,
        "type": "MX",
        "records": [
            {"content": "10 mail1.octodns-test.ru."},
            {"content": "20 mail2.octodns-test.ru."},
        ],
    }

    def test_to_octodns_record_mx(self):
        record = to_octodns_record(self._mx_rrset)
        self.assertEqual(
            self._mx_record._type, record["type"], "Types must equals"
        )
        self.assertEqual(self._mx_record.ttl, record["ttl"], "TTL must equals")
        self.assertListEqual(
            list(map(lambda value: value.rdata_text, self._mx_record.values)),
            list(
                map(
                    lambda value: f"{value['preference']} {value['exchange']}",
                    record["values"],
                )
            ),
            "Values from rrset must equals values in record",
        )

    def test_to_selectel_rrset_mx(self):
        rrset = to_selectel_rrset(self._mx_record)
        self.assertEqual(
            self._mx_record._type, rrset["type"], "Types must equals"
        )
        self.assertEqual(self._mx_record.ttl, rrset["ttl"], "TTL must equals")
        self.assertEqual(
            rrset,
            self._mx_rrset,
            "Values from record must equals values in expected rrset",
        )

    _srv_values = [
        dict(priority=10, weight=60, port=5060, target="bigbox.example.com."),
        dict(priority=20, weight=0, port=5030, target="backupbox.example.com."),
    ]
    _srv_record = SrvRecord(
        zone, "_sip._tcp", dict(type="SRV", ttl=3600, values=_srv_values)
    )
    _srv_rrset = {
        "name": f"_sip._tcp.{zone.name}",
        "ttl": 3600,
        "type": "SRV",
        "records": [
            {"content": "10 60 5060 bigbox.example.com."},
            {"content": "20 0 5030 backupbox.example.com."},
        ],
    }

    def test_to_octodns_record_srv(self):
        record = to_octodns_record(self._srv_rrset)
        self.assertEqual(
            self._srv_record._type, record["type"], "Types must equals"
        )
        self.assertEqual(self._srv_record.ttl, record["ttl"], "TTL must equals")
        self.assertListEqual(
            list(map(lambda value: value.rdata_text, self._srv_record.values)),
            list(
                map(
                    lambda value: f"{value['priority']} {value['weight']} {value['port']} {value['target']}",
                    record["values"],
                )
            ),
            "Values from rrset must equals values in record",
        )

    def test_to_selectel_rrset_srv(self):
        rrset = to_selectel_rrset(self._srv_record)
        self.assertEqual(
            self._srv_record._type, rrset["type"], "Types must equals"
        )
        self.assertEqual(self._srv_record.ttl, rrset["ttl"], "TTL must equals")
        self.assertEqual(
            rrset,
            self._srv_rrset,
            "Values from record must equals values in expected rrset",
        )
