# model_engine/predictor.py
import os
import logging
import torch
import torch.nn.functional as F
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

logger = logging.getLogger(__name__)

# Hardcoded to point directly to your local model folder
MODEL_PATH = os.path.join(os.path.dirname(__file__), 'fine_tuned_distilbert')

# Label mapping — must match your fine-tuned model's classes
ID2LABEL = {0: 'legitimate', 1: 'phishing'}

MAX_INPUT_LENGTH = 512
MAX_URL_CHARS = 200

def load_model():
    """Load your fine-tuned DistilBERT model and tokenizer from the local folder."""
    if not os.path.isdir(MODEL_PATH):
        raise FileNotFoundError(f"Could not find the model folder at {MODEL_PATH}")

    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    logger.info(f"Loading custom DistilBERT model on {device} from {MODEL_PATH}")

    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
    
    model.to(device)
    model.eval()

    return model, tokenizer

def preprocess(body_text: str, urls: list[str], tokenizer) -> dict:
    url_string = ' '.join(urls)[:MAX_URL_CHARS]
    combined = f"{body_text.strip()} {url_string}".strip()

    return tokenizer(
        combined,
        return_tensors='pt',
        truncation=True,
        max_length=MAX_INPUT_LENGTH,
        padding=True,
    )

def predict(body_text: str, urls: list[str], model, tokenizer) -> dict:
    if model is None or tokenizer is None:
        raise RuntimeError("Model or tokenizer not loaded.")

    device = next(model.parameters()).device
    inputs = preprocess(body_text, urls, tokenizer)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probs = F.softmax(logits, dim=-1)

    predicted_class_id = int(torch.argmax(probs, dim=-1).item())
    score = float(probs[0][predicted_class_id].item())
    label = ID2LABEL.get(predicted_class_id, 'legitimate')

    return {
        'score': score,
        'label': label,
        'raw_logits': logits[0].tolist(),
    }