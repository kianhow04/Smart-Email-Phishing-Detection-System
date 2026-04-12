

# Create your views here.
# detector/views.py
from django.shortcuts import render
from django.contrib import messages
from .forms import EmlUploadForm
from .apps import DetectorConfig

# Import your three powerful engines!
from eml_parser.parser import parse_eml
from model_engine.predictor import predict
from xai_engine.explainer import explain

def scanner_view(request):
    if request.method == 'POST':
        form = EmlUploadForm(request.POST, request.FILES)
        
        if form.is_valid():
            uploaded_file = request.FILES['eml_file']
            
            # --- 1. PARSE THE EMAIL ---
            parsed_data = parse_eml(uploaded_file)
            
            if parsed_data.get('error'):
                messages.error(request, f"Error parsing email: {parsed_data['error']}")
                return render(request, 'detector/scan.html', {'form': form})

            text_to_analyze = parsed_data['body_text']
            urls_to_analyze = parsed_data['all_urls']
            
            # Grab the model loaded during Django startup (Step 8)
            model = DetectorConfig.model
            tokenizer = DetectorConfig.tokenizer

            # --- 2. RUN DISTILBERT PREDICTION ---
            try:
                prediction = predict(text_to_analyze, urls_to_analyze, model, tokenizer)
            except Exception as e:
                messages.error(request, "Machine Learning Engine failed to process this email.")
                return render(request, 'detector/scan.html', {'form': form})

            # --- 3. GENERATE LIME EXPLANATION ---
            # We only generate an explanation if the model thinks it is phishing
            explanations = []
            if prediction['label'] == 'phishing':
                explanations = explain(text_to_analyze, model, tokenizer)

            # --- 4. PREPARE THE RESULTS ---
            context = {
                'form': form,
                'parsed_data': parsed_data,
                'prediction': prediction,
                'explanations': explanations,
                'is_scanned': True
            }
            
            return render(request, 'detector/scan.html', context)

    else:
        # If the user just visited the page, show them an empty form
        form = EmlUploadForm()

    return render(request, 'detector/scan.html', {'form': form, 'is_scanned': False})