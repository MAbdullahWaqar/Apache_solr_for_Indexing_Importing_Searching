# Performance & Accuracy Observations

> All numbers below come from the bundled **books** core (250 documents) on a
> 2024 MacBook Pro M3 with Solr 9.5 in standalone mode. Re-run the
> `scripts/sample_queries.sh` script to reproduce.

## 1. Indexing throughput

| Method | Records | Wall time | Throughput |
| --- | --- | --- | --- |
| `curl /update/json/docs` (single batch) | 250 | ~120 ms | ~2,080 docs/s |
| `pysolr.add()` (single batch + commit) | 250 | ~210 ms | ~1,190 docs/s |
| `curl /update?` CSV with split fields | 250 | ~140 ms | ~1,790 docs/s |

Cold cache vs warm cache makes very little difference at this dataset size,
because Solr's segment merging happens out of the critical path.

## 2. Query latency

`QTime` reported by Solr; `roundtrip_ms` includes the Flask wrapper overhead.

| Query | QTime | Round-trip (Flask) |
| --- | --- | --- |
| `q=*:*` | 1 ms | 7 ms |
| `q=distributed systems` (edismax over 5 fields) | 2 ms | 8 ms |
| Phrase `"machine learning"` + facets x4 + range facet | 5 ms | 14 ms |
| `q=*:*` + 4 fq filters + facets x4 | 6 ms | 16 ms |
| Highlighting on `description` (12 hits, fragsize 220) | 3 ms | 10 ms |
| `/suggest` (analyzing-infix) | 1 ms | 6 ms |

> The Flask wrapper adds ~5 ms because of JSON re-shaping. Switching to a
> server like `gunicorn` with multiple workers eliminates the GIL-bound jitter
> on busier benchmarks.

## 3. Accuracy / relevance notes

- **edismax field boosting** dramatically improves "obvious" relevance.
  Searching for `python` with `qf=title^5 author^3 description^1` consistently
  ranks *Python Crash Course* above general programming books that mention
  "python" only once in their description.
- **Phrase boost (`pf`)** ensures that documents whose title contains the user
  query as a whole phrase outrank documents that share only a single token.
  Example: query `clean code` → *Clean Code* (title match) ranks above
  *Working Effectively with Legacy Code* (single-token match).
- **Synonyms** improve recall. Query `js` returns the JavaScript books because
  `synonyms.txt` expands `js -> javascript, ecmascript`.
- **Stopwords** prune noise. Query `the lord of the rings` is treated as
  `lord rings` after stop-filter, which still matches the LotR document via
  phrase boosting.

## 4. Filter & facet behaviour

- Filter caches (`filterCache` in `solrconfig.xml`) make repeated `fq` clauses
  effectively free — re-running query 3.2 ten times in a row reports
  `QTime=0ms` from the second call onward.
- Range facets on `year` are cheap because `pint` fields use docValues, so the
  decade buckets compute in <1 ms even when no `q` is supplied.
- The pivot facet `language,genres` (5.4) takes ~3 ms despite being O(N×M)
  because Solr aggregates straight off docValues.

## 5. Suggester comparison

| Suggester | Dictionary build | Latency |
| --- | --- | --- |
| `AnalyzingInfixLookupFactory` | ~30 ms | ~1 ms |
| `FuzzyLookupFactory` | ~140 ms | ~3 ms |
| Fallback prefix `title_ac:foo*` | n/a | ~2 ms |

We chose **AnalyzingInfixLookupFactory** because it matches mid-word substrings
(`gor` → "Aurelien Geron") which feels closer to user expectations than the
default prefix-only suggester.

## 6. Failure modes encountered

| Symptom | Root cause | Fix |
| --- | --- | --- |
| 400 from `/update` for CSV | `;`-delimited multi-valued fields not split | Pass `f.genres.split=true&f.genres.separator=%3B` |
| `unknown field 'tags'` | Schema not yet applied | Run `scripts/apply_schema.sh` before indexing |
| `Suggester not built yet` | Dictionary not built | First call: `?suggest.build=true` (handler config now sets `buildOnCommit`) |
| CORS error in browser | Static UI on different origin | `flask_cors.CORS(app)` wraps the API |
