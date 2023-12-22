from unittest import TestCase

import requests_mock

from octodns_selectel.dns_client import DNSClient
from octodns_selectel.exceptions import ApiException


class TestSelectelDNSClient(TestCase):
    zone_name = "test-octodns.ru."
    zone_uuid = "01073035-cc25-4956-b0c9-b3a270091c37"
    rrset_uuid = "f651a6dh-60ca-4b53-800e-4b7fc37d81f2"
    API_URL = 'https://api.selectel.ru/domains/v2'
    library_version = "0.0.1"
    openstack_token = "oasdjoinfhusaiuhsduhsuidahuishiuhsdiu"
    dns_client = DNSClient(library_version, openstack_token)
    _PAGINATION_LIMIT = 50
    _PAGINATION_OFFSET = 0

    def test_zone_path(self):
        self.assertEqual(DNSClient._zone_path, "/zones")

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

    @requests_mock.Mocker()
    def test_request_pass_openstack_token(self, fake_http):
        fake_http.get(
            f'{self.API_URL}/zones',
            headers={"X-Auth-Token": self.openstack_token},
            json={},
        )
        self.dns_client._request("GET", DNSClient._zone_path)
        self.assertEqual(
            fake_http.last_request.headers["X-Auth-Token"],
            self.openstack_token,
            "OpenStack token must pass in X-Auth-Token header",
        )

    @requests_mock.Mocker()
    def test_request_unauthorized_with_html_body(self, fake_http):
        response_unauthorized_html = """
            <html>
            <head><title>401 Authorization Required</title></head>
            <body>
                <center><h1>401 Authorization Required</h1></center>
                <hr><center>nginx</center>
            </body>
            </html>
        """
        fake_http.get(
            f'{self.API_URL}/zones',
            status_code=401,
            headers={"X-Auth-Token": self.openstack_token},
            text=response_unauthorized_html,
        )
        with self.assertRaises(ApiException) as api_exception:
            self.dns_client._request("GET", DNSClient._zone_path)
        self.assertEqual(
            'Authorization failed. Invalid or empty token.',
            str(api_exception.exception),
        )

    @requests_mock.Mocker()
    def test_request_bad_request_with_description(self, fake_http):
        bad_response = dict(
            error="bad_request",
            description=(
                "Data field in DNS should start with quote (\") "
                "at position 0 of 'Example TXT Record'"
            ),
        )
        fake_http.post(
            f'{self.API_URL}/zones',
            headers={"X-Auth-Token": self.openstack_token},
            status_code=422,
            json=bad_response,
        )
        with self.assertRaises(ApiException) as api_exception:
            self.dns_client._request("POST", DNSClient._zone_path)
        print("Msg: " + str(api_exception.exception))
        self.assertEqual(
            f'Bad request. Description: {bad_response.get("description")}.',
            str(api_exception.exception),
        )

    @requests_mock.Mocker()
    def test_request_resource_not_found(self, fake_http):
        bad_response_with_resource_not_found = dict(
            error="zone_not_found", description="invalid value"
        )
        fake_http.get(
            f'{self.API_URL}/zones/{self.zone_uuid}',
            headers={"X-Auth-Token": self.openstack_token},
            status_code=404,
            json=bad_response_with_resource_not_found,
        )
        with self.assertRaises(ApiException) as api_exception:
            self.dns_client._request(
                "GET", DNSClient._zone_path_specific(self.zone_uuid)
            )
        self.assertEqual(
            f'Resource not found: {bad_response_with_resource_not_found["error"]}.',
            str(api_exception.exception),
        )

    @requests_mock.Mocker()
    def test_request_resource_conflict(self, fake_http):
        bad_response_with_resource_not_found = dict(
            error="this_rrset_is_already_exists", description="invalid value"
        )
        fake_http.get(
            f'{self.API_URL}/zones/{self.zone_uuid}',
            headers={"X-Auth-Token": self.openstack_token},
            status_code=409,
            json=bad_response_with_resource_not_found,
        )
        with self.assertRaises(ApiException) as api_exception:
            self.dns_client._request(
                "GET", DNSClient._zone_path_specific(self.zone_uuid)
            )
        self.assertEqual(
            f'Conflict: {bad_response_with_resource_not_found["error"]}.',
            str(api_exception.exception),
        )

    @requests_mock.Mocker()
    def test_request_internal_error(self, fake_http):
        fake_http.get(
            f'{self.API_URL}/zones',
            headers={"X-Auth-Token": self.openstack_token},
            status_code=500,
            json={},
        )
        with self.assertRaises(ApiException) as api_exception:
            self.dns_client._request("GET", DNSClient._zone_path)
        self.assertEqual('Internal server error.', str(api_exception.exception))

    @requests_mock.Mocker()
    def test_request_all_entities_without_offset(self, fake_http):
        response_without_offset = dict(
            count=1,
            next_offset=0,
            result=[
                dict(
                    uuid="0eb2f04e-74fd-4264-a4b8-396e5fc95f00",
                    name=self.zone_name,
                    ttl=3600,
                    type="SOA",
                    records=[
                        dict(
                            content="a.ns.selectel.ru. support.selectel.ru. 2023122202 10800 "
                            "3600 604800 60",
                            disabled=False,
                        )
                    ],
                    zone=self.zone_uuid,
                ),
                dict(
                    uuid="0eb2f04e-74fd-4264-a4b8-396e5fc95f00",
                    name=self.zone_name,
                    ttl=3600,
                    type="NS",
                    records=[
                        dict(content="a.ns.selectel.ru.", disabled=False),
                        dict(content="b.ns.selectel.ru.", disabled=False),
                        dict(content="c.ns.selectel.ru.", disabled=False),
                        dict(content="d.ns.selectel.ru.", disabled=False),
                    ],
                    zone=self.zone_uuid,
                ),
            ],
        )
        fake_http.get(
            f'{self.API_URL}/zones/{self.zone_uuid}/rrset',
            headers={"X-Auth-Token": self.openstack_token},
            status_code=200,
            json=response_without_offset,
        )
        all_entities = self.dns_client._request_all_entities(
            DNSClient._rrset_path(self.zone_uuid)
        )
        self.assertEqual(response_without_offset["result"], all_entities)
