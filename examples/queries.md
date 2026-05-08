# Sample Solr queries — books core

The base URL throughout is:

```
http://localhost:8983/solr/books
```

> Each query also works in the Solr Admin UI at `/solr/#/books/query`.

---

## 1. Sanity / metadata

| # | Description | URL |
| --- | --- | --- |
| 1.1 | Total document count | `/select?q=*:*&rows=0` |
| 1.2 | Schema fields | `/schema/fields` |
| 1.3 | Core stats | `/admin/cores?action=STATUS&core=books` |

## 2. Full-text search

| # | Description | URL |
| --- | --- | --- |
| 2.1 | Default `_text_` search | `/select?q=algorithms` |
| 2.2 | edismax across boosted fields (the UI default) | `/select?defType=edismax&qf=title^5+author^3+description^1&q=distributed+systems` |
| 2.3 | Phrase search | `/select?q=%22machine+learning%22` |
| 2.4 | Boolean operators | `/select?q=python+AND+(beginner+OR+intro)` |
| 2.5 | Field-targeted search | `/select?q=author:Tolkien` |
| 2.6 | Fuzzy search (Levenshtein 1) | `/select?q=algoritm~1` |
| 2.7 | Wildcard | `/select?q=title:Comp*` |

## 3. Filtering (`fq`)

| # | Description | URL |
| --- | --- | --- |
| 3.1 | Genre filter | `/select?q=*:*&fq=genres:Programming` |
| 3.2 | Multiple filters (AND) | `/select?q=*:*&fq=genres:Fiction&fq=language:English` |
| 3.3 | Year range | `/select?q=*:*&fq=year:[2010 TO 2020]` |
| 3.4 | Rating range | `/select?q=*:*&fq=rating:[4.5 TO *]` |
| 3.5 | Boolean | `/select?q=*:*&fq=in_stock:true` |
| 3.6 | NOT | `/select?q=*:*&fq=-genres:Fiction` |
| 3.7 | Date range | `/select?q=*:*&fq=pub_date:[2015-01-01T00:00:00Z TO NOW]` |

## 4. Sorting

| # | Description | URL |
| --- | --- | --- |
| 4.1 | By rating descending | `/select?q=*:*&sort=rating desc` |
| 4.2 | By multiple keys | `/select?q=*:*&sort=in_stock desc, rating desc` |
| 4.3 | By a function | `/select?q=*:*&sort=div(price,rating) asc` |

## 5. Faceting

| # | Description | URL |
| --- | --- | --- |
| 5.1 | Top genres | `/select?q=*:*&rows=0&facet=true&facet.field=genres` |
| 5.2 | Multi-field facets | `/select?q=*:*&rows=0&facet=true&facet.field=language&facet.field=publisher` |
| 5.3 | Range facet by decade | `/select?q=*:*&rows=0&facet=true&facet.range=year&facet.range.start=1900&facet.range.end=2030&facet.range.gap=10` |
| 5.4 | Pivot facet | `/select?q=*:*&rows=0&facet=true&facet.pivot=language,genres` |
| 5.5 | JSON facet (avg rating per language) | `/select?q=*:*&rows=0&json.facet={"by_lang":{"type":"terms","field":"language","facet":{"avg_rating":"avg(rating)"}}}` |

## 6. Highlighting

| # | Description | URL |
| --- | --- | --- |
| 6.1 | Default highlighter | `/select?q=algorithms&hl=true&hl.fl=title,description` |
| 6.2 | Custom mark tags | `/select?q=python&hl=true&hl.fl=description&hl.simple.pre=<mark>&hl.simple.post=</mark>` |
| 6.3 | Larger fragments | `/select?q=cloud&hl=true&hl.fl=description&hl.fragsize=400` |

## 7. Pagination

| # | Description | URL |
| --- | --- | --- |
| 7.1 | Page 1 (10 rows) | `/select?q=*:*&start=0&rows=10` |
| 7.2 | Page 3 (10 rows) | `/select?q=*:*&start=20&rows=10` |
| 7.3 | Cursor for deep paging | `/select?q=*:*&sort=id asc&rows=50&cursorMark=*` |

## 8. Suggest / spellcheck

| # | Description | URL |
| --- | --- | --- |
| 8.1 | Build suggest dictionaries | `/suggest?suggest=true&suggest.build=true&suggest.dictionary=titleSuggester` |
| 8.2 | Suggest 'des' | `/suggest?suggest=true&suggest.q=des&suggest.dictionary=titleSuggester` |
| 8.3 | Spellcheck 'algoritm' | `/select?q=algoritm&spellcheck=true&spellcheck.collate=true` |

## 9. Joins / streaming (advanced)

| # | Description | URL |
| --- | --- | --- |
| 9.1 | Function score boost newer books | `/select?q=*:*&boost=recip(ms(NOW,pub_date),3.16e-11,1,1)` |
| 9.2 | Streaming expression — top 5 by rating | `/stream?expr=top(n=5,sort="rating desc",search(books,q="*:*",fl="id,title,rating",sort="rating desc"))` |
