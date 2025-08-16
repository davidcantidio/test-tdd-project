#!/usr/bin/env python3
"""
Script para comparar estruturas entre arquivos e detectar diferenças
Tarefa 1.1.1.7 - Comparar estruturas entre arquivos e detectar diferenças
"""

import json
import os
from typing import Dict, Any, List, Set, Tuple
from collections import defaultdict, Counter
from pathlib import Path

def load_json_file(file_path: str) -> Tuple[Dict[str, Any], bool]:
    """Carrega um arquivo JSON e retorna os dados"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data, True
    except Exception as e:
        print(f"❌ Erro ao carregar {file_path}: {e}")
        return {}, False

def extract_schema(data: Any, prefix: str = "", depth: int = 0, max_depth: int = 5) -> Dict[str, Any]:
    """Extrai o esquema estrutural de dados JSON"""
    
    schema = {}
    
    if depth >= max_depth:
        return {"_type": type(data).__name__, "_truncated": True}
    
    if isinstance(data, dict):
        schema["_type"] = "object"
        schema["_fields"] = {}
        schema["_field_count"] = len(data)
        
        for key, value in data.items():
            field_path = f"{prefix}.{key}" if prefix else key
            schema["_fields"][key] = extract_schema(value, field_path, depth + 1, max_depth)
            
    elif isinstance(data, list):
        schema["_type"] = "array"
        schema["_length"] = len(data)
        
        if data:
            # Analisa tipos únicos nos elementos da array
            element_types = set()
            sample_schemas = []
            
            for item in data[:3]:  # Analisa até 3 itens como amostra
                item_schema = extract_schema(item, f"{prefix}[]", depth + 1, max_depth)
                element_types.add(item_schema.get("_type", "unknown"))
                sample_schemas.append(item_schema)
            
            schema["_element_types"] = list(element_types)
            schema["_sample_schema"] = sample_schemas[0] if sample_schemas else None
            
    else:
        schema["_type"] = type(data).__name__
        if isinstance(data, (str, int, float, bool)) and data is not None:
            schema["_sample"] = str(data)[:50]  # Primeiros 50 chars como amostra
    
    return schema

def compare_schemas(schema1: Dict[str, Any], schema2: Dict[str, Any], path: str = "") -> List[Dict[str, Any]]:
    """Compara dois esquemas e retorna as diferenças"""
    
    differences = []
    
    # Verifica tipo básico
    type1 = schema1.get("_type", "unknown")
    type2 = schema2.get("_type", "unknown")
    
    if type1 != type2:
        differences.append({
            "path": path or "root",
            "type": "type_mismatch",
            "schema1_type": type1,
            "schema2_type": type2
        })
        return differences  # Tipos diferentes, não continua comparação profunda
    
    # Compara objetos
    if type1 == "object":
        fields1 = set(schema1.get("_fields", {}).keys())
        fields2 = set(schema2.get("_fields", {}).keys())
        
        # Campos exclusivos
        only_in_1 = fields1 - fields2
        only_in_2 = fields2 - fields1
        common_fields = fields1 & fields2
        
        if only_in_1:
            differences.append({
                "path": path or "root",
                "type": "fields_only_in_first",
                "fields": list(only_in_1)
            })
        
        if only_in_2:
            differences.append({
                "path": path or "root",
                "type": "fields_only_in_second",
                "fields": list(only_in_2)
            })
        
        # Compara campos comuns recursivamente
        for field in common_fields:
            field_path = f"{path}.{field}" if path else field
            field_diffs = compare_schemas(
                schema1["_fields"][field],
                schema2["_fields"][field],
                field_path
            )
            differences.extend(field_diffs)
    
    # Compara arrays
    elif type1 == "array":
        elem_types1 = set(schema1.get("_element_types", []))
        elem_types2 = set(schema2.get("_element_types", []))
        
        if elem_types1 != elem_types2:
            differences.append({
                "path": path or "root",
                "type": "array_element_types",
                "schema1_types": list(elem_types1),
                "schema2_types": list(elem_types2)
            })
        
        # Compara sample schemas se disponíveis
        sample1 = schema1.get("_sample_schema")
        sample2 = schema2.get("_sample_schema")
        
        if sample1 and sample2:
            sample_diffs = compare_schemas(sample1, sample2, f"{path}[]")
            differences.extend(sample_diffs)
    
    return differences

def compare_field_values(data1: Dict[str, Any], data2: Dict[str, Any], fields_to_compare: List[str]) -> List[Dict[str, Any]]:
    """Compara valores de campos específicos entre dois datasets"""
    
    value_differences = []
    
    for field_path in fields_to_compare:
        value1 = get_nested_value(data1, field_path)
        value2 = get_nested_value(data2, field_path)
        
        if value1 != value2:
            value_differences.append({
                "field": field_path,
                "value1": str(value1)[:100] if value1 is not None else None,
                "value2": str(value2)[:100] if value2 is not None else None,
                "type1": type(value1).__name__,
                "type2": type(value2).__name__
            })
    
    return value_differences

def get_nested_value(data: Any, path: str) -> Any:
    """Obtém valor de um campo aninhado usando path com notação de ponto"""
    
    if not path:
        return data
    
    parts = path.split('.')
    current = data
    
    for part in parts:
        if part.endswith('[]'):
            # Handle array notation
            key = part[:-2]
            if isinstance(current, dict) and key in current:
                current = current[key]
                if isinstance(current, list) and current:
                    current = current[0]  # Pega primeiro elemento como amostra
                else:
                    return None
            else:
                return None
        else:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
    
    return current

def analyze_structural_patterns(all_schemas: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa padrões estruturais entre todos os esquemas"""
    
    patterns = {
        "structure_groups": defaultdict(list),
        "field_frequency": Counter(),
        "type_consistency": defaultdict(lambda: defaultdict(int)),
        "depth_analysis": {},
        "complexity_metrics": {}
    }
    
    # Agrupa por estrutura similar
    for filename, schema in all_schemas.items():
        structure_key = schema.get("_type", "unknown")
        if structure_key == "object":
            # Para objetos, usa número de campos como parte da chave
            field_count = schema.get("_field_count", 0)
            structure_key = f"object_{field_count}_fields"
        
        patterns["structure_groups"][structure_key].append(filename)
        
        # Conta frequência de campos
        if schema.get("_type") == "object":
            count_fields_recursive(schema, patterns["field_frequency"], patterns["type_consistency"])
        
        # Analisa profundidade
        max_depth = calculate_max_depth(schema)
        patterns["depth_analysis"][filename] = max_depth
        
        # Métricas de complexidade
        patterns["complexity_metrics"][filename] = calculate_complexity(schema)
    
    return patterns

def count_fields_recursive(schema: Dict[str, Any], field_counter: Counter, type_tracker: Dict, prefix: str = ""):
    """Conta campos recursivamente e rastreia tipos"""
    
    if schema.get("_type") == "object" and "_fields" in schema:
        for field_name, field_schema in schema["_fields"].items():
            field_path = f"{prefix}.{field_name}" if prefix else field_name
            field_counter[field_path] += 1
            type_tracker[field_path][field_schema.get("_type", "unknown")] += 1
            
            # Recursão para campos aninhados
            if field_schema.get("_type") == "object":
                count_fields_recursive(field_schema, field_counter, type_tracker, field_path)

def calculate_max_depth(schema: Dict[str, Any], current_depth: int = 0) -> int:
    """Calcula profundidade máxima do esquema"""
    
    if current_depth > 10:  # Previne recursão infinita
        return current_depth
    
    max_depth = current_depth
    
    if schema.get("_type") == "object" and "_fields" in schema:
        for field_schema in schema["_fields"].values():
            depth = calculate_max_depth(field_schema, current_depth + 1)
            max_depth = max(max_depth, depth)
    elif schema.get("_type") == "array" and schema.get("_sample_schema"):
        depth = calculate_max_depth(schema["_sample_schema"], current_depth + 1)
        max_depth = max(max_depth, depth)
    
    return max_depth

def calculate_complexity(schema: Dict[str, Any]) -> Dict[str, Any]:
    """Calcula métricas de complexidade do esquema"""
    
    metrics = {
        "total_fields": 0,
        "nested_objects": 0,
        "arrays": 0,
        "max_depth": 0,
        "unique_types": set()
    }
    
    def analyze_recursive(s: Dict[str, Any], depth: int = 0):
        s_type = s.get("_type", "unknown")
        metrics["unique_types"].add(s_type)
        metrics["max_depth"] = max(metrics["max_depth"], depth)
        
        if s_type == "object" and "_fields" in s:
            if depth > 0:
                metrics["nested_objects"] += 1
            metrics["total_fields"] += len(s["_fields"])
            
            for field_schema in s["_fields"].values():
                analyze_recursive(field_schema, depth + 1)
        elif s_type == "array":
            metrics["arrays"] += 1
            if s.get("_sample_schema"):
                analyze_recursive(s["_sample_schema"], depth + 1)
    
    analyze_recursive(schema)
    metrics["unique_types"] = list(metrics["unique_types"])
    
    return metrics

def generate_comparison_matrix(all_schemas: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, int]]:
    """Gera matriz de comparação entre todos os pares de arquivos"""
    
    matrix = {}
    files = list(all_schemas.keys())
    
    for i, file1 in enumerate(files):
        matrix[file1] = {}
        for j, file2 in enumerate(files):
            if i != j:
                differences = compare_schemas(all_schemas[file1], all_schemas[file2])
                matrix[file1][file2] = len(differences)
            else:
                matrix[file1][file2] = 0
    
    return matrix

def main():
    """Executa comparação estrutural completa"""
    
    epic_files = [
        ('/home/david/Documentos/canimport/test-tdd-project/epics/epic_template.json', 'epic_template.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/example_epic_0.json', 'example_epic_0.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/template_epic.json', 'main_template_epic.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/epic_1.json', 'epic_1.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/template_epic.json', 'template_template_epic.json')
    ]
    
    print("🔍 COMPARANDO ESTRUTURAS ENTRE ARQUIVOS - TAREFA 1.1.1.7")
    print("=" * 60)
    print()
    
    # Carrega todos os arquivos e extrai esquemas
    all_data = {}
    all_schemas = {}
    
    for file_path, filename in epic_files:
        if os.path.exists(file_path):
            print(f"📄 Processando {filename}...")
            data, success = load_json_file(file_path)
            
            if success:
                all_data[filename] = data
                schema = extract_schema(data)
                all_schemas[filename] = schema
                
                complexity = calculate_complexity(schema)
                print(f"   ✅ Esquema extraído | Campos: {complexity['total_fields']} | Profundidade: {complexity['max_depth']}")
            else:
                print(f"   ❌ Falha ao processar")
        else:
            print(f"⚠️  Arquivo não encontrado: {filename}")
        print()
    
    if len(all_schemas) < 2:
        print("❌ Necessário pelo menos 2 arquivos para comparação")
        return {}
    
    # Análise de padrões estruturais
    print("=" * 80)
    print("📊 ANÁLISE DE PADRÕES ESTRUTURAIS")
    print("=" * 80)
    
    patterns = analyze_structural_patterns(all_schemas)
    
    # Grupos estruturais
    print("\n🏗️  Grupos por Estrutura:")
    for group_key, files in patterns["structure_groups"].items():
        print(f"   • {group_key}: {len(files)} arquivo(s)")
        for f in files:
            print(f"     - {f}")
    
    # Complexidade
    print("\n📈 Métricas de Complexidade:")
    for filename, metrics in patterns["complexity_metrics"].items():
        print(f"   • {filename}:")
        print(f"     - Total de campos: {metrics['total_fields']}")
        print(f"     - Profundidade máxima: {metrics['max_depth']}")
        print(f"     - Objetos aninhados: {metrics['nested_objects']}")
        print(f"     - Arrays: {metrics['arrays']}")
    
    # Matriz de comparação
    print("\n=" * 80)
    print("🔄 MATRIZ DE DIFERENÇAS ESTRUTURAIS")
    print("=" * 80)
    
    matrix = generate_comparison_matrix(all_schemas)
    
    # Imprime matriz
    files = list(all_schemas.keys())
    short_names = {f: f.split('.')[0][:10] for f in files}
    
    print("\n   ", end="")
    for f in files:
        print(f"{short_names[f]:>12}", end="")
    print()
    
    for file1 in files:
        print(f"{short_names[file1]:>12}", end="")
        for file2 in files:
            diff_count = matrix[file1][file2]
            if diff_count == 0:
                print(f"{'--':>12}", end="")
            else:
                print(f"{diff_count:>12}", end="")
        print()
    
    # Comparações detalhadas entre pares críticos
    print("\n=" * 80)
    print("🔍 COMPARAÇÕES DETALHADAS CRÍTICAS")
    print("=" * 80)
    
    # Compara estruturas nested vs flat
    nested_files = [f for f in all_schemas.keys() if all_schemas[f].get("_type") == "object" and 
                   "epic" in all_schemas[f].get("_fields", {})]
    flat_files = [f for f in all_schemas.keys() if f not in nested_files]
    
    if nested_files and flat_files:
        print(f"\n📋 Comparação: Nested ({nested_files[0]}) vs Flat ({flat_files[0]})")
        diffs = compare_schemas(all_schemas[nested_files[0]], all_schemas[flat_files[0]])
        
        for diff in diffs[:5]:  # Primeiras 5 diferenças
            print(f"   • {diff['type']} em {diff['path']}")
            if 'fields' in diff:
                print(f"     Campos: {', '.join(diff['fields'][:5])}")
    
    # Identifica campos inconsistentes
    print("\n⚠️  CAMPOS COM TIPOS INCONSISTENTES:")
    type_inconsistencies = []
    
    for field_path, type_counts in patterns["type_consistency"].items():
        if len(type_counts) > 1:
            type_inconsistencies.append({
                "field": field_path,
                "types": list(type_counts.keys()),
                "occurrences": dict(type_counts)
            })
    
    for inconsistency in type_inconsistencies[:10]:
        print(f"   • {inconsistency['field']}: {inconsistency['types']}")
    
    if len(type_inconsistencies) > 10:
        print(f"   ... e mais {len(type_inconsistencies) - 10} campos")
    
    # Recomendações
    print("\n=" * 80)
    print("💡 RECOMENDAÇÕES PARA NORMALIZAÇÃO")
    print("=" * 80)
    
    recommendations = generate_normalization_recommendations(patterns, matrix, type_inconsistencies)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print("\n✅ Comparação estrutural completa!")
    
    return {
        "schemas": all_schemas,
        "patterns": patterns,
        "comparison_matrix": matrix,
        "type_inconsistencies": type_inconsistencies,
        "recommendations": recommendations
    }

def generate_normalization_recommendations(patterns: Dict[str, Any], matrix: Dict[str, Dict[str, int]], 
                                          type_inconsistencies: List[Dict[str, Any]]) -> List[str]:
    """Gera recomendações para normalização baseadas nas diferenças encontradas"""
    
    recommendations = []
    
    # Verifica grupos estruturais
    structure_groups = patterns["structure_groups"]
    if len(structure_groups) > 1:
        recommendations.append("🔄 Unificar estrutura: escolher entre nested (com wrapper 'epic') ou flat (direto na raiz)")
    
    # Verifica inconsistências de tipos
    if type_inconsistencies:
        recommendations.append(f"📝 Padronizar tipos de {len(type_inconsistencies)} campos com tipos inconsistentes")
    
    # Verifica complexidade
    max_depths = [m["max_depth"] for m in patterns["complexity_metrics"].values()]
    if max(max_depths) > 5:
        recommendations.append("🏗️  Considerar achatamento de estruturas muito profundas (>5 níveis)")
    
    # Verifica variação estrutural
    total_diffs = sum(sum(row.values()) for row in matrix.values())
    if total_diffs > 50:
        recommendations.append("⚠️  Alta variação estrutural detectada - criar esquema unificado obrigatório")
    
    # Campos obrigatórios
    field_freq = patterns["field_frequency"]
    mandatory_fields = [f for f, count in field_freq.items() if count >= 4]
    if mandatory_fields:
        recommendations.append(f"✅ Definir {len(mandatory_fields)} campos como obrigatórios no schema")
    
    # Arrays inconsistentes
    array_fields = [f for f, types in patterns["type_consistency"].items() if "array" in types]
    if array_fields:
        recommendations.append("📊 Normalizar estrutura de arrays para consistência")
    
    # Identificadores
    recommendations.append("🔑 Padronizar formato de IDs (epic_id, task_id) para chaves primárias")
    
    # Timestamps
    recommendations.append("⏰ Adicionar campos de auditoria padrão (created_at, updated_at)")
    
    return recommendations

if __name__ == "__main__":
    main()