from django.contrib import admin
from .models import CTFs

# Register your models here.
admin.site.register(CTFs)

from .models import Comment
admin.site.register(Comment)
