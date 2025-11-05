import { ReactNode, useState } from 'react';
import { Link, useLocation } from 'wouter';
import { 
  LayoutGrid, 
  Wallet, 
  CreditCard, 
  FileText, 
  User,
  Settings,
  Search,
  Bell,
  HelpCircle,
  Plus,
  X,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  BookOpen,
  BarChart3
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface DashboardLayoutProps {
  children: ReactNode;
}

const sidebarIcons = [
  { icon: LayoutGrid, label: 'Dashboard', path: '/' },
  { icon: FileText, label: 'Análise Individual', path: '/analise' },
  { icon: Wallet, label: 'Análise em Lote', path: '/lote' },
  { icon: BarChart3, label: 'Métricas', path: '/metricas' },
];

const tabs = [
  { name: 'Overview', path: '/' },
  { name: 'Análise Individual', path: '/analise' },
  { name: 'Análise em Lote', path: '/lote' },
  { name: 'Métricas', path: '/metricas' },
];

const mockNotifications = [
  {
    id: 1,
    type: 'alert',
    icon: AlertTriangle,
    title: 'Alto Risco Detectado',
    description: 'Cliente #45821 - R$ 50.000',
    time: '5 min atrás',
    color: 'text-red-500'
  },
  {
    id: 2,
    type: 'success',
    icon: CheckCircle,
    title: 'Análise Concluída',
    description: '150 clientes processados',
    time: '15 min atrás',
    color: 'text-green-500'
  },
  {
    id: 3,
    type: 'info',
    icon: TrendingUp,
    title: 'Meta Atingida',
    description: 'Taxa de aprovação: 75%',
    time: '1 hora atrás',
    color: 'text-blue-500'
  }
];

export default function DashboardLayout({ children }: DashboardLayoutProps) {
  const [location, setLocation] = useLocation();
  const [searchOpen, setSearchOpen] = useState(false);
  const [helpOpen, setHelpOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  return (
    <div className="flex h-screen bg-[#0B0E12] text-foreground overflow-hidden">
      {/* Sidebar Vertical */}
      <aside className="w-24 bg-black/40 backdrop-blur-xl border-r border-white/5 flex flex-col items-center py-8 gap-6">
        {/* Logo */}
        <Link href="/">
          <button className="w-12 h-12 rounded-2xl bg-gradient-to-br from-primary to-chart-2 flex items-center justify-center mb-4 hover:scale-110 transition-transform">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" className="text-white">
              <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
              <path d="M12 6v6l4 2" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </button>
        </Link>

        {/* Navigation Icons */}
        <nav className="flex-1 flex flex-col gap-4">
          {sidebarIcons.map((item, index) => {
            const Icon = item.icon;
            const isActive = location === item.path;
            return (
              <Link key={index} href={item.path}>
                <button
                  className={`w-14 h-14 rounded-2xl flex items-center justify-center transition-all duration-200 group relative ${
                    isActive
                      ? 'bg-primary/15 text-primary'
                      : 'text-muted-foreground hover:text-primary hover:bg-white/5'
                  }`}
                  title={item.label}
                >
                  <Icon className="w-6 h-6" strokeWidth={1.5} />
                  {/* Tooltip */}
                  <div className="absolute left-20 px-3 py-2 bg-black/90 backdrop-blur-xl border border-white/10 rounded-lg text-sm text-foreground whitespace-nowrap opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" style={{ zIndex: 99999 }}>
                    {item.label}
                  </div>
                </button>
              </Link>
            );
          })}
        </nav>


      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Top Header */}
        <header className="border-b border-white/5 bg-black/20 backdrop-blur-xl">
          <div className="flex items-center justify-between px-8 py-4">
            {/* Logo + Tabs */}
            <div className="flex items-center gap-8">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-xl bg-primary flex items-center justify-center">
                  <span className="text-sm font-bold text-white">S</span>
                </div>
                <span className="text-lg font-bold text-foreground">Santander</span>
              </div>

              {/* Tabs */}
              <nav className="flex items-center gap-2">
                {tabs.map((tab) => {
                  const isActive = location === tab.path;
                  return (
                    <Link key={tab.path} href={tab.path}>
                      <button
                        className={`px-5 py-2 rounded-xl text-sm font-medium transition-all duration-200 ${
                          isActive
                            ? 'bg-primary/10 text-primary border border-primary/20'
                            : 'text-muted-foreground hover:text-foreground hover:bg-white/5'
                        }`}
                      >
                        {tab.name}
                      </button>
                    </Link>
                  );
                })}
              </nav>
            </div>

            {/* Right Icons */}
            <div className="flex items-center gap-3">
              {/* Search */}
              <button 
                onClick={() => setSearchOpen(true)}
                className="w-10 h-10 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-white/5 transition-all"
              >
                <Search className="w-5 h-5" />
              </button>

              {/* Notifications Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <button className="w-10 h-10 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-white/5 transition-all relative">
                    <Bell className="w-5 h-5" />
                    <span className="absolute top-1 right-1 w-2 h-2 bg-primary rounded-full animate-pulse" />
                  </button>
                </DropdownMenuTrigger>
                <DropdownMenuContent 
                  align="end" 
                  className="w-80 bg-[#1A1D2E]/95 backdrop-blur-xl border-white/10 p-0"
                >
                  <div className="p-4 border-b border-white/5">
                    <h3 className="text-sm font-bold text-foreground">Notificações</h3>
                    <p className="text-xs text-muted-foreground">Você tem {mockNotifications.length} notificações</p>
                  </div>
                  <div className="max-h-96 overflow-y-auto">
                    {mockNotifications.map((notification) => {
                      const Icon = notification.icon;
                      return (
                        <DropdownMenuItem 
                          key={notification.id}
                          className="p-4 cursor-pointer hover:bg-white/5 focus:bg-white/5"
                        >
                          <div className="flex items-start gap-3">
                            <div className={`w-10 h-10 rounded-xl bg-white/5 flex items-center justify-center ${notification.color}`}>
                              <Icon className="w-5 h-5" />
                            </div>
                            <div className="flex-1 min-w-0">
                              <p className="text-sm font-medium text-foreground">{notification.title}</p>
                              <p className="text-xs text-muted-foreground">{notification.description}</p>
                              <p className="text-xs text-muted-foreground mt-1">{notification.time}</p>
                            </div>
                          </div>
                        </DropdownMenuItem>
                      );
                    })}
                  </div>
                  <div className="p-3 border-t border-white/5">
                    <button className="w-full text-center text-sm text-primary hover:text-primary/80 transition-colors">
                      Ver todas as notificações
                    </button>
                  </div>
                </DropdownMenuContent>
              </DropdownMenu>

              {/* Help */}
              <button 
                onClick={() => setHelpOpen(true)}
                className="w-10 h-10 rounded-xl flex items-center justify-center text-muted-foreground hover:text-foreground hover:bg-white/5 transition-all"
              >
                <HelpCircle className="w-5 h-5" />
              </button>
              
              {/* User Profile */}
              <div className="flex items-center gap-3 ml-2 pl-3 border-l border-white/10">
                <div className="w-10 h-10 rounded-full bg-primary flex items-center justify-center">
                  <span className="text-sm font-bold text-white">AD</span>
                </div>
                <div className="text-left">
                  <p className="text-sm font-medium text-foreground">Admin Santander</p>
                  <p className="text-xs text-muted-foreground">admin@santander.com.br</p>
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Content Area */}
        <main className="flex-1 overflow-y-auto">
          {children}
        </main>
      </div>

      {/* Search Modal */}
      <Dialog open={searchOpen} onOpenChange={setSearchOpen}>
        <DialogContent className="bg-[#1A1D2E]/95 backdrop-blur-xl border-white/10 max-w-2xl">
          <DialogHeader>
            <DialogTitle className="text-foreground">Buscar</DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Pesquise por clientes, análises ou documentos
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground" />
              <Input
                placeholder="Digite sua busca..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10 bg-white/5 border-white/10 focus:border-primary/50"
                autoFocus
              />
            </div>
            {searchQuery && (
              <div className="space-y-2">
                <p className="text-sm text-muted-foreground">Resultados para "{searchQuery}":</p>
                <div className="space-y-2">
                  {[
                    { title: 'Cliente #45821', type: 'Cliente', risk: 'Alto' },
                    { title: 'Análise em Lote - 150 clientes', type: 'Análise', risk: 'Médio' },
                    { title: 'Relatório Mensal', type: 'Documento', risk: 'Baixo' }
                  ].map((result, index) => (
                    <button
                      key={index}
                      className="w-full p-3 rounded-xl bg-white/5 hover:bg-white/10 transition-all text-left"
                    >
                      <p className="text-sm font-medium text-foreground">{result.title}</p>
                      <p className="text-xs text-muted-foreground">{result.type} • Risco: {result.risk}</p>
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </DialogContent>
      </Dialog>

      {/* Help Modal */}
      <Dialog open={helpOpen} onOpenChange={setHelpOpen}>
        <DialogContent className="bg-[#1A1D2E]/95 backdrop-blur-xl border-white/10 max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-foreground flex items-center gap-2">
              <BookOpen className="w-5 h-5 text-primary" />
              Central de Ajuda
            </DialogTitle>
            <DialogDescription className="text-muted-foreground">
              Documentação e guia de uso do sistema
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-6">
            {/* Overview */}
            <div>
              <h3 className="text-lg font-bold text-foreground mb-3">Dashboard Overview</h3>
              <p className="text-sm text-muted-foreground mb-2">
                Visualize métricas executivas em tempo real: total de análises, tendências de risco, 
                metas de performance, distribuição por categoria e limites de exposição.
              </p>
            </div>

            {/* Análise Individual */}
            <div>
              <h3 className="text-lg font-bold text-foreground mb-3">Análise Individual</h3>
              <p className="text-sm text-muted-foreground mb-2">
                Avalie o risco de crédito de um cliente específico preenchendo os campos:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1 ml-4">
                <li>Idade, Renda Mensal, Valor do Empréstimo</li>
                <li>Prazo, Score de Crédito, Dívida/Renda Ratio</li>
                <li>Número de Contas, Taxa de Juros</li>
              </ul>
              <p className="text-sm text-muted-foreground mt-2">
                O sistema retorna: status (aprovado/negado), probabilidade, score de risco e fatores principais.
              </p>
            </div>

            {/* Análise em Lote */}
            <div>
              <h3 className="text-lg font-bold text-foreground mb-3">Análise em Lote</h3>
              <p className="text-sm text-muted-foreground mb-2">
                Processe múltiplas análises simultaneamente:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1 ml-4">
                <li>Faça upload de arquivo CSV ou Excel</li>
                <li>Baixe o template para garantir formato correto</li>
                <li>Visualize resultados em tabela interativa</li>
                <li>Exporte resultados processados</li>
              </ul>
            </div>

            {/* Métricas */}
            <div>
              <h3 className="text-lg font-bold text-foreground mb-3">Métricas do Modelo</h3>
              <p className="text-sm text-muted-foreground mb-2">
                Acompanhe a performance do modelo de machine learning:
              </p>
              <ul className="list-disc list-inside text-sm text-muted-foreground space-y-1 ml-4">
                <li><strong>AUC-ROC:</strong> Área sob a curva ROC (0.94)</li>
                <li><strong>Precision:</strong> Precisão das predições (92.3%)</li>
                <li><strong>Recall:</strong> Sensibilidade do modelo (94.9%)</li>
                <li><strong>F1-Score:</strong> Média harmônica (93.6%)</li>
              </ul>
            </div>


          </div>
        </DialogContent>
      </Dialog>
    </div>
  );
}
