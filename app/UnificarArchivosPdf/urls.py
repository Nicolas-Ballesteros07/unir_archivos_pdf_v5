from django.urls import path
from . import views

urlpatterns = [
    path('', views.merge_zip_view, name='merge_zip'),
    path('download-zip-final/', views.download_zip_final, name='download_zip_final'),
    path('merge-excel/', views.merge_excel_view, name='merge_excel'),
    path('generate-named-pdf/<int:record_index>/', views.generate_named_pdf, name='generate_named_pdf'),

    # Health check endpoint
    path('health/', views.health_check, name='health_check'),
]