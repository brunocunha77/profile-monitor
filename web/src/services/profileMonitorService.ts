export interface SignalTargetRow {
  id: number; source: string; handle: string; label: string | null; profile_url: string | null; external_id: string | null;
  active: boolean; collection_status: string; last_collected_at: string | null; last_collection_error: string | null;
  full_name: string | null; biography: string | null; follower_count: number | null; media_count: number | null;
  profile_picture_url: string | null; is_private: boolean | null; is_verified: boolean | null;
}
export type InstagramConnectionStatus = 'connected' | 'checkpoint' | 'cooldown' | 'error' | 'disconnected';
export interface InstagramConnection { username: string; status: InstagramConnectionStatus; last_error?: string | null; connected_at?: string | null; updated_at?: string | null; paused_until?: string | null; }
export type SignalTargetPreview = Pick<SignalTargetRow, 'handle' | 'external_id' | 'full_name' | 'biography' | 'follower_count' | 'media_count' | 'profile_picture_url' | 'is_private' | 'is_verified'>;
export interface SignalRow { id: number; signal_type: 'follow_observed' | 'comment' | 'like'; target_handle: string; target_label: string | null; content: string | null; occurred_at: string; base_score: number; score_reason: string | null; }
export interface SignalProspectRow { id: number; source: string; actor_id: string; actor_handle: string; actor_name: string | null; actor_url: string | null; actor_bio: string | null; actor_followers: number | null; actor_posts: number | null; actor_is_private: boolean | null; actor_profile_picture_url: string | null; score: number; score_reason: string; confidence: 'low' | 'medium' | 'high'; signal_count: number; target_count: number; first_signal_at: string | null; last_signal_at: string | null; status: 'novo' | 'em_contato' | 'convertido' | 'descartado'; lead_id: number | null; signals: SignalRow[]; }

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { ...init, headers: { 'Content-Type': 'application/json', ...(init.headers || {}) } });
  const payload = response.status === 204 ? null : await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(String((payload as { error?: string })?.error || 'Não foi possível concluir a operação.'));
  return payload as T;
}

export const salesSignalsService = {
  async getInstagramConnection(_clientId: number) { return request<{ connected: boolean; connection: InstagramConnection | null }>('/api/instagram/connection'); },
  async connectInstagram(_clientId: number, username: string, _password: string) { return request<{ connected: boolean; connection: { username: string; status: string } }>('/api/instagram/connect', { method: 'POST', body: JSON.stringify({ username }) }); },
  async disconnectInstagram(_clientId: number) { return request<void>('/api/instagram/connection', { method: 'DELETE' }); },
  async listTargets(_clientId: number) { return request<{ targets: SignalTargetRow[] }>('/api/targets'); },
  async previewTarget(_clientId: number, handle: string) { return request<SignalTargetPreview>('/api/targets/preview', { method: 'POST', body: JSON.stringify({ handle }) }); },
  async addTarget(_clientId: number, handle: string) { return request<SignalTargetRow>('/api/targets', { method: 'POST', body: JSON.stringify({ handle }) }); },
  async setTargetActive(_clientId: number, id: number, active: boolean) { return request<SignalTargetRow>(`/api/targets/${id}`, { method: 'PATCH', body: JSON.stringify({ active }) }); },
  async collectTarget(_clientId: number, id: number) { return request<{ accepted: boolean; target: { id: number; handle: string } }>(`/api/targets/${id}/collect`, { method: 'POST', body: '{}' }); },
  async removeTarget(_clientId: number, id: number) { return request<void>(`/api/targets/${id}`, { method: 'DELETE' }); },
  async listProspects(_clientId: number) { return request<{ prospects: SignalProspectRow[] }>('/api/prospects'); },
  async enrichProspect(_clientId: number, id: number) { return request<SignalProspectRow>(`/api/prospects/${id}/enrich`, { method: 'POST', body: '{}' }); },
  async getProspectImage(_clientId: number, _id: number) { throw new Error('Foto indisponível.'); },
  async setStatus(_clientId: number, id: number, status: SignalProspectRow['status']) { return request<SignalProspectRow>(`/api/prospects/${id}/status`, { method: 'POST', body: JSON.stringify({ status }) }); },
  async promoteToLead(_clientId: number, id: number) { return request<{ lead_id: number }>(`/api/prospects/${id}/lead`, { method: 'POST', body: '{}' }); },
};
