# 🔧 Ref Tools MCP Configuration

**MCP Server:** ref-tools-mcp  
**Purpose:** Token-efficient documentation search with hallucination prevention  
**Status:** **CONFIGURED** ✅  
**Date:** 2025-08-21

---

## 📊 **Ref Tools MCP Overview**

**Ref Tools MCP** é um servidor MCP (Model Context Protocol) que oferece:
- **Busca inteligente de documentação** com eficiência de tokens
- **Leitura contextual de URLs** com filtros relevantes
- **Prevenção de alucinações** através de dados reais
- **Suporte a múltiplos transports**: stdio e HTTP
- **Compatibilidade OpenAI Deep Research**

### **🎯 Principais Recursos**

1. **ref_search_documentation**: Busca em documentação pública/privada
2. **ref_read_url**: Leitura contextual de URLs específicas  
3. **Filtros inteligentes**: Remove seções irrelevantes para economizar tokens
4. **Session tracking**: Evita resultados repetidos
5. **Context-aware**: Retorna apenas os 5k tokens mais relevantes

---

## ⚙️ **Configuração para Claude Code**

### **1. Instalação Streamable HTTP (Recomendado)**

```json
{
  "mcpServers": {
    "ref-tools": {
      "type": "http",
      "url": "https://api.ref.tools/mcp",
      "headers": {
        "x-ref-api-key": "SEU_REF_API_KEY_AQUI"
      }
    }
  }
}
```

### **2. Instalação Local (Stdio)**

```json
{
  "mcpServers": {
    "ref-tools": {
      "command": "npx",
      "args": ["ref-tools-mcp@latest"],
      "env": {
        "REF_API_KEY": "SEU_REF_API_KEY_AQUI"
      }
    }
  }
}
```

### **3. Obtenção da API Key**

1. Acesse [ref.tools](https://ref.tools)
2. Faça sign up para obter uma API key
3. Configure a variável de ambiente ou header

---

## 🛠️ **Setup Local para Desenvolvimento**

### **1. Clone e Build**

```bash
# Clone o repositório
git clone https://github.com/ref-tools/ref-tools-mcp.git
cd ref-tools-mcp

# Instale dependências
npm install

# Build do projeto
npm run build

# Para desenvolvimento com rebuild automático
npm run watch
```

### **2. Testing com MCP Inspector**

```bash
# Teste local com inspector
npm run inspect

# Ou execute ambos (watch + inspect)
npm run dev
```

### **3. Configuração de Ambiente**

```bash
# Adicione ao seu .env
REF_API_KEY=your_api_key_here

# Para HTTP transport
TRANSPORT=http
PORT=8080

# Para stdio transport (padrão)
TRANSPORT=stdio
```

---

## 🔍 **Tools Disponíveis**

### **1. ref_search_documentation**

**Descrição**: Busca poderosa em documentação técnica  
**Parâmetros**:
- `query` (required): Query para buscar documentação relevante

**Exemplo de uso**:
```json
{
  "name": "ref_search_documentation",
  "arguments": {
    "query": "Python fastapi cors middleware setup"
  }
}
```

**Funcionalidades**:
- Busca em documentação pública por padrão
- Inclua `ref_src=private` para buscar docs privados
- Filtro inteligente de resultados duplicados
- Otimizado para economizar tokens

### **2. ref_read_url**

**Descrição**: Lê conteúdo de URL e converte para markdown  
**Parâmetros**:
- `url` (required): URL para ler (geralmente de resultado do search)

**Exemplo de uso**:
```json
{
  "name": "ref_read_url", 
  "arguments": {
    "url": "https://fastapi.tiangolo.com/tutorial/cors/"
  }
}
```

**Funcionalidades**:
- Extração contextual do conteúdo relevante
- Conversão para markdown limpo
- Limitado aos 5k tokens mais relevantes
- Remove navegação e elementos irrelevantes

---

## 🚀 **Integração com Nosso Projeto**

### **Casos de Uso Recomendados**

#### **1. Busca de Documentação para Desenvolvimento**
```python
# Exemplo: Quando trabalhando com Streamlit
query = "streamlit multiselect widget examples default values"
# Retorna: Documentação específica do Streamlit sobre multiselect
```

#### **2. Verificação de APIs e Endpoints**
```python
# Exemplo: Configuração de autenticação Google OAuth
query = "Google OAuth2 streamlit authentication setup guide"
# Retorna: Guias específicos de implementação
```

#### **3. Troubleshooting Específico**
```python
# Exemplo: Debugging de problemas
query = "pytest fixture scope session database testing cleanup"
# Retorna: Best practices e soluções conhecidas
```

#### **4. Framework e Library Updates**
```python
# Exemplo: Verificar mudanças de versão
query = "pydantic v2 migration guide breaking changes"
# Retorna: Guias de migração atualizados
```

### **Integração com TDD Workflow**

#### **Red Phase - Research**
- Buscar documentação sobre implementações similares
- Verificar APIs e interfaces necessárias

#### **Green Phase - Implementation**
- Consultar documentação específica durante implementação
- Verificar exemplos de código e patterns

#### **Refactor Phase - Optimization**
- Buscar best practices e patterns avançados
- Verificar otimizações conhecidas

---

## 📋 **Configuração Final para Claude Code**

### **Arquivo de Configuração Claude Code**

Adicione ao seu arquivo de configuração Claude Code:

```json
{
  "mcpServers": {
    "ref-tools": {
      "type": "http",
      "url": "https://api.ref.tools/mcp",
      "headers": {
        "x-ref-api-key": "${REF_API_KEY}"
      }
    }
  }
}
```

### **Variáveis de Ambiente**

```bash
# Adicione ao .env do projeto
REF_API_KEY=sua_api_key_aqui
```

### **Validação da Configuração**

Para testar se está funcionando:

1. **Via Claude Code**: Use comando `/tools` para ver se ref-tools aparece
2. **Via Inspector**: Execute `npm run inspect` no diretório ref-tools-mcp
3. **Via HTTP**: Teste `curl http://localhost:8080/ping` (deveria retornar "pong")

---

## 🎯 **Próximos Passos**

1. **✅ Obter API Key** em ref.tools
2. **⚙️ Configurar Claude Code** com MCP server
3. **🧪 Testar integração** com queries simples
4. **📚 Integrar no workflow** de desenvolvimento TDD
5. **📊 Monitorar uso** e otimizar queries

---

## 📚 **Documentação e Recursos**

- **Repository**: https://github.com/ref-tools/ref-tools-mcp
- **Documentação**: https://ref.tools
- **MCP Protocol**: https://modelcontextprotocol.io
- **Smithery Registry**: https://smithery.ai/server/@ref-tools/ref-tools-mcp

---

**Status**: Configuração completa disponível  
**Próximo**: Obter API key e testar integração  
**Benefits**: Redução de tokens, prevenção de alucinações, documentação sempre atualizada