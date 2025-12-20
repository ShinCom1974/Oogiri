from django import forms

class AnswerForm(forms.Form):
    """大喜利の回答を受け付けるフォーム"""
    answer_text = forms.CharField(
        label='あなたの回答',
        widget=forms.Textarea(attrs={'rows': 5, 'placeholder': '面白い回答を入力してください。'})
    )