# Solr configuration

Files in this folder describe how the **books** core is indexed and queried.

| File | Purpose |
| --- | --- |
| `managed-schema.xml` | Reference schema with all fields, types, and copyFields. |
| `solrconfig-snippets.xml` | `/select`, `/suggest`, and `/spell` request handlers and components to merge into the core's `solrconfig.xml`. |
| `synonyms.txt` | Query-time synonym expansion (`js -> javascript`, `k8s -> kubernetes`, etc.). |
| `stopwords.txt` | Stopwords removed at index and query time. |

## Applying the schema with the Schema API

The recommended path on Solr 9 is to use the Schema API rather than editing
`managed-schema` directly.  See `scripts/apply_schema.sh` for the exact REST
calls; it is idempotent, so re-running on an existing core is safe.

## Field-type strategy

* **`text_en`** — Standard tokenizer + stopwords + lowercase + Porter stemmer.
  Used for `title`, `author`, `description`, and the `_text_` catch-all.
  Synonyms expand only at query time so the index stays compact.
* **`text_suggest`** — Edge-n-gram analyzer used for `title_ac`, the field that
  powers prefix-style autocomplete.
* **`string` / `strings`** — Untokenised, suitable for facets and exact match
  filters (`genres`, `language`, `publisher`, `tags`).
* **`pint` / `pfloat` / `pdate`** — Point fields with `docValues` so they can be
  used in facets, range queries, and sorts efficiently.

## copyFields rationale

| Source | Destination | Reason |
| --- | --- | --- |
| `title`, `author`, `description`, `genres`, `tags` | `_text_` | Single-field full-text fallback. |
| `title` | `title_str` | Exact-match sort/group. |
| `title` | `title_ac` | Edge-n-gram autocomplete. |
| `author` | `author_str` | Author facet without tokenisation. |
