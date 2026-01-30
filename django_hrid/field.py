from typing import Iterable

from django.conf import settings
from django.core.exceptions import FieldError
from django.db.models import CharField, Field
from django.utils.functional import cached_property
from hrid import HRID

from .exceptions import ConfigError, RealFieldDoesNotExistError


# Default elements if not specified
DEFAULT_ELEMENTS = ("adjective", "noun", "verb")


class HRIDField(CharField):
    """
    A Django model field that provides human-readable IDs.

    This field creates a virtual field that encodes/decodes an integer field
    (typically the primary key) to a human-readable format like "calm-apple-hop".

    Example usage:
        class MyModel(models.Model):
            hrid = HRIDField()  # Encodes the 'id' field by default

            # Or with custom configuration:
            hrid = HRIDField(
                real_field_name='id',
                elements=('adjective', 'animal', 'verb'),
                scramble=True,
                prefix='item_',
            )

    Settings (in Django settings.py):
        DJANGO_HRID_ELEMENTS: Default elements tuple
        DJANGO_HRID_DELIMITER: Default delimiter (default: '-')
        DJANGO_HRID_SCRAMBLE: Default scramble setting (default: False)
        DJANGO_HRID_WORD_LISTS: Custom word lists dict
    """

    concrete = False
    allowed_lookups = ("exact", "in", "isnull")

    def __init__(
        self,
        real_field_name: str = "id",
        *args,
        hrid_instance: HRID | None = None,
        elements: Iterable[str] | None = None,
        delimiter: str | None = None,
        scramble: bool = True,
        scramble_seed: str | None = None,
        word_lists: dict[str, list[str]] | None = None,
        prefix: str = "",
        **kwargs,
    ):
        """
        Initialize the HRIDField.

        :param real_field_name: Name of the integer field to encode (default: 'id')
        :param hrid_instance: Pre-configured HRID instance (overrides other params)
        :param elements: Tuple of element types, e.g., ('adjective', 'noun', 'verb')
        :param delimiter: Separator between words (default: '-')
        :param scramble: Whether to scramble sequential IDs for visual variety (default: True)
        :param scramble_seed: Seed for scrambling. Auto-derived from model name if not set.
        :param word_lists: Custom word lists dict
        :param prefix: Optional prefix for the encoded value, e.g., 'user_'
        """
        kwargs.pop("editable", None)
        super().__init__(*args, editable=False, **kwargs)
        self.real_field_name = real_field_name
        self.prefix = prefix

        # Store configuration for later initialization
        self._explicit_hrid_instance = hrid_instance
        self._elements = elements
        self._delimiter = delimiter
        self._scramble = scramble
        self._scramble_seed = scramble_seed
        self._word_lists = word_lists

        self.hrid_instance = None
        self.attached_to_model = None

    def contribute_to_class(self, cls, name):
        self.attname = name
        self.name = name

        if getattr(self, "model", None) is None and cls._meta.abstract is False:
            self.model = cls

        if self.attached_to_model is not None:
            raise FieldError(
                f"Field '{self.name}' is already attached to another model({self.attached_to_model})."
            )
        self.attached_to_model = cls

        self.column = None

        if self.verbose_name is None:
            self.verbose_name = self.name

        setattr(cls, name, self)

        cls._meta.add_field(self, private=True)

        self.hrid_instance = self._get_hrid_instance()

    def _get_hrid_instance(self) -> HRID:
        """Create or return the HRID instance for encoding/decoding."""
        if self._explicit_hrid_instance:
            if any(
                x is not None
                for x in [self._elements, self._delimiter, self._word_lists]
            ):
                raise ConfigError(
                    "If hrid_instance is set, elements, delimiter, "
                    "and word_lists should not be set"
                )
            return self._explicit_hrid_instance

        # Get configuration from settings or use defaults
        elements = self._elements
        if elements is None:
            elements = getattr(settings, "DJANGO_HRID_ELEMENTS", None) or DEFAULT_ELEMENTS

        delimiter = self._delimiter
        if delimiter is None:
            delimiter = getattr(settings, "DJANGO_HRID_DELIMITER", None) or "-"

        word_lists = self._word_lists
        if word_lists is None:
            word_lists = getattr(settings, "DJANGO_HRID_WORD_LISTS", None)

        # Auto-derive scramble_seed from model name if not explicitly set
        scramble_seed = self._scramble_seed
        if scramble_seed is None and self._scramble and self.attached_to_model:
            scramble_seed = self.attached_to_model._meta.label  # e.g., "myapp.User"

        return HRID(
            elements=elements,
            delimiter=delimiter,
            scramble=self._scramble,
            scramble_seed=scramble_seed,
            word_lists=word_lists,
        )

    def get_internal_type(self):
        return "CharField"

    def get_prep_value(self, value):
        """Convert HRID string to integer for database queries."""
        if value is None:
            return None

        # Handle prefix
        if self.prefix:
            if value.startswith(self.prefix):
                value = value[len(self.prefix) :]
            else:
                return None

        try:
            return self.hrid_instance.decode(value)
        except ValueError:
            return None

    def from_db_value(self, value, expression, connection, *args):
        """Convert integer from database to HRID string."""
        if value is None:
            return None
        try:
            encoded_value = self.hrid_instance.encode(value)
            return f"{self.prefix}{encoded_value}"
        except (ValueError, TypeError):
            return None

    def get_col(self, alias, output_field=None):
        if output_field is None:
            output_field = self
        col = self.real_col.get_col(alias, output_field)
        return col

    @cached_property
    def real_col(self):
        """Get the actual database column this field references."""
        # `maybe_field` is intended for `pk`, which does not appear in `_meta.fields`
        maybe_field = getattr(self.attached_to_model._meta, self.real_field_name, None)
        if isinstance(maybe_field, Field):
            return maybe_field
        try:
            field = next(
                col
                for col in self.attached_to_model._meta.fields
                if col.name == self.real_field_name
                or col.attname == self.real_field_name
            )
        except StopIteration:
            raise RealFieldDoesNotExistError(
                f"{self.__class__.__name__}({self}) can't find real field "
                f"using real_field_name: {self.real_field_name}"
            )
        return field

    def __get__(self, instance, name=None):
        """Get the HRID string when accessing the field on an instance."""
        if not instance:
            return self
        real_value = getattr(instance, self.real_field_name, None)
        # The instance is not saved yet?
        if real_value is None:
            return ""
        assert isinstance(real_value, int), f"Expected int, got {type(real_value)}"
        encoded_value = self.hrid_instance.encode(real_value)
        return f"{self.prefix}{encoded_value}"

    def __set__(self, instance, value):
        """HRID field is read-only, setting is a no-op."""
        pass

    def __deepcopy__(self, memo=None):
        new_instance = super().__deepcopy__(memo)
        for attr in ("hrid_instance", "attached_to_model"):
            if hasattr(new_instance, attr):
                setattr(new_instance, attr, None)
        # Remove cached values from cached_property
        for key in ("real_col",):
            if key in new_instance.__dict__:
                del new_instance.__dict__[key]
        return new_instance

    @classmethod
    def get_lookups(cls):
        all_lookups = super().get_lookups()
        return {k: all_lookups[k] for k in cls.allowed_lookups if k in all_lookups}
