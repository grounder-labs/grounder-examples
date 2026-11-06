#!/usr/bin/env python3
# Copyright 2026 Grounder Labs, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Run one Grounder search with a search key, or with the token oauth-login.py saved."""

import argparse
import json
import os
import urllib.error
import urllib.request

ENDPOINT = "https://api.grounder.net/v1/search"


def credential(token_file):
    """The search key in GROUNDER_KEY, else the access token oauth-login.py saved."""
    key = os.environ.get("GROUNDER_KEY", "").strip()
    if key:
        return key
    try:
        with open(token_file) as handle:
            return json.load(handle)["access_token"]
    except FileNotFoundError:
        raise SystemExit("Set GROUNDER_KEY to a search key, "
                         "or sign in with oauth-login.py first.") from None


def search(query, top_k, token):
    request = urllib.request.Request(
        ENDPOINT,
        json.dumps({"query": query, "top_k": top_k}).encode(),
        {"Authorization": f"Bearer {token}",
         "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        try:
            # Every error is {"error": {"code": ..., "message": ...}}
            detail = json.load(error)["error"]
            reason = f"{detail['code']}: {detail['message']}"
        except (ValueError, KeyError, TypeError):
            reason = "no error body"
        raise SystemExit(f"Grounder answered HTTP {error.code}, "
                         f"{reason}") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="what to search for")
    parser.add_argument("--top-k", type=int, default=5,
                        help="how many results (1-100, default 5)")
    parser.add_argument("--token-file", default="grounder-token.private.json",
                        help="the token oauth-login.py saved, used when "
                             "GROUNDER_KEY is not set")
    args = parser.parse_args()
    result = search(args.query, args.top_k, credential(args.token_file))
    for hit in result["results"]:
        print(hit["rank"], hit["title"], hit["url"],
              hit["provenance"]["found_by"])


if __name__ == "__main__":
    main()
