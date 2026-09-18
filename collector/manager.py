"""Executa uma rodada manual por vez para a conta coletora local."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s %(levelname)s %(message)s")
LOG = logging.getLogger("profile-monitor-manager")

API_URL = os.environ["MONITOR_CONTROL_API_URL"].rstrip("/")
SECRET = os.environ["MONITOR_CONTROL_API_TOKEN"]
STATE_ROOT = Path(os.getenv("MONITOR_SESSION_ROOT", "./state"))
REFRESH_SECONDS = int(os.getenv("WORKER_DISCOVERY_SECONDS", "5"))


def workers(active_client_ids: list[int]) -> dict:
    response = requests.post(
        f"{API_URL}/v1/workers/claim",
        headers={"Authorization": f"Bearer {SECRET}"},
        json={"active_client_ids": active_client_ids},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def finish(webhook_url: str, exit_code: int) -> None:
    error = None if exit_code == 0 else f"O coletor encerrou com codigo {exit_code}."
    requests.patch(
        f"{webhook_url}/connection",
        json={"manual_run": "finished", "error": error},
        timeout=30,
    ).raise_for_status()


def main() -> None:
    children: dict[int, tuple[subprocess.Popen, str]] = {}
    while True:
        try:
            payload = workers(list(children))
            configured = {int(item["client_id"]): item for item in payload.get("workers", [])}

            for client_id, (process, webhook_url) in list(children.items()):
                exit_code = process.poll()
                if exit_code is None:
                    continue
                try:
                    finish(webhook_url, exit_code)
                except Exception:
                    LOG.exception("Falha ao encerrar a rodada manual do cliente %s.", client_id)
                children.pop(client_id, None)
                LOG.info("Rodada manual do cliente %s encerrada (codigo %s).", client_id, exit_code)

            for client_id, item in configured.items():
                if client_id in children:
                    continue
                state_dir = STATE_ROOT / f"client-{client_id}"
                state_dir.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env.update({
                    "MONITOR_SIGNAL_WEBHOOK_URL": item["webhook_url"],
                    "COLLECTOR_STATE_DIR": str(state_dir),
                    "RUN_ONCE": "true",
                    "COLLECTOR_TARGET_IDS": str(item.get("target_id") or ""),
                    "COLLECTOR_USERNAME": str(item.get("username") or ""),
                    "COLLECTOR_PASSWORD": str(item.get("password") or ""),
                })
                requests.patch(
                    f"{item['webhook_url']}/connection",
                    json={"status": "connected", "manual_run": "started"},
                    timeout=30,
                ).raise_for_status()
                process = subprocess.Popen([sys.executable, str(Path(__file__).with_name("collector.py"))], env=env)
                children[client_id] = (process, item["webhook_url"])
                LOG.info("Rodada manual iniciada para o cliente %s.", client_id)
        except Exception:
            LOG.exception("Falha ao sincronizar rodadas manuais.")
        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
