# 🏗️ TDD Core - Domain Layer

## 📋 Overview
Clean Architecture implementation following Domain-Driven Design principles for the TDD Enterprise Framework. This module provides isolated business logic foundation for migrating from a monolithic Streamlit application to an API-first architecture.

**Status:** ✅ História 1.1 Complete - Structure Ready  
**Next:** História 1.2 - Domain Entities Extraction  
**Framework:** Clean Architecture + DDD + SOLID Principles  

## 🏛️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                  │
│           (Adapters, Mappers, Repositories, AI)         │
├─────────────────────────────────────────────────────────┤
│                    Application Layer                     │
│              (Services, DTOs, Validators, Use Cases)    │
├─────────────────────────────────────────────────────────┤
│                      Domain Layer                        │
│           (Entities, Value Objects, Exceptions)         │
└─────────────────────────────────────────────────────────┘
```

### 🎯 Design Principles

#### SOLID Principles
- **S**ingle Responsibility: Each class has one reason to change
- **O**pen/Closed: Open for extension, closed for modification  
- **L**iskov Substitution: Objects replaceable with instances of their subtypes
- **I**nterface Segregation: Client-specific interfaces over general-purpose
- **D**ependency Inversion: Depend on abstractions, not concretions

#### Domain-Driven Design (DDD)
- **Ubiquitous Language:** Common terminology throughout codebase
- **Bounded Context:** Clear boundaries between domain areas
- **Entities:** Objects with identity that can change over time
- **Value Objects:** Immutable objects describing entity aspects
- **Repositories:** Abstract data access layer
- **Services:** Business logic that doesn't belong to entities

#### Clean Architecture
- **Independence:** Frameworks, UI, databases are plugins
- **Testability:** Business rules tested without external elements
- **Framework Independence:** Not bound to any framework
- **Database Independence:** Business rules don't know about database

## 📁 Structure

### Domain Layer (`domain/`)
Pure business logic with zero external dependencies.

- **`entities/`**: Core business objects (ProductVision, Project, Epic, Task)
- **`value_objects/`**: Immutable descriptive objects (Priority, ComplexityScore)  
- **`exceptions/`**: Domain-specific exceptions
- **`repositories/`**: Abstract interfaces for data access

### Application Layer (`application/`)
Orchestrates domain objects to implement use cases.

- **`services/`**: Application services (VisionService, EpicService, AIService)
- **`dto/`**: Data Transfer Objects for external communication
- **`validators/`**: Input validation and business rule enforcement
- **`use_cases/`**: Specific business scenarios and workflows

### Infrastructure Layer (`infrastructure/`)
External interfaces and framework-specific implementations.

- **`adapters/`**: Framework adapters (StreamlitAdapter, FastAPIAdapter)
- **`mappers/`**: Data transformation between layers
- **`repositories/`**: Concrete repository implementations (SQLite, PostgreSQL)
- **`ai/`**: AI service implementations (OpenAI, Mock, Local)

## 🚀 Usage

```python
# Import the core module
import tdd_core

# Get version information
print(tdd_core.get_version())  # "1.0.0"

# Get architecture information
info = tdd_core.get_info()
print(info["architecture"])  # "Clean Architecture + DDD"

# Future usage (after migration):
# from tdd_core.application.services import VisionService
# from tdd_core.infrastructure.adapters import StreamlitAdapter
```

## 🧪 Testing Strategy

### Unit Tests
- Domain entities and value objects (História 1.2-1.3)
- Application services with mocked dependencies (História 2.x)
- Individual validators and mappers (História 3.x-4.x)

### Integration Tests  
- Service interactions with repositories (História 3.3)
- Adapter integrations with external frameworks (História 3.1)
- End-to-end use case scenarios (História 5.x)

### Performance Tests
- Query performance (<10ms target)
- Topological sorting (0.19ms target - validated)
- Cache effectiveness (LRU optimization)

## 📈 Migration Path

This module enables gradual migration following Marco 0:

1. **✅ História 1.1:** Extract domain structure (Complete)
2. **🔄 História 1.2:** Extract domain entities (Next)
3. **⏳ História 1.3:** Implement value objects  
4. **⏳ História 2.x:** Migrate application services
5. **⏳ História 3.x:** Create infrastructure adapters
6. **⏳ História 4.x:** Migrate DTOs and validators
7. **⏳ História 5.x:** Complete testing and documentation

## 🔗 Integration

### With Existing Streamlit App (História 3.1)
```python
# Use adapter pattern to maintain compatibility
from tdd_core.infrastructure.adapters import StreamlitAdapter

adapter = StreamlitAdapter()
vision_service = adapter.get_vision_service()
```

### With Future API (Marco 1)
```python
# Direct usage in API endpoints
from tdd_core.application.services import VisionService
from tdd_core.infrastructure.repositories import SQLiteProjectRepository

repository = SQLiteProjectRepository("database.db")
service = VisionService(repository)
```

### With Future CLI (Marco 1)
```python
# CLI command integration
from tdd_core.application.use_cases import CreateProjectWizard

wizard = CreateProjectWizard()
project = wizard.execute(vision_data)
```

## 📝 Development Guidelines

### Coding Standards
- Type hints required for all public interfaces
- Docstrings following Google style
- Maximum line length: 88 characters
- Use dataclasses for entities and DTOs

### Dependency Rules
- **Domain layer:** No external dependencies (only stdlib)
- **Application layer:** Only depends on domain layer
- **Infrastructure layer:** Can depend on any layer + external frameworks

### Testing Requirements
- Minimum 95% code coverage target
- All public methods must have tests
- Integration tests for adapter patterns
- Performance benchmarks for critical paths (<10ms queries, 0.19ms topological sort)

## 🎯 Key Features (Planned)

### From Existing System
- **TDD Methodology:** Red/Green/Refactor cycle management
- **TDAH Optimization:** Focus tracking, productivity analytics  
- **Database Integration:** SQLite with optimized queries (<10ms)
- **Gamification:** Achievement types, streaks, milestone tracking
- **Security:** Grade A+ compliance (GDPR, SOC 2, ISO 27001 ready)

### Enhanced with Clean Architecture
- **Universal Framework:** Generic 4-phase structure (Roteiro→Capítulos→Histórias→Tarefas)
- **AI-Driven Epic Generation:** Automated epic creation with topological ordering (0.19ms validated)
- **Priority Weight Configuration:** Project-specific priority weights (História 3.2)
- **Multi-Client Support:** Streamlit + API + CLI + Future Mobile

## 📚 References

- **Marco 0 Documentation:** `docs/marco_0_domain_extraction.md`
- **PRD Final:** `prd_final.md` - Marco 0 section
- **Project History:** `CLAUDE.md` - Phase tracking and standards
- **Architecture Patterns:** Clean Architecture (Robert C. Martin)
- **Domain Design:** Domain-Driven Design (Eric Evans)

## 🚀 Future Enhancements (Post-Marco 0)

- **GraphQL API Support:** Type-safe queries and mutations
- **Event-Driven Architecture:** Domain events and event sourcing
- **CQRS Implementation:** Command/Query Responsibility Segregation  
- **Microservices Decomposition:** Service boundaries by bounded contexts
- **Multi-Tenancy Support:** Isolated domains per tenant

## 🔧 Development Status

### ✅ Completed (História 1.1)
- [x] Clean Architecture structure (16 directories, 16 __init__.py files)
- [x] Layer separation (domain/application/infrastructure)  
- [x] Poetry configuration integration
- [x] Basic module imports and version system
- [x] Documentation and development guidelines

### 🔄 In Progress
- [ ] Domain entities extraction (História 1.2)
- [ ] Value objects implementation (História 1.3)

### ⏳ Planned (Marco 0)
- [ ] Service migration (História 2.x)
- [ ] Infrastructure adapters (História 3.x)  
- [ ] DTO and validator migration (História 4.x)
- [ ] Complete testing suite (História 5.x)

---

**Generated by História 1.1 - TDD Core Structure**  
**Version:** 1.0.0  
**Architecture:** Clean Architecture + DDD  
**Status:** Structure Complete ✅  
**Next Phase:** Domain Entities Extraction (História 1.2)