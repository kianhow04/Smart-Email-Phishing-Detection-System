from django import forms
import os

class EmlUploadForm(forms.Form):
    eml_file = forms.FileField(
        label='Upload Suspicious Email (.eml)',
        help_text='Only .eml files are supported.'
    )

    def clean_eml_file(self):
        file = self.cleaned_data.get('eml_file')
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext != '.eml':
                raise forms.ValidationError("Unsupported file extension. Please upload an .eml file.")
        return file