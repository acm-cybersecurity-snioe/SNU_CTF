# Update your forms.py

from django import forms
from .models import Comments


# class CommentForm(forms.ModelForm):
#     class Meta:
#         model = Comment
#         fields = ['content']


# class ReplyForm(forms.ModelForm):
#     class Meta:
#         model = Comment
#         fields = ['text']
#         widgets = {
#             'text': forms.Textarea(attrs={
#                 'rows': 2, 
#                 'placeholder': 'Write a reply...',
#                 'class': 'form-control reply-textarea'
#             })
#         }

class Comments_form(forms.ModelForm):
    
    #inner class META
    class Meta:
        model = Comments
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'placeholder': 'Any Thoughts...?',
                'rows': 3,
                'class': 'form-control'
            })
        }
      
