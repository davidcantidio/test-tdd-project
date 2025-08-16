#!/usr/bin/env python3
"""
Script para catalogar campos únicos e criar inventário master
Tarefa 1.1.1.4 - Catalogar campos únicos e criar inventário master
"""

import json
import os
from typing import Dict, Any, List, Set
from collections import defaultdict, Counter

def extract_all_field_paths(data: Any, prefix: str = "", max_depth: int = 5) -> Set[str]:
    """Extrai todos os caminhos de campos recursivamente"""
    fields = set()
    
    if max_depth <= 0:
        return fields
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            fields.add(current_path)
            
            # Recursão para campos aninhados
            nested_fields = extract_all_field_paths(value, current_path, max_depth - 1)
            fields.update(nested_fields)
            
    elif isinstance(data, list) and data:
        # Analisa estrutura dos itens da lista
        for i, item in enumerate(data[:3]):  # Analisa primeiros 3 itens para detectar variações
            if isinstance(item, dict):
                array_prefix = f"{prefix}[]"
                nested_fields = extract_all_field_paths(item, array_prefix, max_depth - 1)
                fields.update(nested_fields)
            elif isinstance(item, list):
                array_prefix = f"{prefix}[]"
                nested_fields = extract_all_field_paths(item, array_prefix, max_depth - 1)
                fields.update(nested_fields)
    
    return fields

def get_field_type_info(data: Any, field_path: str) -> Dict[str, Any]:
    """Obtém informações detalhadas sobre um campo específico"""
    try:
        # Navega pelo caminho do campo
        parts = field_path.split('.')
        current = data
        
        for part in parts:
            if part.endswith('[]'):
                # Campo de array
                array_key = part[:-2]
                if isinstance(current, dict) and array_key in current:
                    current = current[array_key]
                    if isinstance(current, list) and current:
                        current = current[0]  # Primeiro item para análise
                else:
                    return {'type': 'unknown', 'found': False}
            else:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return {'type': 'unknown', 'found': False}
        
        # Analisa o valor final
        value_type = type(current).__name__
        sample_value = None
        
        if value_type in ['str', 'int', 'float', 'bool']:
            sample_value = current
        elif value_type == 'list':
            sample_value = f"array[{len(current)}] of {type(current[0]).__name__ if current else 'empty'}"
        elif value_type == 'dict':
            sample_value = f"object with {len(current)} keys"
        
        return {
            'type': value_type,
            'found': True,
            'sample_value': sample_value
        }
        
    except Exception:
        return {'type': 'unknown', 'found': False}

def analyze_all_files() -> Dict[str, Any]:
    """Analisa todos os arquivos e cataloga campos únicos"""
    
    epic_files = [
        ('/home/david/Documentos/canimport/test-tdd-project/epics/epic_template.json', 'epic_template.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/example_epic_0.json', 'example_epic_0.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/template_epic.json', 'main_template_epic.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/epic_1.json', 'epic_1.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/template_epic.json', 'template_template_epic.json')
    ]
    
    # Carrega todos os dados
    file_data = {}
    all_fields = set()
    field_frequency = Counter()
    field_types = defaultdict(lambda: defaultdict(int))
    
    print("📋 CATALOGANDO CAMPOS ÚNICOS - TAREFA 1.1.1.4")
    print("=" * 60)
    print()
    
    for file_path, filename in epic_files:
        if os.path.exists(file_path):
            print(f"📄 Processando {filename}...")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                file_data[filename] = data
                
                # Extrai todos os campos deste arquivo
                file_fields = extract_all_field_paths(data)
                all_fields.update(file_fields)
                
                # Conta frequência
                for field in file_fields:
                    field_frequency[field] += 1
                
                # Analisa tipos
                for field in file_fields:
                    type_info = get_field_type_info(data, field)
                    if type_info['found']:
                        field_types[field][type_info['type']] += 1
                
                print(f"   ✅ {len(file_fields)} campos únicos encontrados")
                
            except Exception as e:
                print(f"   ❌ Erro: {e}")
        else:
            print(f"⚠️  Arquivo não encontrado: {filename}")
        
        print()
    
    return {
        'total_unique_fields': len(all_fields),
        'field_frequency': field_frequency,
        'field_types': dict(field_types),
        'all_fields': sorted(list(all_fields)),
        'file_data': file_data
    }

def generate_field_report(analysis: Dict[str, Any]):
    """Gera relatório detalhado dos campos"""
    
    print("=" * 80)
    print("📊 INVENTÁRIO MASTER DE CAMPOS")
    print("=" * 80)
    print()
    
    total_fields = analysis['total_unique_fields']
    field_freq = analysis['field_frequency']
    field_types = analysis['field_types']
    
    print(f"🔢 Total de campos únicos encontrados: {total_fields}")
    print()
    
    # Análise de frequência
    print("📈 FREQUÊNCIA DOS CAMPOS (em quantos arquivos aparece)")
    print("-" * 60)
    
    # Agrupa por frequência
    freq_groups = defaultdict(list)
    for field, count in field_freq.items():
        freq_groups[count].append(field)
    
    for frequency in sorted(freq_groups.keys(), reverse=True):
        fields = freq_groups[frequency]
        print(f"\n🔹 Presentes em {frequency}/5 arquivos ({len(fields)} campos):")
        for field in sorted(fields)[:10]:  # Primeiros 10
            # Tipos encontrados para este campo
            types = list(field_types.get(field, {}).keys())
            type_info = f" ({', '.join(types)})" if types else ""
            print(f"   • {field}{type_info}")
        if len(fields) > 10:
            print(f"   ... e mais {len(fields) - 10} campos")
    
    print()
    print("=" * 80)
    print("🧮 ANÁLISE DE CONSISTÊNCIA DE TIPOS")
    print("=" * 80)
    
    # Campos com tipos inconsistentes
    inconsistent_fields = []
    for field, types in field_types.items():
        if len(types) > 1:
            inconsistent_fields.append((field, types))
    
    if inconsistent_fields:
        print(f"⚠️  {len(inconsistent_fields)} campos com tipos inconsistentes:")
        print()
        for field, types in sorted(inconsistent_fields)[:10]:
            type_list = [f"{t}({c})" for t, c in types.items()]
            print(f"   • {field}: {', '.join(type_list)}")
        if len(inconsistent_fields) > 10:
            print(f"   ... e mais {len(inconsistent_fields) - 10} campos")
    else:
        print("✅ Todos os campos têm tipos consistentes")
    
    print()
    print("=" * 80)
    print("🗂️  CAMPOS OBRIGATÓRIOS vs OPCIONAIS")
    print("=" * 80)
    
    # Classifica campos por obrigatoriedade
    mandatory_fields = [f for f, c in field_freq.items() if c >= 4]  # Em 4+ arquivos
    common_fields = [f for f, c in field_freq.items() if 2 <= c < 4]  # Em 2-3 arquivos  
    rare_fields = [f for f, c in field_freq.items() if c == 1]  # Apenas 1 arquivo
    
    print(f"🔴 OBRIGATÓRIOS (4+ arquivos): {len(mandatory_fields)} campos")
    for field in sorted(mandatory_fields)[:8]:
        print(f"   • {field}")
    if len(mandatory_fields) > 8:
        print(f"   ... e mais {len(mandatory_fields) - 8}")
    
    print(f"\n🟡 COMUNS (2-3 arquivos): {len(common_fields)} campos")
    for field in sorted(common_fields)[:8]:
        print(f"   • {field}")
    if len(common_fields) > 8:
        print(f"   ... e mais {len(common_fields) - 8}")
    
    print(f"\n🟢 RAROS (1 arquivo): {len(rare_fields)} campos")
    for field in sorted(rare_fields)[:8]:
        print(f"   • {field}")
    if len(rare_fields) > 8:
        print(f"   ... e mais {len(rare_fields) - 8}")
    
    print()
    print("✅ Catalogação de campos únicos completa!")
    
    return {
        'mandatory_fields': mandatory_fields,
        'common_fields': common_fields,
        'rare_fields': rare_fields,
        'inconsistent_types': inconsistent_fields
    }

def main():
    """Executa análise completa de campos únicos"""
    analysis = analyze_all_files()
    report = generate_field_report(analysis)
    
    # Salva resultado para próximas etapas
    return {**analysis, **report}

if __name__ == "__main__":
    main()