"""Session-level handlers: tempo, transport, time signature."""


def get_session_info(control_surface, params):
    """Return global session state."""
    song = control_surface.song()
    master = song.master_track
    return {
        "tempo": song.tempo,
        "time_signature_numerator": song.signature_numerator,
        "time_signature_denominator": song.signature_denominator,
        "track_count": len(song.tracks),
        "return_track_count": len(song.return_tracks),
        "master_volume": master.mixer_device.volume.value,
        "master_pan": master.mixer_device.panning.value,
        "is_playing": song.is_playing,
        "loop": song.loop,
        "loop_start": song.loop_start,
        "loop_length": song.loop_length,
    }


def set_tempo(control_surface, params):
    """Set the session tempo in BPM."""
    tempo = params.get("tempo")
    if tempo is None:
        raise ValueError("Missing required parameter: tempo")
    tempo = float(tempo)
    if tempo < 20 or tempo > 999:
        raise ValueError("Tempo must be between 20 and 999 BPM")
    control_surface.song().tempo = tempo
    return {"tempo": tempo}


def start_playback(control_surface, params):
    """Start transport playback."""
    control_surface.song().start_playing()
    return {"is_playing": True}


def stop_playback(control_surface, params):
    """Stop transport playback."""
    control_surface.song().stop_playing()
    return {"is_playing": False}


READ_HANDLERS = {
    "get_session_info": get_session_info,
}

WRITE_HANDLERS = {
    "set_tempo": set_tempo,
    "start_playback": start_playback,
    "stop_playback": stop_playback,
}
