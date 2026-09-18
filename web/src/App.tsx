import { Toaster } from 'sonner';
import { Activity, BarChart3, Bot, ClipboardList, Facebook, Gauge, Headphones, Home, Instagram, MessageSquare, Settings, Target } from 'lucide-react';
import PesquisaPage from './pages/pesquisa';
import './styles.css';

const menu = [
  ['Visão Geral', Home], ['Produtividade', Activity], ['Diagnósticos', BarChart3], ['Ações', ClipboardList], ['Pesquisa', Target],
  ['Atendimento', MessageSquare], ['Pipeline', Gauge], ['Funis', Facebook], ['Assistente Inteligente', Bot], ['Integrações', Headphones], ['Configurações', Settings],
] as const;

export default function App() {
  return <div className="shell"><aside className="sidebar"><div className="brand"><span className="brand-mark">◉</span><span>Smart<span>CHAT</span></span></div><nav>{menu.map(([label, Icon], index) => <div key={label}>{[1, 5, 8, 9].includes(index) && <p className="nav-heading">{index === 1 ? 'ANÁLISE' : index === 5 ? 'OPERAÇÃO' : index === 8 ? 'INTELIGÊNCIA' : 'CONFIGURAÇÃO'}</p>}<a className={label === 'Pesquisa' ? 'nav-item active' : 'nav-item'}><Icon size={19}/><span>{label}</span></a></div>)}</nav></aside><section className="page"><PesquisaPage /></section><Toaster position="bottom-right" richColors /></div>;
}
