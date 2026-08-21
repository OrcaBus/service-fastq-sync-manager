#!/usr/bin/env python3
"""
Property-based tests for Fastq Set requirements classification.

**Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6**

Tests the `has_somalier_fingerprint` and `check_fastq_set_against_requirements_list`
functions which determine whether a Fastq Set meets its requirements based on
the presence of the `somalier` attribute.
"""

import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock
import importlib.util

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# --- Module Setup ---
# The layer imports `orcabus_api_tools.fastq` and related modules which are
# Lambda layer packages not available in the local dev environment.
# We create mock modules in sys.modules before importing.
# We also need to mock `requests` which is used by the layer.

_mock_modules = {
    "orcabus_api_tools": MagicMock(),
    "orcabus_api_tools.fastq": MagicMock(),
    "orcabus_api_tools.fastq.models": MagicMock(),
    "orcabus_api_tools.fastq_unarchiving": MagicMock(),
    "orcabus_api_tools.fastq_unarchiving.models": MagicMock(),
    "orcabus_api_tools.fastq_decompression": MagicMock(),
    "orcabus_api_tools.fastq_decompression.models": MagicMock(),
    "requests": MagicMock(),
}

for mod_name, mock_mod in _mock_modules.items():
    sys.modules.setdefault(mod_name, mock_mod)

# --- Direct module loading ---
# The fastq_sync_tools package __init__.py imports from utils.utils which has a broken
# type annotation (REQUIREMENT undefined). We load the globals and utils modules directly
# using importlib.util to avoid triggering the __init__.py import chain.

_layer_src = (
    Path(__file__).resolve().parents[2]
    / "app"
    / "layers"
    / "fastq_sync_tools_layer"
    / "src"
    / "fastq_sync_tools"
)

# Load globals module directly
_globals_spec = importlib.util.spec_from_file_location(
    "fastq_sync_tools_globals", _layer_src / "utils" / "globals.py"
)
_globals_mod = importlib.util.module_from_spec(_globals_spec)
_globals_spec.loader.exec_module(_globals_mod)

FASTQ_SET_REQUIREMENT = _globals_mod.FASTQ_SET_REQUIREMENT

# Load exceptions module (needed by utils.py)
_exceptions_spec = importlib.util.spec_from_file_location(
    "fastq_sync_tools_exceptions", _layer_src / "utils" / "exceptions.py"
)
_exceptions_mod = importlib.util.module_from_spec(_exceptions_spec)
_exceptions_spec.loader.exec_module(_exceptions_mod)

# Make the globals and exceptions modules importable by utils.py
sys.modules["fastq_sync_tools"] = MagicMock()
sys.modules["fastq_sync_tools.utils"] = MagicMock()
sys.modules["fastq_sync_tools.utils.globals"] = _globals_mod
sys.modules["fastq_sync_tools.utils.exceptions"] = _exceptions_mod

# Now load utils.py — it imports from .globals and .exceptions via relative imports.
# We load it with the proper package context so relative imports resolve.
# Note: utils.py has a broken type annotation at line 352 (REQUIREMENT undefined).
# We inject the missing name into the module namespace before loading.
_utils_path = _layer_src / "utils" / "utils.py"
_utils_spec = importlib.util.spec_from_file_location(
    "fastq_sync_tools.utils.utils",
    _utils_path,
    submodule_search_locations=[],
)
_utils_mod = importlib.util.module_from_spec(_utils_spec)
_utils_mod.__package__ = "fastq_sync_tools.utils"
# Inject the missing REQUIREMENT name (it's just FASTQ_REQUIREMENT by another name)
_utils_mod.REQUIREMENT = _globals_mod.FASTQ_REQUIREMENT
_utils_spec.loader.exec_module(_utils_mod)

has_somalier_fingerprint = _utils_mod.has_somalier_fingerprint
check_fastq_set_against_requirements_list = _utils_mod.check_fastq_set_against_requirements_list


# --- Strategies ---

# Strategy for arbitrary dict values representing somalier data (non-null)
somalier_value_strategy = st.dictionaries(
    keys=st.text(min_size=1, max_size=10),
    values=st.recursive(
        st.none() | st.booleans() | st.integers() | st.floats(allow_nan=False) | st.text(max_size=20),
        lambda children: st.lists(children, max_size=3) | st.dictionaries(st.text(max_size=5), children, max_size=3),
        max_leaves=5,
    ),
    min_size=0,
    max_size=5,
)

# Strategy for somalier attribute: either None or a non-null dict
somalier_strategy = st.one_of(st.none(), somalier_value_strategy)

# Strategy for a minimal FastqSet-like dict with at least a `somalier` field
# The FastqSet TypedDict has a `somalier` field that can be None or a dict
fastq_set_strategy = somalier_strategy.map(lambda s: {"somalier": s})

# Strategy for requirements lists from FASTQ_SET_REQUIREMENT (currently only 'hasFingerprint')
# Generate non-empty subsets of the available requirements
requirements_strategy = st.lists(
    st.sampled_from(["hasFingerprint"]),
    min_size=1,
    max_size=1,
    unique=True,
)


# --- Property 1 Tests ---


@pytest.mark.pbt
class TestProperty1RequirementsClassification:
    """
    Feature: fastq-set-sync, Property 1: requirements classification is determined by somalier presence

    For any Fastq Set object and requirements list containing `hasFingerprint`,
    the `check_fastq_set_against_requirements_list` function SHALL classify
    `hasFingerprint` as satisfied if and only if the Fastq Set's `somalier`
    attribute is non-null. The overall `hasAllRequirements` result SHALL be `true`
    if and only if every requirement in the list is classified as satisfied.

    **Validates: Requirements 3.2, 3.3, 3.4, 3.5, 3.6**
    """

    @settings(max_examples=100)
    @given(fastq_set=fastq_set_strategy)
    def test_has_somalier_fingerprint_returns_true_iff_somalier_not_none(
        self, fastq_set: dict
    ):
        """
        has_somalier_fingerprint returns True if and only if
        the FastqSet's `somalier` attribute is not None.

        **Validates: Requirements 3.2, 3.3**
        """
        result = has_somalier_fingerprint(fastq_set)

        if fastq_set["somalier"] is not None:
            assert result is True
        else:
            assert result is False

    @settings(max_examples=100)
    @given(
        fastq_set=fastq_set_strategy,
        requirements=requirements_strategy,
    )
    def test_has_fingerprint_in_satisfied_iff_somalier_not_none(
        self, fastq_set: dict, requirements: list
    ):
        """
        For a requirements list containing 'hasFingerprint':
        - 'hasFingerprint' is in the satisfied list iff somalier is not None
        - 'hasFingerprint' is in the unsatisfied list iff somalier is None

        **Validates: Requirements 3.2, 3.3**
        """
        satisfied, unsatisfied = check_fastq_set_against_requirements_list(
            fastq_set, requirements
        )

        if fastq_set["somalier"] is not None:
            assert "hasFingerprint" in satisfied
            assert "hasFingerprint" not in unsatisfied
        else:
            assert "hasFingerprint" not in satisfied
            assert "hasFingerprint" in unsatisfied

    @settings(max_examples=100)
    @given(
        fastq_set=fastq_set_strategy,
        requirements=requirements_strategy,
    )
    def test_has_all_requirements_equals_empty_unsatisfied(
        self, fastq_set: dict, requirements: list
    ):
        """
        The overall 'hasAllRequirements' is True if and only if
        len(unsatisfied) == 0.

        **Validates: Requirements 3.4, 3.5**
        """
        satisfied, unsatisfied = check_fastq_set_against_requirements_list(
            fastq_set, requirements
        )

        has_all_requirements = len(unsatisfied) == 0

        if fastq_set["somalier"] is not None:
            assert has_all_requirements is True
        else:
            assert has_all_requirements is False

    @settings(max_examples=100)
    @given(
        fastq_set=fastq_set_strategy,
        requirements=requirements_strategy,
    )
    def test_satisfied_and_unsatisfied_partition_requirements(
        self, fastq_set: dict, requirements: list
    ):
        """
        The satisfied and unsatisfied lists together form a complete partition
        of the input requirements (no requirement is lost or duplicated).

        **Validates: Requirements 3.4, 3.5**
        """
        satisfied, unsatisfied = check_fastq_set_against_requirements_list(
            fastq_set, requirements
        )

        # Every requirement ends up in exactly one of the two lists
        assert sorted(satisfied + unsatisfied) == sorted(requirements)
        # No duplicates within either list
        assert len(set(satisfied)) == len(satisfied)
        assert len(set(unsatisfied)) == len(unsatisfied)
        # No overlap
        assert set(satisfied).isdisjoint(set(unsatisfied))

    @settings(max_examples=100)
    @given(somalier_value=somalier_value_strategy)
    def test_non_null_somalier_always_satisfies_fingerprint(
        self, somalier_value: dict
    ):
        """
        Any non-null somalier value (including empty dict) satisfies the
        hasFingerprint requirement.

        **Validates: Requirements 3.2**
        """
        fastq_set = {"somalier": somalier_value}
        satisfied, unsatisfied = check_fastq_set_against_requirements_list(
            fastq_set, ["hasFingerprint"]
        )

        assert "hasFingerprint" in satisfied
        assert len(unsatisfied) == 0

    def test_null_somalier_never_satisfies_fingerprint(self):
        """
        A null somalier value never satisfies the hasFingerprint requirement.

        **Validates: Requirements 3.3**
        """
        fastq_set = {"somalier": None}
        satisfied, unsatisfied = check_fastq_set_against_requirements_list(
            fastq_set, ["hasFingerprint"]
        )

        assert "hasFingerprint" not in satisfied
        assert "hasFingerprint" in unsatisfied
        assert len(unsatisfied) == 1
