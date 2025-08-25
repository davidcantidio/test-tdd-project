#!/usr/bin/env python3
"""
Script para testar a validade do token do GitHub
"""

import os
import sys
import pytest

# Tenta importar bibliotecas, se não estiverem disponíveis usa método alternativo
try:
    import requests
except ImportError:
    print("⚠️  Biblioteca 'requests' não encontrada. Usando urllib como fallback.")
    import urllib.request
    import json
    requests = None

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False

def load_env_manually():
    """Carrega .env manualmente se python-dotenv não estiver disponível"""
    env_path = '.env'
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()

def test_github_token():
    """Testa se o token do GitHub está funcionando"""
    
    # Carrega variáveis de ambiente
    if HAS_DOTENV:
        from dotenv import load_dotenv
        load_dotenv()
    else:
        load_env_manually()
    
    # Obtém o token
    token = os.getenv('GITHUB_TOKEN')

    if not token:
        pytest.skip("GITHUB_TOKEN não encontrado no arquivo .env")
    
    # Testa o token fazendo uma requisição para a API do GitHub
    headers = {
        'Authorization': f'token {token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    
    try:
        if requests:
            # Usa requests se disponível
            response = requests.get('https://api.github.com/user', headers=headers)
            status_code = response.status_code
            if status_code == 200:
                user_data = response.json()
            else:
                user_data = None
        else:
            # Usa urllib como fallback
            req = urllib.request.Request('https://api.github.com/user', headers=headers)
            try:
                with urllib.request.urlopen(req) as response:
                    status_code = response.status
                    user_data = json.loads(response.read().decode())
            except urllib.error.HTTPError as e:
                status_code = e.code
                user_data = None
        
        if status_code == 200 and user_data:
            print(f"✅ Token válido! Autenticado como: {user_data.get('login', 'Unknown')}")
            print(f"   Nome: {user_data.get('name', 'N/A')}")
            print(f"   Email: {user_data.get('email', 'N/A')}")
            
            # Verifica rate limit
            if requests:
                rate_response = requests.get('https://api.github.com/rate_limit', headers=headers)
                if rate_response.status_code == 200:
                    rate_data = rate_response.json()
            else:
                req = urllib.request.Request('https://api.github.com/rate_limit', headers=headers)
                try:
                    with urllib.request.urlopen(req) as response:
                        rate_data = json.loads(response.read().decode())
                except:
                    rate_data = None
            
            if rate_data:
                core_limit = rate_data['rate']
                print(f"\n📊 Rate Limit:")
                print(f"   Limite: {core_limit['limit']} requisições/hora")
                print(f"   Restante: {core_limit['remaining']} requisições")

            assert True
        elif status_code == 401:
            pytest.fail("Token inválido ou expirado")
        else:
            pytest.fail(f"Erro ao validar token: HTTP {status_code}")
            
    except Exception as e:
        pytest.fail(f"Erro de conexão: {e}")

if __name__ == "__main__":
    success = False
    try:
        test_github_token()
        success = True
    finally:
        sys.exit(0 if success else 1)
