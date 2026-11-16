import json
import unittest

from seedess_sdk import Seedess, SeedessError


def fake_transport(status=200, body=None):
    calls = []

    def transport(method, url, headers, payload):
        calls.append({"method": method, "url": url, "headers": headers, "body": payload})
        return status, json.dumps(body).encode() if body is not None else b""

    transport.calls = calls
    return transport


class SeedessTests(unittest.TestCase):
    def test_create_stream_uses_bearer_and_body(self):
        transport = fake_transport(201, {"ok": True, "id": "demo", "publicToken": "pk_1"})
        client = Seedess("key_test", transport=transport)

        stream = client.create_stream("https://origin/master.m3u8", id="demo", live=True)

        self.assertEqual(stream["id"], "demo")
        call = transport.calls[0]
        self.assertEqual(call["method"], "POST")
        self.assertEqual(call["url"], "https://seedess.com/api/v1/streams")
        self.assertEqual(call["headers"]["authorization"], "Bearer key_test")
        self.assertEqual(
            json.loads(call["body"]),
            {"url": "https://origin/master.m3u8", "id": "demo", "live": True},
        )

    def test_path_ids_are_encoded(self):
        transport = fake_transport(200, {"ok": True})
        client = Seedess("key_test", transport=transport)
        client.get_stream("a/b")
        self.assertEqual(transport.calls[0]["url"], "https://seedess.com/api/v1/streams/a%2Fb")

    def test_disable_and_enable_map_to_kill_and_revive(self):
        transport = fake_transport(200, {"ok": True})
        client = Seedess("key_test", transport=transport)
        client.disable_peers("demo")
        client.enable_peers("demo")
        self.assertEqual(transport.calls[0]["url"], "https://seedess.com/api/v1/streams/demo/kill")
        self.assertEqual(transport.calls[1]["url"], "https://seedess.com/api/v1/streams/demo/revive")

    def test_telemetry_has_no_api_key(self):
        transport = fake_transport(204, None)
        client = Seedess("key_test", transport=transport)
        client.send_telemetry("s", "demo", p2p_bytes=10)
        call = transport.calls[0]
        self.assertEqual(call["url"], "https://seedess.com/api/v1/telemetry")
        self.assertNotIn("authorization", call["headers"])
        self.assertEqual(json.loads(call["body"])["p2pBytes"], 10)

    def test_error_envelope_becomes_seedess_error(self):
        transport = fake_transport(429, {"ok": False, "error": {"code": "QUOTA_EXCEEDED", "message": "Limit reached"}})
        client = Seedess("key_test", transport=transport)
        with self.assertRaises(SeedessError) as caught:
            client.create_stream("https://origin/master.m3u8")
        self.assertEqual(caught.exception.status, 429)
        self.assertEqual(caught.exception.code, "QUOTA_EXCEEDED")
        self.assertEqual(str(caught.exception), "Limit reached")

    def test_rejects_public_token(self):
        with self.assertRaises(ValueError):
            Seedess("pk_stream")


if __name__ == "__main__":
    unittest.main()
