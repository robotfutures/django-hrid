# django-hrid

Human-readable IDs for Django models. Encode your integer primary keys as memorable word combinations like `calm-apple-hop` instead of exposing sequential integers or using opaque UUIDs.

## Installation

```bash
pip install django-hrid
```

## Quick Start

```python
from django.db import models
from django_hrid import HRIDField

class Article(models.Model):
    title = models.CharField(max_length=200)
    hrid = HRIDField()  # Encodes the 'id' field
```

```python
>>> article = Article.objects.create(title="Hello World")
>>> article.hrid
'calm-apple-hop'

>>> Article.objects.get(hrid='calm-apple-hop')
<Article: Hello World>
```

## Features

- **Human-readable**: IDs like `serene-mountain-dance` are easier to remember, communicate, and type than `a1b2c3d4` or `12345`
- **Deterministic**: Same integer always produces the same HRID (and vice versa)
- **Scrambled mode**: Make sequential IDs look random while remaining reversible
- **Customizable**: Choose word lists, delimiters, and prefixes
- **Query support**: Filter by HRID in Django querysets

## Configuration

### Basic Usage

```python
class MyModel(models.Model):
    hrid = HRIDField()  # Uses default: adjective-noun-verb
```

### Scrambled IDs

Sequential IDs (1, 2, 3...) normally produce similar-looking HRIDs. Enable scrambling to spread them across the ID space:

```python
class MyModel(models.Model):
    # Without scramble: 1 -> "calm-apple-hop", 2 -> "calm-apple-run", 3 -> "calm-apple-fly"
    # With scramble:    1 -> "wild-tiger-dance", 2 -> "serene-river-flow", 3 -> "bright-falcon-soar"
    hrid = HRIDField(scramble=True)
```

### Custom Elements

```python
class MyModel(models.Model):
    hrid = HRIDField(elements=('adjective', 'animal', 'verb', 'number'))
    # Produces: "happy-dolphin-swim-42"
```

Available elements: `adjective`, `noun`, `verb`, `adverb`, `animal`, `flower`, `number`

### Prefix

Add a prefix for namespacing or readability:

```python
class User(models.Model):
    hrid = HRIDField(prefix='user_')
    # Produces: "user_calm-apple-hop"
```

### Django Settings

Configure defaults in `settings.py`:

```python
DJANGO_HRID_ELEMENTS = ('adjective', 'noun', 'verb')
DJANGO_HRID_DELIMITER = '-'
DJANGO_HRID_SCRAMBLE = False
DJANGO_HRID_WORD_LISTS = None  # Use custom word lists dict
```

## Querying

```python
# Exact match
Article.objects.get(hrid='calm-apple-hop')

# Filter
Article.objects.filter(hrid__in=['calm-apple-hop', 'wild-tiger-run'])

# The HRID is decoded to the integer ID for database queries
```

## How It Works

HRID uses a mixed-radix number system where each word list represents a "digit". For example, with 100 adjectives × 200 nouns × 150 verbs = 3,000,000 unique IDs.

The encoding is fully reversible:
- `encode(42)` → `"calm-apple-hop"`
- `decode("calm-apple-hop")` → `42`

When `scramble=True`, a multiplicative scrambling function spreads sequential inputs across the ID space while remaining fully reversible.

## License

MIT
