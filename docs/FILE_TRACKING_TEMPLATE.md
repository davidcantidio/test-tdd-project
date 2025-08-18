# 📋 **FILE TRACKING TEMPLATE**

**Created:** 2025-08-18  
**Purpose:** Template padrão para tracking de arquivos modificados  
**Usage:** Usar após QUALQUER operação que modifique arquivos

---

## 🎯 **TEMPLATE PADRÃO PÓS-EXECUÇÃO**

```
📊 **ARQUIVOS MODIFICADOS NESTA OPERAÇÃO:**

**Arquivos Criados:**
- [arquivo1.py] - [Descrição do propósito e funcionalidade]
- [arquivo2.md] - [Descrição do conteúdo e objetivo]

**Arquivos Modificados:**
- [arquivo3.py:linhas_X-Y] - [Descrição específica das mudanças]
- [arquivo4.md:seção_Z] - [Descrição das alterações realizadas]

**Arquivos Removidos:**
- [arquivo5_obsoleto.py] - [Razão da remoção]

**Status:** Pronto para revisão manual
**Impact:** [Descrição do impacto funcional/técnico/performance]
**Next:** Validar cada arquivo antes de continuar
```

---

## 📋 **TEMPLATES ESPECÍFICOS POR MÓDULO**

### **🗄️ Database Module**
```
📊 **DATABASE MODULE - ARQUIVOS MODIFICADOS:**

**Core Database:**
- streamlit_extension/database/[arquivo] - [mudança na API/performance/funcionalidade]

**Utils Database:**
- streamlit_extension/utils/database.py - [mudança no DatabaseManager]

**Status:** Pronto para revisão manual
**Performance Impact:** [Impacto na performance: Melhoria/Neutro/Degradação]
**Breaking Changes:** [Sim/Não - detalhes se aplicável]
```

### **📱 Streamlit Extension**
```
📊 **STREAMLIT EXTENSION - ARQUIVOS MODIFICADOS:**

**Database Layer:**
- streamlit_extension/database/[arquivo] - [mudança específica]

**Services Layer:**  
- streamlit_extension/services/[arquivo] - [mudança específica]

**UI Components:**
- streamlit_extension/components/[arquivo] - [mudança específica]
- streamlit_extension/pages/[arquivo] - [mudança específica]

**Utils & Config:**
- streamlit_extension/utils/[arquivo] - [mudança específica]
- streamlit_extension/config/[arquivo] - [mudança específica]

**Status:** Pronto para revisão manual
**Impact:** [Impacto na funcionalidade/performance/segurança]
```

### **🔧 Scripts**
```
📊 **SCRIPTS - ARQUIVOS MODIFICADOS:**

**Testing Scripts:**
- scripts/testing/[arquivo].py - [funcionalidade alterada/corrigida]

**Maintenance Scripts:**
- scripts/maintenance/[arquivo].py - [operação alterada/otimizada]

**Migration Scripts:**
- scripts/migration/[arquivo].py - [processo alterado/corrigido]

**Analysis Scripts:**
- scripts/analysis/[arquivo].py - [análise alterada/melhorada]

**Setup Scripts:**
- scripts/setup/[arquivo].py - [setup alterado/otimizado]

**Status:** Pronto para revisão manual
**Validation:** [Testes executados: --help, --dry-run, integration]
**Impact:** [Impacto nos workflows existentes]
```

### **📚 Documentation**
```
📊 **DOCUMENTATION - ARQUIVOS MODIFICADOS:**

**Main Documentation:**
- README.md - [seção alterada e motivo]
- CLAUDE.md - [atualização de status/práticas]

**Module Documentation:**
- [module]/CLAUDE.md - [seção específica alterada]

**Guides & Tutorials:**
- docs/[guia].md - [conteúdo alterado/adicionado]

**Status:** Pronto para revisão manual
**Impact:** [Impacto na documentação: Correção/Adição/Melhoria]
```

---

## ✅ **CHECKLIST UNIVERSAL**

### **Pré-Operação**
- [ ] Backup dos arquivos críticos
- [ ] Validação de dependências  
- [ ] Verificação de breaking changes potenciais

### **Pós-Operação**
- [ ] Lista completa de arquivos modificados gerada
- [ ] Descrição do propósito de cada mudança
- [ ] Validação manual de cada arquivo
- [ ] Testes funcionais executados (se aplicável)
- [ ] Performance validada (se aplicável)
- [ ] Aprovação recebida antes da próxima etapa

---

## 🚨 **REGRAS OBRIGATÓRIAS**

1. **SEMPRE** gerar lista após cada operação
2. **SEMPRE** pausar para revisão manual
3. **SEMPRE** incluir descrição do propósito
4. **SEMPRE** aguardar aprovação antes de continuar
5. **NUNCA** prosseguir sem completar checklist

---

**Template preparado para uso imediato em todas as operações de modificação de arquivos.**