# Inventário dos .py
find streamlit_extension -type f -name "*.py" | sort > .audit/py_files.txt

# Grafo (origem -> importado)
mkdir -p .audit
python - << 'PY'
import ast, os, csv, pathlib
root = pathlib.Path("streamlit_extension")
rows = []
for p in root.rglob("*.py"):
    mod = p.as_posix()
    try:
        tree = ast.parse(p.read_text(encoding="utf-8", errors="ignore"))
    except Exception:
        continue
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for n in node.names:
                rows.append((mod, n.name))
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                rows.append((mod, node.module))
with open(".audit/import_graph.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["from","imports"])
    w.writerows(rows)
PY

# Módulos nunca importados (prováveis órfãos)
cut -d, -f2 .audit/import_graph.csv | sed '1d' | sed 's/\./\//g' | sed 's/$/.py/' \
| sort -u > .audit/import_targets.txt

comm -23 <(cat .audit/py_files.txt | sed 's#^./##') <(grep -Fxf .audit/import_targets.txt .audit/py_files.txt | sort -u) \
> .audit/never_imported.txt

echo "Possíveis órfãos (nunca importados):"
cat .audit/never_imported.txt

