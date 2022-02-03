# 5Go

Code is [here](./genji_0day.py).

The service contains only one vuln, which is a 0-day in the latest release of GenjiDB.

While comparing the search query with the tree index content
[here](https://github.com/genjidb/genji/blob/f1db356ced2ce5233582a7443342cdd213e81677/internal/tree/tree.go#L174)
Genji truncates the **index content**, not the search query, therefore any prefix of a desired string will match. The
difficulty is in the encoding; database encodes all values in a binary order-preserving way, which is a custom base64
encoding for strings. To be a correct prefix in base64 encoding, a string's length must be a multiple of 3, otherwise
it's padded.

The documents' ID is created as `<name>-<random uuid>`, so the name the user passes is the prefix of the document's ID.
Checker uses names of length 10, therefore the exploit is just getting the document by the first 6 or 9 characters of
the name from attack data.
