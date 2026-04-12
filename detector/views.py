# detector/views.py  — complete file
import json
import re
from django.shortcuts import render, redirect
from django.utils.html import escape
from .forms import EmlUploadForm
from .models import ScanLog
from eml_parser.parser import parse_eml
from model_engine.predictor import predict
from xai_engine.explainer import explain
from detector.apps import DetectorConfig

MAX_UPLOAD_BYTES = 5 * 1024 * 1024  # 5 MB


def build_highlighted_html(body_text: str, explanation_tokens: list) -> str:
    """
    Replace each suspicious token in body_text with a colored <span>.
    Returns HTML-safe string.
    """
    if not explanation_tokens:
        return escape(body_text)

    # Build map: lowercase token → highlight color
    token_color_map = {
        t['token'].lower(): t['highlight_color']
        for t in explanation_tokens
        if t.get('highlight_color', 'transparent') != 'transparent'
    }

    if not token_color_map:
        return escape(body_text)

    # HTML-escape the body first so no raw HTML leaks through
    safe_text = escape(body_text)

    # Sort tokens longest-first to avoid partial replacements
    sorted_tokens = sorted(token_color_map.keys(), key=len, reverse=True)

    for token in sorted_tokens:
        color = token_color_map[token]
        pattern = re.compile(r'\b' + re.escape(token) + r'\b', re.IGNORECASE)
        replacement = (
            f'<span class="token-highlight" '
            f'style="color:{color}; font-weight:600;">\\g<0></span>'
        )
        safe_text = pattern.sub(replacement, safe_text)

    return safe_text


def upload_view(request):
    """
    POST only. Full pipeline: validate → parse → predict → explain → save → redirect.
    """
    if request.method != 'POST':
        return redirect('home')

    form = EmlUploadForm(request.POST, request.FILES)
    if not form.is_valid():
        error_msg = form.errors.get('eml_file', ['Invalid file.'])[0]
        return render(request, 'core/home.html', {'error': error_msg})

    uploaded_file = request.FILES['eml_file']

    if uploaded_file.size > MAX_UPLOAD_BYTES:
        return render(request, 'core/home.html', {
            'error': 'File too large. Maximum size is 5 MB.'
        })

    # Parse
    try:
        parsed = parse_eml(uploaded_file)
    except Exception:
        return render(request, 'core/home.html', {
            'error': 'Failed to parse the .eml file. Please check the file format.'
        })

    if parsed.get('error'):
        return render(request, 'core/home.html', {
            'error': f"Parse error: {parsed['error']}"
        })

    # Predict
    try:
        model = DetectorConfig.model
        tokenizer = DetectorConfig.tokenizer
        prediction = predict(
            parsed['body_text'],
            parsed['all_urls'],
            model,
            tokenizer
        )
    except Exception as e:
        return render(request, 'core/home.html', {
            'error': f"Model inference failed: {e}"
        })

    # Explain
    try:
        explanation = explain(parsed['body_text'], model, tokenizer)
    except Exception:
        explanation = []

    # Save to DB
    log = ScanLog.objects.create(
        filename=uploaded_file.name,
        sender=parsed.get('sender', ''),
        recipient=parsed.get('recipient', ''),
        subject=parsed.get('subject', ''),
        reply_to=parsed.get('reply_to', ''),
        x_mailer=parsed.get('x_mailer', ''),
        email_date=parsed.get('date', ''),
        spf=parsed.get('spf', ''),
        dkim=parsed.get('dkim', ''),
        dmarc=parsed.get('dmarc', ''),
        domain_age=parsed.get('domain_age', ''),
        ssl_status=parsed.get('ssl_status', ''),
        ip_address=parsed.get('ip_address', ''),
        attachments=', '.join(parsed.get('attachments', [])) or 'None',
        label=prediction['label'],
        confidence_score=prediction['score'],
        metadata_json=json.dumps(parsed),
        explanation_json=json.dumps(explanation),
    )

    request.session['last_scan_id'] = log.id
    return redirect('results')


def results_view(request):
    """
    GET only. Reads ScanLog from session, builds context for both tabs.
    """
    scan_id = request.session.get('last_scan_id')
    if not scan_id:
        return redirect('home')

    try:
        log = ScanLog.objects.get(id=scan_id)
    except ScanLog.DoesNotExist:
        return redirect('home')

    explanation_tokens = log.get_explanation()
    body_text = log.get_metadata().get('body_text', '')
    highlighted_html = build_highlighted_html(body_text, explanation_tokens)

    # Build metadata rows for Tab 1
    # Classify each value as: 'danger', 'warning', or 'safe'
    def classify(value):
        if not value or value in ('', 'None', 'Unknown'):
            return 'warning'
        lower = value.lower()
        danger_keywords = ['fail', 'missing', 'blacklist', 'blocked',
                           'mismatch', 'none', 'invalid', 'softfail']
        warning_keywords = ['quarantine', 'new', '<24h', 'unknown']
        if any(k in lower for k in danger_keywords):
            return 'danger'
        if any(k in lower for k in warning_keywords):
            return 'warning'
        return 'safe'

    metadata_rows = [
        {'attr': 'Subject',     'value': log.subject,     'status': classify(log.subject)},
        {'attr': 'X-Mailer',    'value': log.x_mailer,    'status': classify(log.x_mailer)},
        {'attr': 'Reply-To',    'value': log.reply_to,    'status': classify(log.reply_to)},
        {'attr': 'SPF',         'value': log.spf,         'status': classify(log.spf)},
        {'attr': 'DKIM',        'value': log.dkim,        'status': classify(log.dkim)},
        {'attr': 'DMARC',       'value': log.dmarc,       'status': classify(log.dmarc)},
        {'attr': 'Domain Age',  'value': log.domain_age,  'status': classify(log.domain_age)},
        {'attr': 'SSL',         'value': log.ssl_status,  'status': classify(log.ssl_status)},
        {'attr': 'IP',          'value': log.ip_address,  'status': classify(log.ip_address)},
        {'attr': 'Attachments', 'value': log.attachments, 'status': classify(log.attachments)},
    ]

    context = {
        'log': log,
        'score_percent': log.confidence_percent(),
        'metadata_rows': metadata_rows,
        'explanation_tokens': explanation_tokens,
        'highlighted_html': highlighted_html,
    }
    return render(request, 'detector/results.html', context)