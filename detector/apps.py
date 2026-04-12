# detector/apps.py
from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class DetectorConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'detector'

    model = None
    tokenizer = None

    def ready(self):
        """
        Load DistilBERT model ONCE at Django startup.
        Called by Django when the app registry is fully populated.
        NOT called during management commands like makemigrations.
        """
        import sys
        # Skip model loading during migrations or test collection
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return
        try:
            from model_engine.predictor import load_model
            DetectorConfig.model, DetectorConfig.tokenizer = load_model()
            logger.info("DistilBERT model loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load DistilBERT model: {e}")
            DetectorConfig.model = None
            DetectorConfig.tokenizer = None