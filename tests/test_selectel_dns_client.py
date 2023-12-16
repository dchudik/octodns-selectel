from unittest import TestCase

from octodns_selectel.dns_client import DNSClient


class TestSelectelDNSClient(TestCase):
    zone_uuid = "01073035-cc25-4956-b0c9-b3a270091c37"
    rrset_uuid = "f651a6dh-60ca-4b53-800e-4b7fc37d81f2"

    def test_zone_path(self):
        self.assertEqual(DNSClient._zone_path(), "/zones")

    def test_zone_path_specific(self):
        self.assertEqual(
            DNSClient._zone_path_specific(self.zone_uuid),
            f'/zones/{self.zone_uuid}',
        )

    def test_rrset_path(self):
        self.assertEqual(
            DNSClient._rrset_path(self.zone_uuid),
            f'/zones/{self.zone_uuid}/rrset',
        )

    def test_rrset_path_specific(self):
        self.assertEqual(
            DNSClient._rrset_path_specific(self.zone_uuid, self.rrset_uuid),
            f'/zones/{self.zone_uuid}/rrset/{self.rrset_uuid}',
        )
