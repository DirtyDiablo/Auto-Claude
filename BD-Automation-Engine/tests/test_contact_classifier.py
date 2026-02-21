"""Tests for Engine3_OrgChart/scripts/contact_classifier.py.

Tests the 6-tier contact classification logic, location-to-program
mapping, batch classification, and Notion formatting.
"""

import pytest

from Engine3_OrgChart.scripts.contact_classifier import (
    TIER_DEFINITIONS,
    LOCATION_PROGRAM_MAP,
    ClassificationResult,
    classify_by_title,
    infer_program_from_location,
    classify_contact,
    classify_contacts_batch,
    format_for_notion,
)


# ===================================================================
# classify_by_title
# ===================================================================


class TestClassifyByTitle:
    """Verify the 6-tier hierarchy classification from job titles."""

    # --- Tier 1: Executive ---

    @pytest.mark.parametrize("title", [
        "CEO",
        "CTO",
        "CFO",
        "CIO",
        "CISO",
        "Chief Technology Officer",
        "Chief Information Officer",
        "President",
        "General Manager",
        "Executive Vice President",
        "SVP",
        "Senior Vice President",
    ])
    def test_tier_1_executive(self, title):
        tier, confidence = classify_by_title(title)
        assert tier == 1, f"'{title}' should be Tier 1, got {tier}"
        assert confidence >= 0.8

    # --- Tier 2: Director ---

    @pytest.mark.parametrize("title", [
        "Director of BD",
        "Division Head",
        "Associate Director",
    ])
    def test_tier_2_director(self, title):
        tier, _ = classify_by_title(title)
        assert tier == 2, f"'{title}' should be Tier 2, got {tier}"

    def test_vp_classified_as_tier_2(self):
        """VP abbreviation should match Tier 2."""
        tier, _ = classify_by_title("VP")
        assert tier == 2

    def test_vice_president_matches_president_first(self):
        """'Vice President' matches Tier 1 'President' pattern before Tier 2."""
        tier, _ = classify_by_title("Vice President")
        assert tier == 1  # Tier 1 President pattern fires first

    # --- Tier 3: Program Leadership ---

    @pytest.mark.parametrize("title", [
        "Program Manager",
        "Project Manager",
        "Site Lead",
        "Task Order Manager",
        "Deputy Program Manager",
        "Principal Engineer",
        "Chief Engineer",
        "Chief Architect",
        "Principal Scientist",
    ])
    def test_tier_3_program_leadership(self, title):
        tier, _ = classify_by_title(title)
        assert tier == 3, f"'{title}' should be Tier 3, got {tier}"

    # --- Tier 4: Management ---

    @pytest.mark.parametrize("title", [
        "Manager",
        "Team Lead",
        "Technical Lead",
        "Supervisor",
        "Section Chief",
        "Branch Manager",
        "Group Lead",
    ])
    def test_tier_4_management(self, title):
        tier, _ = classify_by_title(title)
        assert tier == 4, f"'{title}' should be Tier 4, got {tier}"

    # --- Tier 5: Senior IC ---

    @pytest.mark.parametrize("title", [
        "Senior Engineer",
        "Senior Developer",
        "Senior Analyst",
        "Sr. Engineer",
        "Lead Engineer",
        "Lead Developer",
        "Staff Engineer",
        "Architect",
        "SME",
        "Subject Matter Expert",
    ])
    def test_tier_5_senior_ic(self, title):
        tier, _ = classify_by_title(title)
        assert tier == 5, f"'{title}' should be Tier 5, got {tier}"

    # --- Tier 6: Individual Contributor ---

    @pytest.mark.parametrize("title", [
        "Engineer",
        "Developer",
        "Analyst",
        "Specialist",
        "Technician",
        "Administrator",
        "Consultant",
    ])
    def test_tier_6_individual_contributor(self, title):
        tier, _ = classify_by_title(title)
        assert tier == 6, f"'{title}' should be Tier 6, got {tier}"

    # --- Edge Cases ---

    def test_empty_title_defaults_to_tier_6(self):
        tier, confidence = classify_by_title("")
        assert tier == 6
        assert confidence == 0.3

    def test_none_title_defaults_to_tier_6(self):
        tier, confidence = classify_by_title(None)
        assert tier == 6
        assert confidence == 0.3

    def test_unrecognized_title_defaults_to_tier_6(self):
        tier, confidence = classify_by_title("Intern")
        assert tier == 6
        assert confidence == 0.5

    def test_case_insensitive(self):
        tier, _ = classify_by_title("ceo")
        assert tier == 1

    def test_title_with_extra_whitespace(self):
        tier, _ = classify_by_title("  Program Manager  ")
        assert tier == 3

    def test_higher_tier_takes_priority(self):
        """CEO should match Tier 1 even though it could match lower patterns."""
        tier, _ = classify_by_title("CEO and Senior Engineer")
        assert tier == 1


# ===================================================================
# infer_program_from_location
# ===================================================================


class TestInferProgramFromLocation:
    def test_san_diego_maps_to_pacaf(self):
        program, hub = infer_program_from_location("San Diego, CA")
        assert program == "AF DCGS - PACAF"
        assert hub == "San Diego Metro"

    def test_fort_belvoir_maps_to_dcgs_a(self):
        program, hub = infer_program_from_location("Fort Belvoir, VA")
        assert program == "Army DCGS-A"
        assert hub == "DC Metro"

    def test_langley_maps_to_af_dcgs(self):
        program, hub = infer_program_from_location("Langley AFB, VA")
        assert program == "AF DCGS - Langley"
        assert hub == "Hampton Roads"

    def test_dayton_maps_to_wright_patt(self):
        program, hub = infer_program_from_location("Dayton, OH")
        assert program == "AF DCGS - Wright-Patt"
        assert hub == "Dayton/Wright-Patt"

    def test_herndon_maps_to_corporate_hq(self):
        program, hub = infer_program_from_location("Herndon, VA")
        assert program == "Corporate HQ"
        assert hub == "DC Metro"

    def test_unknown_location(self):
        program, hub = infer_program_from_location("Unknown City, XX")
        assert program is None
        assert hub == "Unknown"

    def test_empty_location(self):
        program, hub = infer_program_from_location("")
        assert program is None
        assert hub == "Unknown"

    def test_none_location(self):
        program, hub = infer_program_from_location(None)
        assert program is None
        assert hub == "Unknown"

    def test_case_insensitive_matching(self):
        program, _ = infer_program_from_location("SAN DIEGO")
        assert program == "AF DCGS - PACAF"

    def test_tampa_maps_to_socom(self):
        program, _ = infer_program_from_location("Tampa, FL")
        assert program == "SOCOM"


# ===================================================================
# classify_contact
# ===================================================================


class TestClassifyContact:
    def test_full_classification(self):
        contact = {
            "title": "Program Manager",
            "location": "Fort Belvoir, VA",
            "name": "Jane Doe",
            "company": "Leidos",
        }
        result = classify_contact(contact)
        assert isinstance(result, ClassificationResult)
        assert result.tier == 3
        assert result.tier_name == "Program Leadership"
        assert result.bd_priority == "High"
        assert result.program == "Army DCGS-A"
        assert result.location_hub == "DC Metro"
        assert result.confidence >= 0.8

    def test_explicit_program_overrides_location(self):
        contact = {
            "title": "Engineer",
            "location": "San Diego, CA",
            "program": "CUSTOM_PROGRAM",
        }
        result = classify_contact(contact)
        assert result.program == "CUSTOM_PROGRAM"

    def test_alternative_field_names(self):
        """Contact classifier supports both lowercase and Title Case field names."""
        contact = {
            "Job Title": "CEO",
            "Location": "Herndon, VA",
        }
        result = classify_contact(contact)
        assert result.tier == 1

    def test_minimal_contact(self):
        """Contact with no title or location gets default values."""
        result = classify_contact({})
        assert result.tier == 6
        assert result.program is None
        assert result.location_hub == "Unknown"

    def test_outreach_sequence_assigned(self):
        contact = {"title": "Director of Engineering"}
        result = classify_contact(contact)
        assert result.outreach_sequence != ""


# ===================================================================
# classify_contacts_batch
# ===================================================================


class TestClassifyContactsBatch:
    def test_batch_returns_enriched_contacts(self):
        contacts = [
            {"name": "Alice", "title": "CEO", "location": "Herndon, VA"},
            {"name": "Bob", "title": "Engineer", "location": "San Diego, CA"},
        ]
        results = classify_contacts_batch(contacts)
        assert len(results) == 2
        assert "_classification" in results[0]
        assert "_classification" in results[1]

    def test_batch_preserves_original_fields(self):
        contacts = [{"name": "Alice", "title": "CEO", "custom_field": "value"}]
        results = classify_contacts_batch(contacts)
        assert results[0]["custom_field"] == "value"
        assert results[0]["name"] == "Alice"

    def test_batch_classification_fields(self):
        contacts = [{"name": "Test", "title": "Program Manager", "location": "Dayton, OH"}]
        results = classify_contacts_batch(contacts)
        classification = results[0]["_classification"]

        assert "Hierarchy Tier" in classification
        assert "BD Priority" in classification
        assert "Program" in classification
        assert "Location Hub" in classification
        assert "Outreach Sequence" in classification
        assert "Classification Confidence" in classification

    def test_empty_batch(self):
        results = classify_contacts_batch([])
        assert results == []

    def test_batch_does_not_mutate_originals(self):
        original = {"name": "Test", "title": "Engineer"}
        contacts = [original]
        classify_contacts_batch(contacts)
        assert "_classification" not in original


# ===================================================================
# format_for_notion
# ===================================================================


class TestFormatForNotion:
    def test_notion_format_structure(self):
        classification = ClassificationResult(
            tier=1,
            tier_name="Executive",
            bd_priority="Critical",
            bd_emoji="red_circle",
            program="DCGS-A",
            location_hub="DC Metro",
            outreach_sequence="D - Strategic Engagement",
            confidence=0.9,
        )
        result = format_for_notion(classification)
        assert "Hierarchy Tier" in result
        assert "BD Priority" in result
        assert "Program" in result
        assert "Location Hub" in result

    def test_notion_format_tier_string(self):
        classification = ClassificationResult(
            tier=3,
            tier_name="Program Leadership",
            bd_priority="High",
            bd_emoji="orange_circle",
            program="DCGS-A",
            location_hub="DC Metro",
            outreach_sequence="C",
            confidence=0.85,
        )
        result = format_for_notion(classification)
        assert result["Hierarchy Tier"] == "Tier 3 - Program Leadership"

    def test_notion_format_emoji_in_priority(self):
        classification = ClassificationResult(
            tier=1,
            tier_name="Executive",
            bd_priority="Critical",
            bd_emoji="red_circle",
            program=None,
            location_hub="Unknown",
            outreach_sequence="D",
            confidence=0.9,
        )
        result = format_for_notion(classification)
        # Should contain the red circle emoji
        assert "\U0001f534" in result["BD Priority"]

    def test_notion_format_none_program(self):
        classification = ClassificationResult(
            tier=6, tier_name="IC", bd_priority="Standard",
            bd_emoji="white_circle", program=None, location_hub="Unknown",
            outreach_sequence="A", confidence=0.5,
        )
        result = format_for_notion(classification)
        assert result["Program"] is None


# ===================================================================
# TIER_DEFINITIONS structure
# ===================================================================


class TestTierDefinitions:
    def test_all_six_tiers_defined(self):
        assert set(TIER_DEFINITIONS.keys()) == {1, 2, 3, 4, 5, 6}

    def test_each_tier_has_required_fields(self):
        required = {"name", "patterns", "bd_priority", "bd_emoji", "outreach_sequence"}
        for tier_num, tier_def in TIER_DEFINITIONS.items():
            for field in required:
                assert field in tier_def, f"Tier {tier_num} missing '{field}'"

    def test_each_tier_has_patterns(self):
        for tier_num, tier_def in TIER_DEFINITIONS.items():
            assert len(tier_def["patterns"]) > 0, f"Tier {tier_num} has no patterns"
