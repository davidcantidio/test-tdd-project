#!/usr/bin/env python3
"""
Script para auditar estrutura completa dos arquivos JSON de épicos
Tarefa 1.1.1.3 - Extrair estrutura completa de cada JSON (1º, 2º, 3º nível)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Set
from collections import defaultdict

def extract_structure_recursive(data: Any, prefix: str = "", level: int = 1, max_level: int = 3) -> Set[str]:
    """Extrai todos os campos recursivamente até o nível máximo especificado"""
    fields = set()
    
    if level > max_level:
        return fields
        
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            fields.add(f"L{level}: {current_path} ({type(value).__name__})")
            
            # Recursão para próximo nível
            if level < max_level:
                nested_fields = extract_structure_recursive(value, current_path, level + 1, max_level)
                fields.update(nested_fields)
                
    elif isinstance(data, list) and data:
        # Analisa o primeiro item da lista para estrutura
        first_item = data[0]
        array_path = f"{prefix}[]"
        fields.add(f"L{level}: {array_path} (array of {type(first_item).__name__})")
        
        if level < max_level and isinstance(first_item, (dict, list)):
            nested_fields = extract_structure_recursive(first_item, array_path, level + 1, max_level)
            fields.update(nested_fields)
    
    return fields

def analyze_json_file(file_path: str) -> Dict[str, Any]:
    """Analisa um arquivo JSON específico"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Extrai estrutura até 3 níveis
        structure = extract_structure_recursive(data, max_level=3)
        
        # Estatísticas básicas
        stats = {
            'file_size_bytes': os.path.getsize(file_path),
            'root_keys_count': len(data.keys()) if isinstance(data, dict) else 0,
            'total_fields_found': len(structure),
            'structure_type': 'nested' if 'epic' in data else 'flat' if isinstance(data, dict) else 'unknown'
        }
        
        return {
            'file_path': file_path,
            'valid_json': True,
            'stats': stats,
            'structure': sorted(list(structure))
        }
        
    except Exception as e:
        return {
            'file_path': file_path,
            'valid_json': False,
            'error': str(e),
            'stats': {},
            'structure': []
        }

def main():
    """Executa análise de todos os arquivos JSON de épicos"""
    
    # Paths dos arquivos a analisar
    epic_files = [
        '/home/david/Documentos/canimport/test-tdd-project/epics/epic_template.json',
        '/home/david/Documentos/canimport/test-tdd-project/epics/example_epic_0.json',
        '/home/david/Documentos/canimport/test-tdd-project/epics/template_epic.json',
        '/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/epic_1.json',
        '/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/template_epic.json'
    ]
    
    print("=" * 80)
    print("📋 AUDITORIA DE ESTRUTURA DOS ARQUIVOS JSON - TAREFA 1.1.1.3")
    print("=" * 80)
    print()
    
    results = {}
    
    for file_path in epic_files:
        if os.path.exists(file_path):
            filename = os.path.basename(file_path)
            folder = os.path.basename(os.path.dirname(file_path))
            
            print(f"📄 Analisando {folder}/{filename}...")
            analysis = analyze_json_file(file_path)
            results[filename] = analysis
            
            # Exibe resumo
            if analysis['valid_json']:
                stats = analysis['stats']
                print(f"   ✅ Válido | Tamanho: {stats['file_size_bytes']} bytes | "
                      f"Tipo: {stats['structure_type']} | "
                      f"Campos: {stats['total_fields_found']}")
            else:
                print(f"   ❌ Erro: {analysis['error']}")
            print()
        else:
            print(f"⚠️  Arquivo não encontrado: {file_path}")
            print()
    
    # Análise comparativa
    print("=" * 80)
    print("📊 ANÁLISE COMPARATIVA DE ESTRUTURAS")
    print("=" * 80)
    
    # Agrupa por tipo de estrutura
    nested_files = []
    flat_files = []
    
    for filename, analysis in results.items():
        if analysis['valid_json']:
            if analysis['stats']['structure_type'] == 'nested':
                nested_files.append(filename)
            elif analysis['stats']['structure_type'] == 'flat':
                flat_files.append(filename)
    
    print(f"🏗️  Estrutura NESTED (wrapper 'epic'): {len(nested_files)} arquivos")
    for filename in nested_files:
        print(f"   • {filename}")
    print()
    
    print(f"📄 Estrutura FLAT (raiz direta): {len(flat_files)} arquivos")
    for filename in flat_files:
        print(f"   • {filename}")
    print()
    
    # Exibe estrutura detalhada do maior arquivo (example_epic_0.json)
    print("=" * 80)
    print("🔍 ESTRUTURA DETALHADA - example_epic_0.json (dados reais)")
    print("=" * 80)
    
    if 'example_epic_0.json' in results:
        structure = results['example_epic_0.json']['structure']
        for field in structure[:20]:  # Primeiros 20 campos
            print(f"   {field}")
        if len(structure) > 20:
            print(f"   ... e mais {len(structure) - 20} campos")
    
    print()
    print("✅ Análise de estrutura completa!")
    
    return results

if __name__ == "__main__":
    main()