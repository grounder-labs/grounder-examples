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


def request_body(args):
    """The search's options as POST /v1/search takes them."""
    # What the person typed here is the user's own message, so it is sent as such
    body = {"query": args.query, "top_k": args.top_k,
            "context": {"prompt_content": args.query}}
    if args.days:
        body["filters"] = {"recency": {"mode": "rolling", "days": args.days}}
    if args.mode:
        body["mode"] = args.mode
    if args.url or args.site:
        body.setdefault("mode", "grounder-direct")
    if args.url:
        body["urls"] = args.url
    if args.site:
        body["site"] = args.site
    if args.user_agent:
        body["user_agent"] = args.user_agent
    if args.format:
        body["format"] = args.format
    return body


def search(body, token):
    request = urllib.request.Request(
        ENDPOINT,
        json.dumps(body).encode(),
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
    parser.add_argument("--days", type=int,
                        help="only results published within this many days")
    parser.add_argument("--mode", choices=("grounder-provider", "grounder-direct"))
    parser.add_argument("--url", action="append",
                        help="a page to read by address, up to five")
    parser.add_argument("--site", help="find and read a page on this host")
    parser.add_argument("--user-agent", help="your browser's user agent for hosted reads")
    parser.add_argument("--format", choices=("summary", "full-page", "highlights"))
    parser.add_argument("--token-file", default="grounder-token.private.json",
                        help="the token oauth-login.py saved, used when "
                             "GROUNDER_KEY is not set")
    args = parser.parse_args()
    result = search(request_body(args), credential(args.token_file))
    for hit in result["results"]:
        print(hit["rank"], hit["title"], hit["url"],
              hit["provenance"]["found_by"],
              hit["provenance"].get("licensed_basis", ""))
    if result.get("no_topic"):
        print("No topic fits this question.")
    for topic in result["topics"]:
        print(topic["name"], topic["source"], topic["server"], topic["status"])
    usage = result["usage"]
    if usage.get("free_search"):
        left = usage.get("free_searches_left")
        print("cost: free search" + (f", {left} left today" if left is not None else ""))
    else:
        print("cost:", usage["cost_usd"], "USD")
    print("for your model:", result.get("citation_request", ""))


if __name__ == "__main__":
    main()
