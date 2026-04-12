from django.db import models

# Create your models here.
# detector/models.py
import json
from django.db import models
from django.utils import timezone

class ScanLog(models.Model):
    LABEL_CHOICES = [
        ('phishing', 'Phishing'),
        ('legitimate', 'Legitimate'),
    ]

    # File metadata
    filename = models.CharField(max_length=255)
    uploaded_at = models.DateTimeField(default=timezone.now)

    # Email header fields
    sender = models.CharField(max_length=512, blank=True, default='')
    recipient = models.CharField(max_length=512, blank=True, default='')
    subject = models.CharField(max_length=998, blank=True, default='')
    reply_to = models.CharField(max_length=512, blank=True, default='')
    x_mailer = models.CharField(max_length=255, blank=True, default='')
    email_date = models.CharField(max_length=128, blank=True, default='')

    # Authentication headers
    spf = models.CharField(max_length=128, blank=True, default='')
    dkim = models.CharField(max_length=128, blank=True, default='')
    dmarc = models.CharField(max_length=128, blank=True, default='')

    # Network/domain metadata
    domain_age = models.CharField(max_length=128, blank=True, default='')
    ssl_status = models.CharField(max_length=128, blank=True, default='')
    ip_address = models.CharField(max_length=128, blank=True, default='')
    attachments = models.CharField(max_length=512, blank=True, default='')

    # ML prediction
    label = models.CharField(max_length=16, choices=LABEL_CHOICES)
    confidence_score = models.FloatField()  # 0.0 to 1.0

    # Stored JSON blobs
    metadata_json = models.TextField(default='{}')
    explanation_json = models.TextField(default='[]')

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Scan Log'
        verbose_name_plural = 'Scan Logs'

    def __str__(self):
        return f"[{self.label.upper()}] {self.filename} — {self.uploaded_at:%Y-%m-%d %H:%M}"

    def get_metadata(self):
        return json.loads(self.metadata_json)

    def get_explanation(self):
        return json.loads(self.explanation_json)

    def confidence_percent(self):
        return round(self.confidence_score * 100)
