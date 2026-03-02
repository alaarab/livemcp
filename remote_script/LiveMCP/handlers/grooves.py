"""Groove pool handlers: list grooves, get/set properties, assign to clips."""


def get_groove_pool(control_surface, params):
    """Get all grooves in the groove pool."""
    song = control_surface.song()
    grooves = []
    for i, groove in enumerate(song.groove_pool.grooves):
        grooves.append({
            "index": i,
            "name": groove.name,
            "base": groove.base,  # 0=1/4, 1=1/8, 2=1/8T, 3=1/16, 4=1/16T, 5=1/32
            "quantization_amount": groove.quantization_amount,
            "timing_amount": groove.timing_amount,
            "random_amount": groove.random_amount,
            "velocity_amount": groove.velocity_amount,
        })
    return {"grooves": grooves}


def get_groove_properties(control_surface, params):
    """Get detailed properties of a specific groove."""
    song = control_surface.song()
    groove_index = params.get("groove_index")
    if groove_index is None:
        raise ValueError("Missing required parameter: groove_index")
    groove_index = int(groove_index)
    grooves = song.groove_pool.grooves
    if groove_index < 0 or groove_index >= len(grooves):
        raise ValueError("Groove index {0} out of range (0-{1})".format(
            groove_index, len(grooves) - 1))
    groove = grooves[groove_index]
    return {
        "index": groove_index,
        "name": groove.name,
        "base": groove.base,
        "quantization_amount": groove.quantization_amount,
        "timing_amount": groove.timing_amount,
        "random_amount": groove.random_amount,
        "velocity_amount": groove.velocity_amount,
    }


def set_groove_property(control_surface, params):
    """Set a property on a groove."""
    song = control_surface.song()
    groove_index = params.get("groove_index")
    prop = params.get("property")
    value = params.get("value")
    if groove_index is None:
        raise ValueError("Missing required parameter: groove_index")
    if prop is None:
        raise ValueError("Missing required parameter: property")
    if value is None:
        raise ValueError("Missing required parameter: value")
    groove_index = int(groove_index)
    grooves = song.groove_pool.grooves
    if groove_index < 0 or groove_index >= len(grooves):
        raise ValueError("Groove index out of range")
    groove = grooves[groove_index]
    valid_props = {"quantization_amount", "timing_amount", "random_amount", "velocity_amount", "base"}
    if prop not in valid_props:
        raise ValueError("Invalid property: {0}. Must be one of: {1}".format(prop, ", ".join(sorted(valid_props))))
    if prop == "base":
        setattr(groove, prop, int(value))
    else:
        setattr(groove, prop, float(value))
    return {"groove_index": groove_index, "property": prop, "value": getattr(groove, prop)}


def set_clip_groove(control_surface, params):
    """Assign a groove to a clip."""
    song = control_surface.song()
    track_index = int(params.get("track_index"))
    clip_index = int(params.get("clip_index"))
    groove_index = int(params.get("groove_index"))
    track = song.tracks[track_index]
    clip = track.clip_slots[clip_index].clip
    if clip is None:
        raise ValueError("No clip at track {0}, slot {1}".format(track_index, clip_index))
    grooves = song.groove_pool.grooves
    if groove_index < 0 or groove_index >= len(grooves):
        raise ValueError("Groove index out of range")
    clip.groove = grooves[groove_index]
    return {"track_index": track_index, "clip_index": clip_index, "groove_index": groove_index}


def remove_clip_groove(control_surface, params):
    """Remove groove assignment from a clip by setting groove amount to 0."""
    song = control_surface.song()
    track_index = int(params.get("track_index"))
    clip_index = int(params.get("clip_index"))
    track = song.tracks[track_index]
    clip = track.clip_slots[clip_index].clip
    if clip is None:
        raise ValueError("No clip at track {0}, slot {1}".format(track_index, clip_index))
    # The API doesn't support setting groove to None.
    # Instead, we remove the clip from groove influence by using the
    # available API. Note: this is a known limitation.
    try:
        # Try the has_groove check first
        if not clip.has_groove:
            return {"track_index": track_index, "clip_index": clip_index, "groove_removed": True}
    except AttributeError:
        pass
    # Best effort: set groove quantization to 0 to neutralize the groove effect
    raise ValueError("Cannot remove groove assignment via API. "
                     "Set groove quantization_amount, timing_amount, random_amount, "
                     "and velocity_amount to 0.0 on the groove itself instead.")


READ_HANDLERS = {
    "get_groove_pool": get_groove_pool,
    "get_groove_properties": get_groove_properties,
}

WRITE_HANDLERS = {
    "set_groove_property": set_groove_property,
    "set_clip_groove": set_clip_groove,
    "remove_clip_groove": remove_clip_groove,
}
