# Frontend — BookFinder UI

A zero-dependency, single-page UI built with semantic HTML, modern CSS, and
vanilla JavaScript. Talks to the Flask backend at `/api/*`.

## Highlights

- **Real-time search** with 220 ms debounce
- **Autocomplete** suggestions (Solr Suggester or fallback prefix query)
- **Faceted navigation**: genres, languages, publishers, tags, decade range
- **Filters**: in-stock, minimum rating, year range
- **Sort**: relevance, rating, year, price, title
- **Highlighting** of matched terms via `<mark>` tags
- **Pagination** with elision (`1 ... 4 5 6 ... 21`)
- **Detail modal** showing the full document
- **Responsive layout** — sidebar collapses below `960px`
- **Health pill** that polls `/api/health` every 30 seconds
- **Light & dark themes** via `prefers-color-scheme`

## Running

If the Flask backend is up the easiest path is to open
`http://localhost:5000/` — Flask serves these static files for you.

If you prefer a separate dev server:

```bash
python -m http.server 8000 --directory frontend
# Visit http://localhost:8000
```

The script auto-detects whether Flask is on the same origin or on
`http://localhost:5000` and points API calls accordingly.
