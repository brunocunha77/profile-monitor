"""Resolve um perfil publico usando a sessao persistida do coletor."""
from __future__ import annotations
import json
import os
import sys
from pathlib import Path
from instagrapi import Client

def main() -> None:
    payload = json.loads(sys.stdin.read() or "{}")
    handle = str(payload.get("handle") or "").strip().lstrip("@").lower()
    username = str(payload.get("username") or "").strip()
    password = str(payload.get("password") or "")
    session_path = Path(str(payload.get("session_path") or ""))
    if not handle or not session_path.exists():
        raise RuntimeError("Conta coletora desconectada ou perfil invalido.")
    client = Client()
    proxy_url = os.getenv("COLLECTOR_PROXY_URL", "").strip()
    if proxy_url:
        client.set_proxy(proxy_url)
    client.set_country("BR"); client.set_country_code(55); client.set_locale("pt_BR"); client.set_timezone_name("America/Sao_Paulo"); client.set_timezone_offset(-10800)
    client.load_settings(session_path, override_app_version=True)
    if username and password:
        client.login(username, password)
    else:
        settings = client.get_settings()
        session_id = (settings.get("authorization_data") or {}).get("sessionid") or (settings.get("cookies") or {}).get("sessionid")
        if not session_id:
            raise RuntimeError("A sessao do Instagram expirou.")
        client.login_by_sessionid(session_id)
    client.dump_settings(session_path)
    user_id = client.user_id_from_username(handle)
    user = client.user_info_v1(user_id)
    print(json.dumps({"external_id": str(user.pk), "handle": user.username, "full_name": user.full_name, "biography": user.biography, "follower_count": user.follower_count, "media_count": user.media_count, "profile_picture_url": str(user.profile_pic_url or "") or None, "is_private": user.is_private, "is_verified": user.is_verified}, ensure_ascii=True))

if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True))
        raise SystemExit(1)
