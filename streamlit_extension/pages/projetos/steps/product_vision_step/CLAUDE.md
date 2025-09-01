# 🤖 CLAUDE.md - Product Vision Step - Sistema de Refinamento por IA

**Module:** `streamlit_extension/pages/projetos/steps/product_vision_step`  
**Purpose:** Sistema completo de refinamento por IA real para campos de visão de produto  
**Status:** ✅ **PRODUÇÃO COMPLETA** - v2.0 com Refinamento Individual  
**Last Updated:** 2025-09-01 - Refinamento por Campo Implementado

---

## 📋 **Overview - Sistema v2.0**

Sistema avançado de refinamento por IA que oferece **duas modalidades**:

1. **🆕 Refinamento Individual**: Campo por campo, sem exigir outros preenchidos
2. **Refinamento Global**: Todos os campos simultaneamente para máxima coerência

### **Tecnologia Base**
- **IA Real**: OpenAI GPT-5-nano via framework Agno
- **Fallback Inteligente**: Sistema mock para desenvolvimento
- **Arquitetura**: Dual-mode com bypass de validação para refinamento individual

---

## 🏗️ **Arquitetura Técnica**

### **Estrutura de Arquivos**
```
product_vision_step/
├── CLAUDE.md               # This documentation
├── main.py                 # ✅ Main implementation with AI refinement
├── mock_refiner.py         # Mock AI service for development
├── form_mode.py            # Form mode UI components
├── steps_mode.py           # Steps mode UI components
├── summary.py              # Summary display components
├── ai_refine.py            # AI refinement handlers
├── legacy_api.py           # Backward compatibility layer
└── __init__.py             # Package exports
```

### **Classes Principais**

#### **1. SingleFieldRealRefiner (NOVO v2.0)**
```python
class SingleFieldRealRefiner:
    """Refinamento individual com IA real."""
    
    def __init__(self, vision_agent):
        self.vision_agent = vision_agent
    
    def refine_field(self, field_key: str, field_value: Any, context: Dict[str, Any]) -> Any:
        # Prompt especializado para campo individual
        # Usa contexto disponível sem exigir validação
        # Bypassa VisionRefineService que valida todos os campos
```

**Características:**
- ✅ **Não exige todos os campos preenchidos**
- ✅ Prompt especializado por tipo de campo
- ✅ Usa contexto disponível mesmo se parcial
- ✅ Acesso direto ao agente Agno (bypass validações)

#### **2. VisionRefineService (Existente)**
```python
class VisionRefineService:
    """Refinamento global com validação completa."""
    
    def __init__(self):
        self.service = RealVisionService(agent_adapter)
    
    def refine(self, payload):
        # Validação: todos os campos obrigatórios
        # Refinamento simultâneo para coerência máxima
```

**Características:**
- ✅ Exige todos os campos preenchidos
- ✅ Máxima coerência entre campos
- ✅ Usa VisionRefinerAgent completo

---

## 🎯 **Funcionalidades v2.0**

### **🆕 Refinamento Individual**

**Como Funciona:**
1. Usuário preenche apenas um campo (ex: "app delivery")
2. Clica "✨ Refinar este campo" no modo steps
3. IA refina apenas esse campo com contexto disponível
4. Resultado: "Plataforma integrada de delivery que conecta restaurantes e consumidores com experiência otimizada"

**Código:**
```python
def _handle_refine_field(field_key: str) -> None:
    current_value = st.session_state.pv.get(field_key)
    
    # ✅ NOVO: Só valida o campo atual
    if not current_value or not str(current_value).strip():
        st.warning("⚠️ Preencha o campo antes de refinar.")
        return

    # Monta contexto (outros campos podem estar vazios)
    context = {key: st.session_state.pv.get(key, "") for key, _ in PV_FIELDS}
    
    # ✅ NOVO: Usa refinamento individual
    refined_value = _single_field_refiner.refine_field(field_key, current_value, context)
    
    # Aplica resultado
    if refined_value != current_value:
        st.session_state.pv[field_key] = refined_value
        st.success(f"✨ {field_label} foi aprimorado!")
        st.rerun()
```

### **Refinamento Global (Mantido)**

**Como Funciona:**
1. Usuário preenche todos os campos
2. Clica "✨ Refinar Tudo" no modo formulário
3. IA processa tudo simultaneamente
4. Resultado: Todos os campos refinados com coerência

**Código:**
```python
def _handle_refine_all() -> None:
    # Validação: todos os campos obrigatórios
    if not _all_fields_filled(st.session_state.pv):
        st.warning("⚠️ Para refinar com IA, preencha todos os campos primeiro.")
        return

    service = VisionRefineService()
    result = service.refine(st.session_state.pv)
    
    # Aplica todos os campos refinados
    for field_key, _ in PV_FIELDS:
        if field_key in result:
            st.session_state.pv[field_key] = result[field_key]
```

---

## 🔧 **Implementação Técnica**

### **Prompts Especializados**

#### **Refinamento Individual**
```python
prompt = f'''Você é um especialista em Product Management.

Preciso que você refine o campo "{field_label}" de um produto.

Valor atual do campo: "{field_value}"

Contexto disponível:
{context_text}

Por favor, melhore APENAS o campo "{field_label}", mantendo o significado original mas tornando-o mais claro, profissional e impactante.

IMPORTANTE: 
- Retorne APENAS o valor refinado do campo, sem explicações
- Mantenha o escopo original 
- Se o campo já estiver bom, pode retornar o mesmo valor
- Use português brasileiro'''
```

#### **Refinamento Global**
```python
PROMPT_REFINE = """Você é um Product Manager Sênior.
Refine a visão de produto nos seguintes campos específicos:
- vision_statement: Visão clara e inspiradora do produto
- problem_statement: Problema específico a resolver
- target_audience: Público-alvo bem definido
- value_proposition: Valor único oferecido
- constraints: Limitações objetivas (ou vazio, se não existirem)

Mantendo intenção e escopo, mas evitando jargão e redundâncias.
Retorne SOMENTE nos campos do schema solicitado.

Visão bruta:
{raw_json}
"""
```

### **Sistema de Fallback**

```python
# Sistema real com fallback para mock
try:
    # Componentes reais
    from src.ia.services.vision_refine_service import VisionRefineService as RealVisionService
    from src.ia.agents.agno_agent import VisionRefinerAgent, ProductVisionDTO
    
    _agent = VisionRefinerAgent(model_id="gpt-5-nano")
    _adapted_agent = AgentAdapter(_agent)
    _single_field_refiner = SingleFieldRealRefiner(_agent)
    
    class VisionRefineService:
        def __init__(self):
            self.service = RealVisionService(_adapted_agent)
        def refine(self, payload):
            return self.service.refine(payload)
    
    print("✅ Sistema real de IA ativado em main.py com gpt-5-nano")
    
except Exception as e:
    # Fallback para mock
    from .mock_refiner import MockVisionRefineService as VisionRefineService, SingleFieldMockRefiner
    _single_field_refiner = SingleFieldMockRefiner()
    print(f"⚠️ main.py usando mock devido a: {e}")
```

---

## 🧪 **Testes e Validação**

### **Teste Refinamento Individual**
```python
# Simular interface real: apenas vision_statement preenchido
field_key = 'vision_statement'
field_value = 'sistema gestão escolar'
context = {
    'vision_statement': 'sistema gestão escolar',
    'problem_statement': '',  # VAZIO - OK na v2.0!
    'target_audience': '',    # VAZIO - OK na v2.0!
    'value_proposition': '',  # VAZIO - OK na v2.0!
    'constraints': []         # VAZIO - OK na v2.0!
}

refined_value = _single_field_refiner.refine_field(field_key, field_value, context)

# Resultado esperado:
# Input:  "sistema gestão escolar"
# Output: "Ser a plataforma integrada de gestão escolar que simplifica a administração..."
```

### **Teste Refinamento Global**
```python
# Payload completo (todos os campos preenchidos)
full_payload = {
    'vision_statement': 'app educação online',
    'problem_statement': 'ensino presencial limitado', 
    'target_audience': 'estudantes universitários',
    'value_proposition': 'flexibilidade de horários',
    'constraints': ['orçamento baixo', 'prazo curto']
}

service = VisionRefineService()
result = service.refine(full_payload)

# Todos os campos refinados simultaneamente com coerência
```

---

## ✅ **Status de Implementação**

### **v2.0 - COMPLETO (2025-09-01)**
- ✅ **SingleFieldRealRefiner implementado**: Refinamento individual funcional
- ✅ **Bypass de validação**: Não exige mais todos os campos preenchidos
- ✅ **Prompts especializados**: Por tipo de campo para melhor qualidade
- ✅ **Sistema de fallback**: Mock para desenvolvimento, real para produção
- ✅ **Compatibilidade total**: Refinamento global mantido intacto
- ✅ **Testes validados**: Individual e global funcionando com IA real

### **Arquivos Modificados**
- ✅ `main.py`: Adicionado SingleFieldRealRefiner + modificado _handle_refine_field()
- ✅ `product_vision_step.py`: Sistema real ativado (compatibilidade)
- ✅ `__init__.py`: Referências atualizadas (_legacy → main)

---

## 🚀 **Como Usar**

### **1. Refinamento Individual (NOVO)**
```python
# No modo steps do wizard
# 1. Preencher apenas um campo
st.text_input("Declaração de Visão", value="app delivery")

# 2. Clicar botão de refinamento individual
if st.button("✨ Refinar este campo"):
    _handle_refine_field("vision_statement")

# 3. Campo é refinado mesmo com outros vazios!
```

### **2. Refinamento Global (Existente)**
```python
# No modo formulário do wizard
# 1. Preencher todos os campos obrigatórios
# 2. Clicar botão de refinamento global
if st.button("✨ Refinar Tudo"):
    _handle_refine_all()

# 3. Todos os campos refinados simultaneamente
```

---

## 🔍 **Troubleshooting**

### **Problema: "Campos obrigatórios ausentes"**
- ✅ **Resolvido na v2.0**: Refinamento individual não exige mais todos os campos
- Usar "✨ Refinar este campo" em vez de "✨ Refinar Tudo"
- Certificar que o campo atual está preenchido

### **Problema: API Key inválida**
```bash
export OPENAI_API_KEY="sua-chave-real"
```

### **Problema: Fallback para mock**
- Verificar se API key está configurada
- Verificar se imports do sistema real estão funcionando
- Logs mostrarão qual sistema está ativo

---

## 📚 **Referências Técnicas**

### **Arquitetura Base**
- **Agno Framework**: https://docs.agno.dev
- **OpenAI GPT-5-nano**: Modelo de linguagem avançado
- **Pydantic v2**: Validação de dados com model_dump()

### **Padrões Implementados**
- **Adapter Pattern**: AgentAdapter para compatibilização de interfaces
- **Strategy Pattern**: Refinamento individual vs global
- **Factory Pattern**: Criação dinâmica baseada em disponibilidade de API

### **Arquivos Relacionados**
- **[AI Core Module](../../../../../src/CLAUDE.md)** - Documentação completa do módulo IA
- **[VisionRefinerAgent](../../../../../src/ia/agents/agno_agent.py)** - Agente base com GPT-5-nano
- **[VisionRefineService](../../../../../src/ia/services/vision_refine_service.py)** - Serviço de validação
- **[Product Vision Refiners](../../../../../src/ia/product_vision_refiner.py)** - Implementações Real/Mock
- **[Project Wizard](../../CLAUDE.md)** - Documentação do wizard completo

---

*Sistema de refinamento por IA real totalmente operacional com duas modalidades: individual (campo por campo) e global (todos simultaneamente). Produção completa com fallback inteligente.*