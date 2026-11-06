"""
Sign in with ChatGPT for LLM_PROVIDER=chatgpt.

  login   Run on your own computer: opens the browser, writes a 0600 credential file
  import  Run on the server: reads that file from stdin into the database
  status  Show the session (no secrets) and the models this account may use

Run from backend/: python -m scripts.chatgpt_login <command>
"""

import argparse
import json
import os
import secrets
import sys
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qsl, urlparse

from app.services import chatgpt_service as chatgpt

CALLBACK_PATH = "/auth/callback"
LOGIN_TIMEOUT_SECONDS = 300


def wait_for_callback(server: HTTPServer) -> dict:
    received = {}

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            url = urlparse(self.path)
            if url.path != CALLBACK_PATH:
                self.send_error(404)
                return
            received.update(parse_qsl(url.query))
            self.send_response(200)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write("Fertig, du kannst dieses Fenster schließen.".encode())

        def log_message(self, *args):
            pass  # the query string holds the authorization code

    server.RequestHandlerClass = Handler
    server.timeout = LOGIN_TIMEOUT_SECONDS
    while not received:
        server.handle_request()
        if not received and server.timed_out:
            sys.exit("Keine Antwort vom Browser, Anmeldung abgebrochen.")
    return received


class CallbackServer(HTTPServer):
    timed_out = False

    def handle_timeout(self):
        self.timed_out = True


def login(args) -> None:
    out = Path(args.out).expanduser()
    server = CallbackServer(("127.0.0.1", args.port), BaseHTTPRequestHandler)
    redirect_uri = f"http://127.0.0.1:{args.port}{CALLBACK_PATH}"
    state, nonce = secrets.token_urlsafe(32), secrets.token_urlsafe(32)
    verifier, challenge = chatgpt.new_pkce()
    url = chatgpt.build_authorize_url(
        redirect_uri, state, nonce, challenge, args.host_id or chatgpt.new_host_id(), args.client_id
    )

    print(f"Browser öffnet sich. Falls nicht, diese URL aufrufen:\n{url}\n")
    webbrowser.open(url)
    code, client_id = chatgpt.parse_callback(wait_for_callback(server), state, args.client_id)

    tokens = chatgpt.exchange_code(client_id, code, verifier, redirect_uri)
    claims = chatgpt.verify_id_token(tokens["id_token"], client_id, nonce)
    credential = chatgpt.build_credential(tokens, claims, client_id)

    fd = os.open(out, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w") as f:
        json.dump(credential, f)
    print(f"Angemeldet als {credential['email']}. Credentials: {out}")
    print("Nach dem Import diese Datei löschen: Das Refresh-Token rotiert, der Server übernimmt es.")


def import_credential(_args) -> None:
    stored = chatgpt.import_credential(json.load(sys.stdin))
    print(f"Importiert für {stored.get('email')}, Host-ID {stored['ext_agent_host_id']}")


def status(_args) -> None:
    print(json.dumps(chatgpt.session_info(), indent=2))
    print("Modelle für LLM_MODEL:")
    for model in chatgpt.list_models():
        print(f"  {model['slug']}  ({model['display_name']})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    commands = parser.add_subparsers(required=True)

    login_parser = commands.add_parser("login")
    login_parser.add_argument("--out", required=True, help="Pfad der Credential-Datei")
    login_parser.add_argument("--port", type=int, default=1455)
    login_parser.add_argument("--client-id", help="Bei erneutem Login: client_id aus `status`")
    login_parser.add_argument("--host-id", help="Bei erneutem Login: ext_agent_host_id aus `status`")
    login_parser.set_defaults(run=login)

    commands.add_parser("import").set_defaults(run=import_credential)
    commands.add_parser("status").set_defaults(run=status)

    args = parser.parse_args()
    args.run(args)


if __name__ == "__main__":
    main()
