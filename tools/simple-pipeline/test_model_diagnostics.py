import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location('simple_model_diagnostics', Path(__file__).with_name('mattersyn_simple.py'))
simple = importlib.util.module_from_spec(spec)
spec.loader.exec_module(simple)


class ModelDiagnosticTest(unittest.TestCase):
    def response(self, content, finish='stop', tokens=12):
        return {'choices': [{'message': {'content': content}, 'finish_reason': finish}], 'usage': {'completion_tokens': tokens}}

    def call(self, response):
        with mock.patch.object(simple.urllib.request, 'urlopen', return_value=io.BytesIO(json.dumps(response).encode())) as network:
            value = simple.call_model('http://127.0.0.1:8080/v1', 'qwen3-32b', 'synthetic system', 'PRIVATE SOURCE SENTINEL', 0, 1)
        return value, network.call_args.args[0]

    def test_valid_reply_stays_byte_identical(self):
        payload = '{"pairs": []}'
        reply, _ = self.call(self.response(payload))
        self.assertEqual(reply, payload)

    def test_truncated_reply_error_has_counts_not_payload(self):
        payload = '{"pairs": ["PRIVATE RESPONSE SENTINEL"'
        with self.assertRaises(json.JSONDecodeError) as error:
            self.call(self.response(payload, 'length', 6000))
        self.assertIn('finish_reason=length', str(error.exception))
        self.assertIn('completion_tokens=6000', str(error.exception))
        self.assertNotIn('PRIVATE', str(error.exception))

    def test_missing_usage_is_safe_diagnostic(self):
        response = self.response('invalid'); del response['usage']
        with self.assertRaises(json.JSONDecodeError) as error:
            self.call(response)
        self.assertIn('completion_tokens=None', str(error.exception))

    def test_generation_configuration_unchanged(self):
        _, request = self.call(self.response('{"pairs": []}'))
        body = json.loads(request.data)
        self.assertEqual(body['max_tokens'], 10240)
        self.assertEqual(body['response_format'], {'type': 'json_object'})
        self.assertEqual(body['temperature'], 0)
        self.assertEqual(body['seed'], 1)
        self.assertEqual(request.full_url, 'http://127.0.0.1:8080/v1/chat/completions')

    def test_invalid_reply_is_not_silently_accepted(self):
        with self.assertRaises(json.JSONDecodeError):
            self.call(self.response('not JSON'))


if __name__ == '__main__':
    unittest.main()
