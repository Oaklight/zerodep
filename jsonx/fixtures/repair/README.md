# Repair fixtures

Two request bodies that were damaged in transit, taken from the gateway's
`body_parse` error dumps. They keep the damage exactly as received; only the
payload is gone.

Before being stored, every character except the JSON punctuation
(`{}[]",:`), spaces, tabs and newlines was replaced with `x`, and runs of
`x` were capped at 64. Keys, strings and numbers are therefore placeholders,
while the positions and the shape of the damage are unchanged: one body has
spliced tokens and missing delimiters, the other an invalid escape.

`test_jsonx_repair.py` repairs both and checks the result is a dict with the
two top-level keys the documents had, and that `loads(..., repair=True)`
returns the same value.
