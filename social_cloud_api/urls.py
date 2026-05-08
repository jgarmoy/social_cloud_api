from django.urls import path
from . import views 
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('audiencia/', csrf_exempt(views.audiencia_gemini), name = 'audiencia_gemini'),
    path('perfiles/', csrf_exempt(views.perfiles_gemini), name = 'perfiles_gemini'),
    path('post/', csrf_exempt(views.post_gemini), name = 'post_gemini')
]