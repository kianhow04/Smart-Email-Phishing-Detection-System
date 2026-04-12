# xai_engine/explainer.py
import logging
import numpy as np
import torch
import torch.nn.functional as F
from lime.lime_text import LimeTextExplainer

logger = logging.getLogger(__name__)

NUM_LIME_SAMPLES = 50          # Number of perturbed samples (Kept low for fast CPU processing)
NUM_FEATURES = 15              # Top N tokens to return importances for
PHISHING_CLASS_INDEX = 1       # Index of 'phishing' class in model output

def _make_predictor_fn(model, tokenizer, device):
    """
    Returns a function that LIME can call: takes list of strings,
    returns numpy array of shape [n, num_classes] with class probabilities.
    """
    def predictor(texts: list[str]) -> np.ndarray:
        all_probs = []
        for text in texts:
            inputs = tokenizer(
                text,
                return_tensors='pt',
                truncation=True,
                max_length=512,
                padding=True,
            )
            inputs = {k: v.to(device) for k, v in inputs.items()}
            with torch.no_grad():
                outputs = model(**inputs)
            probs = F.softmax(outputs.logits, dim=-1)[0].cpu().numpy()
            all_probs.append(probs)
        return np.array(all_probs)
    return predictor

def _importance_to_color(score: float, max_score: float) -> str:
    """Map a LIME importance score to a UI highlight color."""
    if max_score == 0 or score <= 0:
        return 'transparent'
    intensity = min(score / max_score, 1.0)
    if intensity > 0.6:
        return '#E53935'   # strong red
    elif intensity > 0.3:
        return '#E57C27'   # orange
    else:
        return '#F9A825'   # amber / light

def _generate_explanation(token: str, score: float, max_score: float) -> str:
    """Generate a human-readable explanation for a suspicious token based on heuristics."""
    token_lower = token.lower()
    intensity = score / max_score if max_score > 0 else 0

    phishing_patterns = {
        ('click', 'here', 'link', 'verify', 'login', 'signin'): 'Common phishing tactic to redirect users to malicious sites.',
        ('urgent', 'immediately', 'now', 'asap', 'quickly'): 'Creates urgency to pressure the recipient into acting without thinking.',
        ('suspended', 'locked', 'disabled', 'blocked', 'terminated'): 'Threatens negative consequences to pressure a quick response.',
        ('account', 'password', 'credential', 'ssn', 'social'): 'Requests sensitive personal or account information.',
        ('winner', 'prize', 'reward', 'congratulations', 'won'): 'Uses false incentives typical of social engineering.',
        ('bank', 'paypal', 'amazon', 'microsoft', 'apple', 'google'): 'Brand impersonation — commonly exploited in phishing attacks.',
        ('confirm', 'update', 'validate', 'reactivate'): 'Prompts user to take an action that may expose credentials.',
        ('activity', 'suspicious', 'unusual', 'unauthorized'): 'Creates urgency and fear to prompt immediate action.',
    }

    for keywords, explanation in phishing_patterns.items():
        if token_lower in keywords:
            return explanation

    if intensity > 0.7:
        return 'Strongly associated with phishing email patterns in training data.'
    elif intensity > 0.4:
        return 'Moderately associated with phishing indicators.'
    else:
        return 'Weakly associated with phishing language patterns.'

def explain(text: str, model, tokenizer) -> list[dict]:
    """
    Run LIME text explanation on email body text.
    Returns a list of dictionaries containing tokens and their highlighting colors.
    """
    if model is None or tokenizer is None:
        logger.warning("Model not loaded — returning empty explanation.")
        return []

    if not text or len(text.strip()) < 10:
        return []

    device = next(model.parameters()).device
    predictor_fn = _make_predictor_fn(model, tokenizer, device)

    explainer = LimeTextExplainer(
        class_names=['legitimate', 'phishing'],
        split_expression=r'\W+',    # word-level splits
        bow=False,
    )

    try:
        explanation = explainer.explain_instance(
            text,
            predictor_fn,
            num_features=NUM_FEATURES,
            num_samples=NUM_LIME_SAMPLES,
            labels=(PHISHING_CLASS_INDEX,),
        )
    except Exception as e:
        logger.error(f"LIME explanation failed: {e}")
        return []

    raw_weights = explanation.as_list(label=PHISHING_CLASS_INDEX)
    positive_weights = [(tok, score) for tok, score in raw_weights if score > 0]
    
    if not positive_weights:
        return []

    max_score = max(score for _, score in positive_weights)

    result = []
    for token, score in positive_weights:
        result.append({
            'token': token,
            'importance_score': round(float(score), 4),
            'highlight_color': _importance_to_color(score, max_score),
            'explanation': _generate_explanation(token, score, max_score),
        })

    # Sort by importance descending so the worst words are at the top
    result.sort(key=lambda x: x['importance_score'], reverse=True)
    return result