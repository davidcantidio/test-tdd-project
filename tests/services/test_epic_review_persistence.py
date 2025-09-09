"""
🧪 TDD Tests para Persistência Transacional EpicReview - História 4.1 FASE 1.3

Testes críticos para operações de persistência com:
- Batch update transacional com locks de concorrência
- Rollback automático em falha parcial  
- Idempotência de operações (mesma ordem aplicada 2x)
- Detecção de conflitos (épico ausente, dados modificados)
- Re-fetch pós-commit para confirmar integridade sort_order
- Limites transacionais corretos
- Detecção de deadlocks e timeout

Implementação TDD seguindo metodologia Red-Green-Refactor.
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any, Optional
from contextlib import contextmanager
from dataclasses import dataclass


@dataclass
class MockEpicUpdate:
    """Mock update payload para batch operations"""
    epic_id: int
    sort_order: Optional[int] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


@dataclass
class MockTransactionResult:
    """Mock resultado de transação"""
    success: bool
    affected_rows: int = 0
    error: Optional[str] = None
    rollback_performed: bool = False
    execution_time_ms: float = 0.0


class TestEpicReviewPersistence:
    """TDD Tests para Persistência Transacional - História 4.1"""

    @pytest.fixture
    def mock_database_manager(self):
        """Mock do DatabaseManager com transação"""
        db_manager = Mock()
        
        # Mock de transação
        transaction = Mock()
        transaction.__enter__ = Mock(return_value=transaction)
        transaction.__exit__ = Mock(return_value=None)
        transaction.execute = Mock()
        transaction.commit = Mock()
        transaction.rollback = Mock()
        
        db_manager.get_connection.return_value = transaction
        db_manager.begin_transaction.return_value = transaction
        
        return db_manager

    @pytest.fixture
    def sample_updates(self):
        """Fixture com updates de exemplo"""
        return [
            MockEpicUpdate(epic_id=1, sort_order=0, status="approved"),
            MockEpicUpdate(epic_id=2, sort_order=1, title="Updated Title"),
            MockEpicUpdate(epic_id=3, sort_order=2, description="New description"),
            MockEpicUpdate(epic_id=4, sort_order=3, tags=["tag1", "tag2"]),
            MockEpicUpdate(epic_id=5, sort_order=4, status="rejected"),
        ]

    def test_batch_update_happy_path(self, mock_database_manager, sample_updates):
        """
        História 4.1: Batch update bem-sucedido com todos os épicos
        """
        from streamlit_extension.services.epic_service import EpicService
        
        # Patch do transaction context manager
        with patch('streamlit_extension.database.connection.transaction') as mock_transaction:
            mock_conn = Mock()
            mock_transaction.return_value.__enter__.return_value = mock_conn
            mock_transaction.return_value.__exit__.return_value = None
            
            epic_service = EpicService()
            project_id = 1
            
            # Mock do connection e resultados
            mock_conn.execute.return_value.rowcount = 1
            mock_conn.execute.return_value.fetchall.return_value = [
                {"id": 1, "epic_key": "EPIC_001", "sort_order": 0, "status": "approved", "title": "Epic 1"},
                {"id": 2, "epic_key": "EPIC_002", "sort_order": 1, "status": "pending", "title": "Updated Title"},
                {"id": 3, "epic_key": "EPIC_003", "sort_order": 2, "status": "pending", "title": "Epic 3"},
                {"id": 4, "epic_key": "EPIC_004", "sort_order": 3, "status": "pending", "title": "Epic 4"},
                {"id": 5, "epic_key": "EPIC_005", "sort_order": 4, "status": "rejected", "title": "Epic 5"},
            ]
            
            # Converter sample_updates para formato Dict
            updates_dict = []
            for update in sample_updates:
                update_dict = {"epic_id": update.epic_id}
                if update.sort_order is not None:
                    update_dict["sort_order"] = update.sort_order
                if update.title is not None:
                    update_dict["title"] = update.title
                if update.description is not None:
                    update_dict["description"] = update.description
                if update.tags is not None:
                    update_dict["tags"] = update.tags
                if update.status is not None:
                    update_dict["status"] = update.status
                updates_dict.append(update_dict)
            
            # Executar batch update
            result = epic_service.update_epic_order(project_id, updates_dict)
            
            # Verificar sucesso
            assert result.success == True
            assert result.data == True  # Operação completada
            
            # Verificar que transação foi usada
            mock_transaction.assert_called_once()
            
            # Verificar que execute foi chamado (verificação + updates + re-fetch)
            assert mock_conn.execute.call_count >= len(sample_updates)
            
            # Verificar que commit foi chamado
            mock_conn.commit.assert_called_once()

    def test_partial_failure_rollback(self, mock_database_manager, sample_updates):
        """
        História 4.1: Rollback em falha parcial - alguns updates falham
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para simular falha no 3º update
        def mock_execute_side_effect(*args, **kwargs):
            sql = args[0] if args else ""
            if "UPDATE framework_epics" in sql and "id = 3" in str(kwargs):
                raise Exception("Simulated database error")
            return Mock(rowcount=1)
        
        mock_database_manager.get_connection.return_value.execute.side_effect = mock_execute_side_effect
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, sample_updates)
        
        # Verificar falha
        assert result.success == False
        assert "database error" in result.error.lower()
        
        # Verificar que rollback foi chamado
        mock_database_manager.get_connection.return_value.rollback.assert_called_once()
        
        # Verificar que commit NÃO foi chamado
        mock_database_manager.get_connection.return_value.commit.assert_not_called()

    def test_update_idempotency(self, mock_database_manager, sample_updates):
        """
        História 4.1: Mesma ordem aplicada duas vezes deve ser idempotente
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para simular mesmo estado
        mock_database_manager.get_connection.return_value.execute.return_value.rowcount = 1
        mock_database_manager.get_connection.return_value.fetchall.return_value = [
            {"id": 1, "sort_order": 0}, {"id": 2, "sort_order": 1},
            {"id": 3, "sort_order": 2}, {"id": 4, "sort_order": 3},
            {"id": 5, "sort_order": 4}
        ]
        
        # Primeira aplicação
        result1 = epic_service.update_epic_order(project_id, sample_updates)
        assert result1.success == True
        
        # Segunda aplicação idêntica
        result2 = epic_service.update_epic_order(project_id, sample_updates)
        assert result2.success == True
        
        # Deve ter detectado que não há mudanças
        assert "no changes detected" in result2.message.lower() or result2.data == True
        
        # Verificar que commit foi chamado nas duas vezes (operação válida)
        assert mock_database_manager.get_connection.return_value.commit.call_count == 2

    def test_conflict_detection(self, mock_database_manager):
        """
        História 4.1: Detecção de conflitos - épico ausente ou modificado
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Updates para épicos que não existem
        conflicting_updates = [
            MockEpicUpdate(epic_id=999, sort_order=0),  # Épico inexistente
            MockEpicUpdate(epic_id=1000, sort_order=1),  # Outro inexistente
        ]
        
        # Mock para simular épico não encontrado
        mock_database_manager.get_connection.return_value.execute.return_value.rowcount = 0
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, conflicting_updates)
        
        # Verificar detecção de conflito
        assert result.success == False
        assert "epic not found" in result.error.lower() or "conflict" in result.error.lower()
        
        # Verificar que rollback foi chamado
        mock_database_manager.get_connection.return_value.rollback.assert_called_once()

    def test_concurrency_lock_behavior(self, mock_database_manager, sample_updates):
        """
        História 4.1: Lock durante atualização para prevenir concorrência
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para simular lock
        lock_acquired = threading.Event()
        lock_released = threading.Event()
        
        def mock_execute_with_lock(*args, **kwargs):
            sql = args[0] if args else ""
            if "LOCK" in sql.upper() or "FOR UPDATE" in sql.upper():
                lock_acquired.set()
                # Simular tempo de lock
                time.sleep(0.1)
                lock_released.set()
            return Mock(rowcount=1)
        
        mock_database_manager.get_connection.return_value.execute.side_effect = mock_execute_with_lock
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, sample_updates)
        
        # Verificar sucesso
        assert result.success == True
        
        # Verificar que lock foi usado
        execute_calls = mock_database_manager.get_connection.return_value.execute.call_args_list
        lock_used = any("LOCK" in str(call) or "FOR UPDATE" in str(call) 
                       for call in execute_calls)
        assert lock_used == True, "Lock should be used during update operation"

    def test_sort_order_integrity(self, mock_database_manager, sample_updates):
        """
        História 4.1: Re-fetch pós-commit para confirmar integridade
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para simular dados antes e depois
        expected_final_state = [
            {"id": 1, "sort_order": 0, "status": "approved"},
            {"id": 2, "sort_order": 1, "title": "Updated Title"},
            {"id": 3, "sort_order": 2},
            {"id": 4, "sort_order": 3},
            {"id": 5, "sort_order": 4, "status": "rejected"},
        ]
        
        mock_database_manager.get_connection.return_value.fetchall.return_value = expected_final_state
        mock_database_manager.get_connection.return_value.execute.return_value.rowcount = 1
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, sample_updates)
        
        # Verificar sucesso
        assert result.success == True
        
        # Verificar que re-fetch foi realizado
        execute_calls = mock_database_manager.get_connection.return_value.execute.call_args_list
        fetchall_calls = mock_database_manager.get_connection.return_value.fetchall.call_args_list
        
        # Deve ter pelo menos um SELECT após os UPDATEs
        assert len(fetchall_calls) >= 1
        
        # Verificar integridade dos dados retornados
        final_data = result.metadata.get("final_state", [])
        if final_data:
            sort_orders = [item["sort_order"] for item in final_data]
            assert sort_orders == [0, 1, 2, 3, 4]  # Sequência correta

    def test_transaction_boundaries(self, mock_database_manager, sample_updates):
        """
        História 4.1: Limites transacionais corretos
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para rastrear ordem de calls
        call_sequence = []
        
        def track_calls(method_name):
            def wrapper(*args, **kwargs):
                call_sequence.append(method_name)
                return Mock(rowcount=1)
            return wrapper
        
        mock_database_manager.get_connection.return_value.execute = track_calls("execute")
        mock_database_manager.get_connection.return_value.commit = track_calls("commit")
        mock_database_manager.get_connection.return_value.rollback = track_calls("rollback")
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, sample_updates)
        
        # Verificar sequência correta
        assert "execute" in call_sequence  # Pelo menos um execute
        assert "commit" in call_sequence   # Commit deve ter sido chamado
        assert "rollback" not in call_sequence  # Rollback não deve ter sido chamado
        
        # Commit deve ser a última operação
        last_db_operation = [op for op in call_sequence if op in ["commit", "rollback"]][-1]
        assert last_db_operation == "commit"

    def test_deadlock_detection_and_retry(self, mock_database_manager, sample_updates):
        """
        História 4.1: Detecção de deadlock e retry automático
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para simular deadlock na primeira tentativa
        attempt_count = 0
        
        def mock_execute_with_deadlock(*args, **kwargs):
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count == 1:
                # Primeira tentativa: deadlock
                raise Exception("Deadlock detected")
            else:
                # Segunda tentativa: sucesso
                return Mock(rowcount=1)
        
        mock_database_manager.get_connection.return_value.execute.side_effect = mock_execute_with_deadlock
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, sample_updates)
        
        # Verificar que retry funcionou
        assert result.success == True
        assert attempt_count >= 2  # Pelo menos 2 tentativas
        
        # Verificar metadata sobre retry
        retry_info = result.metadata.get("retry_info", {})
        assert retry_info.get("attempts", 0) >= 2

    def test_timeout_handling(self, mock_database_manager, sample_updates):
        """
        História 4.1: Handling de timeout em operações longas
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Mock para simular timeout
        def mock_execute_timeout(*args, **kwargs):
            time.sleep(0.1)  # Simular operação longa
            raise Exception("Operation timeout")
        
        mock_database_manager.get_connection.return_value.execute.side_effect = mock_execute_timeout
        
        # Executar batch update
        start_time = time.time()
        result = epic_service.update_epic_order(project_id, sample_updates)
        execution_time = time.time() - start_time
        
        # Verificar falha por timeout
        assert result.success == False
        assert "timeout" in result.error.lower()
        
        # Verificar que rollback foi chamado
        mock_database_manager.get_connection.return_value.rollback.assert_called_once()

    def test_large_batch_performance(self, mock_database_manager):
        """
        História 4.1: Performance com batch grande (100+ épicos)
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Criar batch grande
        large_batch = []
        for i in range(150):  # 150 épicos
            large_batch.append(MockEpicUpdate(
                epic_id=i + 1,
                sort_order=i,
                status="approved" if i % 2 == 0 else "pending"
            ))
        
        # Mock otimizado para batch grande
        mock_database_manager.get_connection.return_value.execute.return_value.rowcount = 1
        mock_database_manager.get_connection.return_value.executemany = Mock(return_value=Mock(rowcount=150))
        
        # Executar batch update
        start_time = time.time()
        result = epic_service.update_epic_order(project_id, large_batch)
        execution_time = time.time() - start_time
        
        # Verificar sucesso
        assert result.success == True
        
        # Verificar performance (deve ser < 1 segundo)
        assert execution_time < 1.0, f"Large batch took {execution_time:.3f}s, expected < 1.0s"
        
        # Verificar que executemany foi usado para otimização
        mock_database_manager.get_connection.return_value.executemany.assert_called()

    def test_validation_before_persistence(self, mock_database_manager):
        """
        História 4.1: Validação completa antes de persistir
        """
        from streamlit_extension.services.epic_service import EpicService
        
        epic_service = EpicService(database_manager=mock_database_manager)
        project_id = 1
        
        # Updates com dados inválidos
        invalid_updates = [
            MockEpicUpdate(epic_id=1, title=""),  # Título vazio
            MockEpicUpdate(epic_id=2, sort_order=-1),  # Sort order inválido
            MockEpicUpdate(epic_id=3, tags=["", "  ", None]),  # Tags inválidas
            MockEpicUpdate(epic_id=4, status="invalid_status"),  # Status inválido
        ]
        
        # Executar batch update
        result = epic_service.update_epic_order(project_id, invalid_updates)
        
        # Verificar que falhou na validação
        assert result.success == False
        assert "validation failed" in result.error.lower()
        
        # Verificar que database NÃO foi chamado
        mock_database_manager.get_connection.return_value.execute.assert_not_called()
        
        # Verificar detalhes da validação
        validation_errors = result.metadata.get("validation_errors", [])
        assert len(validation_errors) >= 4  # Pelo menos um erro por update inválido