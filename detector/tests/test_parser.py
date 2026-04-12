# detector/tests/test_parser.py
import os
import pytest
from io import BytesIO
from eml_parser.parser import parse_eml

# Path to fixtures folder
FIXTURES_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

def load_fixture(filename):
    """Helper: open a fixture .eml file as a BytesIO object (mimics Django upload)."""
    filepath = os.path.join(FIXTURES_DIR, filename)
    with open(filepath, 'rb') as f:
        return BytesIO(f.read())

# ─────────────────────────────────────────────────────────────
# Fixture 1: Plain text email
# ─────────────────────────────────────────────────────────────
class TestPlainTextEmail:
    def setup_method(self):
        self.result = parse_eml(load_fixture('plain_text.eml'))

    def test_no_error(self):
        assert self.result['error'] is None

    def test_sender_extracted(self):
        assert 'attacker@phishing-site.com' in self.result['sender']

    def test_subject_extracted(self):
        assert 'Verify Your Account Now' in self.result['subject']

    def test_reply_to_extracted(self):
        assert 'billing@fakebank.com' in self.result['reply_to']

    def test_x_mailer_extracted(self):
        assert 'PHP Script' in self.result['x_mailer']

    def test_spf_fail_detected(self):
        assert 'fail' in self.result['spf'].lower() or 'softfail' in self.result['spf'].lower()

    def test_dkim_fail_detected(self):
        assert 'fail' in self.result['dkim'].lower()

    def test_body_text_not_empty(self):
        assert len(self.result['body_text']) > 10

    def test_url_extracted(self):
        assert any('malicious-link.xyz' in url for url in self.result['all_urls'])

    def test_no_attachments(self):
        assert self.result['attachments'] == []

# ─────────────────────────────────────────────────────────────
# Fixture 2: HTML body email
# ─────────────────────────────────────────────────────────────
class TestHtmlBodyEmail:
    def setup_method(self):
        self.result = parse_eml(load_fixture('html_body.eml'))

    def test_no_error(self):
        assert self.result['error'] is None

    def test_html_body_captured(self):
        assert len(self.result['html_body']) > 0
        assert '<html>' in self.result['html_body'].lower()

    def test_body_text_extracted_from_html(self):
        assert 'limited' in self.result['body_text'].lower()
        assert '<p>' not in self.result['body_text']

    def test_href_url_extracted(self):
        assert any('paypal-fake.xyz' in url for url in self.result['all_urls'])

    def test_spf_pass(self):
        assert 'pass' in self.result['spf'].lower()

# ─────────────────────────────────────────────────────────────
# Fixture 3: Multipart email with attachment
# ─────────────────────────────────────────────────────────────
class TestMultipartEmail:
    def setup_method(self):
        self.result = parse_eml(load_fixture('multipart.eml'))

    def test_no_error(self):
        assert self.result['error'] is None

    def test_plain_body_extracted(self):
        assert 'newsletter' in self.result['plain_body'].lower()

    def test_html_body_extracted(self):
        assert len(self.result['html_body']) > 0

    def test_body_text_prefers_plain(self):
        assert self.result['body_text'] == self.result['plain_body']

    def test_attachment_detected(self):
        assert 'newsletter.pdf' in self.result['attachments']

    def test_url_from_plain_body(self):
        assert any('company.com' in url for url in self.result['all_urls'])

# ─────────────────────────────────────────────────────────────
# Fixture 4: Malformed .eml
# ─────────────────────────────────────────────────────────────
class TestMalformedEmail:
    def setup_method(self):
        self.result = parse_eml(load_fixture('malformed.eml'))

    def test_does_not_raise_exception(self):
        assert isinstance(self.result, dict)

    def test_returns_empty_fields_gracefully(self):
        assert self.result['sender'] == '' or self.result['sender'] is not None
        assert self.result['subject'] == '' or self.result['subject'] is not None

    def test_body_text_is_string(self):
        assert isinstance(self.result['body_text'], str)

    def test_all_urls_is_list(self):
        assert isinstance(self.result['all_urls'], list)

    def test_attachments_is_list(self):
        assert isinstance(self.result['attachments'], list)

# ─────────────────────────────────────────────────────────────
# Fixture 5: Unicode-encoded headers
# ─────────────────────────────────────────────────────────────
class TestUnicodeHeaders:
    def setup_method(self):
        self.result = parse_eml(load_fixture('unicode_headers.eml'))

    def test_no_error(self):
        assert self.result['error'] is None

    def test_subject_decoded(self):
        assert '=?UTF-8?' not in self.result['subject']
        assert len(self.result['subject']) > 0

    def test_sender_decoded(self):
        assert '=?UTF-8?' not in self.result['sender']

    def test_url_extracted_from_unicode_email(self):
        assert any('unicode-phish.xyz' in url for url in self.result['all_urls'])

    def test_body_text_is_valid_string(self):
        assert isinstance(self.result['body_text'], str)
        assert len(self.result['body_text']) > 0

# ─────────────────────────────────────────────────────────────
# Edge case: empty BytesIO (zero-byte file)
# ─────────────────────────────────────────────────────────────
class TestEmptyFile:
    def test_empty_file_does_not_crash(self):
        result = parse_eml(BytesIO(b''))
        assert isinstance(result, dict)
        assert isinstance(result['body_text'], str)
        assert isinstance(result['all_urls'], list)