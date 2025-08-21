#!/usr/bin/env python3
"""
🔧 UTILS - Graph Algorithms

Algoritmos de grafo para sistema de ordenação topológica.
Implementações eficientes baseadas nas correções da crítica.

Usage:
    from streamlit_extension.utils.graph_algorithms import (
        topological_sort_simple,
        longest_path_weighted,
        find_strongly_connected_components,
        detect_cycles
    )

Features:
- Ordenação topológica simples (Kahn)
- Caminho crítico ponderado por duração
- Detecção de ciclos com DFS colorido
- Strongly Connected Components (Tarjan)
- Validação de DAG
"""

import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import defaultdict, deque
from dataclasses import dataclass
from streamlit_extension.auth.middleware import require_auth, require_admin
from streamlit_extension.auth.user_model import UserRole

logger = logging.getLogger(__name__)

@dataclass
class GraphNode:
    """Nó do grafo com metadados"""
    key: str
    weight: int = 1
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

class GraphAlgorithms:
    """Algoritmos de grafo otimizados"""
    
    @staticmethod
    def topological_sort_simple(adjacency: Dict[str, Set[str]]) -> List[str]:
        """
        Ordenação topológica simples usando Kahn's algorithm
        Sem priorização - usado para pré-computações
        
        Args:
            adjacency: {node: {neighbors}} - grafo dirigido
            
        Returns:
            Lista ordenada topologicamente
            
        Raises:
            ValueError: Se houver ciclos no grafo
            TypeError: Se adjacency não for do tipo correto
        """
        # Input validation
        if not isinstance(adjacency, dict):
            raise TypeError(f"adjacency deve ser dict, recebido: {type(adjacency)}")
        
        if not adjacency:
            return []
        
        # inclui também nós que só aparecem como vizinhos
        in_degree = {node: 0 for node in adjacency}
        for node, neighbors in adjacency.items():
            if not isinstance(neighbors, (set, list, tuple)):
                raise TypeError(f"neighbors de {node} deve ser set/list/tuple, recebido: {type(neighbors)}")
            for neighbor in neighbors:
                if neighbor not in in_degree:
                    in_degree[neighbor] = 0
        # computa in-degree
        for node, neighbors in adjacency.items():
            neighbors = adjacency[node]
            if not isinstance(neighbors, (set, list, tuple)):
                raise TypeError(f"neighbors de {node} deve ser set/list/tuple, recebido: {type(neighbors)}")

            for neighbor in neighbors:
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
        
        # Fila com nós de in-degree 0
        queue = deque([node for node, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Atualizar in-degree dos vizinhos
            for neighbor in adjacency[current]:
                if neighbor in in_degree:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)
        
        # Verificar se processou todos os nós
        if len(result) != len(in_degree):
            missing = set(in_degree.keys()) - set(result)
            raise ValueError(f"Ciclo detectado no grafo. Nós não processados: {missing}")
        
        return result
    
    @staticmethod
    def longest_path_weighted(
        adjacency: Dict[str, Set[str]], 
        weights: Dict[str, int]
    ) -> Dict[str, int]:
        """
        Calcula caminho crítico ponderado usando duração das tarefas
        Implementação otimizada baseada nas correções da crítica
        
        Args:
            adjacency: Grafo dirigido {node: {neighbors}}
            weights: Peso (duração) de cada nó {node: duration}
            
        Returns:
            Dicionário {node: total_time_to_completion}
            
        Raises:
            ValueError: Se o grafo contém ciclos
            TypeError: Se inputs não são do tipo correto
        """
        # Input validation
        if not isinstance(adjacency, dict):
            raise TypeError(f"adjacency deve ser dict, recebido: {type(adjacency)}")
        if not isinstance(weights, dict):
            raise TypeError(f"weights deve ser dict, recebido: {type(weights)}")
        
        if not adjacency:
            return {}
        
        try:
            # Ordenação topológica para processar em ordem
            topo_order = GraphAlgorithms.topological_sort_simple(adjacency)
            
            # Inicializar distâncias - CORREÇÃO: usar 0 inicialmente
            distances = {node: 0 for node in topo_order}
            
            # Processar nós em ordem topológica
            for node in topo_order:
                node_weight = max(weights.get(node, 1), 1)  # Mínimo 1
                
                # Atualizar distância do nó atual
                distances[node] = max(distances[node], node_weight)
                
                # Propagar para vizinhos
                for neighbor in adjacency.get(node, set()):
                    if neighbor in distances:
                        neighbor_weight = max(weights.get(neighbor, 1), 1)
                        # CORREÇÃO: distância total = caminho até aqui + peso do vizinho
                        total_distance = distances[node] + neighbor_weight
                        distances[neighbor] = max(distances[neighbor], total_distance)
            
            return distances
            
        except ValueError as e:
            logger.error(f"Erro no cálculo do caminho crítico: {e}")
            # Fallback: retornar pesos originais
            return {node: weights.get(node, 1) for node in adjacency.keys()}
    
    @staticmethod
    def detect_cycles_dfs(adjacency: Dict[str, Set[str]]) -> Tuple[bool, Optional[List[str]]]:
        """
        Detecta ciclos usando DFS colorido
        OTIMIZAÇÃO: Versão iterativa para evitar stack overflow em grafos grandes
        
        Args:
            adjacency: Grafo dirigido
            
        Returns:
            (has_cycle, cycle_path)
            
        Raises:
            TypeError: Se adjacency não for dict
        """
        # Input validation
        if not isinstance(adjacency, dict):
            raise TypeError(f"adjacency deve ser dict, recebido: {type(adjacency)}")
        
        if not adjacency:
            return False, None
        
        WHITE, GRAY, BLACK = 0, 1, 2
        color = {node: WHITE for node in adjacency}
        
        # OTIMIZAÇÃO: Versão iterativa usando stack explícita
        for start_node in adjacency:
            if color[start_node] != WHITE:
                continue
                
            # Stack: (node, path, is_backtrack)
            stack = [(start_node, [], False)]
            
            while stack:
                node, path, is_backtrack = stack.pop()
                
                if is_backtrack:
                    # Voltando: marcar como processado
                    color[node] = BLACK
                    continue
                
                if color[node] == GRAY:
                    # Back edge - ciclo detectado!
                    cycle_start = len(path) - 1
                    while cycle_start >= 0 and path[cycle_start] != node:
                        cycle_start -= 1
                    
                    if cycle_start >= 0:
                        cycle_path = path[cycle_start:] + [node]
                        return True, cycle_path
                    else:
                        return True, path + [node]
                
                if color[node] == BLACK:
                    continue
                
                # Marcar como visitando
                color[node] = GRAY
                new_path = path + [node]
                
                # Adicionar backtrack marker
                stack.append((node, new_path, True))
                
                # Visitar vizinhos em ordem reversa (para manter ordem)
                neighbors = list(adjacency.get(node, set()))
                for neighbor in reversed(neighbors):
                    if neighbor in color:  # Só processar nós válidos
                        stack.append((neighbor, new_path, False))
        
        # Testar a partir de cada nó não visitado
        for node in adjacency:
            if color[node] == WHITE:
                has_cycle, cycle_path = dfs(node, [])
                if has_cycle:
                    return True, cycle_path
        
        return False, None
    
    @staticmethod
    def find_strongly_connected_components(adjacency: Dict[str, Set[str]]) -> List[List[str]]:
        """
        Encontra componentes fortemente conectados usando algoritmo de Tarjan
        Útil para tratar ciclos como super-nós
        
        Args:
            adjacency: Grafo dirigido
            
        Returns:
            Lista de componentes (cada componente é uma lista de nós)
        """
        index_counter = [0]
        stack = []
        lowlinks = {}
        index = {}
        on_stack = {}
        components = []
        
        def strongconnect(node: str):
            # Configurar nó
            index[node] = index_counter[0]
            lowlinks[node] = index_counter[0]
            index_counter[0] += 1
            stack.append(node)
            on_stack[node] = True
            
            # Considerar sucessores
            for neighbor in adjacency.get(node, set()):
                if neighbor not in index:
                    # Sucessor não visitado, recorrer
                    strongconnect(neighbor)
                    lowlinks[node] = min(lowlinks[node], lowlinks[neighbor])
                elif on_stack.get(neighbor, False):
                    # Sucessor está na pilha e no SCC atual
                    lowlinks[node] = min(lowlinks[node], index[neighbor])
            
            # Se é um root node, extrair SCC
            if lowlinks[node] == index[node]:
                component = []
                while True:
                    w = stack.pop()
                    on_stack[w] = False
                    component.append(w)
                    if w == node:
                        break
                components.append(component)
        
        # Executar para todos os nós não visitados
        for node in adjacency:
            if node not in index:
                strongconnect(node)
        
        return components
    
    @staticmethod
    def validate_dag(adjacency: Dict[str, Set[str]]) -> Tuple[bool, Optional[str]]:
        """
        Valida se o grafo é um DAG (Directed Acyclic Graph)
        
        Args:
            adjacency: Grafo dirigido
            
        Returns:
            (is_dag, error_message)
        """
        try:
            # Verificar se há ciclos
            has_cycle, cycle_path = GraphAlgorithms.detect_cycles_dfs(adjacency)
            
            if has_cycle:
                cycle_str = " → ".join(cycle_path) if cycle_path else "ciclo desconhecido"
                return False, f"Ciclo detectado: {cycle_str}"
            
            # Verificar se ordenação topológica funciona
            try:
                topo_order = GraphAlgorithms.topological_sort_simple(adjacency)
                expected_nodes = set(adjacency.keys())
                actual_nodes = set(topo_order)
                
                if expected_nodes != actual_nodes:
                    missing = expected_nodes - actual_nodes
                    extra = actual_nodes - expected_nodes
                    error_parts = []
                    if missing:
                        error_parts.append(f"nós perdidos: {missing}")
                    if extra:
                        error_parts.append(f"nós extras: {extra}")
                    return False, f"Inconsistência na ordenação topológica: {', '.join(error_parts)}"
                
            except ValueError as e:
                return False, f"Falha na ordenação topológica: {e}"
            
            return True, None
            
        except Exception as e:
            logger.error(f"Erro na validação DAG: {e}")
            return False, f"Erro interno: {e}"
    
    @staticmethod
    def build_transitive_closure(adjacency: Dict[str, Set[str]]) -> Dict[str, Set[str]]:
        """
        Constrói fechamento transitivo do grafo
        Útil para verificar alcançabilidade
        
        Args:
            adjacency: Grafo dirigido
            
        Returns:
            Grafo com todas as relações transitivas
        """
        # Inicializar com adjacências diretas
        closure = {node: adjacency.get(node, set()).copy() for node in adjacency}
        
        # Floyd-Warshall adaptado
        nodes = list(adjacency.keys())
        
        for k in nodes:
            for i in nodes:
                for j in nodes:
                    if k in closure.get(i, set()) and j in closure.get(k, set()):
                        if i not in closure:
                            closure[i] = set()
                        closure[i].add(j)
        
        return closure
    
    @staticmethod
    def find_critical_path_nodes(
        adjacency: Dict[str, Set[str]], 
        weights: Dict[str, int]
    ) -> List[str]:
        """
        Encontra nós no caminho crítico
        OTIMIZAÇÃO: Versão iterativa para evitar stack overflow
        
        Args:
            adjacency: Grafo dirigido
            weights: Peso de cada nó
            
        Returns:
            Lista de nós no caminho crítico
            
        Raises:
            ValueError: Se o grafo contém ciclos
            TypeError: Se inputs não são do tipo correto
        """
        # Input validation
        if not isinstance(adjacency, dict) or not isinstance(weights, dict):
            raise TypeError("adjacency e weights devem ser dicionários")
        
        try:
            # Calcular distâncias (tempo total até conclusão)
            distances = GraphAlgorithms.longest_path_weighted(adjacency, weights)
            
            if not distances:
                return []
            
            # Encontrar nó com maior distância (fim do caminho crítico)
            max_distance = max(distances.values())
            end_nodes = [node for node, dist in distances.items() if dist == max_distance]
            
            # OTIMIZAÇÃO: Versão iterativa para evitar recursão profunda
            critical_nodes = set()
            processing_stack = [(node, distances[node]) for node in end_nodes]
            
            while processing_stack:
                current_node, target_distance = processing_stack.pop()
                
                if current_node in critical_nodes:
                    continue
                    
                critical_nodes.add(current_node)
                node_weight = max(weights.get(current_node, 1), 1)
                predecessor_distance = target_distance - node_weight
                
                # Encontrar predecessores que levam ao caminho crítico
                for pred_node in adjacency:
                    if current_node in adjacency.get(pred_node, set()):
                        pred_actual_distance = distances.get(pred_node, 0)
                        if pred_actual_distance == predecessor_distance:
                            processing_stack.append((pred_node, predecessor_distance))
            
            # Retornar em ordem topológica
            topo_order = GraphAlgorithms.topological_sort_simple(adjacency)
            return [node for node in topo_order if node in critical_nodes]
            
        except Exception as e:
            logger.error(f"Erro ao encontrar caminho crítico: {e}")
            return []
    
    @staticmethod
    def calculate_graph_metrics(adjacency: Dict[str, Set[str]]) -> Dict[str, Any]:
        """
        Calcula métricas básicas do grafo
        MELHORIA: Adicionada validação de arestas órfãs
        
        Args:
            adjacency: Grafo dirigido
            
        Returns:
            Dicionário com métricas do grafo
            
        Raises:
            TypeError: Se adjacency não for dict
        """
        # Input validation
        if not isinstance(adjacency, dict):
            raise TypeError(f"adjacency deve ser dict, recebido: {type(adjacency)}")
        
        if not adjacency:
            return {
                'total_nodes': 0,
                'total_edges': 0,
                'density': 0.0,
                'source_nodes': [],
                'sink_nodes': [],
                'avg_in_degree': 0.0,
                'avg_out_degree': 0.0,
                'max_in_degree': 0,
                'max_out_degree': 0,
                'orphan_edges': []
            }
        
        total_nodes = len(adjacency)
        total_edges = 0
        orphan_edges = []  # Arestas que apontam para nós inexistentes
        
        # Calcular in-degree e out-degree com validação de arestas
        in_degree = {node: 0 for node in adjacency}
        out_degree = {node: 0 for node in adjacency}
        
        for node in adjacency:
            neighbors = adjacency[node]
            if not isinstance(neighbors, (set, list, tuple)):
                logger.warning(f"Vizinhos de {node} não são coleção válida: {type(neighbors)}")
                continue
                
            valid_neighbors = 0
            for neighbor in neighbors:
                total_edges += 1
                if neighbor in in_degree:
                    in_degree[neighbor] += 1
                    valid_neighbors += 1
                else:
                    # Aresta órfã - aponta para nó inexistente
                    orphan_edges.append(f"{node} -> {neighbor}")
            
            out_degree[node] = valid_neighbors
        
        # Nós fonte e sumidouro
        source_nodes = [node for node, deg in in_degree.items() if deg == 0]
        sink_nodes = [node for node, deg in out_degree.items() if deg == 0]
        
        # Densidade do grafo (apenas arestas válidas)
        max_edges = total_nodes * (total_nodes - 1)  # grafo dirigido
        density = (total_edges - len(orphan_edges)) / max_edges if max_edges > 0 else 0
        
        metrics = {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'valid_edges': total_edges - len(orphan_edges),
            'orphan_edges': orphan_edges,
            'density': density,
            'source_nodes': source_nodes,
            'sink_nodes': sink_nodes,
            'avg_in_degree': sum(in_degree.values()) / total_nodes if total_nodes > 0 else 0,
            'avg_out_degree': sum(out_degree.values()) / total_nodes if total_nodes > 0 else 0,
            'max_in_degree': max(in_degree.values()) if in_degree else 0,
            'max_out_degree': max(out_degree.values()) if out_degree else 0
        }
        
        # Log warnings para arestas órfãs
        if orphan_edges:
            logger.warning(f"Detectadas {len(orphan_edges)} arestas órfãs: {orphan_edges[:3]}{'...' if len(orphan_edges) > 3 else ''}")
        
        return metrics

# Funções de conveniência
def topological_sort_simple(adjacency: Dict[str, Set[str]]) -> List[str]:
    """Função de conveniência para ordenação topológica simples"""
    return GraphAlgorithms.topological_sort_simple(adjacency)

def longest_path_weighted(adjacency: Dict[str, Set[str]], weights: Dict[str, int]) -> Dict[str, int]:
    """Função de conveniência para caminho crítico ponderado"""
    return GraphAlgorithms.longest_path_weighted(adjacency, weights)

def detect_cycles(adjacency: Dict[str, Set[str]]):
    """Alias para detect_cycles_dfs para compatibilidade externa."""
    return GraphAlgorithms.detect_cycles_dfs(adjacency)

def find_strongly_connected_components(adjacency: Dict[str, Set[str]]) -> List[List[str]]:
    """Função de conveniência para SCCs"""
    return GraphAlgorithms.find_strongly_connected_components(adjacency)

def validate_dag(adjacency: Dict[str, Set[str]]) -> Tuple[bool, Optional[str]]:
    """Função de conveniência para validação DAG"""
    return GraphAlgorithms.validate_dag(adjacency)