#!/usr/bin/env python3
"""
Script para analisar campos temporais e formatos
Tarefa 1.1.1.6 - Analisar campos temporais e formatos
"""

import json
import os
import re
from typing import Dict, Any, List, Set, Optional, Union
from collections import defaultdict, Counter
from datetime import datetime

def identify_temporal_fields(data: Any, prefix: str = "", max_depth: int = 5) -> List[Dict[str, Any]]:
    """Identifica campos que contêm informações temporais"""
    
    temporal_fields = []
    
    if max_depth <= 0:
        return temporal_fields
    
    if isinstance(data, dict):
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            # Verifica se o campo parece temporal pelo nome
            is_temporal_name = is_temporal_field_name(key)
            
            # Verifica se o valor parece temporal
            temporal_analysis = analyze_temporal_value(value)
            
            if is_temporal_name or temporal_analysis['is_temporal']:
                temporal_fields.append({
                    'field_path': current_path,
                    'field_name': key,
                    'value': value,
                    'value_type': type(value).__name__,
                    'is_temporal_by_name': is_temporal_name,
                    'temporal_analysis': temporal_analysis,
                    'depth': len(current_path.split('.'))
                })
            
            # Recursão para campos aninhados
            if isinstance(value, (dict, list)):
                nested_fields = identify_temporal_fields(value, current_path, max_depth - 1)
                temporal_fields.extend(nested_fields)
                
    elif isinstance(data, list) and data:
        # Analisa primeiros itens da lista
        for i, item in enumerate(data[:3]):
            array_prefix = f"{prefix}[]"
            nested_fields = identify_temporal_fields(item, array_prefix, max_depth - 1)
            temporal_fields.extend(nested_fields)
    
    return temporal_fields

def is_temporal_field_name(field_name: str) -> bool:
    """Verifica se o nome do campo sugere informação temporal"""
    
    temporal_indicators = [
        # Data/hora
        'date', 'time', 'datetime', 'timestamp', 'created', 'updated', 'modified',
        'start', 'end', 'finish', 'begin', 'deadline', 'due', 'expires', 'expiry',
        # Específicos do domínio
        'duration', 'estimate', 'elapsed', 'remaining', 'spent', 'logged',
        'session', 'period', 'interval', 'timeout', 'delay', 'schedule',
        # Sufixos comuns
        '_at', '_on', '_date', '_time', '_timestamp', '_duration'
    ]
    
    field_lower = field_name.lower()
    
    return any(indicator in field_lower for indicator in temporal_indicators)

def analyze_temporal_value(value: Any) -> Dict[str, Any]:
    """Analisa se um valor contém informação temporal"""
    
    result = {
        'is_temporal': False,
        'format_type': 'unknown',
        'format_pattern': None,
        'parsed_value': None,
        'confidence': 0.0,
        'issues': []
    }
    
    if value is None:
        return result
    
    # Converte para string para análise
    str_value = str(value).strip()
    
    if not str_value:
        return result
    
    # Tenta diferentes formatos temporais
    temporal_formats = [
        # ISO 8601 e derivados
        ('%Y-%m-%dT%H:%M:%S.%fZ', 'iso8601_microseconds_utc'),
        ('%Y-%m-%dT%H:%M:%SZ', 'iso8601_seconds_utc'),
        ('%Y-%m-%dT%H:%M:%S', 'iso8601_local'),
        ('%Y-%m-%d %H:%M:%S', 'datetime_standard'),
        ('%Y-%m-%d', 'date_iso'),
        ('%d/%m/%Y', 'date_br'),
        ('%m/%d/%Y', 'date_us'),
        ('%d-%m-%Y', 'date_br_dash'),
        ('%Y%m%d', 'date_compact'),
        
        # Formatos de hora
        ('%H:%M:%S', 'time_full'),
        ('%H:%M', 'time_short'),
        
        # Formatos específicos
        ('%Y-%m-%d %H:%M:%S.%f', 'datetime_microseconds'),
        ('%d %b %Y', 'date_text_short'),
        ('%d %B %Y', 'date_text_long'),
    ]
    
    # Tenta parsear com cada formato
    for fmt, format_name in temporal_formats:
        try:
            parsed = datetime.strptime(str_value, fmt)
            result.update({
                'is_temporal': True,
                'format_type': format_name,
                'format_pattern': fmt,
                'parsed_value': parsed.isoformat(),
                'confidence': 1.0
            })
            return result
        except ValueError:
            continue
    
    # Verifica formatos numéricos (timestamps)
    if isinstance(value, (int, float)) or str_value.isdigit():
        timestamp_analysis = analyze_numeric_timestamp(value)
        if timestamp_analysis['is_timestamp']:
            result.update(timestamp_analysis)
            return result
    
    # Verifica duração em minutos/horas (campos estimate_minutes, etc.)
    if isinstance(value, (int, float)) and value > 0:
        duration_analysis = analyze_duration_value(value)
        if duration_analysis['is_duration']:
            result.update(duration_analysis)
            return result
    
    # Verifica padrões de texto temporal
    text_patterns = [
        (r'^\d{4}-\d{2}-\d{2}', 'date_like_pattern'),
        (r'^\d{2}:\d{2}', 'time_like_pattern'),
        (r'\d+\s*(min|hour|day|week|month|year)s?', 'duration_text_pattern'),
        (r'(ago|in)\s+\d+', 'relative_time_pattern'),
        (r'(today|tomorrow|yesterday)', 'relative_date_pattern')
    ]
    
    for pattern, pattern_name in text_patterns:
        if re.search(pattern, str_value, re.IGNORECASE):
            result.update({
                'is_temporal': True,
                'format_type': pattern_name,
                'format_pattern': pattern,
                'confidence': 0.7,
                'issues': ['needs_parsing_validation']
            })
            return result
    
    return result

def analyze_numeric_timestamp(value: Union[int, float]) -> Dict[str, Any]:
    """Analisa se um valor numérico é um timestamp"""
    
    result = {
        'is_temporal': False,
        'is_timestamp': False,
        'format_type': 'unknown',
        'confidence': 0.0
    }
    
    try:
        num_value = float(value)
        
        # Timestamps Unix (segundos desde 1970)
        if 1000000000 <= num_value <= 2147483647:  # ~2001 to ~2038
            try:
                parsed = datetime.fromtimestamp(num_value)
                result.update({
                    'is_temporal': True,
                    'is_timestamp': True,
                    'format_type': 'unix_timestamp_seconds',
                    'parsed_value': parsed.isoformat(),
                    'confidence': 0.9
                })
                return result
            except (ValueError, OSError):
                pass
        
        # Timestamps em milissegundos
        if 1000000000000 <= num_value <= 2147483647000:  # ~2001 to ~2038 in ms
            try:
                parsed = datetime.fromtimestamp(num_value / 1000)
                result.update({
                    'is_temporal': True,
                    'is_timestamp': True,
                    'format_type': 'unix_timestamp_milliseconds',
                    'parsed_value': parsed.isoformat(),
                    'confidence': 0.9
                })
                return result
            except (ValueError, OSError):
                pass
        
    except (ValueError, TypeError):
        pass
    
    return result

def analyze_duration_value(value: Union[int, float]) -> Dict[str, Any]:
    """Analisa se um valor numérico representa duração"""
    
    result = {
        'is_temporal': False,
        'is_duration': False,
        'format_type': 'unknown',
        'confidence': 0.0
    }
    
    try:
        num_value = float(value)
        
        # Duração em minutos (valores típicos: 15, 30, 60, 120, etc.)
        if 1 <= num_value <= 10080:  # 1 minuto a 1 semana
            result.update({
                'is_temporal': True,
                'is_duration': True,
                'format_type': 'duration_minutes',
                'duration_hours': num_value / 60,
                'duration_days': num_value / (60 * 24),
                'confidence': 0.8
            })
            return result
        
        # Duração em segundos
        if 60 <= num_value <= 604800:  # 1 minuto a 1 semana em segundos
            result.update({
                'is_temporal': True,
                'is_duration': True,
                'format_type': 'duration_seconds',
                'duration_minutes': num_value / 60,
                'duration_hours': num_value / 3600,
                'confidence': 0.7
            })
            return result
            
    except (ValueError, TypeError):
        pass
    
    return result

def analyze_file_temporal_fields(file_path: str, file_name: str) -> Dict[str, Any]:
    """Analisa campos temporais em um arquivo específico"""
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Identifica todos os campos temporais
        temporal_fields = identify_temporal_fields(data)
        
        # Agrupa por tipo de formato
        format_groups = defaultdict(list)
        for field in temporal_fields:
            format_type = field['temporal_analysis']['format_type']
            format_groups[format_type].append(field)
        
        # Analisa consistência
        consistency_analysis = analyze_temporal_consistency(temporal_fields)
        
        # Estatísticas
        stats = {
            'total_temporal_fields': len(temporal_fields),
            'unique_formats': len(format_groups),
            'format_distribution': {fmt: len(fields) for fmt, fields in format_groups.items()},
            'fields_by_depth': Counter(field['depth'] for field in temporal_fields)
        }
        
        return {
            'file_name': file_name,
            'valid_analysis': True,
            'temporal_fields': temporal_fields,
            'format_groups': dict(format_groups),
            'consistency_analysis': consistency_analysis,
            'stats': stats
        }
        
    except Exception as e:
        return {
            'file_name': file_name,
            'valid_analysis': False,
            'error': str(e),
            'temporal_fields': [],
            'format_groups': {},
            'consistency_analysis': {},
            'stats': {}
        }

def analyze_temporal_consistency(temporal_fields: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analisa consistência dos formatos temporais"""
    
    # Agrupa campos similares por nome
    name_groups = defaultdict(list)
    for field in temporal_fields:
        base_name = field['field_name'].lower()
        # Remove sufixos comuns para agrupar campos similares
        for suffix in ['_at', '_on', '_date', '_time', '_timestamp']:
            if base_name.endswith(suffix):
                base_name = base_name[:-len(suffix)]
                break
        name_groups[base_name].append(field)
    
    # Verifica inconsistências
    inconsistencies = []
    for name, fields in name_groups.items():
        if len(fields) > 1:
            formats = set(f['temporal_analysis']['format_type'] for f in fields)
            if len(formats) > 1:
                inconsistencies.append({
                    'field_name_base': name,
                    'formats_found': list(formats),
                    'field_paths': [f['field_path'] for f in fields]
                })
    
    # Qualidade geral dos formatos
    format_quality = Counter()
    for field in temporal_fields:
        confidence = field['temporal_analysis']['confidence']
        if confidence >= 0.9:
            format_quality['high'] += 1
        elif confidence >= 0.7:
            format_quality['medium'] += 1
        else:
            format_quality['low'] += 1
    
    return {
        'inconsistencies': inconsistencies,
        'inconsistency_count': len(inconsistencies),
        'format_quality_distribution': dict(format_quality),
        'total_fields_analyzed': len(temporal_fields)
    }

def analyze_all_files() -> Dict[str, Any]:
    """Analisa campos temporais em todos os arquivos"""
    
    epic_files = [
        ('/home/david/Documentos/canimport/test-tdd-project/epics/epic_template.json', 'epic_template.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/example_epic_0.json', 'example_epic_0.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/epics/template_epic.json', 'main_template_epic.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/epic_1.json', 'epic_1.json'),
        ('/home/david/Documentos/canimport/test-tdd-project/tdd-project-template/epics/template_epic.json', 'template_template_epic.json')
    ]
    
    analysis_results = {}
    
    print("📅 ANALISANDO CAMPOS TEMPORAIS - TAREFA 1.1.1.6")
    print("=" * 60)
    print()
    
    for file_path, filename in epic_files:
        if os.path.exists(file_path):
            print(f"⏰ Analisando campos temporais em {filename}...")
            
            analysis = analyze_file_temporal_fields(file_path, filename)
            analysis_results[filename] = analysis
            
            if analysis['valid_analysis']:
                stats = analysis['stats']
                print(f"   ✅ Campos temporais: {stats['total_temporal_fields']} | Formatos: {stats['unique_formats']}")
            else:
                print(f"   ❌ Erro: {analysis['error']}")
        else:
            print(f"⚠️  Arquivo não encontrado: {filename}")
        
        print()
    
    return analysis_results

def generate_temporal_report(analysis_results: Dict[str, Any]):
    """Gera relatório detalhado dos campos temporais"""
    
    print("=" * 80)
    print("⏰ RELATÓRIO DE CAMPOS TEMPORAIS")
    print("=" * 80)
    print()
    
    # Análise por arquivo
    for filename, analysis in analysis_results.items():
        if not analysis['valid_analysis']:
            continue
            
        print(f"📁 {filename}")
        print("-" * 50)
        
        stats = analysis['stats']
        consistency = analysis['consistency_analysis']
        
        print(f"📊 Total de campos temporais: {stats['total_temporal_fields']}")
        print(f"🔀 Formatos únicos: {stats['unique_formats']}")
        
        # Distribuição por formato
        if stats['format_distribution']:
            print(f"📈 Distribuição de formatos:")
            for fmt, count in sorted(stats['format_distribution'].items(), key=lambda x: x[1], reverse=True):
                print(f"   • {fmt}: {count} campos")
        
        # Inconsistências
        if consistency['inconsistency_count'] > 0:
            print(f"⚠️  Inconsistências encontradas: {consistency['inconsistency_count']}")
            for inconsistency in consistency['inconsistencies'][:3]:
                print(f"   • {inconsistency['field_name_base']}: {inconsistency['formats_found']}")
        else:
            print("✅ Formatos consistentes")
        
        # Campos temporais mais relevantes
        temporal_fields = analysis['temporal_fields']
        high_confidence_fields = [f for f in temporal_fields if f['temporal_analysis']['confidence'] >= 0.8]
        
        if high_confidence_fields:
            print(f"🎯 Campos temporais relevantes ({len(high_confidence_fields)}):")
            for field in high_confidence_fields[:5]:
                format_type = field['temporal_analysis']['format_type']
                print(f"   • {field['field_path']}: {format_type}")
        
        print()
    
    # Análise consolidada
    print("=" * 80)
    print("📊 ANÁLISE CONSOLIDADA DE FORMATOS TEMPORAIS")
    print("=" * 80)
    
    # Agrega todos os campos temporais
    all_temporal_fields = []
    for analysis in analysis_results.values():
        if analysis['valid_analysis']:
            all_temporal_fields.extend(analysis['temporal_fields'])
    
    if not all_temporal_fields:
        print("⚠️  Nenhum campo temporal encontrado")
        return {}
    
    # Formatos mais comuns
    all_formats = [f['temporal_analysis']['format_type'] for f in all_temporal_fields]
    format_counter = Counter(all_formats)
    
    print(f"🔢 Total de campos temporais: {len(all_temporal_fields)}")
    print(f"🎯 Formatos únicos encontrados: {len(format_counter)}")
    print()
    
    print("📈 Formatos mais comuns:")
    for fmt, count in format_counter.most_common(10):
        percentage = (count / len(all_temporal_fields)) * 100
        print(f"   • {fmt}: {count} campos ({percentage:.1f}%)")
    print()
    
    # Análise de qualidade
    quality_dist = Counter()
    for field in all_temporal_fields:
        confidence = field['temporal_analysis']['confidence']
        if confidence >= 0.9:
            quality_dist['alta'] += 1
        elif confidence >= 0.7:
            quality_dist['média'] += 1
        else:
            quality_dist['baixa'] += 1
    
    print("🎖️  Qualidade da detecção temporal:")
    for quality, count in quality_dist.items():
        percentage = (count / len(all_temporal_fields)) * 100
        print(f"   • {quality.capitalize()}: {count} campos ({percentage:.1f}%)")
    print()
    
    # Campos por categoria funcional
    field_categories = categorize_temporal_fields(all_temporal_fields)
    
    print("🏷️  Categorias funcionais:")
    for category, fields in field_categories.items():
        print(f"   • {category}: {len(fields)} campos")
        if fields:
            examples = list(set(f['field_name'] for f in fields))[:3]
            print(f"     Exemplos: {', '.join(examples)}")
    print()
    
    # Identificação de problemas críticos
    critical_issues = identify_critical_temporal_issues(all_temporal_fields, analysis_results)
    
    if critical_issues:
        print("⚠️  PROBLEMAS CRÍTICOS IDENTIFICADOS:")
        for issue in critical_issues:
            print(f"   🔴 {issue}")
    else:
        print("✅ Nenhum problema crítico identificado")
    
    print()
    
    # Recomendações para migração
    print("=" * 80)
    print("💡 RECOMENDAÇÕES PARA MIGRAÇÃO")
    print("=" * 80)
    
    recommendations = generate_temporal_recommendations(all_temporal_fields, format_counter)
    
    for i, rec in enumerate(recommendations, 1):
        print(f"{i}. {rec}")
    
    print()
    print("✅ Análise de campos temporais completa!")
    
    return {
        'total_temporal_fields': len(all_temporal_fields),
        'format_distribution': dict(format_counter),
        'quality_distribution': dict(quality_dist),
        'field_categories': {k: len(v) for k, v in field_categories.items()},
        'critical_issues': critical_issues,
        'recommendations': recommendations
    }

def categorize_temporal_fields(temporal_fields: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Categoriza campos temporais por função"""
    
    categories = {
        'auditoria': [],      # created_at, updated_at, etc.
        'estimativa': [],     # estimate_minutes, duration, etc.
        'cronograma': [],     # start_date, end_date, deadline, etc.
        'sessao': [],         # session_start, elapsed_time, etc.
        'versionamento': [],  # version_date, release_date, etc.
        'outros': []
    }
    
    for field in temporal_fields:
        field_name = field['field_name'].lower()
        field_path = field['field_path'].lower()
        
        # Auditoria (created/updated timestamps)
        if any(term in field_name for term in ['created', 'updated', 'modified', 'logged']):
            categories['auditoria'].append(field)
        
        # Estimativas e durações
        elif any(term in field_name for term in ['estimate', 'duration', 'minutes', 'elapsed', 'spent']):
            categories['estimativa'].append(field)
        
        # Cronograma
        elif any(term in field_name for term in ['start', 'end', 'deadline', 'due', 'schedule', 'date']):
            categories['cronograma'].append(field)
        
        # Sessões de trabalho
        elif any(term in field_name for term in ['session', 'timer', 'tracking']):
            categories['sessao'].append(field)
        
        # Versionamento
        elif any(term in field_name for term in ['version', 'release', 'deploy']):
            categories['versionamento'].append(field)
        
        else:
            categories['outros'].append(field)
    
    return categories

def identify_critical_temporal_issues(temporal_fields: List[Dict[str, Any]], analysis_results: Dict[str, Any]) -> List[str]:
    """Identifica problemas críticos nos campos temporais"""
    
    issues = []
    
    # Verifica inconsistências graves entre arquivos
    format_by_field_name = defaultdict(set)
    for field in temporal_fields:
        format_by_field_name[field['field_name']].add(field['temporal_analysis']['format_type'])
    
    inconsistent_fields = [name for name, formats in format_by_field_name.items() if len(formats) > 1]
    
    if inconsistent_fields:
        issues.append(f"Campos com formatos inconsistentes entre arquivos: {', '.join(inconsistent_fields[:3])}")
    
    # Verifica campos de baixa confiança
    low_confidence_count = sum(1 for f in temporal_fields if f['temporal_analysis']['confidence'] < 0.7)
    if low_confidence_count > len(temporal_fields) * 0.2:  # Mais de 20%
        issues.append(f"{low_confidence_count} campos temporais com baixa confiança de detecção")
    
    # Verifica ausência de campos de auditoria
    audit_fields = [f for f in temporal_fields if any(term in f['field_name'].lower() for term in ['created', 'updated'])]
    if len(audit_fields) < 2:
        issues.append("Campos de auditoria (created_at/updated_at) ausentes ou insuficientes")
    
    # Verifica formatos não padronizados
    non_standard_formats = [f for f in temporal_fields if 'unknown' in f['temporal_analysis']['format_type']]
    if non_standard_formats:
        issues.append(f"{len(non_standard_formats)} campos com formatos não reconhecidos")
    
    # Verifica estimate_minutes inconsistente
    estimate_fields = [f for f in temporal_fields if 'estimate' in f['field_name'].lower()]
    estimate_formats = set(f['temporal_analysis']['format_type'] for f in estimate_fields)
    if len(estimate_formats) > 1:
        issues.append("Campo estimate_minutes com formatos inconsistentes")
    
    return issues

def generate_temporal_recommendations(temporal_fields: List[Dict[str, Any]], format_counter: Counter) -> List[str]:
    """Gera recomendações para migração temporal"""
    
    recommendations = []
    
    # Padronização de formato
    most_common_format = format_counter.most_common(1)[0][0] if format_counter else None
    if most_common_format and format_counter[most_common_format] < len(temporal_fields) * 0.8:
        recommendations.append(f"📅 Padronizar todos os timestamps para formato {most_common_format}")
    
    # Campos de auditoria
    audit_fields = [f for f in temporal_fields if any(term in f['field_name'].lower() for term in ['created', 'updated'])]
    if len(audit_fields) < 2:
        recommendations.append("🕒 Adicionar campos de auditoria obrigatórios: created_at, updated_at")
    
    # Durações em minutos
    duration_fields = [f for f in temporal_fields if 'estimate' in f['field_name'].lower()]
    if duration_fields:
        recommendations.append("⏱️  Manter estimate_minutes como INTEGER NOT NULL para consistência")
    
    # Timezone
    recommendations.append("🌍 Definir timezone padrão (UTC) para todos os timestamps")
    
    # Validação
    low_confidence = [f for f in temporal_fields if f['temporal_analysis']['confidence'] < 0.7]
    if low_confidence:
        recommendations.append(f"🔍 Validar manualmente {len(low_confidence)} campos temporais de baixa confiança")
    
    # Indexação
    recommendations.append("📊 Criar índices em campos temporais frequentemente consultados")
    
    # Normalização
    if len(format_counter) > 3:
        recommendations.append("🔄 Implementar normalização automática de formatos temporais no ETL")
    
    return recommendations

def main():
    """Executa análise completa de campos temporais"""
    analysis_results = analyze_all_files()
    summary = generate_temporal_report(analysis_results)
    
    return {
        'detailed_analysis': analysis_results,
        'summary': summary
    }

if __name__ == "__main__":
    main()