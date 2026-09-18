import { Toaster } from 'sonner';
import { Target } from 'lucide-react';
import PesquisaPage from './pages/pesquisa';
import './styles.css';

export default function App() {
  return <div className="shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">◉</span><span>Smart<span>CHAT</span></span></div>
      <nav>
        <p className="nav-heading">ANÁLISE</p>
        <a className="nav-item active"><Target size={19}/><span>Pesquisa</span></a>
      </nav>
    </aside>
    <section className="page"><PesquisaPage /></section>
    <Toaster position="bottom-right" richColors />
  </div>;
}
