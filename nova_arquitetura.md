│ 🏗️ Plano Revisado: Arquitetura API-First com Domínio Extraíd                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ Incorporando críticas e melhorias arquiteturais                                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │ Fase 0: Extração do Domínio (2-3 dias)                                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ 0.1 Criação do Módulo de Domínio Central                                                                                                                       │ │
│ │                                                                                                                                                                │ │
│ │ tdd_core/                           # Novo módulo central                                                                                                      │ │
│ │ ├── __init__.py                                                                                                                                                │ │
│ │ ├── domain/                                                                                                                                                    │ │
│ │ │   ├── entities/                                                                                                                                              │ │
│ │ │   │   ├── product_vision.py       # Entities do domínio                                                                                                      │ │
│ │ │   │   ├── project.py                                                                                                                                         │ │
│ │ │   │   └── epic.py                                                                                                                                            │ │
│ │ │   ├── value_objects/                                                                                                                                         │ │
│ │ │   │   ├── priority.py                                                                                                                                        │ │
│ │ │   │   └── tdd_phase.py                                                                                                                                       │ │
│ │ │   └── exceptions/                                                                                                                                            │ │
│ │ │       └── domain_exceptions.py                                                                                                                               │ │
│ │ ├── application/                                                                                                                                               │ │
│ │ │   ├── services/                   # Services extraídos de streamlit_extension                                                                                │ │
│ │ │   │   ├── vision_service.py       # Sem dependências de framework                                                                                            │ │
│ │ │   │   ├── epic_service.py                                                                                                                                    │ │
│ │ │   │   └── ai_service.py                                                                                                                                      │ │
│ │ │   ├── dto/                                                                                                                                                   │ │
│ │ │   │   ├── product_vision_dto.py   # DTOs existentes                                                                                                          │ │
│ │ │   │   └── epic_dto.py                                                                                                                                        │ │
│ │ │   └── validators/                                                                                                                                            │ │
│ │ │       └── vision_validators.py    # Validadores independentes                                                                                                │ │
│ │ ├── infrastructure/                                                                                                                                            │ │
│ │ │   ├── repositories/                                                                                                                                          │ │
│ │ │   │   ├── abstract/               # Interfaces abstratas                                                                                                     │ │
│ │ │   │   └── sqlite/                 # Implementações SQLite                                                                                                    │ │
│ │ │   └── database/                                                                                                                                              │ │
│ │ │       ├── connection_factory.py   # Factory para SQLite/Postgres                                                                                             │ │
│ │ │       └── migrations/             # Migrações mantidas                                                                                                       │ │
│ │ └── shared/                                                                                                                                                    │ │
│ │     ├── result.py                   # Result pattern                                                                                                           │ │
│ │     └── utils.py                                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ 0.2 Adaptação da Arquitetura Existente                                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ # Mapear services existentes para tdd_core                                                                                                                     │ │
│ │ streamlit_extension/services/vision_service.py → tdd_core/application/services/                                                                                │ │
│ │ streamlit_extension/database/ → tdd_core/infrastructure/database/                                                                                              │ │
│ │ streamlit_extension/dto/ → tdd_core/application/dto/                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ # Criar adapters por framework                                                                                                                                 │ │
│ │ interfaces/                                                                                                                                                    │ │
│ │ ├── fastapi_adapter/                # Backend API                                                                                                              │ │
│ │ ├── cli_adapter/                    # Terminal CLI                                                                                                             │ │
│ │ └── streamlit_adapter/              # Transição gradual                                                                                                        │ │
│ │                                                                                                                                                                │ │
│ │ Fase 1: Backend FastAPI com Arquitetura Limpa (4-5 dias)                                                                                                       │ │
│ │                                                                                                                                                                │ │
│ │ 1.1 Estrutura com Versionamento e Contratos                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │ backend/                                                                                                                                                       │ │
│ │ ├── api/                                                                                                                                                       │ │
│ │ │   ├── v1/                         # Versionamento explícito                                                                                                  │ │
│ │ │   │   ├── routers/                                                                                                                                           │ │
│ │ │   │   │   ├── wizard.py                                                                                                                                      │ │
│ │ │   │   │   ├── projects.py                                                                                                                                    │ │
│ │ │   │   │   └── epics.py                                                                                                                                       │ │
│ │ │   │   └── schemas/                # Pydantic schemas (bordas)                                                                                                │ │
│ │ │   │       ├── request/                                                                                                                                       │ │
│ │ │   │       └── response/                                                                                                                                      │ │
│ │ │   ├── middleware/                                                                                                                                            │ │
│ │ │   │   ├── auth.py                 # OIDC + PKCE                                                                                                              │ │
│ │ │   │   ├── error_handler.py        # RFC 7807                                                                                                                 │ │
│ │ │   │   └── rate_limiter.py                                                                                                                                    │ │
│ │ │   └── dependencies/                                                                                                                                          │ │
│ │ │       ├── auth.py                 # JWT validation                                                                                                           │ │
│ │ │       └── db.py                   # DI de conexões                                                                                                           │ │
│ │ ├── core/                                                                                                                                                      │ │
│ │ │   ├── config.py                   # Pydantic Settings                                                                                                        │ │
│ │ │   ├── security.py                 # Auth flows                                                                                                               │ │
│ │ │   └── observability/                                                                                                                                         │ │
│ │ │       ├── logging.py              # Structured logs                                                                                                          │ │
│ │ │       └── tracing.py              # OpenTelemetry                                                                                                            │ │
│ │ └── adapters/                                                                                                                                                  │ │
│ │     └── service_container.py        # DI adaptado para FastAPI                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ 1.2 Endpoints com Casos de Uso e Idempotência                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ # backend/api/v1/routers/wizard.py                                                                                                                             │ │
│ │ from fastapi import APIRouter, Depends, Header                                                                                                                 │ │
│ │ from fastapi.responses import StreamingResponse                                                                                                                │ │
│ │ from tdd_core.application.services import VisionService                                                                                                        │ │
│ │                                                                                                                                                                │ │
│ │ router = APIRouter(prefix="/wizard", tags=["wizard"])                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │ @router.post("/vision", response_model=VisionResponse)                                                                                                         │ │
│ │ async def create_vision(                                                                                                                                       │ │
│ │     request: VisionRequest,                                                                                                                                    │ │
│ │     idempotency_key: str = Header(...),  # Idempotência                                                                                                        │ │
│ │     service: VisionService = Depends(get_vision_service)                                                                                                       │ │
│ │ ):                                                                                                                                                             │ │
│ │     result = await service.create_vision(request.to_domain_dto())                                                                                              │ │
│ │     if result.success:                                                                                                                                         │ │
│ │         return VisionResponse.from_domain(result.data)                                                                                                         │ │
│ │     raise HTTPException(422, detail=result.error)                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ @router.post("/vision/{id}/refine/{field}")                                                                                                                    │ │
│ │ async def refine_field_stream(                                                                                                                                 │ │
│ │     id: int, field: str, request: RefineRequest                                                                                                                │ │
│ │ ):                                                                                                                                                             │ │
│ │     """Stream SSE para progresso do refinamento IA"""                                                                                                          │ │
│ │     async def generate():                                                                                                                                      │ │
│ │         async for progress in service.refine_with_ai_stream(id, field, request.value):                                                                         │ │
│ │             yield f"data: {progress.json()}\n\n"                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │     return StreamingResponse(generate(), media_type="text/plain")                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ 1.3 Autenticação Multi-Client                                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ # backend/core/security.py                                                                                                                                     │ │
│ │ class AuthFlow:                                                                                                                                                │ │
│ │     """Múltiplos fluxos de autenticação"""                                                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │     # Web: OIDC + PKCE                                                                                                                                         │ │
│ │     async def web_auth(self, code: str, code_verifier: str):                                                                                                   │ │
│ │         # Exchange code for tokens                                                                                                                             │ │
│ │         # Store httpOnly cookies + CSRF                                                                                                                        │ │
│ │         pass                                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │     # CLI: Device Code Flow                                                                                                                                    │ │
│ │     async def cli_device_flow(self):                                                                                                                           │ │
│ │         # Return device_code + user_code + verification_uri                                                                                                    │ │
│ │         pass                                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │     # Development: Personal Access Token                                                                                                                       │ │
│ │     async def validate_pat(self, token: str):                                                                                                                  │ │
│ │         # Validate development token                                                                                                                           │ │
│ │         pass                                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ 1.4 Configuração com SQLite WAL + Postgres                                                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │ # backend/core/config.py                                                                                                                                       │ │
│ │ from pydantic_settings import BaseSettings                                                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │ class Settings(BaseSettings):                                                                                                                                  │ │
│ │     # Database                                                                                                                                                 │ │
│ │     database_url: str = "sqlite:///./framework.db?mode=WAL"                                                                                                    │ │
│ │     database_pool_size: int = 1  # SQLite: 1 worker                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │     # Auth                                                                                                                                                     │ │
│ │     oidc_client_id: str                                                                                                                                        │ │
│ │     oidc_client_secret: str                                                                                                                                    │ │
│ │     jwt_secret: str                                                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │     # CORS                                                                                                                                                     │ │
│ │     nuxt_origin: str = "http://localhost:3000"                                                                                                                 │ │
│ │     allow_credentials: bool = True                                                                                                                             │ │
│ │                                                                                                                                                                │ │
│ │     # Observability                                                                                                                                            │ │
│ │     log_level: str = "INFO"                                                                                                                                    │ │
│ │     enable_tracing: bool = True                                                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │     model_config = SettingsConfigDict(env_file=".env")                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ Fase 2: Cliente Gerado e CLI Tipado (2-3 dias)                                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ 2.1 Geração Automática de Clientes                                                                                                                             │ │
│ │                                                                                                                                                                │ │
│ │ # CI/CD Pipeline para gerar clientes                                                                                                                           │ │
│ │ # TypeScript para Nuxt                                                                                                                                         │ │
│ │ npx openapi-typescript backend/openapi.json -o frontend/types/api.ts                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ # Python para CLI                                                                                                                                              │ │
│ │ openapi-python-client generate --path backend/openapi.json --config client-config.yaml                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ 2.2 CLI com Modos Online/Offline                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ # cli/commands/wizard.py                                                                                                                                       │ │
│ │ from rich.console import Console                                                                                                                               │ │
│ │ from rich.live import Live                                                                                                                                     │ │
│ │ from rich.table import Table                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ class WizardCLI:                                                                                                                                               │ │
│ │     def __init__(self, mode: str = "online"):                                                                                                                  │ │
│ │         self.mode = mode                                                                                                                                       │ │
│ │         self.client = APIClient() if mode == "online" else None                                                                                                │ │
│ │         self.core_service = VisionService() if mode == "offline" else None                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │     async def interactive_wizard(self):                                                                                                                        │ │
│ │         console = Console()                                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │         # Product Vision                                                                                                                                       │ │
│ │         vision_data = await self._collect_vision_input()                                                                                                       │ │
│ │                                                                                                                                                                │ │
│ │         # AI Refinement com progress                                                                                                                           │ │
│ │         if Confirm.ask("Refine with AI?"):                                                                                                                     │ │
│ │             with Live(self._create_progress_table(), refresh_per_second=4):                                                                                    │ │
│ │                 if self.mode == "online":                                                                                                                      │ │
│ │                     refined = await self._refine_via_api_stream(vision_data)                                                                                   │ │
│ │                 else:                                                                                                                                          │ │
│ │                     refined = await self.core_service.refine_vision(vision_data)                                                                               │ │
│ │                                                                                                                                                                │ │
│ │         # Epic Generation                                                                                                                                      │ │
│ │         epics = await self._generate_epics(refined)                                                                                                            │ │
│ │         console.print(f"✨ Generated {len(epics)} epics successfully!")                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │     async def _refine_via_api_stream(self, vision_data):                                                                                                       │ │
│ │         """Consume SSE stream para mostrar progresso"""                                                                                                        │ │
│ │         async with self.client.stream_refine(vision_data) as stream:                                                                                           │ │
│ │             async for chunk in stream:                                                                                                                         │ │
│ │                 # Update progress table                                                                                                                        │ │
│ │                 pass                                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ 2.3 Autenticação CLI com Device Flow                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ # cli/auth.py                                                                                                                                                  │ │
│ │ import keyring                                                                                                                                                 │ │
│ │ from rich.console import Console                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ class CLIAuth:                                                                                                                                                 │ │
│ │     def login(self):                                                                                                                                           │ │
│ │         """Device Code Flow para CLI"""                                                                                                                        │ │
│ │         console = Console()                                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │         # Iniciar device flow                                                                                                                                  │ │
│ │         device_resp = self.client.start_device_flow()                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │         console.print(f"""                                                                                                                                     │ │
│ │ [yellow]Go to:[/yellow] {device_resp.verification_uri}                                                                                                         │ │
│ │ [yellow]Enter code:[/yellow] {device_resp.user_code}                                                                                                           │ │
│ │         """)                                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │         # Poll para tokens                                                                                                                                     │ │
│ │         tokens = self.client.poll_device_flow(device_resp.device_code)                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │         # Armazenar no keyring do OS                                                                                                                           │ │
│ │         keyring.set_password("tdd-cli", "access_token", tokens.access_token)                                                                                   │ │
│ │         keyring.set_password("tdd-cli", "refresh_token", tokens.refresh_token)                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │         console.print("[green]✅ Login successful![/green]")                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │ Fase 3: Frontend Nuxt com Contratos Tipados (6-8 dias)                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ 3.1 Setup com Geração de Tipos                                                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ // frontend/nuxt.config.ts                                                                                                                                     │ │
│ │ export default defineNuxtConfig({                                                                                                                              │ │
│ │   modules: [                                                                                                                                                   │ │
│ │     '@tanstack/vue-query-nuxt',                                                                                                                                │ │
│ │     '@vueuse/nuxt',                                                                                                                                            │ │
│ │     '@nuxt/ui'  // Shadcn alternative                                                                                                                          │ │
│ │   ],                                                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │   // Auto-import types gerados                                                                                                                                 │ │
│ │   typescript: {                                                                                                                                                │ │
│ │     typeCheck: true                                                                                                                                            │ │
│ │   },                                                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │   // Build hook para gerar tipos                                                                                                                               │ │
│ │   hooks: {                                                                                                                                                     │ │
│ │     'build:before': () => {                                                                                                                                    │ │
│ │       // Gerar tipos do OpenAPI                                                                                                                                │ │
│ │     }                                                                                                                                                          │ │
│ │   }                                                                                                                                                            │ │
│ │ })                                                                                                                                                             │ │
│ │                                                                                                                                                                │ │
│ │ 3.2 Composables com Vue Query e SSE                                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │ // composables/useWizard.ts                                                                                                                                    │ │
│ │ import type {                                                                                                                                                  │ │
│ │   VisionRequest,                                                                                                                                               │ │
│ │   VisionResponse,                                                                                                                                              │ │
│ │   RefineFieldResponse                                                                                                                                          │ │
│ │ } from '~/types/api'                                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ export const useWizard = () => {                                                                                                                               │ │
│ │   // Vue Query para cache e otimistic updates                                                                                                                  │ │
│ │   const { data: vision, mutate: saveVision } = useMutation({                                                                                                   │ │
│ │     mutationFn: (data: VisionRequest) =>                                                                                                                       │ │
│ │       $api.wizard.createVision({ body: data }),                                                                                                                │ │
│ │     onSuccess: (result) => {                                                                                                                                   │ │
│ │       // Invalidate related queries                                                                                                                            │ │
│ │       queryClient.invalidateQueries(['vision'])                                                                                                                │ │
│ │     }                                                                                                                                                          │ │
│ │   })                                                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │   // SSE para refinamento                                                                                                                                      │ │
│ │   const refineField = async (field: string, value: string) => {                                                                                                │ │
│ │     const eventSource = new EventSource(                                                                                                                       │ │
│ │       `/api/v1/wizard/vision/${visionId}/refine/${field}`                                                                                                      │ │
│ │     )                                                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │     return new Promise((resolve) => {                                                                                                                          │ │
│ │       eventSource.onmessage = (event) => {                                                                                                                     │ │
│ │         const progress = JSON.parse(event.data)                                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │         if (progress.status === 'completed') {                                                                                                                 │ │
│ │           eventSource.close()                                                                                                                                  │ │
│ │           resolve(progress.result)                                                                                                                             │ │
│ │         }                                                                                                                                                      │ │
│ │       }                                                                                                                                                        │ │
│ │     })                                                                                                                                                         │ │
│ │   }                                                                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │   return {                                                                                                                                                     │ │
│ │     vision: readonly(vision),                                                                                                                                  │ │
│ │     saveVision,                                                                                                                                                │ │
│ │     refineField,                                                                                                                                               │ │
│ │     isLoading: computed(() => /* loading states */)                                                                                                            │ │
│ │   }                                                                                                                                                            │ │
│ │ }                                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ 3.3 Componentes com Streaming                                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ <!-- components/wizard/AIRefineModal.vue -->                                                                                                                   │ │
│ │ <template>                                                                                                                                                     │ │
│ │   <UModal v-model="isOpen">                                                                                                                                    │ │
│ │     <div class="p-6">                                                                                                                                          │ │
│ │       <h3 class="text-lg font-semibold mb-4">                                                                                                                  │ │
│ │         AI Refinement in Progress                                                                                                                              │ │
│ │       </h3>                                                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │       <!-- Progress with streaming updates -->                                                                                                                 │ │
│ │       <div v-if="refineProgress">                                                                                                                              │ │
│ │         <UProgress                                                                                                                                             │ │
│ │           :value="refineProgress.percentage"                                                                                                                   │ │
│ │           :indicator="false"                                                                                                                                   │ │
│ │         />                                                                                                                                                     │ │
│ │         <p class="text-sm text-gray-600 mt-2">                                                                                                                 │ │
│ │           {{ refineProgress.current_step }}                                                                                                                    │ │
│ │         </p>                                                                                                                                                   │ │
│ │       </div>                                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │       <!-- Result -->                                                                                                                                          │ │
│ │       <div v-if="refineResult" class="mt-4">                                                                                                                   │ │
│ │         <UTextarea                                                                                                                                             │ │
│ │           v-model="refineResult.refined_text"                                                                                                                  │ │
│ │           :rows="4"                                                                                                                                            │ │
│ │         />                                                                                                                                                     │ │
│ │         <div class="flex justify-end gap-2 mt-4">                                                                                                              │ │
│ │           <UButton @click="rejectRefinement">                                                                                                                  │ │
│ │             Reject                                                                                                                                             │ │
│ │           </UButton>                                                                                                                                           │ │
│ │           <UButton @click="acceptRefinement" color="primary">                                                                                                  │ │
│ │             Accept                                                                                                                                             │ │
│ │           </UButton>                                                                                                                                           │ │
│ │         </div>                                                                                                                                                 │ │
│ │       </div>                                                                                                                                                   │ │
│ │     </div>                                                                                                                                                     │ │
│ │   </UModal>                                                                                                                                                    │ │
│ │ </template>                                                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │ <script setup lang="ts">                                                                                                                                       │ │
│ │ const { refineField } = useWizard()                                                                                                                            │ │
│ │ const refineProgress = ref(null)                                                                                                                               │ │
│ │ const refineResult = ref(null)                                                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ const startRefinement = async (field: string, value: string) => {                                                                                              │ │
│ │   // Connect to SSE stream                                                                                                                                     │ │
│ │   refineResult.value = await refineField(field, value)                                                                                                         │ │
│ │ }                                                                                                                                                              │ │
│ │ </script>                                                                                                                                                      │ │
│ │                                                                                                                                                                │ │
│ │ Fase 4: Segurança e Observabilidade (2-3 dias)                                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ 4.1 Implementação de Auth Completa                                                                                                                             │ │
│ │                                                                                                                                                                │ │
│ │ # backend/middleware/auth.py                                                                                                                                   │ │
│ │ from fastapi import Request, HTTPException                                                                                                                     │ │
│ │ from fastapi.security import HTTPBearer                                                                                                                        │ │
│ │ import jwt                                                                                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │ class MultiAuthMiddleware:                                                                                                                                     │ │
│ │     """Suporte a múltiplos tipos de auth"""                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │     async def __call__(self, request: Request, call_next):                                                                                                     │ │
│ │         # Cookie-based (Web)                                                                                                                                   │ │
│ │         if "session_token" in request.cookies:                                                                                                                 │ │
│ │             user = await self.validate_session_cookie(request)                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │         # Bearer token (CLI/API)                                                                                                                               │ │
│ │         elif "authorization" in request.headers:                                                                                                               │ │
│ │             user = await self.validate_bearer_token(request)                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │         # Development PAT                                                                                                                                      │ │
│ │         elif "x-api-key" in request.headers:                                                                                                                   │ │
│ │             user = await self.validate_api_key(request)                                                                                                        │ │
│ │                                                                                                                                                                │ │
│ │         else:                                                                                                                                                  │ │
│ │             raise HTTPException(401, "Authentication required")                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │         request.state.user = user                                                                                                                              │ │
│ │         return await call_next(request)                                                                                                                        │ │
│ │                                                                                                                                                                │ │
│ │ 4.2 Observabilidade Completa                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ # backend/core/observability/logging.py                                                                                                                        │ │
│ │ import structlog                                                                                                                                               │ │
│ │ from opentelemetry import trace                                                                                                                                │ │
│ │ from opentelemetry.exporter.jaeger.thrift import JaegerExporter                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │ # Structured logging                                                                                                                                           │ │
│ │ structlog.configure(                                                                                                                                           │ │
│ │     processors=[                                                                                                                                               │ │
│ │         structlog.stdlib.filter_by_level,                                                                                                                      │ │
│ │         structlog.stdlib.add_logger_name,                                                                                                                      │ │
│ │         structlog.stdlib.add_log_level,                                                                                                                        │ │
│ │         structlog.processors.JSONRenderer()                                                                                                                    │ │
│ │     ]                                                                                                                                                          │ │
│ │ )                                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ # Tracing                                                                                                                                                      │ │
│ │ tracer = trace.get_tracer(__name__)                                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │ @tracer.start_as_current_span("vision_refinement")                                                                                                             │ │
│ │ async def refine_vision_with_tracing(vision_id: int, field: str):                                                                                              │ │
│ │     span = trace.get_current_span()                                                                                                                            │ │
│ │     span.set_attribute("vision.id", vision_id)                                                                                                                 │ │
│ │     span.set_attribute("vision.field", field)                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │     logger.info("Starting vision refinement",                                                                                                                  │ │
│ │                vision_id=vision_id,                                                                                                                            │ │
│ │                field=field)                                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │     # Business logic                                                                                                                                           │ │
│ │     result = await service.refine(vision_id, field)                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │     span.set_attribute("refinement.success", result.success)                                                                                                   │ │
│ │     return result                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ 4.3 Health Checks e Métricas                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ # backend/api/health.py                                                                                                                                        │ │
│ │ from fastapi import APIRouter                                                                                                                                  │ │
│ │ from prometheus_client import Counter, generate_latest                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ router = APIRouter()                                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ # Métricas                                                                                                                                                     │ │
│ │ requests_total = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ @router.get("/healthz")                                                                                                                                        │ │
│ │ async def health_check():                                                                                                                                      │ │
│ │     """Liveness probe"""                                                                                                                                       │ │
│ │     return {"status": "healthy", "timestamp": datetime.utcnow()}                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ @router.get("/readyz")                                                                                                                                         │ │
│ │ async def readiness_check():                                                                                                                                   │ │
│ │     """Readiness probe - verifica dependências"""                                                                                                              │ │
│ │     checks = {                                                                                                                                                 │ │
│ │         "database": await check_database(),                                                                                                                    │ │
│ │         "ai_service": await check_ai_service()                                                                                                                 │ │
│ │     }                                                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │     if all(checks.values()):                                                                                                                                   │ │
│ │         return {"status": "ready", "checks": checks}                                                                                                           │ │
│ │     else:                                                                                                                                                      │ │
│ │         raise HTTPException(503, {"status": "not ready", "checks": checks})                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │ @router.get("/metrics")                                                                                                                                        │ │
│ │ async def metrics():                                                                                                                                           │ │
│ │     """Prometheus metrics"""                                                                                                                                   │ │
│ │     return Response(generate_latest(), media_type="text/plain")                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │ Fase 5: Testes e Qualidade (2-3 days)                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │ 5.1 Testes de Contrato                                                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │ # tests/contract/test_openapi_compliance.py                                                                                                                    │ │
│ │ import pytest                                                                                                                                                  │ │
│ │ from openapi_spec_validator import validate_spec                                                                                                               │ │
│ │ from fastapi.testclient import TestClient                                                                                                                      │ │
│ │                                                                                                                                                                │ │
│ │ def test_openapi_spec_valid():                                                                                                                                 │ │
│ │     """OpenAPI spec é válido"""                                                                                                                                │ │
│ │     client = TestClient(app)                                                                                                                                   │ │
│ │     spec = client.get("/openapi.json").json()                                                                                                                  │ │
│ │     validate_spec(spec)  # Raises if invalid                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ def test_vision_endpoint_contract():                                                                                                                           │ │
│ │     """Endpoint respeita contrato OpenAPI"""                                                                                                                   │ │
│ │     client = TestClient(app)                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │     # Valid request                                                                                                                                            │ │
│ │     response = client.post("/api/v1/wizard/vision", json={                                                                                                     │ │
│ │         "vision_statement": "Create a task management app",                                                                                                    │ │
│ │         "problem_statement": "Teams lack organization",                                                                                                        │ │
│ │         "target_audience": "Small teams"                                                                                                                       │ │
│ │     })                                                                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │     assert response.status_code == 201                                                                                                                         │ │
│ │     assert "id" in response.json()                                                                                                                             │ │
│ │     assert "created_at" in response.json()                                                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │ 5.2 Testes de API com Fixtures                                                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ # tests/api/conftest.py                                                                                                                                        │ │
│ │ @pytest.fixture                                                                                                                                                │ │
│ │ async def db_session():                                                                                                                                        │ │
│ │     """Database session para testes"""                                                                                                                         │ │
│ │     async with get_test_db_session() as session:                                                                                                               │ │
│ │         yield session                                                                                                                                          │ │
│ │         await session.rollback()                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ @pytest.fixture                                                                                                                                                │ │
│ │ async def authenticated_client(db_session):                                                                                                                    │ │
│ │     """Cliente autenticado para testes"""                                                                                                                      │ │
│ │     user = await create_test_user(db_session)                                                                                                                  │ │
│ │     token = generate_test_token(user)                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │     client = AsyncClient(app=app, base_url="http://test")                                                                                                      │ │
│ │     client.headers.update({"authorization": f"Bearer {token}"})                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │     return client                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ # tests/api/test_wizard.py                                                                                                                                     │ │
│ │ async def test_create_vision_success(authenticated_client):                                                                                                    │ │
│ │     response = await authenticated_client.post("/api/v1/wizard/vision", json={                                                                                 │ │
│ │         "vision_statement": "Test vision"                                                                                                                      │ │
│ │     })                                                                                                                                                         │ │
│ │                                                                                                                                                                │ │
│ │     assert response.status_code == 201                                                                                                                         │ │
│ │     data = response.json()                                                                                                                                     │ │
│ │     assert data["vision_statement"] == "Test vision"                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ Fase 6: DevOps e Deploy (2 dias)                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ 6.1 Docker Compose Otimizado                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ # docker-compose.yml                                                                                                                                           │ │
│ │ version: '3.8'                                                                                                                                                 │ │
│ │                                                                                                                                                                │ │
│ │ services:                                                                                                                                                      │ │
│ │   backend:                                                                                                                                                     │ │
│ │     build:                                                                                                                                                     │ │
│ │       context: .                                                                                                                                               │ │
│ │       dockerfile: backend/Dockerfile                                                                                                                           │ │
│ │     environment:                                                                                                                                               │ │
│ │       - DATABASE_URL=postgresql://user:pass@postgres:5432/tdd_db                                                                                               │ │
│ │       - WORKERS=2  # Postgres permite múltiplos workers                                                                                                        │ │
│ │       - LOG_LEVEL=INFO                                                                                                                                         │ │
│ │     depends_on:                                                                                                                                                │ │
│ │       postgres:                                                                                                                                                │ │
│ │         condition: service_healthy                                                                                                                             │ │
│ │     healthcheck:                                                                                                                                               │ │
│ │       test: ["CMD", "curl", "-f", "http://localhost:8000/healthz"]                                                                                             │ │
│ │       interval: 30s                                                                                                                                            │ │
│ │       timeout: 10s                                                                                                                                             │ │
│ │       retries: 3                                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │   frontend:                                                                                                                                                    │ │
│ │     build: ./frontend                                                                                                                                          │ │
│ │     environment:                                                                                                                                               │ │
│ │       - NUXT_PUBLIC_API_BASE=http://localhost:8000/api/v1                                                                                                      │ │
│ │       - NUXT_PUBLIC_WS_BASE=ws://localhost:8000/ws                                                                                                             │ │
│ │     depends_on:                                                                                                                                                │ │
│ │       - backend                                                                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │   postgres:                                                                                                                                                    │ │
│ │     image: postgres:15-alpine                                                                                                                                  │ │
│ │     environment:                                                                                                                                               │ │
│ │       POSTGRES_DB: tdd_db                                                                                                                                      │ │
│ │       POSTGRES_USER: tdd_user                                                                                                                                  │ │
│ │       POSTGRES_PASSWORD: tdd_pass                                                                                                                              │ │
│ │     volumes:                                                                                                                                                   │ │
│ │       - postgres_data:/var/lib/postgresql/data                                                                                                                 │ │
│ │     healthcheck:                                                                                                                                               │ │
│ │       test: ["CMD-SHELL", "pg_isready -U tdd_user -d tdd_db"]                                                                                                  │ │
│ │       interval: 10s                                                                                                                                            │ │
│ │       timeout: 5s                                                                                                                                              │ │
│ │       retries: 5                                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │   redis:                                                                                                                                                       │ │
│ │     image: redis:7-alpine                                                                                                                                      │ │
│ │     command: redis-server --appendonly yes                                                                                                                     │ │
│ │     volumes:                                                                                                                                                   │ │
│ │       - redis_data:/data                                                                                                                                       │ │
│ │                                                                                                                                                                │ │
│ │ volumes:                                                                                                                                                       │ │
│ │   postgres_data:                                                                                                                                               │ │
│ │   redis_data:                                                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ 6.2 CI/CD com Validação de Contratos                                                                                                                           │ │
│ │                                                                                                                                                                │ │
│ │ # .github/workflows/api.yml                                                                                                                                    │ │
│ │ name: Backend API                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ on: [push, pull_request]                                                                                                                                       │ │
│ │                                                                                                                                                                │ │
│ │ jobs:                                                                                                                                                          │ │
│ │   test:                                                                                                                                                        │ │
│ │     runs-on: ubuntu-latest                                                                                                                                     │ │
│ │     services:                                                                                                                                                  │ │
│ │       postgres:                                                                                                                                                │ │
│ │         image: postgres:15                                                                                                                                     │ │
│ │         env:                                                                                                                                                   │ │
│ │           POSTGRES_PASSWORD: postgres                                                                                                                          │ │
│ │         options: >-                                                                                                                                            │ │
│ │           --health-cmd pg_isready                                                                                                                              │ │
│ │           --health-interval 10s                                                                                                                                │ │
│ │           --health-timeout 5s                                                                                                                                  │ │
│ │           --health-retries 5                                                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │     steps:                                                                                                                                                     │ │
│ │       - uses: actions/checkout@v4                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │       - name: Setup Python                                                                                                                                     │ │
│ │         uses: actions/setup-python@v4                                                                                                                          │ │
│ │         with:                                                                                                                                                  │ │
│ │           python-version: '3.11'                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │       - name: Install Poetry                                                                                                                                   │ │
│ │         run: |                                                                                                                                                 │ │
│ │           curl -sSL https://install.python-poetry.org | python3 -                                                                                              │ │
│ │           echo "$HOME/.local/bin" >> $GITHUB_PATH                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │       - name: Install dependencies                                                                                                                             │ │
│ │         run: poetry install                                                                                                                                    │ │
│ │                                                                                                                                                                │ │
│ │       - name: Run tests                                                                                                                                        │ │
│ │         run: |                                                                                                                                                 │ │
│ │           poetry run pytest tests/unit --cov=tdd_core                                                                                                          │ │
│ │           poetry run pytest tests/api --cov=backend                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │       - name: Validate OpenAPI                                                                                                                                 │ │
│ │         run: |                                                                                                                                                 │ │
│ │           poetry run python -c "from backend.main import app; import json; print(json.dumps(app.openapi()))" > openapi.json                                    │ │
│ │           npx swagger-codegen-cli validate -i openapi.json                                                                                                     │ │
│ │                                                                                                                                                                │ │
│ │       - name: Generate clients                                                                                                                                 │ │
│ │         run: |                                                                                                                                                 │ │
│ │           # Generate TypeScript client for frontend                                                                                                            │ │
│ │           npx openapi-typescript openapi.json -o frontend-types.ts                                                                                             │ │
│ │           # Generate Python client for CLI                                                                                                                     │ │
│ │           openapi-python-client generate --path openapi.json                                                                                                   │ │
│ │                                                                                                                                                                │ │
│ │ 📋 Cronograma Revisado com Fases de Risco                                                                                                                      │ │
│ │                                                                                                                                                                │ │
│ │ | Fase                | Dias       | Entregas                                    | Riscos                              |                                       │ │
│ │ |---------------------|------------|---------------------------------------------|-------------------------------------|                                       │ │
│ │ | 0. Extração Domínio | 2-3        | tdd_core module, adapters                   | Refatoração breaking changes        |                                       │ │
│ │ | 1. Backend + Auth   | 4-5        | API v1, OIDC/Device flow, observability     | Auth complexity, SQLite concurrency |                                       │ │
│ │ | 2. CLI Tipado       | 2-3        | Generated client, Device flow, offline mode | Token management, UX terminal       |                                       │ │
│ │ | 3. Frontend Stream  | 6-8        | Nuxt UI, SSE, generated types               | SSE complexity, UI state sync       |                                       │ │
│ │ | 4. Segurança/Obs    | 2-3        | Multi-auth, tracing, health checks          | Performance overhead                |                                       │ │
│ │ | 5. Testes/Qualidade | 2-3        | Contract tests, API tests, E2E              | Coverage gaps, flaky tests          |                                       │ │
│ │ | 6. DevOps/Deploy    | 2          | Docker, CI/CD, monitoring                   | Postgres migration, deployment      |                                       │ │
│ │ | TOTAL               | 20-27 dias | Sistema completo production-ready           | Complexidade elevada                |                                       │ │
│ │                                                                                                                                                                │ │
│ │ 🎯 Decisões Críticas Antecipadas                                                                                                                               │ │
│ │                                                                                                                                                                │ │
│ │ Database Strategy                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ - Dev: SQLite + WAL + 1 worker FastAPI                                                                                                                         │ │
│ │ - Prod: PostgreSQL + connection pool + async SQLAlchemy                                                                                                        │ │
│ │ - Migration: Factory pattern para ambos                                                                                                                        │ │
│ │                                                                                                                                                                │ │
│ │ Auth Strategy                                                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ - Web: OIDC + PKCE + httpOnly cookies + CSRF                                                                                                                   │ │
│ │ - CLI: Device Code Flow + OS keyring                                                                                                                           │ │
│ │ - Dev: Personal Access Tokens                                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ Long-running Tasks                                                                                                                                             │ │
│ │                                                                                                                                                                │ │
│ │ - MVP: SSE streaming para progresso                                                                                                                            │ │
│ │ - Prod: Redis + RQ/Celery queue                                                                                                                                │ │
│ │                                                                                                                                                                │ │
│ │ Client Generation                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ - TypeScript: openapi-typescript no build                                                                                                                      │ │
│ │ - Python CLI: openapi-python-client no CI                                                                                                                      │ │
│ │ - Versioning: /api/v1 com breaking change detection                                                                                                            │ │
│ │                                                                                                                                                                │ │
│ │ 🚦 Go/No-Go Gates                                                                                                                                              │ │
│ │                                                                                                                                                                │ │
│ │ Gate 1 (Após Fase 0):                                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │ - ✅ tdd_core extraído sem breaking changes                                                                                                                     │ │
│ │ - ✅ Streamlit ainda funciona via adapter                                                                                                                       │ │
│ │ - ✅ Services isolados de framework                                                                                                                             │ │
│ │                                                                                                                                                                │ │
│ │ Gate 2 (Após Fase 1):                                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │ - ✅ API funciona com SQLite WAL                                                                                                                                │ │
│ │ - ✅ Auth básica implementada                                                                                                                                   │ │
│ │ - ✅ OpenAPI válido e versionado                                                                                                                                │ │
│ │ - ✅ Health checks respondendo                                                                                                                                  │ │
│ │                                                                                                                                                                │ │
│ │ Gate 3 (Após Fase 3):                                                                                                                                          │ │
│ │                                                                                                                                                                │ │
│ │ - ✅ CLI e Frontend consomem API                                                                                                                                │ │
│ │ - ✅ SSE streaming funciona                                                                                                                                     │ │
│ │ - ✅ Tipos gerados sem drift                                                                                                                                    │ │
│ │ - ✅ UX comparável ao Streamlit       