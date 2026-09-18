"""Local control plane for Profile Monitor. No external collection is triggered by this server."""
from __future__ import annotations

import json
import os
import secrets
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / '.env')
PORT = int(os.getenv('MONITOR_PORT', '8081'))
TOKEN = os.getenv('MONITOR_CONTROL_API_TOKEN', '')
DATA_PATH = ROOT / 'state' / 'control.json'


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def load_state() -> dict:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding='utf-8'))
    return {
        'connection': {'status': 'not_configured', 'last_error': None, 'updated_at': now()},
        'targets': [], 'run': None, 'signals': [],
    }


def save_state(state: dict) -> None:
    DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    DATA_PATH.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding='utf-8')


def target_row(target: dict) -> dict:
    handle = target['handle']
    return {
        'id': target['id'], 'source': 'instagram', 'handle': handle, 'label': None,
        'profile_url': f'https://instagram.com/{handle}', 'external_id': target.get('external_id'),
        'active': target.get('active', True), 'collection_status': target.get('collection_status', 'pending'),
        'last_collected_at': target.get('last_collected_at'), 'last_collection_error': target.get('last_collection_error'),
        'full_name': target.get('full_name'), 'biography': target.get('biography'),
        'follower_count': target.get('follower_count'), 'media_count': target.get('media_count'),
        'profile_picture_url': target.get('profile_picture_url'), 'is_private': target.get('is_private'),
        'is_verified': target.get('is_verified'),
    }


def public_state(state: dict) -> dict:    return {
        **state,
        'configuration': {
            'control_token': bool(TOKEN),
            'collector_username': bool(os.getenv('COLLECTOR_USERNAME')),
            'collector_password': bool(os.getenv('COLLECTOR_PASSWORD')),
            'proxy': bool(os.getenv('COLLECTOR_PROXY_URL')),
        },
    }


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_args):
        return

    def body(self) -> dict:
        length = int(self.headers.get('Content-Length', '0'))
        return json.loads(self.rfile.read(length) or b'{}')

    def send_json(self, value: dict, status: int = 200) -> None:
        raw = json.dumps(value, ensure_ascii=True).encode()
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def serve_dashboard(self) -> None:
        raw = (ROOT / 'dashboard.html').read_bytes()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Length', str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def is_worker(self) -> bool:
        return len(TOKEN) >= 32 and self.headers.get('Authorization') == f'Bearer {TOKEN}'

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        state = load_state()
        if path == '/':
            return self.serve_dashboard()
        if path == '/api/status':
            return self.send_json(public_state(state))
        if path == '/api/targets':
            return self.send_json({'targets': [target_row(target) for target in state['targets']]})
        if path == '/api/prospects':
            return self.send_json({'prospects': []})
        if path == '/api/instagram/connection':
            connection = state['connection']
            status = connection.get('status')
            if status in {'checkpoint', 'cooldown', 'error'}:
                return self.send_json({'connected': False, 'connection': {'username': os.getenv('COLLECTOR_USERNAME', ''), 'status': status, 'last_error': connection.get('last_error'), 'updated_at': connection.get('updated_at')}})
            username = os.getenv('COLLECTOR_USERNAME', '')
            configured = bool(username and os.getenv('COLLECTOR_PASSWORD'))
            return self.send_json({'connected': configured, 'connection': {'username': username, 'status': 'connected'} if configured else None})
        if path.startswith('/runs/') and path.endswith('/targets'):
            return self.send_json({'targets': [target for target in state['targets'] if target['active']]})
        return self.send_json({'error': 'Not found'}, HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        state = load_state()
        if path == '/api/targets/preview':
            payload = self.body(); handle = str(payload.get('handle', '')).strip().lstrip('@').lower()
            if not handle or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789._' for ch in handle):
                return self.send_json({'error': 'Informe um @usuario valido.'}, 400)
            return self.send_json({'handle': handle, 'external_id': None, 'full_name': None, 'biography': None, 'follower_count': None, 'media_count': None, 'profile_picture_url': None, 'is_private': None, 'is_verified': None})
        if path == '/api/targets':
            payload = self.body(); handle = str(payload.get('handle', '')).strip().lstrip('@').lower()
            if not handle or any(ch not in 'abcdefghijklmnopqrstuvwxyz0123456789._' for ch in handle):
                return self.send_json({'error': 'Informe um @usuario valido.'}, 400)
            if any(target['handle'] == handle for target in state['targets']):
                return self.send_json({'error': 'Esse perfil ja esta na lista.'}, 409)
            target = {'id': len(state['targets']) + 1, 'handle': handle, 'active': True, 'collection_status': 'pending', 'last_collected_at': None, 'last_collection_error': None}
            state['targets'].append(target); save_state(state)
            return self.send_json(target_row(target), 201)
        if path.startswith('/api/targets/') and path.endswith('/collect'):
            try: target_id = int(path.split('/')[3])
            except ValueError: return self.send_json({'error': 'Alvo invalido.'}, 400)
            if (state.get('run') or {}).get('status') in {'requested', 'running'}:
                return self.send_json({'error': 'Ja existe uma coleta em andamento.'}, 409)
            target = next((item for item in state['targets'] if item['id'] == target_id and item['active']), None)
            if not target: return self.send_json({'error': 'Alvo indisponivel.'}, 404)
            run_token = secrets.token_urlsafe(32)
            state['run'] = {'id': secrets.token_hex(8), 'token': run_token, 'target_id': target_id, 'status': 'requested', 'requested_at': now(), 'started_at': None, 'finished_at': None, 'error': None}
            target['collection_status'] = 'requested'; save_state(state)
            return self.send_json({'accepted': True, 'run': {key: value for key, value in state['run'].items() if key != 'token'}}, 202)
        if path == '/api/instagram/connect':
            return self.send_json({'error': 'Configure a conta coletora no .env e valide-a pelo worker; o painel não recebe senha.'}, 409)
        if path == '/v1/workers/claim':
            if not self.is_worker(): return self.send_json({'error': 'Unauthorized'}, 401)
            run = state.get('run')
            if not run or run['status'] != 'requested': return self.send_json({'connected_client_ids': [], 'workers': []})
            if not os.getenv('COLLECTOR_USERNAME') or not os.getenv('COLLECTOR_PASSWORD'):
                return self.send_json({'error': 'Collector credentials missing.'}, 409)
            host = self.headers.get('Host', f'127.0.0.1:{PORT}')
            webhook_url = f'http://{host}/runs/{run["token"]}'
            return self.send_json({'connected_client_ids': [1], 'workers': [{'client_id': 1, 'webhook_url': webhook_url, 'username': os.getenv('COLLECTOR_USERNAME'), 'password': os.getenv('COLLECTOR_PASSWORD'), 'target_id': run['target_id'], 'run_once': True}]})
        if path.startswith('/runs/'):
            payload = self.body(); run = state.get('run')
            if not run or path != f'/runs/{run["token"]}': return self.send_json({'error': 'Run not found'}, 404)
            state['signals'].extend(payload.get('signals', [])); save_state(state)
            return self.send_json({'received': True, 'accepted': len(payload.get('signals', []))}, 202)
        return self.send_json({'error': 'Not found'}, 404)

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path; state = load_state()
        if path == '/api/instagram/connection':
            state['connection'] = {'status': 'disconnected', 'last_error': None, 'updated_at': now()}; save_state(state)
            self.send_response(204); self.end_headers(); return
        if path.startswith('/api/targets/'):
            try: target_id = int(path.split('/')[3])
            except (ValueError, IndexError): return self.send_json({'error': 'Alvo invalido.'}, 400)
            state['targets'] = [item for item in state['targets'] if item['id'] != target_id]; save_state(state)
            self.send_response(204); self.end_headers(); return
        return self.send_json({'error': 'Not found'}, 404)

    def do_PATCH(self) -> None:
        path = urlparse(self.path).path; state = load_state()
        if path.startswith('/api/targets/'):
            try: target_id = int(path.split('/')[3])
            except (ValueError, IndexError): return self.send_json({'error': 'Alvo invalido.'}, 400)
            target = next((item for item in state['targets'] if item['id'] == target_id), None)
            if not target: return self.send_json({'error': 'Alvo indisponivel.'}, 404)
            target['active'] = bool(self.body().get('active', target.get('active', True))); save_state(state)
            return self.send_json(target_row(target))
        run = state.get('run')
        if not run or not path.startswith('/runs/') or not path.startswith(f'/runs/{run["token"]}'):
            return self.send_json({'error': 'Run not found'}, 404)
        payload = self.body()
        if path.endswith('/connection'):
            manual = payload.get('manual_run'); state['connection']['status'] = payload.get('status', state['connection']['status']); state['connection']['last_error'] = payload.get('error'); state['connection']['updated_at'] = now()
            if manual == 'started': run['status'] = 'running'; run['started_at'] = now()
            if manual == 'finished': run['status'] = 'finished'; run['finished_at'] = now(); run['error'] = payload.get('error')
        elif '/targets/' in path and path.endswith('/status'):
            target_id = int(path.split('/')[-2]); target = next((item for item in state['targets'] if item['id'] == target_id), None)
            if target:
                target['collection_status'] = payload.get('status', target['collection_status']); target['last_collection_error'] = payload.get('error'); target['last_collected_at'] = now()
        else:
            return self.send_json({'error': 'Not found'}, 404)
        save_state(state); return self.send_json({'updated': True})


if __name__ == '__main__':
    print(f'Profile Monitor control plane: http://127.0.0.1:{PORT}')
    ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()




