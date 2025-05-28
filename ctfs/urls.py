from django.urls import path
from . import views



urlpatterns = [
    # Main CTF list page - shows all categories
    path('', views.ctf_list, name='ctfs_url'),
    path('leaderboard/', views.leaderboard, name='leaderboard'),
    
    # Shows all CTFs of a specific type (e.g., /ctfs/stg/)
    path('<str:type>/', views.ctf_type, name='ctf_type'),
    
    # CTF detail using title (current implementation)
    path('<str:type>/<str:title>/', views.ctf_detail, name='ctf_detail'),
   
    # Leaderboard
    
    # Create CTF (admin only)
    path('create/', views.create_ctf, name='create_ctf'),
]