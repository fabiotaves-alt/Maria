import { useState } from 'react'
import { invoke } from '@tauri-apps/api/core'
import { Send, Mic, Paperclip } from 'lucide-react'
import { motion } from 'framer-motion'

interface Message {
  role: 'user' | 'assistant' | 'system'
  content: string
}

export function ConversarPage() {
  const [mensagem, setMensagem] = useState('')
  const [carregando, setCarregando] = useState(false)
  const [mensagens, setMensagens] = useState<Message[]>([
    { role: 'assistant', content: 'Olá! Sou a MARIA, sua assistente de IA pessoal. Como posso ajudar você hoje?' }
  ])

  const enviarMensagem = async () => {
    if (!mensagem.trim() || carregando) return

    const texto = mensagem
    setMensagem('')
    setMensagens(prev => [...prev, { role: 'user', content: texto }])
    setCarregando(true)

    try {
      // Tenta usar o comando Tauri, fallback para API HTTP direta
      let resposta: string
      try {
        resposta = await invoke<string>('send_message', { message: texto })
      } catch {
        // Fallback para HTTP direto se backend Tauri não estiver disponível
        const response = await fetch('http://localhost:8081/chat', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            id: crypto.randomUUID(),
            comando: 'chat',
            dados: { mensagem: texto }
          })
        })
        const data = await response.json()
        resposta = data.dados || 'Erro ao processar mensagem'
      }

      setMensagens(prev => [...prev, { role: 'assistant', content: resposta }])
    } catch (erro) {
      setMensagens(prev => [...prev, { 
        role: 'system', 
        content: `Erro: ${erro instanceof Error ? erro.message : String(erro)}` 
      }])
    } finally {
      setCarregando(false)
    }
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      enviarMensagem()
    }
  }

  return (
    <div className="flex flex-col h-full gradient-bg">
      {/* Header com aura */}
      <header className="p-6 border-b border-white/10">
        <div className="flex items-center gap-4">
          <motion.div 
            className="w-16 h-16 rounded-full bg-gradient-to-br from-pink-500 to-purple-600 aura-pink flex items-center justify-center text-2xl font-bold"
            animate={{ scale: [1, 1.05, 1] }}
            transition={{ duration: 3, repeat: Infinity }}
          >
            M
          </motion.div>
          <div>
            <h1 className="text-2xl font-bold text-white">MARIA</h1>
            <p className="text-maria-pink text-sm">Assistente de IA Pessoal • 100% Local</p>
          </div>
        </div>
      </header>

      {/* Área de mensagens */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        {mensagens.map((msg, idx) => (
          <motion.div
            key={idx}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-[80%] rounded-2xl px-4 py-3 glass-panel ${
                msg.role === 'user' 
                  ? 'bg-maria-pink/20 border-pink-500/30' 
                  : msg.role === 'system'
                  ? 'bg-red-500/20 border-red-500/30'
                  : 'bg-white/10'
              }`}
            >
              <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
            </div>
          </motion.div>
        ))}
        
        {carregando && (
          <motion.div 
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex justify-start"
          >
            <div className="glass-panel px-4 py-3 rounded-2xl">
              <div className="flex gap-2">
                <div className="w-2 h-2 bg-maria-pink rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-maria-pink rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-maria-pink rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </motion.div>
        )}
      </div>

      {/* Input area */}
      <div className="p-6 border-t border-white/10">
        <div className="glass-panel p-2 flex items-end gap-2">
          <button className="glass-button p-2" title="Anexar arquivo">
            <Paperclip size={20} />
          </button>
          
          <textarea
            value={mensagem}
            onChange={(e) => setMensagem(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Digite sua mensagem..."
            className="flex-1 bg-transparent border-none outline-none resize-none text-white placeholder-gray-400 py-2 px-3 max-h-32 min-h-[44px]"
            rows={1}
          />
          
          <button className="glass-button p-2" title="Usar voz">
            <Mic size={20} />
          </button>
          
          <button
            onClick={enviarMensagem}
            disabled={carregando || !mensagem.trim()}
            className="bg-maria-pink hover:bg-pink-600 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg p-3 transition-all duration-200 aura-pink"
          >
            <Send size={20} />
          </button>
        </div>
        
        <p className="text-xs text-gray-400 mt-2 text-center">
          MARIA processa tudo localmente • Seus dados nunca saem do seu computador
        </p>
      </div>
    </div>
  )
}
