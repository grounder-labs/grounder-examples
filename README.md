# Grounder (grounder.net) client examples

## Connect an MCP client

Use `https://api.grounder.net/mcp` for the full custom connector, or
`https://api.grounder.net/mcp/directory` for the directory-safe profile. Both use
account sign-in; the directory profile offers search by query (plus a location or time zone the user stated), provider listing
and account information, without the user's prompt and chat ids that the full connector asks for and without `report_sources`.

Client-specific setup: https://grounder.net/docs/mcp.
Privacy and retention: https://grounder.net/privacy and
https://grounder.net/docs/data-use. Search records and backups are kept indefinitely.

## Authorize native HTTP search

An MCP sign-in does not grant HTTP access; this asks for a search grant. A search key from the account's Search keys
page (https://grounder.net/account/keys) is the other way in. There is no need to supply provider credentials.

Run on your own computer, with Python 3:

```sh
python oauth-login.py --output ./grounder-token.private.json
```

Sign in in the browser and allow the named client. The script registers a public
client, uses PKCE S256 and a local one-shot loopback callback, checks the returned
state and saves tokens with mode 0600. It never prints tokens or runs a search.
Keep the token file out of Git and backups intended for public distribution.
The access token lasts one hour; refresh tokens rotate on use.

## Native search

This is a real, recorded user search, not a wiring check or benchmark:

```python
import json
import urllib.request

with open("grounder-token.private.json") as token_file:
    token = json.load(token_file)["access_token"]

request = urllib.request.Request(
    "https://api.grounder.net/v1/search",
    json.dumps({"query": "offshore wind capacity", "top_k": 5}).encode(),
    {"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
)
with urllib.request.urlopen(request, timeout=60) as response:
    result = json.load(response)
for hit in result["results"]:
    print(hit["rank"], hit["title"], hit["url"], hit["provenance"]["found_by"])
```

## Existing Tavily and Brave clients

Keep the provider's request format and replace its endpoint and credential:

- Tavily: `https://api.grounder.net/compat/tavily/search`. Send the search-scoped
  access token as a Bearer header or in the legacy `api_key` field.
- Brave: `https://api.grounder.net/compat/brave/res/v1/web/search`. Send the
  search-scoped access token as `X-Subscription-Token` or a Bearer header.

These are compatibility shims, not full provider API replicas. See
https://grounder.net/docs/drop-in for ignored options. A refresh token is never an
access token. Request a new search grant rather than reusing an MCP-only token.

## Refresh

POST a form to `https://api.grounder.net/oauth/token` with `grant_type=refresh_token`,
the saved `client_id`, the current `refresh_token`, `scope=search` and
`resource=https://api.grounder.net/v1/search`. Save both returned tokens privately
before reusing them: the previous refresh token is consumed. Never commit them.

## Public files

Machine-readable docs are at
https://grounder.net/llms.txt, https://grounder.net/llms-full.txt,
https://grounder.net/docs.md and https://grounder.net/openapi.json.
The official MCP Registry listing is `net.grounder/search`.

## License

Apache License 2.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). Copyright 2026
Grounder Labs, Inc. The license grants no rights to the Grounder name or marks.
