from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from instagrapi import Client


def main():
    payload = json.load(sys.stdin)
    target = Path(payload['session_path']).resolve()
    target.parent.mkdir(parents=True, exist_ok=True)

    client = Client()
    proxy_url = os.getenv("INSTAGRAM_PROXY_URL", "").strip()
    if proxy_url:
        client.set_proxy(proxy_url)
    client.delay_range = [2, 5]
    client.set_country('BR')
    client.set_country_code(55)
    client.set_locale('pt_BR')
    client.set_timezone_name('America/Sao_Paulo')
    client.set_timezone_offset(-10800)
    if target.exists():
        client.load_settings(target, override_app_version=True)
    else:
        # Persiste UUIDs antes do primeiro login; novas tentativas reutilizam o
        # mesmo dispositivo em vez de parecerem aparelhos diferentes.
        client.dump_settings(target)

    code = payload.get('verification_code') or None
    try:
        logged_in = client.login(
            str(payload['username']),
            str(payload['password']),
            verification_code=code,
        )
        if not logged_in:
            raise RuntimeError('O Instagram não confirmou a sessão.')
        client.account_info()
    finally:
        client.dump_settings(target)

    print(json.dumps({'connected': True, 'username': payload['username']}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        print(json.dumps({'connected': False, 'error': str(exc)}))
        raise SystemExit(2)
