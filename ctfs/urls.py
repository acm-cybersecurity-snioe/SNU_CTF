from django.urls import path
from . import views

urlpatterns = [
    # Main CTF list page - shows all categories
    path('', views.ctf_list, name='ctfs_url'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Create CTF (admin only)
    path('create/', views.create_ctf, name='create_ctf'),
    
    # Shows all CTFs of a specific type (e.g., /ctfs/stg/)
    path('<str:type>/', views.ctf_type, name='ctf_type'),
    
    # CTF detail using slug (preferred)
    path('<str:type>/<slug:slug>/', views.ctf_detail_slug, name='ctf_detail_slug'),
    
]