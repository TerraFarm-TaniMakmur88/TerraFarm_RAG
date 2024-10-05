from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
import whisper
import tempfile
import os
import uuid
import json
from .rag import answer_question
import tempfile
from dotenv import load_dotenv
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs

load_dotenv()

# Set API Key for ElevenLabs
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
client = ElevenLabs(api_key=ELEVENLABS_API_KEY)

# Model Whisper
model = whisper.load_model('base')

def home(request):
    return HttpResponse("Welcome to Terrafarm RAG!")

@csrf_exempt
def transcribe_audio(request):
    if request.method == 'POST':
        if 'audio' in request.FILES:
            audio_file = request.FILES['audio']

            # Save temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
                for chunk in audio_file.chunks():
                    temp_audio_file.write(chunk)
                temp_audio_file_path = temp_audio_file.name
            
            try:
                # Transcribe
                result = model.transcribe(temp_audio_file_path)
                transcription = result['text']

                # Delete temp file
                os.remove(temp_audio_file_path)

                # Return transcribe JSON text
                return JsonResponse({'transcription': transcription})
            
            except Exception as e:
                # Delete temp file
                os.remove(temp_audio_file_path)
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No audio file provided'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=405)
    
@csrf_exempt
def text_to_speech_file(request):
    if request.method == 'POST':
        text = request.POST.get('text', '')
        if text:
            try: 
                # Generate audio 
                response = client.text_to_speech.convert(
                    voice_id="pNInz6obpgDQGcFmaJgB",  # ID suara (contoh: suara Adam)
                    output_format="mp3_44100_128",     # Format output audio
                    text=text,
                    model_id="eleven_monolingual_v1",  # Model yang digunakan
                    voice_settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.5,
                        use_speaker_boost=True,
                    ),
                )

                # Save audio to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
                    for chunk in response:
                        if chunk:
                            temp_audio_file.write(chunk)
                    temp_audio_file_path = temp_audio_file.name

                # Read audio file and send as response
                with open(temp_audio_file_path, 'rb') as f:
                    audio_data = f.read()
                
                # Delete temp file
                os.remove(temp_audio_file_path)

                response = HttpResponse(audio_data, content_type='audio/mpeg')
                response['Content-Disposition'] = 'attachment; filename="speech.mp3"'
                return response

            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        
        else:
            return JsonResponse({'error': 'No text provided.'}, status=400)
        
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
def rag_answer(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        question = data.get('question', '')
        if question:
            try:
                answer = answer_question(question)
                return JsonResponse({'answer': answer})
            except Exception as e:
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No question provided.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)

@csrf_exempt
def speech_to_speech(request):
    if request.method == 'POST':
        if 'audio' in request.FILES:
            audio_file = request.FILES['audio']

            # Save temp file for audio input
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_audio_file:
                for chunk in audio_file.chunks():
                    temp_audio_file.write(chunk)
                temp_audio_file_path = temp_audio_file.name
            
            try:
                # Step 1: Transcribe the audio to text
                result = model.transcribe(temp_audio_file_path)
                transcription = result['text']

                # Step 2: Use RAG model to get the answer
                answer = answer_question(transcription)

                # Step 3: Convert the RAG answer back to speech using ElevenLabs
                response = client.text_to_speech.convert(
                    voice_id="pNInz6obpgDQGcFmaJgB",  # ID suara (contoh: suara Adam)
                    output_format="mp3_44100_128",     # Format output audio
                    text=answer,
                    model_id="eleven_monolingual_v1",  # Model yang digunakan
                    voice_settings=VoiceSettings(
                        stability=0.5,
                        similarity_boost=0.75,
                        style=0.5,
                        use_speaker_boost=True,
                    ),
                )

                # Save output audio to a temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as temp_output_audio:
                    for chunk in response:
                        if chunk:
                            temp_output_audio.write(chunk)
                    temp_output_audio_path = temp_output_audio.name

                # Return the audio response
                with open(temp_output_audio_path, 'rb') as f:
                    audio_data = f.read()

                # Clean up temp files
                os.remove(temp_audio_file_path)
                os.remove(temp_output_audio_path)

                # Send back the generated speech as an audio file
                http_response = HttpResponse(audio_data, content_type='audio/mpeg')
                http_response['Content-Disposition'] = 'attachment; filename="response_speech.mp3"'
                return http_response

            except Exception as e:
                os.remove(temp_audio_file_path)
                return JsonResponse({'error': str(e)}, status=500)
        else:
            return JsonResponse({'error': 'No audio file provided.'}, status=400)
    else:
        return JsonResponse({'error': 'Invalid request method.'}, status=405)




