"""Regression coverage for the Streamlit Calm world package."""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path
from urllib.parse import parse_qs, urlparse


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ultra_brain_streamlit_entry", ROOT / "app.py")
if SPEC is None or SPEC.loader is None:  # pragma: no cover - import machinery guard
    raise RuntimeError("Unable to load app.py")
APP = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = APP
SPEC.loader.exec_module(APP)


class StreamlitCalmThemeTests(unittest.TestCase):
    def test_calm_is_a_dedicated_korean_world_package(self) -> None:
        calm = APP.THEMES["Calm"]
        self.assertEqual(calm["asset"], "world-calm.png")
        self.assertEqual(calm["layout"], "wetland")
        self.assertEqual(calm["world"], "차분한 새벽 습지의 세계")
        self.assertIn("새벽빛", calm["detail"])
        self.assertEqual(APP.CANONICAL_WORLD_IDS["calm"], "calm-wetland-world")
        self.assertEqual({name.lower() for name in APP.THEMES}, set(APP.CANONICAL_WORLD_IDS))

    def test_calm_uses_a_real_widescreen_asset(self) -> None:
        calm_path = APP.PUBLIC_ROOT / APP.THEMES["Calm"]["asset"]
        official_path = APP.PUBLIC_ROOT / APP.THEMES["Official"]["asset"]
        data = calm_path.read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual((int.from_bytes(data[16:20], "big"), int.from_bytes(data[20:24], "big")), (1672, 941))
        self.assertNotEqual(data, official_path.read_bytes())
        self.assertNotEqual(APP.world_art_data_uri("world-calm.png"), APP.world_art_data_uri("ultra-brain-world.png"))

    def test_calm_propagates_with_the_complete_contract(self) -> None:
        url = APP.build_ecosystem_url(
            "Calm",
            APP.adjustment_defaults(),
            revision=12,
            base_url="https://example.test/ecosystem",
        )
        query = parse_qs(urlparse(url).query, keep_blank_values=True)
        self.assertEqual(query["theme"], ["calm"])
        self.assertEqual(query["world"], ["calm-wetland-world"])
        self.assertEqual(query["revision"], ["12"])
        self.assertEqual(query["propagation"], ["automatic"])
        self.assertEqual(set(query["applied_targets"][0].split(",")), set(APP.CANONICAL_PROPAGATION_TARGETS))
        for query_name in APP.CANONICAL_ADJUSTMENT_KEYS.values():
            self.assertIn(query_name, query)


if __name__ == "__main__":
    unittest.main()
