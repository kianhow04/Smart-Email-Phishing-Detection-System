from django.contrib import admin

# Register your models here.
# detector/admin.py
from django.contrib import admin
from .models import ScanLog

@admin.register(ScanLog)
class ScanLogAdmin(admin.ModelAdmin):
    list_display = ('filename', 'sender', 'subject', 'label', 'confidence_score', 'uploaded_at')
    list_filter = ('label', 'uploaded_at')
    search_fields = ('filename', 'sender', 'subject')
    readonly_fields = ('uploaded_at', 'metadata_json', 'explanation_json')
    ordering = ('-uploaded_at',)