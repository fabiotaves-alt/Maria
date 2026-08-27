package com.tristar.maria.dao;

import org.junit.jupiter.api.*;
import java.sql.SQLException;
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
}
