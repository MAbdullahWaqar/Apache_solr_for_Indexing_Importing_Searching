#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# sample_queries.sh
#
# A guided tour of representative Solr queries against the books core.
# Each block prints the URL, hits Solr, and pretty-prints the JSON.
# -----------------------------------------------------------------------------
set -euo pipefail

SOLR_PORT="${SOLR_PORT:-8983}"
CORE_NAME="${CORE_NAME:-books}"
BASE="http://localhost:${SOLR_PORT}/solr/${CORE_NAME}"

run() {
  local title="$1"; shift
  local url="$1"; shift
  echo
  echo "===================================================================="
  echo "  ${title}"
  echo "  ${url}"
  echo "===================================================================="
  curl -fsS "${url}" | python3 -m json.tool | head -60
}

# 1. Match all (sanity check)
run "1. Match all - first page" \
    "${BASE}/select?q=*:*&rows=5&fl=id,title,author,rating"

# 2. Full-text search with edismax
run "2. Full-text 'distributed systems' across boosted fields" \
    "${BASE}/select?q=distributed%20systems&rows=5&fl=id,title,author,score"

# 3. Phrase search
run "3. Phrase search %22machine%20learning%22" \
    "${BASE}/select?q=%22machine%20learning%22&rows=5&fl=id,title"

# 4. Field-targeted search
run "4. Author field 'Tolkien'" \
    "${BASE}/select?q=author:Tolkien&fl=id,title,author"

# 5. Range filter
run "5. Books with rating >= 4.5 sorted by rating desc" \
    "${BASE}/select?q=*:*&fq=rating:%5B4.5%20TO%20*%5D&sort=rating%20desc&rows=5&fl=id,title,rating"

# 6. Date range
run "6. Books published in the 2010s" \
    "${BASE}/select?q=*:*&fq=pub_date:%5B2010-01-01T00:00:00Z%20TO%202019-12-31T23:59:59Z%5D&rows=5&fl=id,title,pub_date"

# 7. Faceted search
run "7. Top-10 genres facet" \
    "${BASE}/select?q=*:*&rows=0&facet=true&facet.field=genres&facet.limit=10"

# 8. Multi-facet
run "8. Genres + languages facets, in stock only" \
    "${BASE}/select?q=*:*&fq=in_stock:true&rows=0&facet=true&facet.field=genres&facet.field=language"

# 9. Range facet by decade
run "9. Decade range facet (1900-2030 / 10y)" \
    "${BASE}/select?q=*:*&rows=0&facet=true&facet.range=year&facet.range.start=1900&facet.range.end=2030&facet.range.gap=10"

# 10. Filtering + boosting
run "10. Programming books boosted by rating, top 5" \
    "${BASE}/select?q=programming&fq=genres:Programming&sort=rating%20desc&rows=5&fl=id,title,rating"

# 11. Highlighting
run "11. Highlight 'algorithms' in description" \
    "${BASE}/select?q=description:algorithms&hl=true&hl.method=original&hl.fl=description&hl.simple.pre=%3Cmark%3E&hl.simple.post=%3C/mark%3E&rows=3&fl=id,title,description"

# 12. Pagination (page 3, 10 per page)
run "12. Pagination - start=20, rows=10" \
    "${BASE}/select?q=*:*&start=20&rows=10&fl=id,title"

# 13. Did you mean (spellcheck)
run "13. Spellcheck for 'algoritm'" \
    "${BASE}/select?q=algoritm&spellcheck=true&spellcheck.collate=true&rows=0"

# 14. Autocomplete fallback using the indexed edge-ngram field title_ac.
# The Flask UI also uses this fallback if a Solr /suggest handler is not present.
run "14. Autocomplete prefix 'des' via title_ac" \
    "${BASE}/select?q=title_ac:des*&rows=5&fl=id,title,author"

# 15. JSON Facet API
run "15. Stats facet - average rating per language" \
    "${BASE}/select?q=*:*&rows=0&json.facet=%7B%22by_lang%22%3A%7B%22type%22%3A%22terms%22%2C%22field%22%3A%22language%22%2C%22limit%22%3A10%2C%22facet%22%3A%7B%22avg_rating%22%3A%22avg(rating)%22%7D%7D%7D"

echo
echo "Done."
