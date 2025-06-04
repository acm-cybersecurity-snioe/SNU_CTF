# Update your forms.py

from django import forms
from .models import Comment

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 3, 
                'placeholder': 'Add a comment...',
                'class': 'form-control comment-textarea'
            })
        }

class ReplyForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'rows': 2, 
                'placeholder': 'Write a reply...',
                'class': 'form-control reply-textarea'
            })
        }