from django.contrib import admin
from .models import CTFs
from .models import Comments

# Register your models here.
admin.site.register(CTFs)

admin.site.register(Comments)
