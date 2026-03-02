"""Browser navigation and 3-strategy item loading for LiveMCP."""

# All known browser root categories
BROWSER_ROOTS = {
    "instruments": "instruments",
    "sounds": "sounds",
    "drums": "drums",
    "audio_effects": "audio_effects",
    "audio effects": "audio_effects",
    "midi_effects": "midi_effects",
    "midi effects": "midi_effects",
    "clips": "clips",
    "samples": "samples",
    "packs": "packs",
    "plugins": "plugins",
    "user_library": "user_library",
    "userlibrary": "user_library",
    "user library": "user_library",
    "user_folders": "user_folders",
    "max_for_live": "max_for_live",
    "max for live": "max_for_live",
    "m4l": "max_for_live",
}

# File extensions we handle
EXTENSIONS = (".amxd", ".adg", ".adv", ".als", ".alc")


def get_browser_root(browser, root_name):
    """Resolve a root name to a browser object."""
    attr = BROWSER_ROOTS.get(root_name.lower())
    if attr and hasattr(browser, attr):
        return getattr(browser, attr)
    # Try direct attribute lookup
    if hasattr(browser, root_name):
        return getattr(browser, root_name)
    return None


def load_browser_item(control_surface, browser, track, item_uri):
    """Load a browser item onto a track using 3-strategy fallback.

    Strategy 1: Direct URI match across all categories
    Strategy 2: Path-based navigation (parses URI into folder path)
    Strategy 3: Recursive name search in user_library
    """
    log = control_surface.log_message

    # Strategy 1: URI match
    item = find_item_by_uri(browser, item_uri, log)

    # Strategy 2: Path navigation
    if not item:
        log("LiveMCP: URI search failed, trying path navigation for: {0}".format(item_uri))
        item = navigate_to_item(browser, item_uri, log)

    # Strategy 3: Name search in user library
    if not item:
        log("LiveMCP: Path nav failed, trying name search")
        target = extract_name_from_uri(item_uri)
        if target and hasattr(browser, "user_library"):
            item = search_by_name(browser.user_library, target, log)

    if not item:
        raise ValueError("Browser item not found: {0}".format(item_uri))

    control_surface.song().view.selected_track = track
    browser.load_item(item)
    return {"loaded": True, "item_name": item.name, "track_name": track.name, "uri": item_uri}


def _uri_variants(uri):
    """Generate URI variants with both space-encoded and space-decoded forms."""
    variants = [uri]
    if " " in uri:
        variants.append(uri.replace(" ", "%20"))
    if "%20" in uri:
        decoded = uri.replace("%20", " ")
        if decoded not in variants:
            variants.append(decoded)
    return variants


def find_item_by_uri(browser, uri, log, max_depth=15):
    """Strategy 1: Recursive search matching exact URI across all categories."""
    categories = [
        "instruments", "sounds", "drums", "audio_effects", "midi_effects",
        "user_library", "user_folders", "max_for_live",
    ]
    for variant in _uri_variants(uri):
        for cat_name in categories:
            if not hasattr(browser, cat_name):
                continue
            root = getattr(browser, cat_name)
            result = _search_uri_recursive(root, variant, max_depth, 0)
            if result:
                log("LiveMCP: Found by URI in {0}: {1}".format(cat_name, result.name))
                return result
    return None


def _search_uri_recursive(item, uri, max_depth, depth):
    """DFS search for an item matching the given URI."""
    if depth >= max_depth:
        return None
    try:
        if hasattr(item, "uri") and item.uri == uri:
            return item
        if hasattr(item, "children"):
            for child in item.children:
                result = _search_uri_recursive(child, uri, max_depth, depth + 1)
                if result:
                    return result
    except Exception:
        pass
    return None


def navigate_to_item(browser, uri, log):
    """Strategy 2: Parse URI into path segments and walk the browser tree."""
    try:
        path_parts = _parse_uri_to_path(uri)
        if not path_parts:
            return None

        # Determine root
        root_name = path_parts[0].lower().replace(" ", "_").replace("%20", "_")
        root = get_browser_root(browser, root_name)
        if not root:
            log("LiveMCP: No browser root for: {0}".format(root_name))
            return None

        # Walk the path
        current = root
        for i, part in enumerate(path_parts[1:], 1):
            part_clean = part.replace("%20", " ")
            part_no_ext = _strip_extension(part_clean)
            found = False

            if hasattr(current, "children"):
                for child in current.children:
                    name = child.name if hasattr(child, "name") else ""
                    if name == part_clean or name == part_no_ext:
                        current = child
                        found = True
                        break

            if not found:
                log("LiveMCP: Path segment not found: {0}".format(part_clean))
                return None

        if hasattr(current, "is_loadable") and current.is_loadable:
            log("LiveMCP: Found by path navigation: {0}".format(current.name))
            return current
        return None
    except Exception as e:
        log("LiveMCP: Path navigation error: {0}".format(e))
        return None


def search_by_name(root_item, target_name, log, max_depth=10):
    """Strategy 3: Recursive DFS search by item name."""
    target_no_ext = _strip_extension(target_name)
    return _search_name_recursive(root_item, target_name, target_no_ext, log, max_depth, 0)


def _search_name_recursive(item, target_name, target_no_ext, log, max_depth, depth):
    """DFS through browser children matching by name."""
    if depth >= max_depth:
        return None
    try:
        if hasattr(item, "name"):
            name = item.name
            if (name == target_name or name == target_no_ext):
                if hasattr(item, "is_loadable") and item.is_loadable:
                    log("LiveMCP: Found by name search: {0}".format(name))
                    return item
        if hasattr(item, "children"):
            for child in item.children:
                result = _search_name_recursive(
                    child, target_name, target_no_ext, log, max_depth, depth + 1
                )
                if result:
                    return result
    except Exception:
        pass
    return None


def get_browser_tree(browser, category_type="all", max_depth=3):
    """Get hierarchical browser tree with actual recursive children."""
    categories = []

    if category_type == "all":
        cat_names = [
            "sounds", "drums", "instruments", "audio_effects",
            "midi_effects", "max_for_live", "plugins", "clips",
            "samples", "packs", "user_library",
        ]
    elif category_type == "instruments":
        cat_names = ["instruments", "plugins"]
    elif category_type == "sounds":
        cat_names = ["sounds"]
    elif category_type == "drums":
        cat_names = ["drums"]
    elif category_type == "audio_effects":
        cat_names = ["audio_effects"]
    elif category_type == "midi_effects":
        cat_names = ["midi_effects"]
    else:
        cat_names = [category_type]

    for name in cat_names:
        if hasattr(browser, name):
            root = getattr(browser, name)
            categories.append(_build_tree_item(root, max_depth, 0))

    return {"categories": categories}


def _build_tree_item(item, max_depth, depth):
    """Build a tree node with recursive children up to max_depth."""
    node = {
        "name": item.name if hasattr(item, "name") else "",
        "uri": item.uri if hasattr(item, "uri") else "",
        "is_folder": item.is_folder if hasattr(item, "is_folder") else False,
        "is_loadable": item.is_loadable if hasattr(item, "is_loadable") else False,
    }
    children = []
    if depth < max_depth and hasattr(item, "children"):
        try:
            for child in item.children:
                children.append(_build_tree_item(child, max_depth, depth + 1))
        except Exception:
            pass
    node["children"] = children
    return node


def get_items_at_path(browser, path, log):
    """Navigate browser by slash-separated path and return children."""
    parts = [p.strip() for p in path.split("/") if p.strip()]
    if not parts:
        return {"error": "Empty path"}

    root_name = parts[0].lower()
    root = get_browser_root(browser, root_name)
    if not root:
        return {"error": "Unknown browser root: {0}".format(parts[0])}

    current = root
    for part in parts[1:]:
        part_lower = part.lower()
        found = False
        if hasattr(current, "children"):
            for child in current.children:
                if hasattr(child, "name") and child.name.lower() == part_lower:
                    current = child
                    found = True
                    break
        if not found:
            return {"error": "Path segment not found: {0}".format(part)}

    items = []
    if hasattr(current, "children"):
        for child in current.children:
            items.append({
                "name": child.name if hasattr(child, "name") else "",
                "uri": child.uri if hasattr(child, "uri") else "",
                "is_folder": child.is_folder if hasattr(child, "is_folder") else False,
                "is_loadable": child.is_loadable if hasattr(child, "is_loadable") else False,
            })

    return {"path": path, "items": items, "count": len(items)}


def extract_name_from_uri(uri):
    """Extract a filename/item name from a URI string, URL-decoded."""
    # Handle URIs like 'query:UserLibrary#Presets:Audio%20Effects:...:Name.amxd'
    name = uri.split(":")[-1].split("/")[-1].replace("%20", " ")
    return name if name else None


def _parse_uri_to_path(uri):
    """Parse a URI into navigable path segments."""
    # Handle 'query:Category#Path:Segments:Here'
    if "#" in uri:
        after_hash = uri.split("#", 1)[1]
        parts = after_hash.replace("%20", " ").split(":")
        # Map first segment to a browser root attribute name
        root_map = {
            "UserLibrary": "user_library",
            "M4L": "max_for_live",
        }
        mapped = root_map.get(parts[0])
        if mapped:
            parts[0] = mapped
        elif parts[0] == "Presets" and len(parts) > 1:
            # 'Presets:Audio Effects:...' -> 'audio_effects:...'
            effect_type = parts[1].lower().replace(" ", "_")
            if effect_type in BROWSER_ROOTS:
                parts = [BROWSER_ROOTS[effect_type]] + parts[2:]
            else:
                parts = parts[1:]
        return parts
    # Handle simple 'category/path/item' format
    if "/" in uri:
        return uri.replace("%20", " ").split("/")
    return None


def _strip_extension(name):
    """Remove known file extensions from a name."""
    for ext in EXTENSIONS:
        if name.lower().endswith(ext):
            return name[:-len(ext)]
    return name
