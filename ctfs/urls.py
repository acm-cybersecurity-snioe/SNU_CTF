from django.urls import path
from . import views


urlpatterns = [
    path('', views.ctf_list, name='ctfs_url'),  #for /ctfs
    path('<str:type>/', views.ctf_type, name='ctf_type'),   #for /ctfs/types
    path('<str:type>/<str:title>/', views.ctf_detail,name ='ctf_detail'),   #for /ctfs/types/title
    path('leaderboard/', views.leaderboard, name='leaderboard'),

]
