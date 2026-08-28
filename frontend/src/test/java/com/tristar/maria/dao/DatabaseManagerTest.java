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
    @DisplayName("Deve criar todas as tabelas necessárias")
    public void testTabelasCriadas() throws SQLException {
        var dao = dbManager.getConversaDAO();
        assertNotNull(dao);
        
        var memoriaDao = dbManager.getMemoriaDAO();
        assertNotNull(memoriaDao);
        
        var automacaoDao = dbManager.getAutomacaoDAO();
        assertNotNull(automacaoDao);
        
        var configDao = dbManager.getConfiguracaoDAO();
        assertNotNull(configDao);
    }
    
    @Test
    @DisplayName("Deve adicionar e recuperar memórias")
    public void testMemoriaCrud() throws SQLException {
        var memoriaDao = dbManager.getMemoriaDAO();
        
        // Adicionar memória
        memoriaDao.adicionarMemoria("Teste de memória", "teste", "unit");
        
        // Recuperar memórias
        List<MemoriaDAO.Memoria> memorias = memoriaDao.getMemorias(null);
        assertTrue(memorias.size() > 0);
        
        // Buscar por termo
        List<MemoriaDAO.Memoria> buscadas = memoriaDao.buscarMemorias("Teste");
        assertTrue(buscadas.size() > 0);
        
        // Deletar memória
        if (!buscadas.isEmpty()) {
            memoriaDao.deletarMemoria(buscadas.get(0).getId());
        }
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
    @DisplayName("Deve gerenciar configurações")
    public void testConfiguracaoCrud() throws SQLException {
        var configDao = dbManager.getConfiguracaoDAO();
        
        // Salvar configuração
        configDao.salvarConfiguracao("teste_chave", "teste_valor");
        
        // Buscar configuração
        String valor = configDao.buscarConfiguracao("teste_chave").orElse(null);
        assertEquals("teste_valor", valor);
        
        // Atualizar configuração
        configDao.salvarConfiguracao("teste_chave", "valor_atualizado");
        String novoValor = configDao.buscarConfiguracao("teste_chave").orElse(null);
        assertEquals("valor_atualizado", novoValor);
    }
    
    @Test
    @DisplayName("Deve fechar conexão corretamente")
    public void testFechaConexao() {
        dbManager.fechar();
        // Após fechar, nova chamada deve criar nova conexão
        assertDoesNotThrow(() -> dbManager.conectar());
    }
}
