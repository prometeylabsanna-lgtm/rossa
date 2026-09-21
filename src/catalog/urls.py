from django.urls import path

from catalog import views

app_name = 'catalog'

urlpatterns = [
    path('katalog/', views.catalog_index, name='index'),
    path('katalog/<path:path>/', views.category_page, name='category'),
    path('tovar/<slug:slug>/', views.product_detail, name='product'),
    path('poshuk/', views.search, name='search'),
]
