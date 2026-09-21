from django.urls import path

from core import views

app_name = 'core'

urlpatterns = [
    path('', views.home, name='home'),
    path('pro-nas/', views.about, name='about'),
    path('spivpratsya/', views.collab, name='collab'),
    path('kontakty/', views.contacts, name='contacts'),
    path('dyakuyemo/', views.thanks, name='thanks'),
    path('otrymannya/', views.legal, {'slug': 'otrymannya'}, name='delivery'),
    path('oferta/', views.legal, {'slug': 'oferta'}, name='offer'),
    path('privacy/', views.legal, {'slug': 'privacy'}, name='privacy'),
]
