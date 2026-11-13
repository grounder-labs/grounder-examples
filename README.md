# Grounder (grounder.net) client examples

Grounder is one HTTP API and one MCP server in front of many web search providers and live-data APIs. Every way in
reaches the same account: the same features, providers and routing settings, under the same free searches and credit.
Pick the one that fits the client:

| Way in | Credential | Fits |
|---|---|---|
| [HTTP API with a search key](#search-keys) | `Authorization: Bearer <key>` | Scripts, servers, CI and gateways |
| [HTTP API with a sign-in](#sign-in-instead-of-a-key) | A `search`-scoped OAuth access token | An app whose users sign in, with no key to copy |
| [MCP](#mcp) | A sign-in in the client, or a search key | Agents and chat apps |
| [Tavily and Brave drop-ins](#existing-tavily-and-brave-clients) | A search key or an access token | Code already written for Tavily or Brave |

Neither credential needs provider keys: Grounder holds those. Every search is recorded under your account; see
https://grounder.net/privacy and https://grounder.net/docs/data-use. Search records and backups are kept indefinitely.

## Search keys

Make a key under [Search keys](https://grounder.net/account/keys) on your account. Keep it in an environment variable,
never in code or Git:

```sh
export GROUNDER_KEY='<your key>'
```

There are two kinds:

- A full key searches, and also reads the account from a terminal or agent with `GET /v1/account`.
- A search-only key searches, lists features and providers, and calls the drop-in
  endpoints. Everything else answers `403 forbidden`. Use one for a key that is shared, such as one a gateway hands to
  several people. Choose "Search only" when you make it, or see https://grounder.net/docs/api for making one through the API.

## Search

`search.py` runs one search with the key in `GROUNDER_KEY`. When no key is set, it uses the token `oauth-login.py` saved.
Run on your own computer, with Python 3 and nothing to install:

```sh
python search.py "offshore wind capacity"
```

It prints each result's rank, title, address, the provider that found it and why it is licensed, then the providers
called, the features used, the cost and the sentence to give your model so it cites what it uses. `--days`, `--domain`,
`--feature`, `--url` and `--provider` set the search's other options. This is a real search, recorded and
counted under your account, not a wiring check or benchmark. The same request with curl:

```sh
curl https://api.grounder.net/v1/search \
  -H "Authorization: Bearer $GROUNDER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query": "offshore wind capacity", "top_k": 5}'
```

The request and response fields are at https://grounder.net/docs/api/search.

## Sign in instead of a key

An app that should not hold a key can ask its user to sign in and allow it to search. An MCP sign-in does not grant
HTTP access; this asks for a search grant. Run on your own computer, with Python 3:

```sh
python oauth-login.py --output ./grounder-token.private.json
```

Sign in in the browser and allow the named client. The script registers a public
client, uses PKCE S256 and a local one-shot loopback callback, checks the returned
state and saves tokens with mode 0600. It never prints tokens or runs a search.
Keep the token file out of Git and backups intended for public distribution.
`search.py` reads it when `GROUNDER_KEY` is not set.

The access token lasts one hour and works on the search addresses only: `POST /v1/search`,
`POST /v1/search/{request_id}/cited` and the drop-in endpoints. Every other address that checks who you are takes a
search key.

### Refresh

Refresh tokens rotate on use. POST a form to `https://api.grounder.net/oauth/token` with `grant_type=refresh_token`,
the saved `client_id`, the current `refresh_token`, `scope=search` and
`resource=https://api.grounder.net/v1/search`. Save both returned tokens privately
before reusing them: the previous refresh token is consumed. Never commit them.

## MCP

Use `https://api.grounder.net/mcp` for the full custom connector, or
`https://api.grounder.net/mcp/directory` for the directory-safe profile. The directory profile offers search by query
(plus a location or time zone the user stated), provider listing and account information, without the user's prompt
and chat ids that the full connector asks for and without `report_sources`.

Both take either credential. Sign in when the client opens Grounder's screen, or, in a client that sends headers, send
a search key as `Authorization: Bearer <key>` instead. Over MCP, a search-only key lists `search` and `list_providers`
alone.

The full connector's tools are `search`, `user_info` and `list_providers`. The same lists are public over REST: `GET /v1/features` and `GET /v1/providers`.

Client-specific setup: https://grounder.net/docs/mcp.

## Existing Tavily and Brave clients

Keep the provider's request format and replace its endpoint and credential:

- Tavily: `https://api.grounder.net/compat/tavily/search`. Send a search key or a
  search-scoped access token as a Bearer header or in the legacy `api_key` field.
- Brave: `https://api.grounder.net/compat/brave/res/v1/web/search`. Send a search key
  or a search-scoped access token as `X-Subscription-Token` or a Bearer header.

These are compatibility shims, not full provider API replicas. See
https://grounder.net/docs/drop-in for ignored options. A refresh token is never an
access token. Request a new search grant rather than reusing an MCP-only token.

## Public files

Machine-readable docs are at
https://grounder.net/llms.txt, https://grounder.net/llms-full.txt,
https://grounder.net/docs.md and https://grounder.net/openapi.json.
The official MCP Registry listing is `net.grounder/search`.

## License

Apache License 2.0: see [LICENSE](LICENSE) and [NOTICE](NOTICE). Copyright 2026
Grounder Labs, Inc. The license grants no rights to the Grounder name or marks.
