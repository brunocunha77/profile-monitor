"""Coletor incremental de sinais públicos do Instagram para o Sales OS.

A primeira execução de cada alvo cria baseline e não emite oportunidades.
Execuções seguintes enviam apenas relações/interações ainda não conhecidas.
"""
from __future__ import annotations

import json
import logging
import os
import sqlite3
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import requests
from dotenv import load_dotenv
from instagrapi import Client

load_dotenv()
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("sales-os-instagram")

WEBHOOK_URL = os.environ["SALES_OS_SIGNAL_WEBHOOK_URL"].rstrip("/")
USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
INTERVAL = int(os.getenv("COLLECT_INTERVAL_SECONDS", "900"))
FOLLOWERS_WINDOW = int(os.getenv("FOLLOWERS_WINDOW", "80"))
MEDIA_LIMIT = int(os.getenv("RECENT_MEDIA_LIMIT", "4"))
LIKERS_LIMIT = int(os.getenv("LIKERS_PER_MEDIA", "30"))
PROFILE_ENRICHMENTS_PER_RUN = int(os.getenv("PROFILE_ENRICHMENTS_PER_RUN", "12"))
STATE_DIR = Path(os.getenv("COLLECTOR_STATE_DIR", "./state")).resolve()
RUN_ONCE = os.getenv("RUN_ONCE", "false").lower() == "true"
PROXY_URL = os.getenv("INSTAGRAM_PROXY_URL", "").strip()
TARGET_IDS = {int(value) for value in os.getenv("COLLECTOR_TARGET_IDS", "").split(",") if value.strip().isdigit()}
STATE_DIR.mkdir(parents=True, exist_ok=True)

@dataclass
class Target:
    id: int
    handle: str
    external_id: str | None

class State:
    def __init__(self, path: Path):
        self.db = sqlite3.connect(path)
        self.db.execute("create table if not exists known_events (target_id integer, event_key text, first_seen text, primary key(target_id,event_key))")
        self.db.execute("create table if not exists baselines (target_id integer primary key, completed_at text)")
        self.db.commit()

    def is_baselined(self, target_id: int) -> bool:
        return self.db.execute("select 1 from baselines where target_id=?", (target_id,)).fetchone() is not None

    def remember(self, target_id: int, event_key: str) -> bool:
        cursor = self.db.execute("insert or ignore into known_events(target_id,event_key,first_seen) values(?,?,?)", (target_id, event_key, now()))
        self.db.commit()
        return cursor.rowcount == 1

    def finish_baseline(self, target_id: int):
        self.db.execute("insert or replace into baselines(target_id,completed_at) values(?,?)", (target_id, now()))
        self.db.commit()

def now() -> str:
    return datetime.now(timezone.utc).isoformat()

def value(obj: Any, name: str, default: Any = None) -> Any:
    return getattr(obj, name, default)

def actor_payload(user: Any) -> dict[str, Any]:
    pk = str(value(user, "pk", value(user, "id", "")))
    username = str(value(user, "username", ""))
    return {
        "id": pk,
        "handle": username,
        "name": value(user, "full_name"),
        "url": f"https://instagram.com/{username}" if username else None,
        "followers": value(user, "follower_count"),
        "posts": value(user, "media_count"),
        "bio": value(user, "biography"),
        "is_private": value(user, "is_private"),
        "profile_picture_url": str(value(user, "profile_pic_url", "") or "") or None,
    }

PROFILE_CACHE: dict[str, dict[str, Any]] = {}
PROFILE_ENRICHMENTS = 0

def enriched_actor(client: Client, user: Any) -> dict[str, Any]:
    global PROFILE_ENRICHMENTS
    actor = actor_payload(user)
    actor_id = actor["id"]
    if not actor_id:
        return actor
    if actor_id not in PROFILE_CACHE:
        if PROFILE_ENRICHMENTS >= PROFILE_ENRICHMENTS_PER_RUN:
            return actor
        PROFILE_ENRICHMENTS += 1
        try:
            PROFILE_CACHE[actor_id] = actor_payload(client.user_info_v1(int(actor_id)))
        except Exception as exc:
            LOG.warning("Perfil @%s nao pode ser enriquecido: %s", actor.get("handle"), type(exc).__name__)
            PROFILE_CACHE[actor_id] = actor
    return PROFILE_CACHE[actor_id]
def fetch_targets() -> list[Target]:
    response = requests.get(f"{WEBHOOK_URL}/targets", timeout=30)
    response.raise_for_status()
    targets = [Target(int(row["id"]), str(row["handle"]), row.get("external_id")) for row in response.json().get("targets", [])]
    return [target for target in targets if not TARGET_IDS or target.id in TARGET_IDS]

def report(target: Target, status: str, error: str | None = None, external_id: str | None = None, profile: dict[str, Any] | None = None):
    response = requests.patch(f"{WEBHOOK_URL}/targets/{target.id}/status", json={"status": status, "error": error, "external_id": external_id, "profile": profile}, timeout=30)
    response.raise_for_status()

def report_connection(status: str, error: str | None = None, pause_hours: int = 0, manual_run: str | None = None):
    """Tell the API to stop scheduling this account after a security checkpoint."""
    response = requests.patch(
        f"{WEBHOOK_URL}/connection",
        json={"status": status, "error": error, "pause_hours": pause_hours, "manual_run": manual_run},
        timeout=30,
    )
    response.raise_for_status()

def is_security_checkpoint(exc: Exception) -> bool:
    text = f"{type(exc).__name__}: {exc}".lower()
    return any(marker in text for marker in ("challenge", "checkpoint", "feedback_required", "login_required", "too many redirects"))
def send(signals: list[dict[str, Any]]):
    if not signals:
        return
    for start in range(0, len(signals), 200):
        response = requests.post(WEBHOOK_URL, json={"source": "instagram", "signals": signals[start:start + 200]}, timeout=60)
        response.raise_for_status()
        LOG.info("Lote enviado: %s", response.json())

def login() -> Client:
    client = Client()
    # Keep login and polling traffic on the account's stable egress IP.
    if PROXY_URL:
        client.set_proxy(PROXY_URL)
    client.set_country('BR')
    client.set_country_code(55)
    client.set_locale('pt_BR')
    client.set_timezone_name('America/Sao_Paulo')
    client.set_timezone_offset(-10800)
    session_file = STATE_DIR / "session.json"
    if session_file.exists():
        try:
            settings = client.load_settings(session_file, override_app_version=True)
            if PROXY_URL:
                client.set_proxy(PROXY_URL)
            session_id = (settings.get("authorization_data") or {}).get("sessionid") or (settings.get("cookies") or {}).get("sessionid")
            if session_id:
                client.login_by_sessionid(session_id)
                client.dump_settings(session_file)
                LOG.info("Sessão existente validada para @%s.", client.username)
                return client
        except Exception as exc:
            LOG.warning("Sessão salva recusada (%s); renovando pela conexão segura.", type(exc).__name__)
    if not USERNAME or not PASSWORD:
        raise RuntimeError("Sessão ausente e credenciais de fallback não configuradas.")
    verification_code = None
    totp_seed = os.getenv("INSTAGRAM_TOTP_SEED")
    if totp_seed:
        verification_code = client.totp_generate_code(totp_seed)
    logged_in = client.login(USERNAME, PASSWORD, verification_code=verification_code)
    if not logged_in:
        raise RuntimeError("O Instagram não confirmou a sessão.")
    client.account_info()
    client.dump_settings(session_file)
    LOG.info("Sessão renovada para @%s.", client.username)
    return client

def collect_followers(client: Client, target: Target, target_pk: str, state: State, emit: bool) -> list[dict[str, Any]]:
    signals = []
    for user in client.iter_user_followers_v1(target_pk, amount=FOLLOWERS_WINDOW, page_size=min(200, FOLLOWERS_WINDOW), order="date_followed_latest"):
        actor = actor_payload(user)
        if not actor["id"] or not actor["handle"]:
            continue
        key = f"follow:{actor['id']}"
        if state.remember(target.id, key) and emit:
            actor = enriched_actor(client, user)
            signals.append({"external_id": f"ig:{target_pk}:{key}", "signal_type": "follow_observed", "actor": actor, "target": {"handle": target.handle, "url": f"https://instagram.com/{target.handle}"}, "occurred_at": now()})
    return signals

def collect_engagement(client: Client, target: Target, target_pk: str, state: State, emit: bool) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    medias = client.user_medias_v1(target_pk, amount=MEDIA_LIMIT)
    for media in medias:
        media_pk = str(value(media, "pk", ""))
        if not media_pk:
            continue
        try:
            comments = client.media_comments(media_pk, amount=0)
            for comment in comments:
                user = value(comment, "user")
                actor = actor_payload(user)
                comment_pk = str(value(comment, "pk", ""))
                key = f"comment:{comment_pk}"
                if actor["id"] and comment_pk and state.remember(target.id, key) and emit:
                    created = value(comment, "created_at_utc")
                    actor = enriched_actor(client, user)
                    signals.append({"external_id": f"ig:{target_pk}:{key}", "signal_type": "comment", "actor": actor, "target": {"handle": target.handle, "url": f"https://instagram.com/{target.handle}"}, "content": str(value(comment, "text", "")), "occurred_at": created.isoformat() if created else now()})
        except Exception as exc:
            LOG.warning("Comentários indisponíveis em %s: %s", media_pk, exc)
        try:
            likers = client.media_likers(media_pk)[:LIKERS_LIMIT]
            for user in likers:
                actor = actor_payload(user)
                key = f"like:{media_pk}:{actor['id']}"
                if actor["id"] and state.remember(target.id, key) and emit:
                    actor = enriched_actor(client, user)
                    signals.append({"external_id": f"ig:{target_pk}:{key}", "signal_type": "like", "actor": actor, "target": {"handle": target.handle, "url": f"https://instagram.com/{target.handle}"}, "occurred_at": now()})
        except Exception as exc:
            LOG.warning("Curtidas indisponíveis em %s: %s", media_pk, exc)
    return signals

def collect_target(client: Client, target: Target, state: State):
    emit = state.is_baselined(target.id)
    try:
        target_pk = target.external_id or str(client.user_id_from_username(target.handle))
        profile_info = client.user_info_v1(int(target_pk))
        profile = actor_payload(profile_info)
        profile["is_verified"] = value(profile_info, "is_verified")
        signals = collect_followers(client, target, target_pk, state, emit)
        signals.extend(collect_engagement(client, target, target_pk, state, emit))
        send(signals)
        if not emit:
            state.finish_baseline(target.id)
            report(target, "baseline", external_id=target_pk, profile=profile)
            LOG.info("Baseline concluído para @%s; nenhum sinal emitido.", target.handle)
        else:
            report(target, "active", external_id=target_pk, profile=profile)
            LOG.info("@%s: %d sinal(is) novo(s).", target.handle, len(signals))
    except Exception as exc:
        LOG.exception("Falha ao coletar @%s", target.handle)
        try:
            report(target, "error", error=str(exc)[:1000])
        except Exception:
            LOG.exception("Falha também ao reportar estado do alvo.")

def main():
    global PROFILE_ENRICHMENTS
    state = State(STATE_DIR / "collector.sqlite3")
    try:
        client = login()
    except Exception as exc:
        if is_security_checkpoint(exc):
            LOG.warning('Conta pausada por verificação de segurança do Instagram: %s', type(exc).__name__)
            try:
                report_connection('checkpoint', 'O Instagram pediu uma confirmação no aplicativo oficial.', pause_hours=48)
            except Exception:
                LOG.exception('Não foi possível registrar a pausa da conta.')
        raise
    while True:
        PROFILE_ENRICHMENTS = 0
        for target in fetch_targets():
            collect_target(client, target, state)
            time.sleep(15)
        if RUN_ONCE:
            break
        LOG.info("Rodada concluída. Próxima em %ss.", INTERVAL)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
