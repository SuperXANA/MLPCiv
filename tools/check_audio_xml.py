#!/usr/bin/env python3
"""Static checks for MLPCiv audio XML; run with Python 3, outside Civ4.

This checks repository structure and identifiers, not XDR validation in MSXML,
installed media, the executable's loading rules, or audible playback.
"""

import argparse
from collections import defaultdict
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


SCRIPT_NS = "x-schema:AudioScriptSchema.xml"
DEFINE_NS = "x-schema:AudioDefinesSchema.xml"
COMMON_FIELDS = "ScriptID SoundID SoundType iMinVolume iMaxVolume iPitchChangeDown iPitchChangeUp"
TAIL_FIELDS = "bTaperForSoundtracks iLengthOfSound fMinDryLevel fMaxDryLevel fMinWetLevel fMaxWetLevel iNotPlayPercent"
FIELDS_2D = (COMMON_FIELDS + " iMinLeftPan iMaxLeftPan iMinRightPan iMaxRightPan bLooping iMinTimeDelay iMaxTimeDelay " + TAIL_FIELDS).split()
FIELDS_3D = (COMMON_FIELDS + " bLooping iMinTimeDelay iMaxTimeDelay StartPosition EndPosition iMinVelocity iMaxVelocity iMinDistanceFromListener iMaxDistanceFromListener iMinDistanceForMaxVolume iMaxDistanceForMaxVolume iMinCutoffDistance iMaxCutoffDistance " + TAIL_FIELDS).split()
SOUND_FIELDS = "SoundID Filename LoadType bIsCompressed bInGeneric".split()
DEFINE_SECTIONS = "SoundDatas ContextTypes SoundTypes PositionTypes ScriptTypes LoadTypes EffectTypes GameEnvironmentTypes Effects SpeakerConfigs AudioSystemInit".split()
QUARRY_ID = "SND_TUTORIAL_BUILD_QUARRY_0"
QUARRY_RECORDS = [
    (QUARRY_ID, "Sounds/Tutorial/Tut_49A", "DYNAMIC_RES", "1", "1"),
    (QUARRY_ID, "Sounds/Tutorial/Tut_50A", "DYNAMIC_RES", "1", "1"),
]


def qname(namespace, name):
    return "{%s}%s" % (namespace, name)


def local_name(element):
    return element.tag.rsplit("}", 1)[-1] if isinstance(element.tag, str) else "comment"


def value(record, namespace, name):
    return record.findtext(qname(namespace, name), default="").strip()


def load_xml(path, namespace, root_name, errors):
    try:
        parser = ET.XMLParser(target=ET.TreeBuilder(insert_comments=True))
        root = ET.parse(path, parser=parser).getroot()
    except (OSError, ET.ParseError) as exc:
        errors.append("%s: XML parse/read error: %s" % (path.name, exc))
        return None
    if root.tag != qname(namespace, root_name):
        errors.append("%s: expected root {%s}%s, got %s" % (path.name, namespace, root_name, root.tag))
        return None
    return root


def check_fields(record, namespace, fields, where, errors):
    if record.attrib or [child.tag for child in record] != [qname(namespace, name) for name in fields]:
        errors.append("%s: wrong record fields/order (expected %s)" % (where, ", ".join(fields)))
    if record.text and record.text.strip():
        errors.append("%s: unexpected record text" % where)
    for child in record:
        name = local_name(child)
        if list(child) or child.attrib or not (child.text or "").strip():
            errors.append("%s: %s must contain a nonempty scalar value" % (where, name))
            continue
        if child.tail and child.tail.strip():
            errors.append("%s: unexpected text after %s" % (where, name))
        text = child.text.strip()
        if name in ("ScriptID", "SoundID") and child.text != text:
            errors.append("%s: whitespace in %s" % (where, name))
        if name.startswith("b") and text not in ("0", "1", "true", "false"):
            errors.append("%s: invalid boolean %s" % (where, name))
        if name.startswith("i"):
            try:
                int(text)
            except ValueError:
                errors.append("%s: invalid integer %s" % (where, name))


def audit(repo_root):
    """Return (errors, narrowly acknowledgeable issues, counts). Never edit XML."""
    audio_dir = Path(repo_root) / "Assets/XML/Audio"
    errors, known = [], []
    defines = load_xml(audio_dir / "AudioDefines.xml", DEFINE_NS, "AudioDefines", errors)
    sounds = defaultdict(list)
    load_types, sound_types = set(), set()
    if defines is not None:
        if defines.attrib or [local_name(e) for e in defines] != DEFINE_SECTIONS or any(e.tag != qname(DEFINE_NS, local_name(e)) for e in defines):
            errors.append("AudioDefines.xml: wrong top-level sections/order/namespace")
        load_types = {e.text for e in defines.findall("{%s}LoadTypes/{%s}LoadType" % (DEFINE_NS, DEFINE_NS))}
        sound_types = {e.text for e in defines.findall("{%s}SoundTypes/{%s}SoundType" % (DEFINE_NS, DEFINE_NS))}
        containers = defines.findall(qname(DEFINE_NS, "SoundDatas"))
        if len(containers) != 1:
            errors.append("AudioDefines.xml: expected one SoundDatas container")
        for container in containers:
            if container.attrib or (container.text and container.text.strip()):
                errors.append("AudioDefines.xml: unexpected SoundDatas attributes/text")
            for record in container:
                if record.tag != qname(DEFINE_NS, "SoundData"):
                    errors.append("AudioDefines.xml: SoundDatas may contain only SoundData (no comments)")
                    continue
                sound_id = value(record, DEFINE_NS, "SoundID")
                check_fields(record, DEFINE_NS, SOUND_FIELDS, "AudioDefines.xml " + sound_id, errors)
                sounds[sound_id].append(record)
                if value(record, DEFINE_NS, "LoadType") not in load_types:
                    errors.append("AudioDefines.xml %s: unknown LoadType" % sound_id)
        for sound_id, records in sorted(sounds.items()):
            if len(records) < 2:
                continue
            issue = "AudioDefines.xml: duplicate SoundID %s (%d records)" % (sound_id, len(records))
            actual = [tuple(value(r, DEFINE_NS, name) for name in SOUND_FIELDS) for r in records]
            if sound_id == QUARRY_ID and actual == QUARRY_RECORDS:
                known.append(issue + "; conflicting Tut_49A/Tut_50A inherited from AdvCiv 1.14")
            else:
                errors.append(issue)

    counts = {"SoundData": sum(map(len, sounds.values()))}
    for dimension, fields in (("2D", FIELDS_2D), ("3D", FIELDS_3D)):
        filename = "Audio%sScripts.xml" % dimension
        root = load_xml(audio_dir / filename, SCRIPT_NS, "Script%sSounds" % dimension, errors)
        scripts = defaultdict(list)
        if root is None:
            continue
        if root.attrib or (root.text and root.text.strip()):
            errors.append("%s: unexpected root attributes/text" % filename)
        for record in root:
            # Header comments are harmless here; SoundDatas is stricter above.
            if record.tag is ET.Comment:
                continue
            if record.tag != qname(SCRIPT_NS, "Script%sSound" % dimension):
                errors.append("%s: unexpected child %s" % (filename, local_name(record)))
                continue
            script_id = value(record, SCRIPT_NS, "ScriptID")
            check_fields(record, SCRIPT_NS, fields, filename + " " + script_id, errors)
            scripts[script_id].append(record)
            target = value(record, SCRIPT_NS, "SoundID")
            if target not in sounds:
                errors.append("%s %s: missing SoundID target %s" % (filename, script_id, target))
            if value(record, SCRIPT_NS, "SoundType") not in sound_types:
                errors.append("%s %s: unknown SoundType" % (filename, script_id))
        for script_id, records in sorted(scripts.items()):
            if len(records) > 1:
                errors.append("%s: duplicate ScriptID %s (%d records)" % (filename, script_id, len(records)))
        counts[dimension] = sum(map(len, scripts.values()))
    return errors, known, counts


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--allow-known-quarry-conflict", action="store_true", help="acknowledge only the exact two inherited quarry records; still print the conflict")
    args = parser.parse_args()
    errors, known, counts = audit(args.root)
    for issue in errors:
        print("ERROR: " + issue)
    for issue in known:
        print(("KNOWN (unresolved): " if args.allow_known_quarry_conflict else "ERROR: ") + issue)
    print("Records: " + ", ".join("%s=%s" % item for item in sorted(counts.items())))
    if errors or (known and not args.allow_known_quarry_conflict):
        print("FAIL: static audio audit; see diagnostics above.")
        return 1
    print("PASS: static checks%s; game loading/playback unverified." % (" except the acknowledged quarry conflict" if known else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
