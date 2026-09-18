"""Local control plane for Profile Monitor. No external collection is triggered by this server."""
from __future__ import annotations

import json
import os
import secrets
import hashlib
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
        'targets': [], 'run': None, 'signals': [], 'prospect_statuses': {}, 'lead_ids': {},
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


def public_state(state: dict) -> dict:
    return {
        **state,
        'configuration': {
            'control_token': bool(TOKEN),
            'collector_username': bool(os.getenv('COLLECTOR_USERNAME')),
            'collector_password': bool(os.getenv('COLLECTOR_PASSWORD')),
            'proxy': bool(os.getenv('COLLECTOR_PROXY_URL')),
        },
    }



def prospect_id(actor_key: str) -> int:
    return int(hashlib.sha256(actor_key.encode('utf-8')).hexdigest()[:12], 16)


def signal_score(signal_type: str) -> int:
    return {'comment': 50, 'like': 18, 'follow_observed': 20}.get(signal_type, 10)


def prospect_rows(state: dict) -> list[dict]:
    grouped: dict[str, dict] = {}
    seen_signals: set[str] = set()
    for signal in state.get('signals', []):
        actor = signal.get('actor') or {}
        actor_key = str(actor.get('id') or actor.get('handle') or '').strip().lower()
        if not actor_key:
            continue
        target = signal.get('target') or {}
        unique_key = str(signal.get('external_id') or f"{actor_key}:{signal.get('signal_type')}:{signal.get('occurred_at')}:{target.get('handle')}")
        if unique_key in seen_signals:
            continue
        seen_signals.add(unique_key)
        row = grouped.setdefault(actor_key, {'actor': actor, 'signals': []})
        row['actor'] = {**row['actor'], **{key: value for key, value in actor.items() if value not in (None, '')}}
        row['signals'].append(signal)

    statuses = state.setdefault('prospect_statuses', {})
    lead_ids = state.setdefault('lead_ids', {})
    prospects = []
    for actor_key, data in grouped.items():
        actor = data['actor']
        signals = sorted(data['signals'], key=lambda item: item.get('occurred_at') or '', reverse=True)
        targets = {str((item.get('target') or {}).get('handle') or '') for item in signals}
        kinds = {item.get('signal_type') for item in signals}
        score = min(100, sum(signal_score(str(item.get('signal_type'))) for item in signals) + (15 if len(targets) > 1 else 0))
        confidence = 'high' if 'comment' in kinds or len(targets) > 1 else ('medium' if len(signals) > 1 else 'low')
        row_id = prospect_id(actor_key)
        rendered_signals = []
        for index, signal in enumerate(signals, start=1):
            target = signal.get('target') or {}
            rendered_signals.append({'id': index, 'signal_type': signal.get('signal_type', 'follow_observed'), 'target_handle': target.get('handle', ''), 'target_label': None, 'content': signal.get('content'), 'occurred_at': signal.get('occurred_at') or now(), 'base_score': signal_score(str(signal.get('signal_type'))), 'score_reason': signal.get('score_reason')})
        prospects.append({'id': row_id, 'source': 'instagram', 'actor_id': str(actor.get('id') or actor_key), 'actor_handle': actor.get('handle') or actor_key, 'actor_name': actor.get('name'), 'actor_url': actor.get('url') or f"https://instagram.com/{actor.get('handle') or actor_key}", 'actor_bio': actor.get('bio'), 'actor_followers': actor.get('followers'), 'actor_posts': actor.get('posts'), 'actor_is_private': actor.get('is_private'), 'actor_profile_picture_url': actor.get('profile_picture_url'), 'score': score, 'score_reason': 'Sinais recentes observados na audiência monitorada.', 'confidence': confidence, 'signal_count': len(signals), 'target_count': len(targets), 'first_signal_at': signals[-1].get('occurred_at'), 'last_signal_at': signals[0].get('occurred_at'), 'status': statuses.get(str(row_id), 'novo'), 'lead_id': lead_ids.get(str(row_id)), 'signals': rendered_signals})
    return sorted(prospects, key=lambda row: (row['last_signal_at'] or '', row['score']), reverse=True)


def find_prospect(state: dict, requested_id: int) -> dict | None:
    return next((row for row in prospect_rows(state) if row['id'] == requested_id), None)
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
            return self.send_json({'prospects': prospect_rows(state)})
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
        if path.startswith('/api/prospects/') and path.endswith('/enrich'):
            try: requested_id = int(path.split('/')[3])
            except (ValueError, IndexError): return self.send_json({'error': 'Oportunidade inválida.'}, 400)
            prospect = find_prospect(state, requested_id)
            if not prospect: return self.send_json({'error': 'Oportunidade não encontrada.'}, 404)
            return self.send_json(prospect)
        if path.startswith('/api/prospects/') and path.endswith('/lead'):
            try: requested_id = int(path.split('/')[3])
            except (ValueError, IndexError): return self.send_json({'error': 'Oportunidade inválida.'}, 400)
            if not find_prospect(state, requested_id): return self.send_json({'error': 'Oportunidade não encontrada.'}, 404)
            lead_id = state.setdefault('lead_ids', {}).setdefault(str(requested_id), requested_id)
            state.setdefault('prospect_statuses', {})[str(requested_id)] = 'convertido'
            save_state(state)
            return self.send_json({'lead_id': lead_id})
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
        if path.startswith('/api/prospects/') and path.endswith('/status'):
            try: requested_id = int(path.split('/')[3])
            except (ValueError, IndexError): return self.send_json({'error': 'Oportunidade inválida.'}, 400)
            if not find_prospect(state, requested_id): return self.send_json({'error': 'Oportunidade não encontrada.'}, 404)
            status = self.body().get('status')
            if status not in {'novo', 'em_contato', 'convertido', 'descartado'}:
                return self.send_json({'error': 'Status inválido.'}, 400)
            state.setdefault('prospect_statuses', {})[str(requested_id)] = status
            save_state(state)
            return self.send_json(find_prospect(state, requested_id))
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




