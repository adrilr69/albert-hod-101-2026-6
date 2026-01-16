# Assignment — Levenshtein Distance (Edit Distance)

## Goal
Implement the Levenshtein(s, t) function that returns the edit distance between two strings s and t.

## Batch computation
- Apply the function to all pairs in the provided dataset.
- Store the result in a new column `distance`.
- Export the results to a CSV.

## Complexity analysis
- Measure runtime for pairs of increasing length (e.g. 100, 500, 1000, 2000).
- Plot time vs. product of lengths (n*m).
- Fit a regression to confirm the expected linear relationship with (n*m).

## Files
- `levenshtein.py` — implementation + batch CSV output
- `complexity_analysis.py` — timings + plot + regression
- `outputs/` — generated CSV and figures (if included)

