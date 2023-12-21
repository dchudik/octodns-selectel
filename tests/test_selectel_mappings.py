import collections
import ipaddress
from unittest import TestCase

from octodns.record import (
    AaaaRecord,
    AliasRecord,
    ARecord,
    CnameRecord,
    MxRecord,
    SrvRecord,
    SshfpRecord,
)
from octodns.zone import Zone

from octodns_selectel.exceptions import SelectelException
from octodns_selectel.mappings import to_octodns_record, to_selectel_rrset

PairTest = collections.namedtuple("PairTest", ["record", "rrset"])


class TestSelectelMappings(TestCase):
    def setUp(self):
        self.zone = Zone("test-octodns.ru.", [])
        self.ttl = 3600

    def _assert_mapping_common(self, test_pairs):
        for tc in test_pairs:
            with self.subTest():
                rrset_from_record = to_selectel_rrset(tc.record)
                self.assertEqual(
                    rrset_from_record.get("name"),
                    tc.rrset["name"],
                    "Names must equals",
                )
                self.assertEqual(
                    rrset_from_record.get("type"),
                    tc.rrset["type"],
                    "Types must equals",
                )
                self.assertEqual(
                    rrset_from_record.get("ttl"),
                    tc.rrset["ttl"],
                    "TTLs must equals",
                )

                record_data_from_rrset = to_octodns_record(tc.rrset)
                self.assertEqual(
                    record_data_from_rrset.get("type"),
                    tc.record._type,
                    "Types must equals",
                )
                self.assertEqual(
                    record_data_from_rrset.get("ttl"),
                    tc.record.ttl,
                    "TTLs must equals",
                )

    def _assert_mapping_values(self, test_pairs):
        for tc in test_pairs:
            with self.subTest():
                rrset_from_record = to_selectel_rrset(tc.record)
                self.assertListEqual(
                    rrset_from_record.get("records"), tc.rrset["records"]
                )

                record_data_from_rrset = to_octodns_record(tc.rrset)
                self.assertListEqual(
                    record_data_from_rrset.get("values"), tc.record.values
                )

    def _assert_mapping_mx(self, test_pairs):
        for tc in test_pairs:
            with self.subTest():
                rrset_from_record = to_selectel_rrset(tc.record)
                self.assertListEqual(
                    list(
                        map(
                            lambda value: value.get("content"),
                            rrset_from_record.get("records"),
                        )
                    ),
                    list(map(lambda value: value.rdata_text, tc.record.values)),
                )

                record_data_from_rrset = to_octodns_record(tc.rrset)
                self.assertListEqual(
                    list(
                        map(
                            lambda value: f"{value['preference']} {value['exchange']}",
                            record_data_from_rrset.get("values"),
                        )
                    ),
                    list(map(lambda value: value.rdata_text, tc.record.values)),
                )

    def _srv_to_string(self, srv):
        return (
            f"{srv['priority']} {srv['weight']} {srv['port']} {srv['target']}"
        )

    def _assert_mapping_srv(self, test_pairs):
        for tc in test_pairs:
            with self.subTest():
                rrset_from_record = to_selectel_rrset(tc.record)
                self.assertListEqual(
                    list(
                        map(
                            lambda value: value.get("content"),
                            rrset_from_record.get("records"),
                        )
                    ),
                    list(map(lambda value: value.rdata_text, tc.record.values)),
                )

                record_data_from_rrset = to_octodns_record(tc.rrset)
                self.assertListEqual(
                    list(
                        map(
                            lambda srv_value: self._srv_to_string(srv_value),
                            record_data_from_rrset.get("values"),
                        )
                    ),
                    list(map(lambda value: value.rdata_text, tc.record.values)),
                )

    def _sshfp_to_string(self, sshfp):
        return f'{sshfp["algorithm"]} {sshfp["fingerprint_type"]} {sshfp["fingerprint"]}'

    def _assert_mapping_sshfp(self, test_pairs):
        for tc in test_pairs:
            with self.subTest():
                rrset_from_record = to_selectel_rrset(tc.record)
                self.assertListEqual(
                    list(
                        map(
                            lambda value: value.get("content"),
                            rrset_from_record.get("records"),
                        )
                    ),
                    list(map(lambda value: value.rdata_text, tc.record.values)),
                )

                record_data_from_rrset = to_octodns_record(tc.rrset)
                self.assertListEqual(
                    sorted(
                        list(
                            map(
                                lambda sshfp_value: self._sshfp_to_string(
                                    sshfp_value
                                ),
                                record_data_from_rrset.get("values"),
                            )
                        )
                    ),
                    list(map(lambda value: value.rdata_text, tc.record.values)),
                )

    def _assert_mapping_value(self, test_pairs):
        for tc in test_pairs:
            with self.subTest():
                rrset_from_record = to_selectel_rrset(tc.record)
                self.assertListEqual(
                    rrset_from_record.get("records"), tc.rrset["records"]
                )

                record_data_from_rrset = to_octodns_record(tc.rrset)
                self.assertEqual(
                    record_data_from_rrset.get("value"), tc.record.value
                )

    def test_mapping_record_a(self):
        ipv4_list = ["10.20.30.40", "50.60.70.80"]
        test_pairs = (
            PairTest(
                ARecord(self.zone, "a", dict(ttl=self.ttl, value=ipv4_list[0])),
                dict(
                    name=f"a.{self.zone.name}",
                    ttl=self.ttl,
                    type="A",
                    records=[dict(content=ipv4_list[0])],
                ),
            ),
            PairTest(
                ARecord(self.zone, "a", dict(ttl=self.ttl, values=ipv4_list)),
                dict(
                    name=f"a.{self.zone.name}",
                    ttl=self.ttl,
                    type="A",
                    records=[
                        dict(content=ipv4_list[0]),
                        dict(content=ipv4_list[1]),
                    ],
                ),
            ),
            PairTest(
                ARecord(self.zone, "", dict(ttl=self.ttl, values=ipv4_list)),
                dict(
                    name=self.zone.name,
                    ttl=self.ttl,
                    type="A",
                    records=[
                        dict(content=ipv4_list[0]),
                        dict(content=ipv4_list[1]),
                    ],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_values(test_pairs)

    def test_mapping_record_aaaa(self):
        ipv6_list = [
            str(
                ipaddress.IPv6Address("4ad4:a6c4:f856:08be:5a5f:7f16:cc3a:fab9")
            ),
            str(
                ipaddress.IPv6Address("da78:f69b:8e5a:6221:d0c9:64b8:c6c0:2eab")
            ),
        ]
        test_pairs = (
            PairTest(
                AaaaRecord(
                    self.zone,
                    "aaaa",
                    dict(type="AAAA", ttl=self.ttl, value=ipv6_list[0]),
                ),
                dict(
                    name=f"aaaa.{self.zone.name}",
                    ttl=self.ttl,
                    type="AAAA",
                    records=[dict(content=ipv6_list[0])],
                ),
            ),
            PairTest(
                AaaaRecord(
                    self.zone,
                    "aaaa",
                    dict(type="AAAA", ttl=self.ttl, values=ipv6_list),
                ),
                dict(
                    name=f"aaaa.{self.zone.name}",
                    ttl=self.ttl,
                    type="AAAA",
                    records=[
                        dict(content=ipv6_list[0]),
                        dict(content=ipv6_list[1]),
                    ],
                ),
            ),
            PairTest(
                AaaaRecord(
                    self.zone,
                    "",
                    dict(type="AAAA", ttl=self.ttl, values=ipv6_list),
                ),
                dict(
                    name=self.zone.name,
                    ttl=self.ttl,
                    type="AAAA",
                    records=[
                        dict(content=ipv6_list[0]),
                        dict(content=ipv6_list[1]),
                    ],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_values(test_pairs)

    def test_mapping_record_mx(self):
        mx_list_dict = [
            dict(preference=10, exchange="mail1.octodns-test.ru."),
            dict(preference=20, exchange="mail2.octodns-test.ru."),
        ]
        mx_list_str = [
            f'{mx_record["preference"]} {mx_record["exchange"]}'
            for mx_record in mx_list_dict
        ]
        test_pairs = (
            PairTest(
                MxRecord(
                    self.zone,
                    "mx",
                    dict(type="MX", ttl=self.ttl, value=mx_list_dict[0]),
                ),
                dict(
                    name=f"mx.{self.zone.name}",
                    ttl=self.ttl,
                    type="MX",
                    records=[dict(content=mx_list_str[0])],
                ),
            ),
            PairTest(
                MxRecord(
                    self.zone,
                    "mx",
                    dict(type="MX", ttl=self.ttl, values=mx_list_dict),
                ),
                dict(
                    name=f"mx.{self.zone.name}",
                    ttl=self.ttl,
                    type="MX",
                    records=[
                        dict(content=mx_list_str[0]),
                        dict(content=mx_list_str[1]),
                    ],
                ),
            ),
            PairTest(
                MxRecord(
                    self.zone,
                    "",
                    dict(type="MX", ttl=self.ttl, values=mx_list_dict),
                ),
                dict(
                    name=self.zone.name,
                    ttl=self.ttl,
                    type="MX",
                    records=[
                        dict(content=mx_list_str[0]),
                        dict(content=mx_list_str[1]),
                    ],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_mx(test_pairs)

    def test_mapping_record_srv(self):
        srv_list_dict = [
            dict(
                priority=10, weight=60, port=5060, target="bigbox.example.com."
            ),
            dict(
                priority=20,
                weight=0,
                port=5030,
                target="backupbox.example.com.",
            ),
        ]
        srv_list_str = [
            self._srv_to_string(srv_value) for srv_value in srv_list_dict
        ]
        test_pairs = (
            PairTest(
                SrvRecord(
                    self.zone,
                    "_sip._tcp",
                    dict(type="SRV", ttl=self.ttl, value=srv_list_dict[0]),
                ),
                dict(
                    name=f"_sip._tcp.{self.zone.name}",
                    ttl=self.ttl,
                    type="SRV",
                    records=[dict(content=srv_list_str[0])],
                ),
            ),
            PairTest(
                SrvRecord(
                    self.zone,
                    "_sip._tcp",
                    dict(type="SRV", ttl=self.ttl, values=srv_list_dict),
                ),
                dict(
                    name=f"_sip._tcp.{self.zone.name}",
                    ttl=self.ttl,
                    type="SRV",
                    records=[
                        dict(content=srv_list_str[0]),
                        dict(content=srv_list_str[1]),
                    ],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_srv(test_pairs)

    def test_mapping_record_sshfp(self):
        sshfp_list_dict = [
            dict(
                algorithm=4,
                fingerprint_type=2,
                fingerprint="123456789abcdef67890123456789abcdef67890123456789abcdef123456789",
            ),
            dict(
                algorithm=1,
                fingerprint_type=2,
                fingerprint="4158F281921260B0205508121C6F5CEE879E15F22BDBC319EF2AE9FD308DB3BE",
            ),
        ]
        sshfp_list_str = [
            self._sshfp_to_string(sshfp_value)
            for sshfp_value in sshfp_list_dict
        ]
        test_pairs = (
            PairTest(
                SshfpRecord(
                    self.zone,
                    "sshfp",
                    dict(type="SSHFP", ttl=self.ttl, value=sshfp_list_dict[0]),
                ),
                dict(
                    name=f"sshfp.{self.zone.name}",
                    ttl=self.ttl,
                    type="SSHFP",
                    records=[dict(content=sshfp_list_str[0])],
                ),
            ),
            PairTest(
                SshfpRecord(
                    self.zone,
                    "sshfp",
                    dict(type="SSHFP", ttl=self.ttl, values=sshfp_list_dict),
                ),
                dict(
                    name=f"sshfp.{self.zone.name}",
                    ttl=self.ttl,
                    type="SSHFP",
                    records=[
                        dict(content=sshfp_list_str[0]),
                        dict(content=sshfp_list_str[1]),
                    ],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_sshfp(test_pairs)

    def test_mapping_record_cname(self):
        cname_value = "proxydomain.ru."
        test_pairs = (
            PairTest(
                CnameRecord(
                    self.zone,
                    "cname",
                    dict(type="CNAME", ttl=self.ttl, value=cname_value),
                ),
                dict(
                    name=f"cname.{self.zone.name}",
                    ttl=self.ttl,
                    type="CNAME",
                    records=[dict(content=cname_value)],
                ),
            ),
            PairTest(
                CnameRecord(
                    self.zone,
                    "",
                    dict(type="CNAME", ttl=self.ttl, value=cname_value),
                ),
                dict(
                    name=self.zone.name,
                    ttl=self.ttl,
                    type="CNAME",
                    records=[dict(content=cname_value)],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_value(test_pairs)

    def test_mapping_record_alias(self):
        cname_value = "proxydomain.ru."
        test_pairs = (
            PairTest(
                AliasRecord(
                    self.zone,
                    "alias",
                    dict(type="ALIAS", ttl=self.ttl, value=cname_value),
                ),
                dict(
                    name=f"alias.{self.zone.name}",
                    ttl=self.ttl,
                    type="ALIAS",
                    records=[dict(content=cname_value)],
                ),
            ),
            PairTest(
                AliasRecord(
                    self.zone,
                    "",
                    dict(type="ALIAS", ttl=self.ttl, value=cname_value),
                ),
                dict(
                    name=self.zone.name,
                    ttl=self.ttl,
                    type="ALIAS",
                    records=[dict(content=cname_value)],
                ),
            ),
        )
        self._assert_mapping_common(test_pairs)
        self._assert_mapping_value(test_pairs)

    def test_mapping_record_raise_exception_invalid_type(self):
        invalid_type_record = ARecord(
            self.zone,
            "bad",
            dict(
                type="INCORRECT",
                ttl=self.ttl,
                values=["10.20.30.40", "50.60.70.80"],
            ),
        )
        invalid_type_record._type = "INCORRECT"
        invalid_type_rrset = dict(
            name=f"bad.{self.zone.name}", ttl=self.ttl, type="INCORRECT"
        )

        with self.assertRaises(SelectelException) as selectel_exception:
            _ = to_octodns_record(invalid_type_rrset)
            self.assertEquals(
                selectel_exception.exception,
                'DNS Record with type: INCORRECT not supported',
            )

        with self.assertRaises(SelectelException) as selectel_exception:
            _ = to_selectel_rrset(invalid_type_record)
            print(invalid_type_record._type)
            self.assertEquals(
                selectel_exception.exception,
                'DNS Record with type: INCORRECT not supported',
            )
