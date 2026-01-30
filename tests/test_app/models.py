from django.db import models

from django_hrid import HRIDField


class BasicModel(models.Model):
    """Model with default HRID configuration."""
    name = models.CharField(max_length=100)
    hrid = HRIDField()

    class Meta:
        app_label = "test_app"


class ScrambledModel(models.Model):
    """Model with scrambled HRIDs for sequential IDs."""
    name = models.CharField(max_length=100)
    hrid = HRIDField(scramble=True)

    class Meta:
        app_label = "test_app"


class PrefixedModel(models.Model):
    """Model with a prefix on the HRID."""
    name = models.CharField(max_length=100)
    hrid = HRIDField(prefix="item_")

    class Meta:
        app_label = "test_app"


class CustomElementsModel(models.Model):
    """Model with custom word elements."""
    name = models.CharField(max_length=100)
    hrid = HRIDField(elements=("adjective", "animal", "verb", "number"))

    class Meta:
        app_label = "test_app"
