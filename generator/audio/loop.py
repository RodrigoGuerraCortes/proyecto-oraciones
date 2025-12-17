from moviepy.editor import concatenate_videoclips


def audio_loop(audio, duration):
    clips = []
    t = 0

    while t < duration:
        sub = audio.subclip(0, min(audio.duration, duration - t))
        clips.append(sub)
        t += audio.duration

    return concatenate_videoclips(clips)
