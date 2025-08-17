#!/bin/bash
# 🔍 AUDIT SCRIPT REFINADO - Identifica órfãos reais no módulo streamlit_extension

set -euo pipefail

AUDIT_DIR=".audit"
MODULE="streamlit_extension"

echo "🔍 Iniciando auditoria refinada do módulo ${MODULE}..."

# Limpar e criar diretório de auditoria
rm -rf "${AUDIT_DIR}"
mkdir -p "${AUDIT_DIR}"

# 1. Inventário completo de arquivos .py
find "${MODULE}" -type f -name "*.py" | sort > "${AUDIT_DIR}/all_py_files.txt"
echo "📁 Encontrados $(cat ${AUDIT_DIR}/all_py_files.txt | wc -l) arquivos Python"

# 2. Extrair imports APENAS do módulo streamlit_extension usando AST
echo "🔍 Analisando imports internos..."
python3 - << 'EOF'
import ast
import os
import pathlib
from collections import defaultdict

MODULE = "streamlit_extension"
AUDIT_DIR = ".audit"

# Coleta todos os imports internos
internal_imports = set()
import_graph = []
module_to_files = defaultdict(set)

root = pathlib.Path(MODULE)
for py_file in root.rglob("*.py"):
    file_path = py_file.as_posix()
    
    try:
        content = py_file.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(content)
    except Exception as e:
        print(f"⚠️  Erro parsing {file_path}: {e}")
        continue
    
    # Mapear arquivo para seu módulo Python
    rel_path = py_file.relative_to(root)
    if rel_path.name == "__init__.py":
        if len(rel_path.parts) == 1:
            module_name = MODULE
        else:
            module_name = f"{MODULE}.{'.'.join(rel_path.parts[:-1])}"
    else:
        if len(rel_path.parts) == 1:
            module_name = f"{MODULE}.{rel_path.stem}"
        else:
            module_name = f"{MODULE}.{'.'.join(rel_path.parts[:-1])}.{rel_path.stem}"
    
    module_to_files[module_name].add(file_path)
    
    # Extrair imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                import_name = alias.name
                if import_name.startswith(MODULE):
                    internal_imports.add(import_name)
                    import_graph.append((file_path, import_name))
        
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.startswith(MODULE):
                # Import from absoluto
                base_module = node.module
                internal_imports.add(base_module)
                import_graph.append((file_path, base_module))
                
                # Imports específicos
                for alias in node.names:
                    if alias.name != "*":
                        full_import = f"{base_module}.{alias.name}"
                        internal_imports.add(full_import)
                        import_graph.append((file_path, full_import))
            
            elif node.level > 0:
                # Import relativo - resolver caminho
                file_parts = pathlib.Path(file_path).parts[1:]  # Remove 'streamlit_extension'
                if pathlib.Path(file_path).name == "__init__.py":
                    current_package_parts = file_parts[:-1]  # Remove '__init__.py'
                else:
                    current_package_parts = file_parts[:-1]  # Remove 'file.py'
                
                # Calcular pacote de destino
                target_parts = list(current_package_parts)
                for _ in range(node.level - 1):
                    if target_parts:
                        target_parts.pop()
                
                if node.module:
                    target_parts.extend(node.module.split('.'))
                
                if target_parts:
                    target_module = f"{MODULE}.{'.'.join(target_parts)}"
                else:
                    target_module = MODULE
                
                internal_imports.add(target_module)
                import_graph.append((file_path, target_module))
                
                # Imports específicos relativos
                for alias in node.names:
                    if alias.name != "*":
                        full_import = f"{target_module}.{alias.name}"
                        internal_imports.add(full_import)
                        import_graph.append((file_path, full_import))

# Salvar imports internos
with open(f"{AUDIT_DIR}/internal_imports.txt", "w") as f:
    for imp in sorted(internal_imports):
        f.write(f"{imp}\n")

# Salvar grafo de imports
with open(f"{AUDIT_DIR}/import_graph_refined.txt", "w") as f:
    f.write("from_file,imports_module\n")
    for from_file, imports_module in sorted(import_graph):
        f.write(f"{from_file},{imports_module}\n")

# Mapear imports para arquivos possíveis
imported_files = set()
for import_name in internal_imports:
    # Tentar diferentes padrões de arquivo
    if import_name in module_to_files:
        imported_files.update(module_to_files[import_name])
    
    # Tentar como arquivo direto
    file_patterns = [
        import_name.replace(".", "/") + ".py",
        import_name.replace(".", "/") + "/__init__.py"
    ]
    
    for pattern in file_patterns:
        if pathlib.Path(pattern).exists():
            imported_files.add(pattern)

# Salvar arquivos importados
with open(f"{AUDIT_DIR}/imported_files.txt", "w") as f:
    for file_path in sorted(imported_files):
        f.write(f"{file_path}\n")

print(f"✅ Encontrados {len(internal_imports)} imports internos")
print(f"✅ Mapeados para {len(imported_files)} arquivos importados")
EOF

# 3. Identificar órfãos reais
echo "🔍 Identificando arquivos nunca importados..."
comm -23 <(sort "${AUDIT_DIR}/all_py_files.txt") <(sort "${AUDIT_DIR}/imported_files.txt") > "${AUDIT_DIR}/real_orphans.txt"

echo "📊 RESULTADOS:"
echo "   Total arquivos: $(cat ${AUDIT_DIR}/all_py_files.txt | wc -l)"
echo "   Arquivos importados: $(cat ${AUDIT_DIR}/imported_files.txt | wc -l)"
echo "   Órfãos reais: $(cat ${AUDIT_DIR}/real_orphans.txt | wc -l)"

# 4. Análise de segurança para deleção
echo "🛡️ Analisando segurança para deleção..."
python3 - << 'EOF'
import pathlib

AUDIT_DIR = ".audit"

# Carregar órfãos
with open(f"{AUDIT_DIR}/real_orphans.txt") as f:
    orphans = [line.strip() for line in f if line.strip()]

# Categorizar órfãos por nível de segurança
safe_to_delete = []
risky_to_delete = []
never_delete = []

for orphan in orphans:
    path = pathlib.Path(orphan)
    
    # NUNCA deletar
    if (path.name == "__init__.py" or 
        path.name == "streamlit_app.py" or
        "main" in path.name or
        "app" in path.name or
        path.suffix != ".py"):
        never_delete.append(orphan)
        continue
    
    # ARRISCADO deletar
    if (any(keyword in path.name for keyword in 
           ["service", "manager", "handler", "auth", "config", "database"]) or
        any(keyword in str(path) for keyword in 
           ["auth/", "config/", "services/", "utils/database"])):
        risky_to_delete.append(orphan)
        continue
    
    # SEGURO deletar
    safe_to_delete.append(orphan)

# Salvar resultados
with open(f"{AUDIT_DIR}/safe_to_delete.txt", "w") as f:
    for file_path in safe_to_delete:
        f.write(f"{file_path}\n")

with open(f"{AUDIT_DIR}/risky_to_delete.txt", "w") as f:
    for file_path in risky_to_delete:
        f.write(f"{file_path}\n")

with open(f"{AUDIT_DIR}/never_delete.txt", "w") as f:
    for file_path in never_delete:
        f.write(f"{file_path}\n")

print(f"✅ SEGURO deletar: {len(safe_to_delete)} arquivos")
print(f"⚠️  ARRISCADO deletar: {len(risky_to_delete)} arquivos")
print(f"🚫 NUNCA deletar: {len(never_delete)} arquivos")

if safe_to_delete:
    print("\n🗑️ ARQUIVOS SEGUROS PARA DELEÇÃO:")
    for file_path in safe_to_delete:
        print(f"   {file_path}")
EOF

echo "✅ Auditoria refinada concluída. Verifique os resultados em ${AUDIT_DIR}/"