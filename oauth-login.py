#!/usr/bin/env python3
# Copyright 2026 Grounder Labs, Inc.
# SPDX-License-Identifier: Apache-2.0

"""Authorize HTTP search with PKCE and save a private, short-lived token file."""

import argparse
import base64
import hashlib
import json
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ORIGIN = "https://api.grounder.net"
RESOURCE = f"{ORIGIN}/v1/search"


def post(endpoint, payload, form=False):
    data = urllib.parse.urlencode(payload) if form else json.dumps(payload)
    content_type = ("application/x-www-form-urlencoded" if form
                    else "application/json")
    request = urllib.request.Request(f"{ORIGIN}{endpoint}", data.encode(),
                                     {"Content-Type": content_type})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError(f"{endpoint} returned HTTP {error.code}") from None


def callback_handler(state, callback):
    """A handler that records the one request that is the sign-in's return and answers every other with 404.

    The return address is on the person's own machine, so more than the browser's redirect can reach it: a favicon request,
    a port scan, a page in another tab, a socket opened and never used. None of them is the sign-in, and none may end the wait.
    """

    class Handler(BaseHTTPRequestHandler):
        timeout = 5  # a connection that sends nothing is dropped, not waited for

        def log_message(self, *_args):
            pass

        def reply(self, status, text):
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(text.encode())

        def do_GET(self):
            parsed = urllib.parse.urlparse(self.path)
            values = urllib.parse.parse_qs(parsed.query)
            if parsed.path != "/callback" or values.get("state") != [state]:
                return self.reply(404, "Not found")
            if len(values.get("code", [])) == 1:
                callback["code"] = values["code"][0]
                return self.reply(200, "Return to your terminal. You may close this tab.")
            callback["error"] = f"Authorization denied: {values.get('error', ['no code'])[0]}"
            self.reply(400, "Authorization denied. Return to your terminal.")

    return Handler


def wait_for_callback(server, callback, seconds=180):
    """Serve requests until the sign-in's return arrives or the time is up."""
    deadline = time.monotonic() + seconds
    while not callback and time.monotonic() < deadline:
        server.timeout = max(0.1, deadline - time.monotonic())
        server.handle_request()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()
    if args.output.exists():
        parser.error("output already exists; choose a new private file")
    if not args.output.parent.is_dir():
        parser.error("output directory must already exist")
    verifier = secrets.token_urlsafe(48)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(
        verifier.encode()).digest()).decode().rstrip("=")
    state = secrets.token_urlsafe(32)
    callback = {}

    with HTTPServer(("127.0.0.1", 0), callback_handler(state, callback)) as server:
        redirect_uri = f"http://127.0.0.1:{server.server_port}/callback"
        client = post("/oauth/register", {"redirect_uris": [redirect_uri],
                      "client_name": "Grounder HTTP search",
                      "token_endpoint_auth_method": "none"})
        params = urllib.parse.urlencode({
            "client_id": client["client_id"], "redirect_uri": redirect_uri,
            "response_type": "code", "code_challenge": challenge,
            "code_challenge_method": "S256", "state": state,
            "resource": RESOURCE, "scope": "search",
        })
        url = f"{ORIGIN}/oauth/authorize?{params}"
        print(f"Sign in and allow HTTP search:\n{url}")
        if not args.no_browser:
            webbrowser.open(url)
        wait_for_callback(server, callback)
    if "code" not in callback:
        raise SystemExit(callback.get("error", "Authorization timed out"))
    tokens = post("/oauth/token", {
        "grant_type": "authorization_code", "client_id": client["client_id"],
        "code": callback["code"], "code_verifier": verifier,
        "redirect_uri": redirect_uri, "resource": RESOURCE,
    }, form=True)
    if tokens.get("scope") != "search":
        raise SystemExit("Server did not grant the requested search scope")
    tokens.update({"client_id": client["client_id"], "resource": RESOURCE})
    descriptor = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        json.dump(tokens, output, indent=2)
        output.write("\n")
    print(f"Saved private tokens to {args.output}. No search was run.")


if __name__ == "__main__":
    main()
