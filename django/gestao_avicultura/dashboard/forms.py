# dashboard/forms.py
from django import forms
from .models import ProducaoOvos

class ProducaoOvosForm(forms.ModelForm):
    class Meta:
        model = ProducaoOvos
        fields = ['lote', 'data_producao', 'total_ovos', 'ovos_quebrados']
        widgets = {
            'data_producao': forms.DateInput(attrs={'type': 'date'}),
        }