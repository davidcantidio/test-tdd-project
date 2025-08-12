# 🔄 PLANO DE ROLLBACK - MIGRAÇÃO FASE 1.1.1

## 📋 Objetivo
Procedimento para reverter migração em caso de falha ou problemas.

## ⚠️ Pré-requisitos para Rollback
1. **Backup completo** dos arquivos JSON originais
2. **Snapshot** do banco SQLite antes da migração
3. **Lista de scripts** executados durante migração
4. **Log detalhado** de todas as operações

## 🔧 Procedimentos de Rollback

### 1. Rollback Imediato (< 1 hora após migração)
```bash
# Para SQLite
rm framework.db
cp framework.db.backup framework.db

# Para arquivos JSON
rm -rf epics_migrated/
cp -r epics_backup/ epics/

# Restaura configurações
git checkout HEAD -- .env config/
```

### 2. Rollback Tardio (> 1 hora, com dados novos)
- Exportar dados criados após migração
- Restaurar estado anterior
- Re-importar dados novos compatíveis

### 3. Validação Pós-Rollback
```bash
# Verifica integridade dos dados
python3 validate_rollback.py

# Testa funcionalidades críticas
python3 test_gantt_tracker.py
python3 test_analytics_engine.py
```

## 📊 Critérios para Rollback
- **Performance**: Sistema > 50% mais lento
- **Data Loss**: Perda de qualquer dado crítico
- **Functionality**: Quebra de funcionalidades existentes
- **Integration**: Falha na integração com GitHub
- **User Experience**: Interface inutilizável

## 📝 Checklist de Rollback
- [ ] Backup verificado e acessível
- [ ] Usuários notificados sobre rollback
- [ ] Logs da migração preservados
- [ ] Dados novos exportados (se possível)
- [ ] Sistema restaurado para estado anterior
- [ ] Funcionalidades críticas testadas
- [ ] Performance validada
- [ ] Usuários notificados sobre conclusão
- [ ] Post-mortem agendado
