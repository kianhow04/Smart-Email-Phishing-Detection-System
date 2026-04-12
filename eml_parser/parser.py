# eml_parser/parser.py
import email
import email.policy
import re
import html
from email import message_from_bytes
from email.header import decode_header, make_header
from bs4 import BeautifulSoup
from typing import Any

def _decode_header_value(raw_value: str | None) -> str:
    """Safely decode RFC 2047-encoded header values."""
    if not raw_value:
        return ''
    try:
        return str(make_header(decode_header(raw_value)))
    except Exception:
        return raw_value or ''

def _extract_urls(text: str) -> list[str]:
    """Extract all URLs from plain text using regex."""
    url_pattern = re.compile(
        r'https?://[^\s\'"<>\]\)]+',
        re.IGNORECASE
    )
    return list(set(url_pattern.findall(text)))

def _extract_urls_from_html(html_body: str) -> list[str]:
    """Extract href URLs from HTML using BeautifulSoup."""
    urls = []
    try:
        soup = BeautifulSoup(html_body, 'lxml')
        for tag in soup.find_all(href=True):
            href = tag['href'].strip()
            if href.startswith('http'):
                urls.append(href)
        # Also scan text content for bare URLs
        text_content = soup.get_text(separator=' ', strip=True)
        urls.extend(_extract_urls(text_content))
    except Exception:
        pass
    return list(set(urls))

def _get_plain_text_from_html(html_body: str) -> str:
    """Extract readable text from HTML body."""
    try:
        soup = BeautifulSoup(html_body, 'lxml')
        return soup.get_text(separator=' ', strip=True)
    except Exception:
        return html.unescape(re.sub(r'<[^>]+>', ' ', html_body))

def _extract_auth_result(header_value: str, auth_type: str) -> str:
    """
    Extract SPF/DKIM/DMARC result from Authentication-Results header.
    auth_type: 'spf', 'dkim', or 'dmarc'
    """
    if not header_value:
        return 'Unknown'
    pattern = re.compile(
        rf'{auth_type}=([a-zA-Z]+)',
        re.IGNORECASE
    )
    match = pattern.search(header_value)
    if match:
        result = match.group(1).capitalize()
        # Extract reason if present
        reason_pattern = re.compile(
            rf'{auth_type}=[a-zA-Z]+\s*\(([^)]+)\)',
            re.IGNORECASE
        )
        reason_match = reason_pattern.search(header_value)
        if reason_match:
            return f"{result} ({reason_match.group(1).strip()})"
        return result
    return 'Unknown'

def parse_eml(file_object: Any) -> dict:
    """
    Parse an .eml file object and return a structured dict.
    """
    result = {
        'sender': '',
        'recipient': '',
        'subject': '',
        'date': '',
        'message_id': '',
        'reply_to': '',
        'x_mailer': '',
        'spf': 'Unknown',
        'dkim': 'Unknown',
        'dmarc': 'Unknown',
        'received_headers': [],
        'plain_body': '',
        'html_body': '',
        'body_text': '',      # final text used for ML inference
        'all_urls': [],
        'attachments': [],
        'error': None,
    }

    try:
        raw_bytes = file_object.read()
    except Exception as e:
        result['error'] = f"Cannot read file: {e}"
        return result

    try:
        msg = message_from_bytes(raw_bytes, policy=email.policy.compat32)
    except Exception as e:
        result['error'] = f"Cannot parse .eml: {e}"
        return result

    # ── Headers ───────────────────────────────────────────────────────────────
    try:
        result['sender'] = _decode_header_value(msg.get('From', ''))
        result['recipient'] = _decode_header_value(msg.get('To', ''))
        result['subject'] = _decode_header_value(msg.get('Subject', ''))
        result['date'] = _decode_header_value(msg.get('Date', ''))
        result['message_id'] = msg.get('Message-ID', '').strip()
        result['reply_to'] = _decode_header_value(msg.get('Reply-To', ''))
        result['x_mailer'] = _decode_header_value(msg.get('X-Mailer', ''))
    except Exception as e:
        result['error'] = f"Header decode error: {e}"

    # ── Authentication-Results header ─────────────────────────────────────────
    auth_results_raw = msg.get('Authentication-Results', '')
    received_spf_raw = msg.get('Received-SPF', '')

    if auth_results_raw:
        result['spf'] = _extract_auth_result(auth_results_raw, 'spf')
    if result['spf'] == 'Unknown' and received_spf_raw:
        spf_match = re.match(r'^([a-zA-Z]+)', received_spf_raw.strip())
        if spf_match:
            result['spf'] = spf_match.group(1).capitalize()

    result['dkim'] = _extract_auth_result(auth_results_raw, 'dkim')
    result['dmarc'] = _extract_auth_result(auth_results_raw, 'dmarc')
    result['received_headers'] = msg.get_all('Received', [])

    # ── Body extraction ───────────────────────────────────────────────────────
    plain_parts = []
    html_parts = []
    attachments = []

    try:
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get('Content-Disposition', ''))
                filename = part.get_filename()

                if filename:
                    try:
                        decoded_name = _decode_header_value(filename)
                        attachments.append(decoded_name)
                    except Exception:
                        attachments.append(str(filename))
                    continue

                if 'attachment' in content_disposition.lower():
                    continue

                if content_type == 'text/plain':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        payload = part.get_payload(decode=True)
                        plain_parts.append(payload.decode(charset, errors='replace'))
                    except Exception:
                        plain_parts.append(str(part.get_payload()))

                elif content_type == 'text/html':
                    charset = part.get_content_charset() or 'utf-8'
                    try:
                        payload = part.get_payload(decode=True)
                        html_parts.append(payload.decode(charset, errors='replace'))
                    except Exception:
                        html_parts.append(str(part.get_payload()))
        else:
            content_type = msg.get_content_type()
            charset = msg.get_content_charset() or 'utf-8'
            try:
                payload = msg.get_payload(decode=True)
                if payload is None:
                    payload = msg.get_payload().encode('utf-8', errors='replace')
                decoded_payload = payload.decode(charset, errors='replace')
            except Exception:
                decoded_payload = str(msg.get_payload())

            if content_type == 'text/html':
                html_parts.append(decoded_payload)
            else:
                plain_parts.append(decoded_payload)

    except Exception as e:
        result['error'] = f"Body extraction error: {e}"

    result['plain_body'] = '\n'.join(plain_parts).strip()
    result['html_body'] = '\n'.join(html_parts).strip()
    result['attachments'] = attachments

    # ── Derive body_text for ML ───────────────────────────────────────────────
    if result['plain_body']:
        result['body_text'] = result['plain_body']
    elif result['html_body']:
        result['body_text'] = _get_plain_text_from_html(result['html_body'])
    else:
        result['body_text'] = ''

    # ── URL extraction ────────────────────────────────────────────────────────
    all_urls = []
    all_urls.extend(_extract_urls(result['plain_body']))
    all_urls.extend(_extract_urls_from_html(result['html_body']))
    result['all_urls'] = list(set(all_urls))

    return result