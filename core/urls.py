from django.urls import path
from .views import home, transcribe_audio, text_to_speech_file

urlpatterns = [
    path('', home, name='home'),  
    path('transcribe/', transcribe_audio, name='transcribe_audio'),
    path('text-to-speech/', text_to_speech_file, name='text_to_speech'),
]