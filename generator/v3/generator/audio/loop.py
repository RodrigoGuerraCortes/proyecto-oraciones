from moviepy.editor import concatenate_audioclips

def audio_loop(audio, duration):
    clips = []
    t = 0.0

    while t < duration:
        sub = audio.subclip(0, min(audio.duration, duration - t))
        clips.append(sub)
        t += sub.duration

    return concatenate_audioclips(clips)
