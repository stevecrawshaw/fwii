"""Tests for Config class."""


from fwii.config import Config


class TestConfig:
    def test_loads_from_default_path(self):
        """Config loads successfully from default location."""
        config = Config()
        assert config.project_root.exists()
        assert config.baseline_year == 2020

    def test_warning_area_codes_not_empty(self):
        """warning_area_codes returns a non-empty set."""
        config = Config()
        codes = config.warning_area_codes
        assert isinstance(codes, set)
        assert len(codes) > 0

    def test_warning_area_codes_are_strings(self):
        """All warning area codes are strings starting with 112."""
        config = Config()
        for code in config.warning_area_codes:
            assert isinstance(code, str)
            assert code.startswith("112")

    def test_baseline_returns_baseline_scores(self):
        """baseline property returns BaselineScores when file exists."""
        config = Config()
        baseline = config.baseline
        if baseline is not None:
            assert baseline.year == 2020
            assert baseline.fluvial_score > 0
            assert baseline.coastal_score > 0

    def test_warning_areas_have_is_tidal(self):
        """Each warning area dict has isTidal field."""
        config = Config()
        for area in config.warning_areas:
            assert "isTidal" in area
            assert "fwdCode" in area

    def test_data_paths_exist(self):
        """Data directory paths resolve correctly."""
        config = Config()
        assert config.data_raw_path.parent.exists()
        assert config.data_processed_path.parent.exists()
