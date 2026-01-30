import pytest
from django.test import TestCase

from django_hrid import HRIDField


class TestHRIDFieldBasic(TestCase):
    def test_encode_decode_roundtrip(self):
        """Test that encoding and decoding produces the original value."""
        from tests.test_app.models import BasicModel

        obj = BasicModel.objects.create(name="Test")
        hrid_value = obj.hrid

        # Should be a string with dashes
        assert isinstance(hrid_value, str)
        assert "-" in hrid_value

        # Lookup by hrid should work
        found = BasicModel.objects.get(hrid=hrid_value)
        assert found.id == obj.id

    def test_unsaved_instance_returns_empty_string(self):
        """Unsaved instances should return empty string for HRID."""
        from tests.test_app.models import BasicModel

        obj = BasicModel(name="Unsaved")
        assert obj.hrid == ""

    def test_different_ids_produce_different_hrids(self):
        """Different IDs should produce different HRIDs."""
        from tests.test_app.models import BasicModel

        obj1 = BasicModel.objects.create(name="First")
        obj2 = BasicModel.objects.create(name="Second")

        assert obj1.hrid != obj2.hrid


class TestHRIDFieldScrambled(TestCase):
    def test_scrambled_sequential_ids_look_different(self):
        """Scrambled mode should make sequential IDs look visually different."""
        from tests.test_app.models import ScrambledModel

        # Create several objects
        objects = [ScrambledModel.objects.create(name=f"Item {i}") for i in range(5)]

        hrids = [obj.hrid for obj in objects]

        # With scrambling, consecutive IDs should not share prefixes
        # (without scrambling, they would all start with the same word)
        first_words = [h.split("-")[0] for h in hrids]

        # At least some should be different
        assert len(set(first_words)) > 1, "Scrambled IDs should have varied prefixes"

    def test_scrambled_roundtrip(self):
        """Scrambled encoding should still decode correctly."""
        from tests.test_app.models import ScrambledModel

        obj = ScrambledModel.objects.create(name="Test")
        hrid_value = obj.hrid

        found = ScrambledModel.objects.get(hrid=hrid_value)
        assert found.id == obj.id


class TestHRIDFieldPrefixed(TestCase):
    def test_prefix_is_applied(self):
        """HRID should start with the configured prefix."""
        from tests.test_app.models import PrefixedModel

        obj = PrefixedModel.objects.create(name="Test")
        assert obj.hrid.startswith("item_")

    def test_prefix_lookup_works(self):
        """Lookup with prefix should work."""
        from tests.test_app.models import PrefixedModel

        obj = PrefixedModel.objects.create(name="Test")
        hrid_value = obj.hrid

        found = PrefixedModel.objects.get(hrid=hrid_value)
        assert found.id == obj.id


class TestHRIDFieldCustomElements(TestCase):
    def test_custom_elements_used(self):
        """Custom elements should affect the generated HRID."""
        from tests.test_app.models import CustomElementsModel

        obj = CustomElementsModel.objects.create(name="Test")
        parts = obj.hrid.split("-")

        # Should have 4 parts (adjective, animal, verb, number)
        assert len(parts) == 4

        # Last part should be a number (from 'number' element)
        assert parts[-1].isdigit()


class TestHRIDFieldLookups(TestCase):
    def test_exact_lookup(self):
        """Exact lookup should work."""
        from tests.test_app.models import BasicModel

        obj = BasicModel.objects.create(name="Test")
        found = BasicModel.objects.filter(hrid=obj.hrid).first()
        assert found == obj

    def test_in_lookup(self):
        """IN lookup should work."""
        from tests.test_app.models import BasicModel

        obj1 = BasicModel.objects.create(name="First")
        obj2 = BasicModel.objects.create(name="Second")
        BasicModel.objects.create(name="Third")  # Not in filter

        found = list(BasicModel.objects.filter(hrid__in=[obj1.hrid, obj2.hrid]))
        assert len(found) == 2
        assert obj1 in found
        assert obj2 in found

    def test_invalid_hrid_returns_none(self):
        """Invalid HRID should return no results."""
        from tests.test_app.models import BasicModel

        BasicModel.objects.create(name="Test")
        found = BasicModel.objects.filter(hrid="invalid-hrid-value").first()
        assert found is None
