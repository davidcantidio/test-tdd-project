# 🤖 CLAUDE.md - AI Services Module

**Module:** `src/ia/`  
**Purpose:** Core AI refinement services for Product Vision  
**Status:** ✅ **PRODUCTION READY**  
**Architecture:** Clean separation between agents, services, and refiners  
**Last Updated:** 2025-09-01

---

## 📋 Module Overview

The `src/ia/` module provides the AI-powered refinement capabilities for the Product Vision wizard. It implements a clean architecture with proper separation of concerns between AI agents, services, and refiners.

---

## 🏗️ Directory Structure

```
src/
└── ia/                          # AI/Intelligence services
    ├── agents/
    │   └── agno_agent.py        # Agno framework integration with GPT-5-nano
    ├── services/
    │   └── vision_refine_service.py  # Service layer for vision refinement
    └── product_vision_refiner.py     # Refiner implementations (Real & Mock)
```

---

## 🎯 Core Components

### **1. VisionRefinerAgent** (`agents/agno_agent.py`)
The core AI agent using the Agno framework with OpenAI GPT-5-nano.

**Key Features:**
- Structured output using Pydantic `ProductVisionDTO`
- Validation of required fields before refinement
- JSON mode for consistent responses
- Professional Product Manager prompt engineering

**Usage:**
```python
from src.ia.agents.agno_agent import VisionRefinerAgent, ProductVisionDTO

agent = VisionRefinerAgent(model_id="gpt-5-nano")
refined = agent.refine({
    "vision_statement": "app delivery",
    "problem_statement": "fome rápida",
    "target_audience": "pessoas com pressa",
    "value_proposition": "entrega em 10 minutos",
    "constraints": ["budget limitado"]
})
```

### **2. VisionRefineService** (`services/vision_refine_service.py`)
Service layer that wraps the agent with business logic and error handling.

**Key Features:**
- Enterprise-ready error handling
- Adapter pattern for flexible agent swapping
- Validation and sanitization
- Logging and monitoring hooks

### **3. Product Vision Refiners** (`product_vision_refiner.py`)
High-level refiner implementations for different environments.

**Implementations:**
- **RealGPTRefiner**: Production refiner using actual GPT-5-nano
- **FakeClaudeRefiner**: Mock refiner for testing/development

---

## 📊 Data Models

### **ProductVisionDTO**
```python
class ProductVisionDTO(BaseModel):
    vision_statement: str   # Clear product vision
    problem_statement: str  # Problem being solved
    target_audience: str    # Primary target users
    value_proposition: str  # Unique value offered
    constraints: List[str]  # Limitations/restrictions
```

---

## 🔧 Configuration

### **Environment Variables**
```bash
# Required for production
export OPENAI_API_KEY="your-api-key"

# Optional model selection
export AI_MODEL_ID="gpt-5-nano"  # or "gpt-4", "gpt-3.5-turbo"
```

### **Model Options**
- **gpt-5-nano** (default): Fast, cost-effective for refinement
- **gpt-4**: Higher quality, slower response
- **gpt-3.5-turbo**: Budget option, good performance

---

## 🧪 Testing

### **Unit Tests**
```bash
# Test AI agents
pytest tests/ia/test_agno_agent.py

# Test refiners
pytest tests/product_vision/test_product_vision_refiner.py
```

### **Mock vs Real**
```python
# Development - use mock
from src.ia.product_vision_refiner import FakeClaudeRefiner
refiner = FakeClaudeRefiner()

# Production - use real
from src.ia.product_vision_refiner import RealGPTRefiner
refiner = RealGPTRefiner()
```

---

## 🔗 Integration Points

### **Used By:**
- `/streamlit_extension/pages/projetos/steps/product_vision_step/main.py` - Main UI integration
- `/streamlit_extension/services/vision_service.py` - Service layer wrapper

### **Dependencies:**
- **agno**: AI agent framework
- **pydantic**: Data validation and schemas
- **openai**: LLM provider (via agno)

---

## 🚀 Future Enhancements

### **Planned:**
- [ ] Multi-language support (PT-BR, EN, ES)
- [ ] Field-specific refinement strategies
- [ ] Caching layer for repeated refinements
- [ ] A/B testing framework for prompts
- [ ] Cost optimization with intelligent model selection

### **Under Consideration:**
- Custom fine-tuned models for domain-specific refinement
- Batch processing for multiple visions
- Version control for refinement prompts
- Analytics dashboard for refinement quality

---

## 📚 Related Documentation

### **System Documentation**
- **[Main System](../CLAUDE.md)** - Overall system architecture and overview
- **[Streamlit Extension](../streamlit_extension/CLAUDE.md)** - Complete UI framework documentation

### **Integration Documentation**
- **[Project Wizard](../streamlit_extension/pages/projetos/CLAUDE.md)** - Generic project framework implementation
- **[Product Vision Step](../streamlit_extension/pages/projetos/steps/product_vision_step/CLAUDE.md)** - Detailed AI refinement UI integration

### **Testing & Quality**
- **[Test Framework](../tests/CLAUDE.md)** - Test organization and coverage
- **[AI Tests](../tests/product_vision/)** - Specific AI refinement tests

---

*Core AI services for intelligent Product Vision refinement. Clean architecture with proper separation between agents, services, and implementations.*