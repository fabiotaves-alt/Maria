package com.tristar.maria.dao;

import org.junit.jupiter.api.*;
import java.sql.SQLException;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

@TestInstance(TestInstance.Lifecycle.PER_CLASS)
public class DatabaseManagerTest {
    
    private DatabaseManager dbManager;
    
    @BeforeAll
    public void setUp() throws SQLException {
        dbManager = DatabaseManager.getInstance();
        dbManager.inicializarTabelas();
    }
    
    @Test
    @DisplayName("Deve inicializar o banco de dados sem erros")
    public void testInicializarBancoDados() throws SQLException {
        assertNotNull(dbManager);
        assertNotNull(dbManager.conectar());
        assertFalse(dbManager.conectar().isClosed());
    }
    
    @Test
    @DisplayName("Deve instanciar todos os DAOs necessários")
    public void testTabelasCriadas() throws SQLException {
        var conversaDao = dbManager.getConversaDAO();
        assertNotNull(conversaDao);
        
        var memoriaDao = dbManager.getMemoriaDAO();
        assertNotNull(memoriaDao);
        
        var automacaoDao = dbManager.getAutomacaoDAO();
        assertNotNull(automacaoDao);
        
        var configDao = dbManager.getConfiguracaoDAO();
        assertNotNull(configDao);
    }
    
    @Test
    @DisplayName("Deve adicionar e recuperar memórias com schema unificado")
    public void testMemoriaCrud() throws SQLException {
        var memoriaDao = dbManager.getMemoriaDAO();
        
        // Adicionar memória
        memoriaDao.adicionarMemoria("Teste de fato persistente", "preferencias", "manual");
        
        // Recuperar memórias
        List<MemoriaDAO.Memoria> memorias = memoriaDao.getMemorias(null);
        assertFalse(memorias.isEmpty());
        
        // Buscar por termo
        List<MemoriaDAO.Memoria> buscadas = memoriaDao.buscarMemorias("persistente");
        assertFalse(buscadas.isEmpty());
        assertEquals("Teste de fato persistente", buscadas.get(0).getFato());
        assertEquals("preferencias", buscadas.get(0).getCategoria());
        
        // Deletar memória
        memoriaDao.deletarMemoria(buscadas.get(0).getId());
    }
    
    @Test
    @DisplayName("Deve limpar todas as memórias")
    public void testLimparMemorias() throws SQLException {
        var memoriaDao = dbManager.getMemoriaDAO();
        
        // Adicionar memória para teste
        memoriaDao.adicionarMemoria("Memória para limpar", "teste", "unit");
        
        // Limpar todas
        memoriaDao.limparTodasMemorias();
        
        // Verificar que está vazio
        assertEquals(0, memoriaDao.contarMemorias());
    }
    
    @Test
    @DisplayName("Deve gerenciar configurações chave-valor")
    public void testConfiguracaoCrud() throws SQLException {
        var configDao = dbManager.getConfiguracaoDAO();
        
        // Salvar configuração
        configDao.salvarConfiguracao("teste_chave", "teste_valor", "Chave de teste");
        
        // Buscar configuração
        String valor = configDao.buscarConfiguracao("teste_chave").orElse(null);
        assertEquals("teste_valor", valor);
        
        // Atualizar configuração
        configDao.salvarConfiguracao("teste_chave", "valor_atualizado");
        String novoValor = configDao.buscarConfiguracao("teste_chave").orElse(null);
        assertEquals("valor_atualizado", novoValor);
        
        // Deletar
        configDao.deletarConfiguracao("teste_chave");
        assertFalse(configDao.existe("teste_chave"));
    }
    
    @Test
    @DisplayName("Deve gerenciar automações")
    public void testAutomacaoCrud() throws SQLException {
        var automacaoDao = dbManager.getAutomacaoDAO();
        
        // Criar automação
        automacaoDao.criarAutomacao("Auto Teste", "Quando abrir", "Notificar", true);
        
        List<AutomacaoDAO.Automacao> lista = automacaoDao.buscarPorNome("Auto Teste");
        assertFalse(lista.isEmpty());
        Long id = lista.get(0).getId();
        assertTrue(lista.get(0).isAtiva());
        
        // Toggle
        automacaoDao.toggleAtiva(id, false);
        List<AutomacaoDAO.Automacao> inativas = automacaoDao.getTodasAutomacoes();
        assertTrue(inativas.stream().anyMatch(a -> a.getId().equals(id) && !a.isAtiva()));
        
        // Deletar
        automacaoDao.deletarAutomacao(id);
    }
    
    @Test
    @DisplayName("Deve gerenciar conversas e mensagens com ON DELETE CASCADE")
    public void testConversaEMensagensCascade() throws SQLException {
        var conversaDao = dbManager.getConversaDAO();
        
        long convId = conversaDao.criarConversa("Conversa de Teste JUnit");
        assertTrue(convId > 0);
        
        conversaDao.salvarMensagem(convId, "user", "Olá Maria!", null);
        conversaDao.salvarMensagem(convId, "assistant", "Olá! Como posso ajudar?", null);
        
        assertEquals(2, conversaDao.contarMensagens(convId));
        
        List<ConversaDAO.Mensagem> msgs = conversaDao.getMensagensPorConversa(convId);
        assertEquals(2, msgs.size());
        assertEquals("user", msgs.get(0).getRole());
        assertEquals("Olá Maria!", msgs.get(0).getConteudo());
        
        // Deletar conversa deve deletar mensagens em cascata
        conversaDao.limparConversa(convId);
        assertEquals(0, conversaDao.contarMensagens(convId));
    }
    
    @Test
    @DisplayName("Deve fechar conexão corretamente")
    public void testFechaConexao() {
        dbManager.fechar();
        assertDoesNotThrow(() -> dbManager.conectar());
    }
}
