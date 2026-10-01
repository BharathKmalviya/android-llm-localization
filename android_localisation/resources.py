"""Shared Android XML checks and file operations (standard library only)."""

import collections
import os
import re
import stat
import tempfile
import xml.etree.ElementTree as ET


_LOCALE = re.compile(
    r"values-(?:[a-z]{2,3}(?:-r(?:[A-Z]{2}|\d{3}))?|"
    r"b\+[a-z]{2,3}(?:\+[A-Za-z0-9]{2,8})*)(?:-[A-Za-z0-9]+)*\Z"
)
_FORMAT = re.compile(r"%(?:(\d+)\$)?([-#+ 0,(<]*)(\d+)?(?:\.(\d+))?([tT][a-zA-Z]|[a-zA-Z%])")
_TRANSLATABLE = {"string", "string-array", "plurals"}


def is_locale_folder(folder):
    # `car` is a UI-mode qualifier, not an Android language directory.
    return bool(_LOCALE.fullmatch(folder)) and folder.split("-")[1] != "car"


def locale_folders(res_dir):
    if not os.path.isdir(res_dir):
        return []
    return sorted(name for name in os.listdir(res_dir)
                  if is_locale_folder(name) and os.path.isdir(os.path.join(res_dir, name)))


def parse_resources(xml):
    if re.search(r"<!\s*(?:DOCTYPE|ENTITY)\b", xml, re.IGNORECASE):
        raise ValueError("DTD/entity declarations are not supported")
    try:
        root = ET.fromstring(xml, parser=ET.XMLParser(target=ET.TreeBuilder(insert_comments=True)))
    except ET.ParseError as exc:
        raise ValueError("invalid XML: {}".format(exc)) from exc
    if root.tag != "resources":
        raise ValueError("XML root must be <resources>")
    if (root.text or "").strip() or any((node.tail or "").strip() for node in root):
        raise ValueError("unexpected text outside a resource")
    resource_map(root)  # detect missing names and duplicate resources immediately
    return root


def resource_map(root):
    result = {}
    for node in root:
        if not isinstance(node.tag, str):
            continue  # comments
        name = node.get("name")
        if not name:
            raise ValueError("<{}> resource is missing its name".format(node.tag))
        key = (node.tag, name)
        if key in result:
            raise ValueError("duplicate {} resource '{}'".format(*key))
        result[key] = node
    return result


def _signature(node):
    return (node.tag, node.attrib, _text(node),
            [(_signature(child), child.tail or "") for child in node
             if isinstance(child.tag, str)])


def _text(node):
    # XML comments are not part of the runtime string value.
    return (node.text or "") + "".join(
        (_text(child) if isinstance(child.tag, str) else "") + (child.tail or "")
        for child in node)


def _protected(node):
    return (node.get("translatable") == "false" or node.tag not in _TRANSLATABLE
            or (node.tag == "string" and (node.text or "").strip().startswith("@")))


def format_signature(text):
    """Resolve ordinary, explicit and relative Java argument indexing."""
    tokens = collections.Counter()
    ordinary, previous = 0, None
    for match in _FORMAT.finditer(text):
        explicit, flags, width, precision, conversion = match.groups()
        if conversion in ("%", "n"):
            tokens[(None, conversion, flags, width, precision)] += 1
            continue  # no argument consumed
        if len(conversion) == 1 and conversion not in "bBhHsScCdoxXeEfgGaA":
            raise ValueError("unknown format conversion %{}".format(conversion))
        if len(conversion) == 2 and conversion[1] not in "HIklMSLNpzZsQBbhAaCYyjmdeRTrDFc":
            raise ValueError("unknown date/time conversion %{}".format(conversion))
        if "<" in flags:
            if previous is None:
                raise ValueError("relative format argument has no preceding argument")
            index = previous
        elif explicit is not None:
            index = int(explicit)
            if index < 1:
                raise ValueError("format argument indices start at 1")
        else:
            ordinary += 1
            index = ordinary
        previous = index
        tokens[(index, conversion, flags.replace("<", ""), width, precision)] += 1
    return tokens


def _check_node(source, target, label, formatted=True):
    if source.tag != target.tag or source.attrib != target.attrib:
        raise ValueError("{}: resource tags or attributes changed".format(label))
    if source.get("translatable") == "false" or (source.tag in ("string", "item") and _text(source).strip().startswith("@")):
        if _signature(source) != _signature(target):
            raise ValueError("{}: protected content or resource reference changed".format(label))
        return
    source_children = [n for n in source if isinstance(n.tag, str)]
    target_children = [n for n in target if isinstance(n.tag, str)]
    if len(source_children) != len(target_children):
        raise ValueError("{}: inline markup or item count changed".format(label))
    formatted = formatted and source.get("formatted") != "false"
    if formatted and source.tag in ("string", "item"):
        source_text = _text(source)
        target_text = _text(target)
        source_formats = format_signature(source_text)
        if source_formats != format_signature(target_text):
            raise ValueError("{}: format arguments changed or were dropped".format(label))
        if any(token[0] is not None for token in source_formats) and "%" in _FORMAT.sub("", target_text):
            raise ValueError("{}: unrecognized percent in formatted text; use %% for a literal percent".format(label))
    if source.tag in ("string", "item"):
        for escape in (r"\n", r"\t", r"\r"):
            if _text(source).count(escape) != _text(target).count(escape):
                raise ValueError("{}: {} escape count changed".format(label, escape))
    for left, right in zip(source_children, target_children):
        _check_node(left, right, label, formatted)


def validate_resources(source_xml, target_xml, require_complete=True):
    source, target = parse_resources(source_xml), parse_resources(target_xml)
    if source.attrib != target.attrib:
        raise ValueError("<resources> attributes changed")
    original, translated = resource_map(source), resource_map(target)
    unexpected = translated.keys() - original.keys()
    if unexpected:
        raise ValueError("unexpected resources: {}".format(sorted(unexpected)))
    missing = [key for key, node in original.items()
               if key not in translated and not _protected(node)]
    if missing and require_complete:
        raise ValueError("missing resources: {}".format(missing))
    for key, node in translated.items():
        source_node = original[key]
        label = "{} '{}'".format(*key)
        if _protected(source_node):
            if _signature(source_node) != _signature(node):
                raise ValueError("{}: protected content changed".format(label))
        else:
            _check_node(source_node, node, label)
    return source, target


def missing_resources(source_xml, existing_xml):
    source = parse_resources(source_xml)
    existing = resource_map(parse_resources(existing_xml)) if existing_xml else {}
    if existing_xml:
        validate_resources(source_xml, existing_xml, require_complete=False)
    missing = [key for key, node in resource_map(source).items()
               if key not in existing and not _protected(node)]
    return missing


def merge_missing(source_xml, existing_xml, translated_xml, missing):
    # Accept only missing resources, even if the provider returned others.
    source = parse_resources(source_xml)
    translated = resource_map(parse_resources(translated_xml))
    selected = ET.Element("resources", source.attrib)
    for key in missing:
        if key not in translated:
            raise ValueError("missing translated resource: {}".format(key))
        selected.append(translated[key])
    validate_resources(source_xml, ET.tostring(selected, encoding="unicode"), require_complete=False)
    additions = "\n".join("    " + ET.tostring(node, encoding="unicode").strip()
                          for node in selected)
    # Preserve existing text, comments, namespace prefixes and whitespace exactly.
    base = existing_xml or source_xml
    if not existing_xml:
        validate_resources(source_xml, translated_xml)
        return translated_xml
    closing = re.search(r"</resources\s*>", base)
    if closing:
        merged = base[:closing.start()] + additions + "\n" + base[closing.start():]
    else:
        # Valid empty <resources/> files have no closing tag.
        empty = re.search(r"(<resources\b[^>]*?)/>", base)
        if empty is None:
            raise ValueError("cannot locate the resources closing tag for merging")
        merged = base[:empty.start()] + empty.group(1) + ">\n" + additions + "\n</resources>" + base[empty.end():]
    validate_resources(source_xml, merged)
    return merged


def atomic_write(path, content):
    directory = os.path.dirname(os.path.abspath(path))
    os.makedirs(directory, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".strings-", suffix=".tmp", dir=directory)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        if os.path.exists(path):
            os.chmod(temporary, stat.S_IMODE(os.stat(path).st_mode))
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.chmod(temporary, stat.S_IREAD | stat.S_IWRITE)
            os.unlink(temporary)
