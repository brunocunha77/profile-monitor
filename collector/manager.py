"""Mantem um coletor isolado por cliente conectado ao Sales OS."""
from __future__ import annotations

import logging
import os
import subprocess
import sys
import time
from pathlib import Path

import requests

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
LOG = logging.getLogger("instagram-manager")

API_URL = os.environ["MONITOR_CONTROL_API_URL"].rstrip("/")
SECRET = os.environ["MONITOR_CONTROL_API_TOKEN"]
STATE_ROOT = Path(os.getenv("MONITOR_SESSION_ROOT", "/data/instagram"))
REFRESH_SECONDS = int(os.getenv("WORKER_DISCOVERY_SECONDS", "60"))
RETRY_INITIAL_SECONDS = int(os.getenv("WORKER_RETRY_INITIAL_SECONDS", "900"))
RETRY_MAX_SECONDS = int(os.getenv("WORKER_RETRY_MAX_SECONDS", "21600"))


def workers(active_client_ids: list[int]) -> dict:
    response = requests.post(
        f"{API_URL}/v1/workers/claim",
        headers={"Authorization": f"Bearer {SECRET}"},
        json={"active_client_ids": active_client_ids},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def main() -> None:
    children: dict[int, subprocess.Popen] = {}
    retry_after: dict[int, float] = {}
    retry_delay: dict[int, int] = {}

    while True:
        try:
            payload = workers(list(children))
            connected = set(map(int, payload.get("connected_client_ids", [])))
            configured = {
                int(item["client_id"]): item for item in payload.get("workers", [])
            }

            for client_id, process in list(children.items()):
                exit_code = process.poll()
                if client_id not in connected:
                    if exit_code is None:
                        process.terminate()
                    children.pop(client_id, None)
                    retry_after.pop(client_id, None)
                    retry_delay.pop(client_id, None)
                elif exit_code is not None:
                    delay = retry_delay.get(client_id, RETRY_INITIAL_SECONDS)
                    retry_after[client_id] = time.monotonic() + delay
                    retry_delay[client_id] = min(delay * 2, RETRY_MAX_SECONDS)
                    children.pop(client_id, None)
                    LOG.error(
                        "Coletor do cliente %s encerrou (codigo %s); "
                        "nova tentativa em %ss.",
                        client_id,
                        exit_code,
                        delay,
                    )

            for client_id in list(retry_after):
                if client_id not in connected:
                    retry_after.pop(client_id, None)
                    retry_delay.pop(client_id, None)

            for client_id, item in configured.items():
                if client_id in children:
                    continue
                if time.monotonic() < retry_after.get(client_id, 0):
                    continue

                state_dir = STATE_ROOT / f"client-{client_id}"
                state_dir.mkdir(parents=True, exist_ok=True)
                env = os.environ.copy()
                env.update(
                    {
                        "MONITOR_SIGNAL_WEBHOOK_URL": item["webhook_url"],
                        "COLLECTOR_STATE_DIR": str(state_dir),
                        "RUN_ONCE": "true",
                        "COLLECTOR_TARGET_IDS": str(item.get("target_id") or ""),
                        "COLLECTOR_USERNAME": str(item.get("username") or ""),
                        "COLLECTOR_PASSWORD": str(item.get("password") or ""),
                    }
                )
                requests.patch(
                    f"{item['webhook_url']}/connection",
                    json={"status": "connected", "manual_run": "started"},
                    timeout=30,
                ).raise_for_status()
                children[client_id] = subprocess.Popen(
                    [sys.executable, str(Path(__file__).with_name("collector.py"))],
                    env=env,
                )
                retry_after.pop(client_id, None)
                LOG.info("Coletor iniciado para cliente %s.", client_id)
        except Exception:
            LOG.exception("Falha ao sincronizar workers.")

        time.sleep(REFRESH_SECONDS)


if __name__ == "__main__":
    main()
