"""Run: python3 -m unittest discover -s tests -v (maintenance Python 3)."""

import copy
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import check_audio_xml as audio


class AudioAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.files = {p.name: p.read_bytes() for p in (ROOT / "Assets/XML/Audio").glob("*.xml")}

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.directory = self.root / "Assets/XML/Audio"
        self.directory.mkdir(parents=True)
        for name, data in self.files.items():
            (self.directory / name).write_bytes(data)

    def mutate(self, filename, change):
        path = self.directory / filename
        root = ET.parse(path).getroot()
        change(root)
        ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)

    def assert_error(self, text):
        errors, known, counts = audio.audit(self.root)
        self.assertTrue(any(text in error for error in errors), (errors, known, counts))

    def test_current_repository_has_only_exact_inherited_quarry_conflict(self):
        errors, known, counts = audio.audit(ROOT)
        self.assertEqual(errors, [])
        self.assertEqual(len(known), 1)
        self.assertIn(audio.QUARRY_ID, known[0])
        self.assertEqual(counts, {"SoundData": 1885, "2D": 1249, "3D": 790})

    def test_duplicate_2d_script(self):
        self.mutate("Audio2DScripts.xml", lambda r: r.append(copy.deepcopy(r[0])))
        self.assert_error("duplicate ScriptID")

    def test_duplicate_3d_script(self):
        self.mutate("Audio3DScripts.xml", lambda r: r.append(copy.deepcopy(r[0])))
        self.assert_error("duplicate ScriptID")

    def test_duplicate_sound(self):
        self.mutate("AudioDefines.xml", lambda r: r[0].append(copy.deepcopy(r[0][0])))
        self.assert_error("duplicate SoundID DIPLO_EQUESTRIA")

    def test_changed_quarry_choice_cannot_use_known_exception(self):
        def change(root):
            for record in root[0]:
                if audio.value(record, audio.DEFINE_NS, "SoundID") == audio.QUARRY_ID:
                    record.find(audio.qname(audio.DEFINE_NS, "Filename")).text = "Sounds/Unreviewed"
                    break
        self.mutate("AudioDefines.xml", change)
        self.assert_error("duplicate SoundID " + audio.QUARRY_ID)
        self.assertEqual(audio.audit(self.root)[1], [])

    def test_third_quarry_record_cannot_use_known_exception(self):
        def change(root):
            record = next(r for r in root[0] if audio.value(r, audio.DEFINE_NS, "SoundID") == audio.QUARRY_ID)
            root[0].append(copy.deepcopy(record))
        self.mutate("AudioDefines.xml", change)
        self.assert_error("duplicate SoundID " + audio.QUARRY_ID)

    def test_missing_2d_target(self):
        self.mutate("Audio2DScripts.xml", lambda r: setattr(r[0][1], "text", "MISSING_2D_SOUND"))
        self.assert_error("missing SoundID target MISSING_2D_SOUND")

    def test_missing_3d_target(self):
        self.mutate("Audio3DScripts.xml", lambda r: setattr(r[0][1], "text", "MISSING_3D_SOUND"))
        self.assert_error("missing SoundID target MISSING_3D_SOUND")

    def test_malformed_xml(self):
        (self.directory / "AudioDefines.xml").write_text("<AudioDefines>")
        self.assert_error("XML parse/read error")

    def test_wrong_namespace(self):
        self.mutate("Audio2DScripts.xml", lambda r: setattr(r, "tag", "Script2DSounds"))
        self.assert_error("expected root")

    def test_wrong_record_container(self):
        self.mutate("Audio3DScripts.xml", lambda r: setattr(r[0], "tag", audio.qname(audio.SCRIPT_NS, "Script2DSound")))
        self.assert_error("unexpected child Script2DSound")

    def test_missing_required_field(self):
        self.mutate("Audio2DScripts.xml", lambda r: r[0].remove(r[0][1]))
        self.assert_error("wrong record fields/order")

    def test_reordered_fields(self):
        def change(root):
            record = root[0]
            field = record[0]
            record.remove(field)
            record.append(field)
        self.mutate("Audio3DScripts.xml", change)
        self.assert_error("wrong record fields/order")

    def test_empty_identifier(self):
        self.mutate("Audio2DScripts.xml", lambda r: setattr(r[0][0], "text", ""))
        self.assert_error("ScriptID must contain a nonempty scalar")

    def test_comment_inside_sounddatas(self):
        self.mutate("AudioDefines.xml", lambda r: r[0].append(ET.Comment("not supported in SoundDatas")))
        self.assert_error("SoundDatas may contain only SoundData")

    def test_wrong_define_sections(self):
        self.mutate("AudioDefines.xml", lambda r: r.remove(r[-1]))
        self.assert_error("wrong top-level sections/order/namespace")

    def test_non_scalar_field(self):
        self.mutate("AudioDefines.xml", lambda r: ET.SubElement(r[0][0][1], "unexpected"))
        self.assert_error("Filename must contain a nonempty scalar")

    def test_invalid_integer(self):
        self.mutate("Audio3DScripts.xml", lambda r: setattr(r[0][3], "text", "loud"))
        self.assert_error("invalid integer iMinVolume")

    def test_invalid_boolean(self):
        self.mutate("AudioDefines.xml", lambda r: setattr(r[0][0][3], "text", "yes"))
        self.assert_error("invalid boolean bIsCompressed")

    def test_cli_strictly_reports_unresolved_conflict(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/check_audio_xml.py"), "--root", str(self.root)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("ERROR: AudioDefines.xml: duplicate SoundID " + audio.QUARRY_ID, result.stdout)

    def test_cli_acknowledgement_is_explicit_and_visible(self):
        result = subprocess.run([sys.executable, str(ROOT / "tools/check_audio_xml.py"), "--root", str(self.root), "--allow-known-quarry-conflict"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout)
        self.assertIn("KNOWN (unresolved):", result.stdout)
        self.assertIn("except the acknowledged quarry conflict", result.stdout)

    def test_cli_acknowledgement_does_not_mask_another_failure(self):
        self.mutate("Audio3DScripts.xml", lambda r: setattr(r[0][1], "text", "MISSING_SOUND"))
        result = subprocess.run([sys.executable, str(ROOT / "tools/check_audio_xml.py"), "--root", str(self.root), "--allow-known-quarry-conflict"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1)
        self.assertIn("missing SoundID target MISSING_SOUND", result.stdout)


class MusicSelectionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        directory = ROOT / "Assets/XML/Audio"
        cls.scripts = {audio.value(e, audio.SCRIPT_NS, "ScriptID"): audio.value(e, audio.SCRIPT_NS, "SoundID") for e in ET.parse(directory / "Audio2DScripts.xml").getroot()}
        cls.sounds = {audio.value(e, audio.DEFINE_NS, "SoundID"): audio.value(e, audio.DEFINE_NS, "Filename") for e in ET.parse(directory / "AudioDefines.xml").getroot()[0]}

    def test_supported_reference_repairs(self):
        for suffix in ("NR_WAR", "SITELAE_INTRO_WAR1", "SITELAE_INTRO_WAR2", "THINGPONY_INTRO1", "THINGPONY_INTRO2"):
            with self.subTest(suffix=suffix):
                self.assertEqual(self.scripts["AS2D_DIPLO_" + suffix], "DIPLO_" + suffix)
                self.assertIn("DIPLO_" + suffix, self.sounds)

    def test_sitelae_music_files_preserved(self):
        themes = {
            "INTRO1": "Fire Emblem The Blazing Blade - Remastered - History Unveiled",
            "INTRO2": "Fire Emblem The Sacred Stones - Renastered - Ray of Hope",
            "INTRO_WAR1": "Baten Kaitos Origins - The Light and Darkness of Balance",
            "INTRO_WAR2": "Fire Emblem The Blazing Blade - Remastered - Dragon's Gate II",
            "1": "Touhou Cinematic_Orchestral - Emotional Skyscraper ~Cosmic Mind~ CUT",
            "2": "Baten Kaitos Origins - The Garden of Violent Clouds",
            "3": "Decision of the Enma - Touhou Unplugged_Classic Judgment in the 60th Year SLOW",
            "_WAR1": "Fire Emblem The Sacred Stones - Remastered - Treasured Memories",
            "_WAR2": "Fire Emblem Awakening - Champion ~Ablaze~",
            "_WAR3": "Alternate Equestria - The Primordial Sacrifical Oath SLOW CUT",
        }
        for suffix, filename in themes.items():
            suffix = suffix if suffix[0] in "123_" else "_" + suffix
            sound_id = "DIPLO_SITELAE" + suffix
            with self.subTest(sound_id=sound_id):
                self.assertEqual(self.scripts["AS2D_" + sound_id], sound_id)
                self.assertEqual(self.sounds[sound_id], "Sounds/Diplomacy/" + filename)

    def test_nerath_music_and_shared_themes_preserved(self):
        themes = {
            "AS2D_DIPLO_NERATH_INTRO": ("DIPLO_ALTREALITY_9", "Night Queen VIP"),
            "AS2D_DIPLO_NERATH": ("DIPLO_NERATH", "Nerath, Goddess of Nightmares - Queen of the Mind CUT"),
            "AS2D_DIPLO_INFINITE_ECLIPSE_EVIL": ("DIPLO_INFINITE_ECLIPSE_EVIL", "Fire Emblem Awakening - My Life Force Shall Return CUT"),
            "AS2D_DIPLO_INFINITE_ECLIPSE_EVIL_WAR1": ("DIPLO_INFINITE_ECLIPSE_EVIL_WAR1", "Bayonetta 2 - Aesir"),
            "AS2D_DIPLO_INFINITE_ECLIPSE_EVIL_WAR2": ("DIPLO_INFINITE_ECLIPSE_EVIL_WAR2", "Alternate Equestria - The Final Eclipse"),
        }
        for script_id, (sound_id, filename) in themes.items():
            with self.subTest(script_id=script_id):
                self.assertEqual(self.scripts[script_id], sound_id)
                self.assertEqual(self.sounds[sound_id], "Sounds/Diplomacy/" + filename)

    def test_numbered_thingpony_intro_files_preserved(self):
        self.assertEqual(self.sounds[self.scripts["AS2D_DIPLO_THINGPONY_INTRO1"]], "Sounds/Diplomacy/Mobile Suit Gundam 00 A Wakening of the Trailblazer - High Technology")
        self.assertEqual(self.sounds[self.scripts["AS2D_DIPLO_THINGPONY_INTRO2"]], "Sounds/Diplomacy/Mobile Suit Gundam 00 A Wakening of the Trailblazer - Memory of Planet~Sympathy")

    def test_baseline_sound_restorations(self):
        self.assertEqual(self.sounds["SND_THEIRALLIANCE"], "Sounds/TheirAlliance")
        self.assertEqual(self.sounds["SND_AMB_SUPERNOVA_BLAST"], "Sounds/Ambient/SupernovaBlast")


if __name__ == "__main__":
    unittest.main()
