# Audio identifier review — 2026-11-04

The branch repairs supported audio references and removes identical duplicate
records. It preserves every existing custom `DIPLO_` sound definition, including
all filenames, load settings, and compression flags. One conflicting inherited
tutorial SoundID remains unresolved and is reported by the strict checker.

## Pinned sources and scope

- MLPCiv `master`: [`02df02df15a8a90dc3cec0663e776182109a49eb`](https://github.com/SuperXANA/MLPCiv/commit/02df02df15a8a90dc3cec0663e776182109a49eb).
- AdvCiv `1.14`: [`5970334b64a875b5cdb370c94fc9a98db4eacda6`](https://github.com/SuperXANA/AdvCiv/commit/5970334b64a875b5cdb370c94fc9a98db4eacda6).
- Only `Audio2DScripts.xml` and `AudioDefines.xml` receive game-data changes.
  `Audio3DScripts.xml` and `CIV4LeaderHeadInfos.xml` are inspected, not edited.
  The Barbarian correction and unrelated character definitions are preserved.
- The repository has no audio schemas, mod INI, modular-loading configuration,
  or audio media. The installed mod's complete asset-loading configuration and
  media availability cannot be established from this repository.

## Corrections

| Finding | Change and evidence |
| --- | --- |
| AUDIO-01: nine duplicated 2D ScriptIDs | Keep the first occurrence and remove the identical second occurrence. Seven are Sitelae records; the other two are `AS2D_SONG_DIP_AS_EARLY_PEACE` and `AS2D_TUTORIAL_BUILD_QUARRY_0`. Every field of each removed record matches its retained counterpart. The two non-Sitelae duplicates also occur in the pinned AdvCiv baseline. |
| AUDIO-02: `AS2D_DIPLO_NR_WAR` uses its ScriptID as its SoundID | Point it at the existing `DIPLO_NR_WAR`, retaining `Sounds/Diplomacy/Opus 182 - Resurrection - Dark Baroque Church Organ Music`. `NR` is a separate identifier family from Nerath. No Nerath reference is changed. |
| AUDIO-03: Sitelae's early war intro selects the later intro | Point `AS2D_DIPLO_SITELAE_INTRO_WAR1` at the existing `DIPLO_SITELAE_INTRO_WAR1`. The leader selects WAR1 starting in the Ancient era and WAR2 starting in the Industrial era. Keep WAR2 unchanged. |
| AUDIO-04: Thingpony's unnumbered intro has no sound target | Replace the unnumbered script with `AS2D_DIPLO_THINGPONY_INTRO1`, and add `AS2D_DIPLO_THINGPONY_INTRO2` using the same intro playback settings. Both numbered SoundIDs already exist; the leader already requests these exact two numbered ScriptIDs for Ancient and Modern intros. No leader XML edit or new music selection is needed. |
| AUDIO-05: missing `SND_THEIRALLIANCE` | Restore the exact SoundData values from [AdvCiv 1.14 AudioDefines](https://github.com/SuperXANA/AdvCiv/blob/5970334b64a875b5cdb370c94fc9a98db4eacda6/Assets/XML/Audio/AudioDefines.xml). Existing `AS2D_THEIRALLIANCE` already requests it. |
| AUDIO-06: three 3D supernova scripts have no target | Restore `SND_AMB_SUPERNOVA_BLAST` from the same AdvCiv baseline, with filename `Sounds/Ambient/SupernovaBlast`. It is requested by `AS3D_SS_SUPERNOVA_BLAST`, `_2`, and `_3`. No 3D script edit is necessary. |
| AUDIO-07: two identical duplicate SoundIDs | Remove only the second `SND_COMBAT` and `SND_CBMN_DIE_VOX` records. Retain their existing filenames and settings. AdvCiv's header documents that it removed these duplicates too. |

The seven duplicated Sitelae ScriptIDs are `AS2D_DIPLO_SITELAE_INTRO1`,
`AS2D_DIPLO_SITELAE_INTRO2`, `AS2D_DIPLO_SITELAE_INTRO_WAR1`,
`AS2D_DIPLO_SITELAE_INTRO_WAR2`, `AS2D_DIPLO_SITELAE1`,
`AS2D_DIPLO_SITELAE2`, and `AS2D_DIPLO_SITELAE3`.

## Preserved theme selections

| Script or selection | Sound or filename |
| --- | --- |
| Sitelae early war intro | `DIPLO_SITELAE_INTRO_WAR1` → `Baten Kaitos Origins - The Light and Darkness of Balance` |
| Sitelae later war intro | `DIPLO_SITELAE_INTRO_WAR2` → `Fire Emblem The Blazing Blade - Remastered - Dragon's Gate II` |
| Nerath intro | `AS2D_DIPLO_NERATH_INTRO` → `DIPLO_ALTREALITY_9` → `Night Queen VIP` |
| Nerath later peace theme | `AS2D_DIPLO_NERATH` → `DIPLO_NERATH` → `Nerath, Goddess of Nightmares - Queen of the Mind CUT` |
| Nerath shared early peace theme | `DIPLO_INFINITE_ECLIPSE_EVIL` → `Fire Emblem Awakening - My Life Force Shall Return CUT` |
| Nerath shared war themes | `DIPLO_INFINITE_ECLIPSE_EVIL_WAR1` → `Bayonetta 2 - Aesir`; WAR2 → `Alternate Equestria - The Final Eclipse` |
| Thingpony Ancient intro | `DIPLO_THINGPONY_INTRO1` → `Mobile Suit Gundam 00 A Wakening of the Trailblazer - High Technology` |
| Thingpony Modern intro | `DIPLO_THINGPONY_INTRO2` → `Mobile Suit Gundam 00 A Wakening of the Trailblazer - Memory of Planet~Sympathy` |

All filenames above retain the existing `Sounds/Diplomacy/` prefix. The regression
checks protect all ten Sitelae music files and the listed Nerath mappings.

## Unresolved conflicting duplicate — AUDIO-08

`SND_TUTORIAL_BUILD_QUARRY_0` has two different SoundData records:

| Occurrence | Filename | LoadType | Compression / generic flags |
| --- | --- | --- | --- |
| First | `Sounds/Tutorial/Tut_49A` | `DYNAMIC_RES` | `1` / `1` |
| Second | `Sounds/Tutorial/Tut_50A` | `DYNAMIC_RES` | `1` / `1` |

Both occur in MLPCiv and the pinned AdvCiv baseline. The two identically duplicated
`AS2D_TUTORIAL_BUILD_QUARRY_0` scripts both request this same SoundID; neither
distinguishes the two filenames. Removing the duplicate script is safe, but
removing a conflicting SoundData record would choose a tutorial voice file
without evidence of intended selection or the executable's duplicate priority.
This branch retains both SoundData records. A verified tutorial mapping or an
explicit choice of voice file is needed to finish AUDIO-08.

The default checker fails on this conflict. Its optional acknowledgement accepts
only these exact two ordered records, still prints the unresolved conflict, and
rejects changed values, extra occurrences, and any other duplicates.

## Static regression checks

Use maintenance Python 3; these scripts are not imported by Civ4's Python 2.4:

```sh
python3 -m unittest discover -s tests -v
python3 tools/check_audio_xml.py
python3 tools/check_audio_xml.py --allow-known-quarry-conflict
```

- The regression suite passes, including injected duplicate ScriptIDs in both
  dimensions, duplicate SoundIDs, missing targets in both dimensions, malformed
  XML, wrong namespaces/nesting/field order, absent or empty fields, non-scalar
  values, invalid integer/boolean fields, and comments inside `SoundDatas`.
- The strict checker returns exit status **1**, reporting AUDIO-08.
- Explicitly acknowledging AUDIO-08 returns exit status **0**, with the conflict
  visibly reported. This is not an all-identifiers-unique result.
- After correction: **1,249 2D scripts**, **790 3D scripts**, **1,885 SoundData
  records** representing **1,884 unique SoundIDs**; **zero duplicate ScriptIDs**;
  **zero missing 2D/3D SoundID targets** against this AudioDefines file.
- A semantic comparison verifies that every pre-existing `DIPLO_` SoundData
  record is unchanged. The remote commit retains the original leader and 3D
  script blobs. Only the named references and identical duplicate records change.

The structure checks cover the expected document namespaces, root/container and
record layouts, required field order, scalar fields, and declared load/sound
types. Their field order was checked against the archived Firaxis
[BtS AudioScriptSchema](https://github.com/f1rpo/Civ4CE/blob/ba64c3545b479887739ad0ff78605b51b6fa57f9/BtS/Assets/XML/Audio/AudioScriptSchema.xml)
and inherited
[AudioDefinesSchema](https://github.com/f1rpo/Civ4CE/blob/ba64c3545b479887739ad0ff78605b51b6fa57f9/Civ4/Assets/XML/Audio/AudioDefinesSchema.xml).
This is focused structural validation, not a full MSXML/XDR schema validation.

## Installation and runtime limits

AdvCiv's pinned `AdvCiv.ini` specifies `ModularLoading = 0` and
`NoCustomAssets = 1`; MLPCiv supplies no INI establishing whether those values
match the installed mod. The baseline does not override `Audio3DScripts.xml`,
so its effective 3D data also depends on inherited installation assets.
Restoring the two missing baseline definitions makes the checked-in script
references self-contained; it does not establish that the media files exist.

The inspected leader XML also contains five other ScriptID references absent
from these 2D scripts: `AS2D_DIPLO_AMETHYSTSTAR`, `AS2D_DIPLO_CADANCE`,
`AS2D_DIPLO_ER_WAR`, `AS2D_DIPLO_PEGASUS`, and
`DIPLO_INFINITE_ECLIPSE_GOOD_WAR`. They are outside these supported repairs;
no substitute themes or unrelated character definitions are selected here.
The checker therefore promises SoundID closure for the 2D/3D files, not global
closure of all leader, Python, soundscape, or inherited installation references.

No game initialization or playback test was performed. Remaining verification
requires the actual installed mod, inherited XML/schemas, audio media and INI:
start a fresh game while checking XML/audio logs, exercise Sitelae's early/later
war intros, Thingpony's two intros, Nerath's existing themes, and the baseline
alliance sound. The supernova restoration is a source-level closure repair;
its runtime use in this mod is unverified. These source inconsistencies are not
evidence that a particular crash was reproduced or fixed.
