from pydub import AudioSegment

def get_audio_length(file_path):
    audio = AudioSegment.from_file(file_path)
    duration_seconds = audio.duration_seconds
    return duration_seconds