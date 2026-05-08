# Dataset — Books Catalog

A reproducible, hand-curated catalogue of **~250 books** spanning programming,
distributed systems, fiction, business, science, biographies, and more.

## Files

| File | Format | Use with Solr |
| --- | --- | --- |
| `books.csv` | CSV | `/update/csv` (multi-valued fields use `;` as separator) |
| `books.json` | JSON array | `/update/json/docs` |

## Schema

| Field | Type | Notes |
| --- | --- | --- |
| `id` | string | Unique key, e.g. `book_0007` |
| `title` | text_en | Indexed full-text + copied to `_text_` |
| `author` | text_en | Indexed full-text + copied to `_text_` |
| `genres` | strings (multivalued) | Faceted; CSV uses `;` separator |
| `language` | string | Faceted |
| `year` | pint | Range queries / sort |
| `pages` | pint | Range queries |
| `rating` | pfloat | Range queries / sort |
| `price` | pfloat | Range queries / sort |
| `in_stock` | boolean | Filter |
| `stock_count` | pint | Range queries |
| `publisher` | string | Faceted |
| `isbn` | string | Lookup |
| `pub_date` | pdate | Date sort / range |
| `tags` | strings (multivalued) | Faceted |
| `description` | text_en | Indexed full-text + highlighted |

## Regenerating

The dataset is generated deterministically by:

```bash
python scripts/generate_dataset.py
```

The seed records (~85) are real books; an additional ~165 records are produced
by deterministic recombination so that the index has enough volume to
demonstrate facets, paging, and performance.
