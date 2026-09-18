import { useEffect, useMemo, useState } from 'react';
import { Activity, AtSign, Check, ChevronLeft, ChevronRight, CircleAlert, Clock3, ExternalLink, Eye, Heart, Instagram, LockKeyhole, MessageCircle, Pause, Plus, Radar, RefreshCw, Search, Send, Sparkles, Target, Trash2, UserPlus, X } from 'lucide-react';
import { toast } from 'sonner';

import { salesSignalsService, type InstagramConnection, type SignalProspectRow, type SignalTargetPreview, type SignalTargetRow } from '../../services/profileMonitorService';

type Kind = 'comment' | 'follow' | 'like';
type TargetProfile = { id: number; handle: string; fullName?: string; avatar?: string; followers: string; posts?: string; initials: string; tone: string; active: boolean; signals: number; sync: string };
type Event = { kind: Kind; title: string; detail: string; time: string; points: number };
type Opportunity = { id: number; name: string; handle: string; initials: string; avatar?: string; score: number; level: 'Alta' | 'Média'; source: string; seen: string; summary: string; contacted: boolean; kinds: Kind[]; bio: string; followers: string; posts: number; confidence: 'Alta' | 'Média'; events: Event[] };

const seedTargets: TargetProfile[] = [
  { id: 1, handle: '@medway_residencia', followers: '482 mil', initials: 'MW', tone: 'bg-rose-100 text-rose-700', active: true, signals: 31, sync: 'há 12 min' },
  { id: 2, handle: '@estrategiamed', followers: '719 mil', initials: 'EM', tone: 'bg-blue-100 text-blue-700', active: true, signals: 24, sync: 'há 18 min' },
  { id: 3, handle: '@sanarmed', followers: '1,2 mi', initials: 'SM', tone: 'bg-amber-100 text-amber-700', active: true, signals: 18, sync: 'há 23 min' },
];

const seedOpportunities: Opportunity[] = [
  { id: 1, name: 'Marina Alves', handle: '@marinaalves.med', initials: 'MA', score: 94, level: 'Alta', source: '@medway_residencia', seen: 'há 18 min', summary: 'Perguntou o valor da próxima turma', contacted: false, kinds: ['comment', 'follow'], bio: 'Medicina 11/12 · R1 em 2027 · Salvador', followers: '1.240', posts: 86, confidence: 'Alta', events: [
    { kind: 'comment', title: 'Comentou em uma publicação', detail: '“Qual o valor da próxima turma? Ainda dá tempo de entrar?”', time: 'Hoje, 14:32', points: 50 },
    { kind: 'follow', title: 'Seguidora recém-observada', detail: 'Apareceu entre os seguidores de @medway_residencia.', time: 'Hoje, 13:48', points: 20 },
    { kind: 'like', title: 'Interagiu com outro alvo', detail: 'Curtiu uma publicação de @estrategiamed.', time: 'Ontem, 20:15', points: 24 },
  ] },
  { id: 2, name: 'Pedro Henrique', handle: '@pedrohenrique.md', initials: 'PH', score: 87, level: 'Alta', source: '@estrategiamed', seen: 'há 41 min', summary: 'Interagiu com dois perfis monitorados', contacted: false, kinds: ['follow', 'like'], bio: 'Internato · Foco em cirurgia geral', followers: '892', posts: 54, confidence: 'Média', events: [
    { kind: 'follow', title: 'Seguidor recém-observado', detail: 'Apareceu entre os seguidores de @estrategiamed.', time: 'Hoje, 14:09', points: 20 },
    { kind: 'like', title: 'Curtiu duas publicações', detail: 'Interações recentes em @sanarmed e @estrategiamed.', time: 'Hoje, 13:54', points: 42 },
    { kind: 'follow', title: 'Presença em mais de um alvo', detail: 'Também está na audiência de @sanarmed.', time: 'Hoje, 12:22', points: 25 },
  ] },
  { id: 3, name: 'Camila Rezende', handle: '@camilarezende', initials: 'CR', score: 78, level: 'Alta', source: '@sanarmed', seen: 'há 1h', summary: 'Comentou “manda o link” em um reel', contacted: true, kinds: ['comment'], bio: 'Medicina · 6º ano · Recife', followers: '2.103', posts: 112, confidence: 'Alta', events: [
    { kind: 'comment', title: 'Comentou em um reel', detail: '“Manda o link, por favor”', time: 'Hoje, 13:26', points: 50 },
    { kind: 'comment', title: 'Intenção explícita detectada', detail: 'O texto indica interesse direto em acessar a oferta.', time: 'Hoje, 13:26', points: 28 },
  ] },
  { id: 4, name: 'Lucas Martins', handle: '@lucas.martins', initials: 'LM', score: 63, level: 'Média', source: '@medway_residencia', seen: 'há 3h', summary: 'Novo seguidor com perfil compatível', contacted: false, kinds: ['follow'], bio: 'Acadêmico de medicina · Fortaleza', followers: '654', posts: 39, confidence: 'Média', events: [
    { kind: 'follow', title: 'Seguidor recém-observado', detail: 'Primeira aparição em @medway_residencia.', time: 'Hoje, 11:02', points: 20 },
    { kind: 'follow', title: 'Perfil compatível', detail: 'Bio pública indica formação em medicina.', time: 'Hoje, 11:02', points: 43 },
  ] },
  { id: 5, name: 'Beatriz Lopes', handle: '@beatrizlopes_', initials: 'BL', score: 46, level: 'Média', source: '@estrategiamed', seen: 'ontem', summary: 'Curtiu três conteúdos sobre residência', contacted: false, kinds: ['like'], bio: 'SP · Medicina', followers: '3.410', posts: 164, confidence: 'Média', events: [
    { kind: 'like', title: 'Curtiu três publicações', detail: 'Conteúdos relacionados à preparação para residência.', time: 'Ontem, 19:44', points: 46 },
  ] },
];

const kindMeta = {
  comment: { icon: MessageCircle, label: 'Comentário', tone: 'bg-violet-100 text-violet-700' },
  follow: { icon: UserPlus, label: 'Novo seguidor', tone: 'bg-blue-100 text-blue-700' },
  like: { icon: Heart, label: 'Curtida', tone: 'bg-rose-100 text-rose-700' },
};

const demoMode = import.meta.env.VITE_AUTH_BYPASS === 'true';
const compactNumber = (value: number | null) => value == null ? 'Não informado' : new Intl.NumberFormat('pt-BR', { notation: 'compact', maximumFractionDigits: 1 }).format(value);
const relativeTime = (iso: string | null) => {
  if (!iso) return 'sem coleta';
  const minutes = Math.max(0, Math.round((Date.now() - new Date(iso).getTime()) / 60000));
  if (minutes < 60) return `há ${minutes} min`;
  if (minutes < 1440) return `há ${Math.round(minutes / 60)}h`;
  return `há ${Math.round(minutes / 1440)}d`;
};
const mapTarget = (row: SignalTargetRow): TargetProfile => ({
  id: row.id, handle: `@${row.handle}`, fullName: row.full_name || undefined, avatar: row.profile_picture_url || undefined,
  followers: row.follower_count == null ? (row.collection_status === 'pending' ? 'Preparando' : '—') : `${compactNumber(row.follower_count)} seguidores`,
  posts: row.media_count == null ? undefined : `${compactNumber(row.media_count)} posts`,
  initials: row.handle.slice(0, 2).toUpperCase(), tone: 'bg-slate-100 text-slate-700', active: row.active,
  signals: 0, sync: row.last_collection_error ? 'falha na coleta' : relativeTime(row.last_collected_at),
});
const mapProspect = (row: SignalProspectRow): Opportunity => {
  const signals = row.signals || [];
  const kinds = [...new Set(signals.map(signal => signal.signal_type === 'follow_observed' ? 'follow' : signal.signal_type))] as Kind[];
  const first = signals[0];
  const name = row.actor_name || `@${row.actor_handle}`;
  return {
    id: row.id, name, handle: `@${row.actor_handle}`, initials: name.replace('@', '').split(/\s+/).map(part => part[0]).join('').slice(0, 2).toUpperCase(), avatar: row.actor_profile_picture_url || undefined,
    score: row.score, level: row.score >= 75 ? 'Alta' : 'Média', source: first ? `@${first.target_handle}` : 'sem origem',
    seen: relativeTime(row.last_signal_at), summary: first?.content || (first?.signal_type === 'follow_observed' ? 'Seguidor recém-observado' : 'Interação detectada'),
    contacted: row.status !== 'novo', kinds, bio: row.actor_bio || 'Bio não informada', followers: compactNumber(row.actor_followers),
    posts: row.actor_posts || 0, confidence: row.confidence === 'high' ? 'Alta' : 'Média',
    events: signals.map(signal => ({ kind: signal.signal_type === 'follow_observed' ? 'follow' : signal.signal_type,
      title: signal.signal_type === 'comment' ? 'Comentou em uma publicação' : signal.signal_type === 'like' ? 'Curtida recém-observada' : 'Seguidor recém-observado',
      detail: signal.content || signal.score_reason || `Sinal observado em @${signal.target_handle}.`,
      time: new Date(signal.occurred_at).toLocaleString('pt-BR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }), points: signal.base_score })),
  };
};
function Score({ item }: { item: Opportunity }) {
  const tone = item.score >= 75 ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-amber-200 bg-amber-50 text-amber-700';
  return <div className={`flex h-11 w-11 shrink-0 flex-col items-center justify-center rounded-lg border ${tone}`}><b className="text-sm leading-none tabular-nums">{item.score}</b><span className="mt-0.5 text-[8px] font-semibold uppercase">{item.level}</span></div>;
}

function ProspectAvatar({ item, clientId, size }: { item: Opportunity; clientId?: number; size: 'sm' | 'lg' }) {
  const [src, setSrc] = useState<string | null>(null);
  useEffect(() => {
    if (!clientId || !item.avatar) { setSrc(null); return; }
    let active = true; let objectUrl = '';
    salesSignalsService.getProspectImage(clientId, item.id).then(url => { objectUrl = url; if (active) setSrc(url); }).catch(() => { if (active) setSrc(null); });
    return () => { active = false; if (objectUrl) URL.revokeObjectURL(objectUrl); };
  }, [clientId, item.id, item.avatar]);
  const dimensions = size === 'lg' ? 'h-12 w-12 text-xs' : 'h-9 w-9 text-[10px]';
  return <div className={`flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-slate-900 font-bold text-white ${dimensions}`}>{src ? <img src={src} alt="" className="h-full w-full object-cover" onError={() => setSrc(null)} /> : item.initials}</div>;
}
export default function PesquisaPage() {
  const user = { id_cliente: 1 };
  const [targets, setTargets] = useState<TargetProfile[]>(demoMode ? seedTargets : []);
  const [items, setItems] = useState<Opportunity[]>(demoMode ? seedOpportunities : []);
  const [selectedId, setSelectedId] = useState(1);
  const [query, setQuery] = useState('');
  const [profile, setProfile] = useState('');
  const [profilePreview, setProfilePreview] = useState<SignalTargetPreview | null>(null);
  const [previewing, setPreviewing] = useState(false);
  const [filter, setFilter] = useState<'all' | 'hot' | Kind>('all');
  const [page, setPage] = useState(1);
  const pageSize = 8;
  const [showTargets, setShowTargets] = useState(true);
  const [loading, setLoading] = useState(!demoMode);
  const [error, setError] = useState('');
  const [connectionOpen, setConnectionOpen] = useState(() => new URLSearchParams(window.location.search).get('connect') === 'instagram');
  const [instagramUser, setInstagramUser] = useState('');
  const [instagramPassword, setInstagramPassword] = useState('');
  const [connectedUser, setConnectedUser] = useState<string | null>(demoMode ? 'conta.demo' : null);
  const [instagramConnection, setInstagramConnection] = useState<InstagramConnection | null>(null);
  const [connecting, setConnecting] = useState(false);
  const [enrichedIds, setEnrichedIds] = useState<Set<number>>(() => new Set());
  const [collectingTargetIds, setCollectingTargetIds] = useState<Set<number>>(() => new Set());

  const filtered = useMemo(() => items.filter(item => {
    const term = query.trim().toLowerCase();
    const textMatch = !term || `${item.name} ${item.handle} ${item.source} ${item.summary}`.toLowerCase().includes(term);
    const filterMatch = filter === 'all' || (filter === 'hot' ? item.score >= 75 : item.kinds.includes(filter));
    return textMatch && filterMatch;
  }), [items, query, filter]);
  const pageCount = Math.max(1, Math.ceil(filtered.length / pageSize));
  const pageItems = filtered.slice((page - 1) * pageSize, page * pageSize);
  const selected = pageItems.find(item => item.id === selectedId) || pageItems[0] || null;

  useEffect(() => {
    if (demoMode || !user?.id_cliente) return;
    let cancelled = false;
    setLoading(true);
    Promise.all([salesSignalsService.listTargets(user.id_cliente), salesSignalsService.listProspects(user.id_cliente), salesSignalsService.getInstagramConnection(user.id_cliente)])
      .then(([targetResponse, prospectResponse, connectionResponse]) => {
        if (cancelled) return;
        setTargets(targetResponse.targets.map(mapTarget));
        setItems(prospectResponse.prospects.map(mapProspect));
        setSelectedId(prospectResponse.prospects[0]?.id || 0);
        setConnectedUser(connectionResponse.connection?.username || null);
        setInstagramConnection(connectionResponse.connection);
      })
      .catch(reason => { if (!cancelled) setError(reason instanceof Error ? reason.message : 'Não foi possível carregar a pesquisa.'); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [user?.id_cliente]);

  useEffect(() => {
    if (demoMode || !user?.id_cliente || !selected || enrichedIds.has(selected.id)) return;
    if (selected.bio !== 'Bio não informada' && selected.followers !== 'Não informado' && selected.posts > 0) return;
    setEnrichedIds(current => new Set(current).add(selected.id));
    salesSignalsService.enrichProspect(user.id_cliente, selected.id).then(row => {
      setItems(current => current.map(item => item.id === selected.id ? {
        ...item, name: row.actor_name || item.name, bio: row.actor_bio || 'Bio não informada',
        followers: compactNumber(row.actor_followers), posts: row.actor_posts || 0,
        avatar: row.actor_profile_picture_url || item.avatar,
      } : item));
    }).catch(() => { /* Mantém os dados resumidos quando o perfil não está disponível. */ });
  }, [selected?.id, user?.id_cliente]);
  async function connectInstagram() {
    if (!user?.id_cliente || !instagramUser.trim() || !instagramPassword) return;
    setConnecting(true);
    try {
      const response = await salesSignalsService.connectInstagram(user.id_cliente, instagramUser, instagramPassword);
      setConnectedUser(response.connection.username);
      setInstagramConnection({ username: response.connection.username, status: 'connected' });
      setInstagramPassword(''); setConnectionOpen(false);
      toast.success('Instagram conectado para pesquisa.');
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível conectar o Instagram.'); }
    finally { setConnecting(false); }
  }

  async function disconnectInstagram() {
    if (!user?.id_cliente) return;
    try { await salesSignalsService.disconnectInstagram(user.id_cliente); setConnectedUser(null); setInstagramConnection(null); toast.success('Instagram desconectado.'); }
    catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível desconectar.'); }
  }
  function normalizedProfileHandle() {
    const raw = profile.trim();
    return raw.includes('instagram.com/') ? raw.split('instagram.com/')[1].split(/[/?#]/)[0] : raw.replace(/^@/, '');
  }
  async function addTarget() {
    const rawHandle = normalizedProfileHandle();
    if (!rawHandle || !user?.id_cliente) return;
    if (!profilePreview || profilePreview.handle.toLowerCase() !== rawHandle.toLowerCase()) {
      setPreviewing(true); setProfilePreview(null);
      try { setProfilePreview(await salesSignalsService.previewTarget(user.id_cliente, rawHandle)); }
      catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível localizar o perfil.'); }
      finally { setPreviewing(false); }
      return;
    }
    const handle = `@${profilePreview.handle}`;
    if (targets.some(item => item.handle.toLowerCase() === handle.toLowerCase())) return void toast.info('Esse perfil já está sendo monitorado.');
    try {
      const created = mapTarget(await salesSignalsService.addTarget(user.id_cliente, handle));
      setTargets(current => [...current, created]);
      setProfile(''); setProfilePreview(null);
      toast.success(`${handle} adicionado ao monitoramento.`);
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível adicionar o perfil.'); }
  }

  async function toggleTarget(target: TargetProfile) {
    try {
      if (!demoMode && user?.id_cliente) await salesSignalsService.setTargetActive(user.id_cliente, target.id, !target.active);
      setTargets(current => current.map(item => item.id === target.id ? { ...item, active: !item.active, sync: item.active ? 'pausado' : 'aguardando coleta' } : item));
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível atualizar o perfil.'); }
  }

  async function removeTarget(target: TargetProfile) {
    try {
      if (!demoMode && user?.id_cliente) await salesSignalsService.removeTarget(user.id_cliente, target.id);
      setTargets(current => current.filter(item => item.id !== target.id));
      toast.success('Perfil removido.');
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível remover o perfil.'); }
  }

  async function collectTarget(target: TargetProfile) {
    if (!user?.id_cliente || collectingTargetIds.has(target.id)) return;
    setCollectingTargetIds(current => new Set(current).add(target.id));
    try {
      await salesSignalsService.collectTarget(user.id_cliente, target.id);
      toast.success(`Coleta de ${target.handle} solicitada. Acompanhe o status deste perfil.`);
      setTargets(current => current.map(item => item.id === target.id ? { ...item, sync: 'coleta em andamento' } : item));
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível solicitar a coleta.'); }
    finally { setCollectingTargetIds(current => { const next = new Set(current); next.delete(target.id); return next; }); }
  }
  async function sendToPipeline() {
    if (!selected) return;
    try {
      if (!demoMode && user?.id_cliente) await salesSignalsService.promoteToLead(user.id_cliente, selected.id);
      setItems(current => current.map(item => item.id === selected.id ? { ...item, contacted: true } : item));
      toast.success(`${selected.name} foi enviado para o Pipeline.`);
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível enviar ao Pipeline.'); }
  }

  async function discardSelected() {
    if (!selected) return;
    try {
      if (!demoMode && user?.id_cliente) await salesSignalsService.setStatus(user.id_cliente, selected.id, 'descartado');
      setItems(current => current.filter(item => item.id !== selected.id));
      toast.success(`${selected.name} foi descartado da fila.`);
    } catch (reason) { toast.error(reason instanceof Error ? reason.message : 'Não foi possível descartar a oportunidade.'); }
  }
  const metrics = [
    { label: 'Oportunidades detectadas', value: items.length, note: 'nos últimos 7 dias', icon: Radar, tone: 'bg-violet-100 text-violet-700' },
    { label: 'Alta intenção', value: items.filter(item => item.score >= 75).length, note: 'prioridade de contato', icon: Target, tone: 'bg-emerald-100 text-emerald-700' },
    { label: 'Ainda sem contato', value: items.filter(item => !item.contacted).length, note: 'aguardando sua equipe', icon: Clock3, tone: 'bg-amber-100 text-amber-700' },
  ];

  return <main className="min-h-screen w-full bg-[#f8f9fc] px-4 py-5 text-slate-950 sm:px-5 lg:px-7"><div className="mx-auto max-w-[1500px] space-y-4">
    <header className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between"><div><div className="flex items-center gap-2"><h1 className="text-2xl font-semibold sm:text-3xl">Pesquisa de intenção</h1><span className="rounded-full border border-violet-200 bg-violet-50 px-2 py-1 text-[9px] font-semibold uppercase text-violet-700">{demoMode ? 'Demonstração' : 'Ao vivo'}</span></div><p className="mt-1 max-w-2xl text-xs leading-5 text-slate-500">Sinais públicos dos perfis que você escolheu, organizados para mostrar com quem falar agora.</p></div><div className="flex flex-wrap gap-2"><button onClick={() => setConnectionOpen(true)} className={`inline-flex h-9 items-center justify-center gap-2 rounded-lg border px-3 text-xs font-semibold ${connectedUser ? 'border-emerald-200 bg-emerald-50 text-emerald-700' : 'border-slate-200 bg-white text-slate-700'}`}><Instagram className="h-4 w-4" /> {connectedUser ? `@${connectedUser}` : 'Conectar Instagram'}</button><button onClick={() => setShowTargets(value => !value)} className="inline-flex h-9 items-center justify-center gap-2 rounded-lg bg-violet-600 px-3 text-xs font-semibold text-white hover:bg-violet-700"><Plus className="h-4 w-4" /> Monitorar perfil</button></div></header>

    {instagramConnection && instagramConnection.status !== 'connected' && <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-xs text-amber-900"><b>Coleta pausada.</b> {instagramConnection.last_error || 'O Instagram pediu uma verificação de segurança.'} {instagramConnection.paused_until ? ` Nova tentativa automática bloqueada até ${new Date(instagramConnection.paused_until).toLocaleString('pt-BR')}.` : ' Conclua a verificação no aplicativo oficial e reconecte a conta quando ela estiver liberada.'}</div>}

    {showTargets && <section className="rounded-lg border border-slate-200 bg-white p-4"><div className="flex flex-col gap-4 xl:flex-row xl:items-end"><div className="min-w-0 flex-1"><label className="text-xs font-semibold">Perfis monitorados</label><p className="mt-0.5 text-[10px] text-slate-500">Adicione concorrentes ou referências cuja audiência deseja acompanhar.</p><div className="mt-3 flex flex-col gap-2 sm:flex-row"><div className="relative flex-1"><AtSign className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={profile} onChange={event => { setProfile(event.target.value); setProfilePreview(null); }} onKeyDown={event => event.key === 'Enter' && addTarget()} placeholder="@perfil ou instagram.com/perfil" className="h-10 w-full rounded-lg border border-slate-200 bg-slate-50 pl-9 pr-3 text-xs outline-none focus:border-violet-400 focus:bg-white" /></div><button disabled={previewing || !profile.trim()} onClick={addTarget} className="inline-flex h-10 items-center justify-center gap-2 rounded-lg bg-slate-900 px-4 text-xs font-semibold text-white disabled:opacity-50">{profilePreview ? <Plus className="h-4 w-4" /> : <Search className="h-4 w-4" />} {previewing ? 'Buscando...' : profilePreview ? 'Confirmar perfil' : 'Buscar perfil'}</button></div>{profilePreview && <div className="mt-3 flex items-center gap-3 rounded-lg border border-violet-200 bg-violet-50/50 p-3"><div className="flex h-11 w-11 shrink-0 items-center justify-center overflow-hidden rounded-full bg-white text-xs font-bold">{profilePreview.profile_picture_url ? <img src={profilePreview.profile_picture_url} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" /> : profilePreview.handle.slice(0, 2).toUpperCase()}</div><div className="min-w-0"><p className="truncate text-xs font-semibold">{profilePreview.full_name || `@${profilePreview.handle}`}{profilePreview.is_verified ? ' ✓' : ''}</p><p className="truncate text-[10px] text-slate-500">@{profilePreview.handle} · {compactNumber(profilePreview.follower_count)} seguidores · {compactNumber(profilePreview.media_count)} posts</p></div></div>}</div><div className="grid min-w-0 flex-[1.45] gap-2 sm:grid-cols-2 xl:grid-cols-3">{targets.map(target => <div key={target.id} className="flex min-w-0 items-center gap-2 rounded-lg border border-slate-200 p-2.5"><div className={`flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded-full text-[10px] font-bold ${target.tone}`}>{target.avatar ? <img src={target.avatar} alt="" className="h-full w-full object-cover" referrerPolicy="no-referrer" /> : target.initials}</div><div className="min-w-0 flex-1"><p className="truncate text-[11px] font-semibold">{target.fullName || target.handle}</p><p className="truncate text-[9px] text-slate-500">{target.handle} · {target.followers}{target.posts ? ` · ${target.posts}` : ''}</p><p className="truncate text-[9px] text-slate-400">{target.signals} sinais · {target.sync}</p></div><button disabled={collectingTargetIds.has(target.id) || !target.active || instagramConnection?.status !== 'connected'} onClick={() => void collectTarget(target)} title="Coletar agora" className="text-slate-500 disabled:opacity-40"><RefreshCw className={`h-4 w-4 ${collectingTargetIds.has(target.id) ? 'animate-spin' : ''}`} /></button><button onClick={() => void toggleTarget(target)} title={target.active ? 'Pausar monitoramento' : 'Ativar monitoramento'} className={target.active ? 'text-emerald-600' : 'text-slate-400'}>{target.active ? <Activity className="h-4 w-4" /> : <Pause className="h-4 w-4" />}</button><button onClick={() => void removeTarget(target)} title="Remover perfil" className="text-slate-400 hover:text-red-600"><X className="h-4 w-4" /></button></div>)}</div></div></section>}

    {error && <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-xs text-red-800">{error}</div>}
    {loading && <div className="rounded-lg border border-slate-200 bg-white px-4 py-5 text-center text-xs text-slate-500">Carregando sinais e perfis monitorados...</div>}
    <section className="grid gap-3 sm:grid-cols-3">{metrics.map(({ label, value, note, icon: Icon, tone }) => <div key={label} className="flex items-center gap-3 rounded-lg border border-slate-200 bg-white p-3 shadow-sm"><div className={`flex h-9 w-9 items-center justify-center rounded-lg ${tone}`}><Icon className="h-4 w-4" /></div><div><p className="text-lg font-semibold tabular-nums">{value}</p><p className="text-[10px] font-medium text-slate-700">{label}</p><p className="text-[9px] text-slate-400">{note}</p></div></div>)}</section>

    <section className="overflow-hidden rounded-lg border border-slate-200 bg-white shadow-sm"><div className="flex flex-col gap-3 border-b border-slate-200 p-3 lg:flex-row lg:items-center lg:justify-between"><div><h2 className="text-sm font-semibold">Quem abordar agora</h2><p className="mt-0.5 text-[10px] text-slate-500">Pessoas agrupadas e ordenadas pela força dos sinais.</p></div><div className="flex min-w-0 flex-col gap-2 sm:flex-row"><div className="relative sm:w-64"><Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" /><input value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar pessoa ou perfil de origem" className="h-9 w-full rounded-lg border border-slate-200 bg-slate-50 pl-8 pr-3 text-[11px] outline-none focus:border-violet-400" /></div><div className="flex gap-1 overflow-x-auto">{([['all','Todos'],['hot','Alta intenção'],['follow','Seguidores'],['comment','Comentários']] as const).map(([value,label]) => <button key={value} onClick={() => setFilter(value)} className={`h-9 shrink-0 rounded-lg border px-3 text-[10px] font-semibold ${filter === value ? 'border-violet-300 bg-violet-50 text-violet-700' : 'border-slate-200 text-slate-600'}`}>{label}</button>)}</div><div className="flex items-center gap-1"><button disabled={page === 1} onClick={() => setPage(value => Math.max(1, value - 1))} title="Página anterior" className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 disabled:opacity-40"><ChevronLeft className="h-4 w-4" /></button><span className="min-w-16 text-center text-[10px] text-slate-500">{page} de {pageCount}</span><button disabled={page === pageCount} onClick={() => setPage(value => Math.min(pageCount, value + 1))} title="Próxima página" className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 disabled:opacity-40"><ChevronRight className="h-4 w-4" /></button></div></div></div>

    <div className="grid min-h-[540px] lg:grid-cols-[390px_minmax(0,1fr)]"><div className="border-b border-slate-200 lg:border-b-0 lg:border-r">{pageItems.map(item => <button key={item.id} onClick={() => setSelectedId(item.id)} className={`flex w-full items-start gap-3 border-b border-slate-100 p-3 text-left ${selected?.id === item.id ? 'bg-violet-50/70' : 'hover:bg-slate-50'}`}><ProspectAvatar item={item} clientId={user?.id_cliente} size="sm" /><div className="min-w-0 flex-1"><div className="flex items-center gap-1.5"><span className="truncate text-xs font-semibold">{item.name}</span>{item.contacted && <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[8px] font-semibold text-blue-700">Em contato</span>}</div><p className="mt-0.5 truncate text-[10px] text-slate-500">{item.handle} · via {item.source}</p><p className="mt-2 truncate text-[10px] font-medium text-slate-700">{item.summary}</p><div className="mt-2 flex items-center gap-1.5">{item.kinds.map(kind => { const meta=kindMeta[kind]; const Icon=meta.icon; return <span key={kind} title={meta.label} className={`flex h-5 w-5 items-center justify-center rounded ${meta.tone}`}><Icon className="h-3 w-3" /></span> })}<span className="ml-auto text-[9px] text-slate-400">{item.seen}</span></div></div><Score item={item} /></button>)}</div>

    {selected && <div className="min-w-0 p-4 sm:p-5"><div className="flex flex-col gap-4 border-b border-slate-100 pb-5 sm:flex-row sm:items-start sm:justify-between"><div className="flex min-w-0 items-center gap-3"><ProspectAvatar item={selected} clientId={user?.id_cliente} size="lg" /><div className="min-w-0"><h3 className="truncate text-base font-semibold">{selected.name}</h3><p className="text-[11px] text-slate-500">{selected.handle}</p><p className="mt-1 truncate text-[10px] text-slate-600">{selected.bio}</p></div></div><div className="flex flex-wrap gap-2"><button onClick={() => window.open('https://instagram.com/' + selected.handle.replace(/^@/, ''), '_blank', 'noopener,noreferrer')} className="inline-flex h-9 items-center gap-2 rounded-lg border border-slate-200 px-3 text-[10px] font-semibold"><Instagram className="h-3.5 w-3.5" /> Abrir perfil <ExternalLink className="h-3 w-3" /></button><button onClick={sendToPipeline} className="inline-flex h-9 items-center gap-2 rounded-lg bg-violet-600 px-3 text-[10px] font-semibold text-white"><UserPlus className="h-3.5 w-3.5" /> Enviar ao Pipeline</button><button onClick={() => void discardSelected()} title="Descartar oportunidade" className="flex h-9 w-9 items-center justify-center rounded-lg border border-slate-200 text-slate-500 hover:border-red-200 hover:text-red-600"><Trash2 className="h-4 w-4" /></button></div></div>

    <div className="grid grid-cols-2 gap-3 border-b border-slate-100 py-4 sm:grid-cols-4"><div><p className="text-[9px] uppercase text-slate-400">Score</p><p className="mt-1 text-sm font-semibold text-emerald-700">{selected.score}/100</p></div><div><p className="text-[9px] uppercase text-slate-400">Confiança</p><p className="mt-1 inline-flex items-center gap-1 text-xs font-semibold"><Check className="h-3.5 w-3.5 text-emerald-600" /> {selected.confidence}</p></div><div><p className="text-[9px] uppercase text-slate-400">Seguidores</p><p className="mt-1 text-xs font-semibold">{selected.followers}</p></div><div><p className="text-[9px] uppercase text-slate-400">Publicações</p><p className="mt-1 text-xs font-semibold">{selected.posts}</p></div></div>

    <div className="grid gap-5 py-5 xl:grid-cols-[minmax(0,1fr)_280px]"><div><div className="mb-3 flex justify-between"><h4 className="text-xs font-semibold">Evidências de intenção</h4><span className="text-[9px] text-slate-400">Mais recente primeiro</span></div><div className="space-y-2">{selected.events.map((event,index) => { const meta=kindMeta[event.kind]; const Icon=meta.icon; return <div key={index} className="flex gap-3 rounded-lg border border-slate-200 p-3"><div className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-lg ${meta.tone}`}><Icon className="h-4 w-4" /></div><div className="min-w-0 flex-1"><div className="flex flex-wrap justify-between gap-2"><p className="text-[11px] font-semibold">{event.title}</p><span className="text-[9px] text-slate-400">{event.time}</span></div><p className="mt-1 text-[10px] leading-4 text-slate-600">{event.detail}</p></div><span className="text-[10px] font-semibold text-emerald-700">+{event.points}</span></div> })}</div></div><aside className="space-y-3"><div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3"><div className="flex items-center gap-2 text-emerald-800"><Sparkles className="h-4 w-4" /><p className="text-[11px] font-semibold">Por que abordar agora</p></div><p className="mt-2 text-[10px] leading-4 text-emerald-900/80">{selected.kinds.includes('comment') ? 'Há comentário recente que oferece contexto concreto para uma abordagem.' : selected.kinds.length > 1 ? 'A pessoa apresentou mais de um tipo de sinal observado recentemente.' : 'A pessoa apareceu recentemente na audiência monitorada. É um sinal inicial, ainda sem intenção explícita.'}</p></div><div className="rounded-lg border border-slate-200 p-3"><div className="flex justify-between"><p className="text-[11px] font-semibold">Abordagem sugerida</p><button title="Copiar abordagem" onClick={() => toast.success('Abordagem copiada.')}><Send className="h-3.5 w-3.5 text-slate-400" /></button></div><p className="mt-2 text-[10px] leading-4 text-slate-600">Oi, {selected.name.split(' ')[0]}! Vi seu interesse recente nos conteúdos de {selected.source}. O que mais chamou sua atenção?</p></div><div className="flex gap-2 rounded-lg bg-slate-50 p-3 text-[9px] leading-4 text-slate-500"><CircleAlert className="mt-0.5 h-3.5 w-3.5 shrink-0" />Os sinais orientam o timing. Evite mencionar que as interações foram monitoradas.</div></aside></div></div>}</div></section>
    <div className="flex items-center justify-between text-[9px] text-slate-400"><span>{demoMode ? 'Dados demonstrativos · nenhuma coleta real está ativa' : 'Dados reais recebidos pelo coletor de sinais'}</span><span className="inline-flex items-center gap-1"><Eye className="h-3 w-3" /> Última atualização há 12 min</span></div>
    {connectionOpen && <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/45 p-4" onMouseDown={() => setConnectionOpen(false)}><div onMouseDown={event => event.stopPropagation()} className="w-full max-w-md rounded-lg bg-white p-5 shadow-2xl"><div className="flex items-start justify-between"><div className="flex gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-lg bg-pink-50 text-pink-600"><Instagram className="h-5 w-5" /></div><div><h2 className="text-sm font-semibold">Instagram para pesquisa</h2><p className="mt-1 text-[10px] leading-4 text-slate-500">Conecte uma conta dedicada para monitorar os perfis selecionados.</p></div></div><button onClick={() => setConnectionOpen(false)} title="Fechar"><X className="h-4 w-4 text-slate-400" /></button></div>{connectedUser ? <div className="mt-5"><div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3"><p className="text-xs font-semibold text-emerald-800">@{connectedUser} conectado</p><p className="mt-1 text-[10px] text-emerald-700">A conta está disponível para o worker de coleta.</p></div><button onClick={() => void disconnectInstagram()} className="mt-4 h-9 w-full rounded-lg border border-red-200 text-xs font-semibold text-red-600">Desconectar conta</button></div> : <div className="mt-5 space-y-3"><label className="block"><span className="text-[10px] font-semibold text-slate-600">Usuário</span><input value={instagramUser} onChange={event => setInstagramUser(event.target.value)} autoComplete="username" placeholder="@usuario" className="mt-1 h-10 w-full rounded-lg border border-slate-200 px-3 text-xs outline-none focus:border-violet-400" /></label><label className="block"><span className="text-[10px] font-semibold text-slate-600">Senha</span><input value={instagramPassword} onChange={event => setInstagramPassword(event.target.value)} onKeyDown={event => event.key === 'Enter' && void connectInstagram()} type="password" autoComplete="current-password" className="mt-1 h-10 w-full rounded-lg border border-slate-200 px-3 text-xs outline-none focus:border-violet-400" /></label><div className="flex gap-2 rounded-lg bg-slate-50 p-3 text-[9px] leading-4 text-slate-500"><LockKeyhole className="mt-0.5 h-3.5 w-3.5 shrink-0" />A senha é enviada por conexão local autenticada, criptografada no servidor e nunca exibida novamente.</div><button disabled={connecting || !instagramUser.trim() || !instagramPassword} onClick={() => void connectInstagram()} className="h-10 w-full rounded-lg bg-slate-900 text-xs font-semibold text-white disabled:opacity-50">{connecting ? 'Conectando...' : 'Conectar Instagram'}</button></div>}</div></div>}
  </div></main>;
}















