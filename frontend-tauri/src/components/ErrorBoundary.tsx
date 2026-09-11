import { Component, type ErrorInfo, type ReactNode } from 'react';

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  erro: Error | null;
}

/**
 * Boundary de erro: impede que uma exceção em render de componente
 * quebre a aplicação inteira (tela branca). Renderiza um fallback
 * com a mensagem do erro e um botão para recarregar.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, erro: null };
  }

  static getDerivedStateFromError(erro: Error): ErrorBoundaryState {
    return { hasError: true, erro };
  }

  componentDidCatch(erro: Error, info: ErrorInfo) {
    console.error('[ErrorBoundary] erro não capturado:', erro, info);
  }

  render(): ReactNode {
    if (!this.state.hasError) {
      return this.props.children;
    }
    return (
      <div
        className="h-screen w-screen flex flex-col items-center justify-center gap-4 p-8 text-center"
        style={{ background: 'var(--maria-card)', color: 'var(--maria-text)' }}
      >
        <h1 className="text-lg font-bold">Ocorreu um erro inesperado</h1>
        <p className="text-sm max-w-md" style={{ color: 'var(--maria-muted)' }}>
          {this.state.erro?.message ?? 'Erro desconhecido'}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 rounded-lg text-sm font-medium"
          style={{ background: 'var(--maria-pink)', color: '#fff' }}
        >
          Recarregar
        </button>
      </div>
    );
  }
}
