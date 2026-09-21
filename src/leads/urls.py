from django.urls import path

from leads import views

app_name = 'leads'

urlpatterns = [
    path('zayavka/zamovlennya/', views.order_submit, name='order'),
    path('zayavka/spivpratsya/', views.partnership_submit, name='partnership'),
    path('zayavka/kontakty/', views.contact_submit, name='contact'),
]
