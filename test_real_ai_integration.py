#!/usr/bin/env python3
"""
Script de teste para verificar integração com IA real.

Uso:
    export OPENAI_API_KEY="sua-chave-real"
    python test_real_ai_integration.py
"""

import os
import sys
from typing import Dict, Any

def test_real_ai_integration():
    """Testa a integração com o sistema real de IA."""
    
    # Verificar se há API key
    api_key = os.environ.get('OPENAI_API_KEY', '')
    
    if not api_key or api_key.startswith('test-'):
        print("⚠️ OPENAI_API_KEY não configurada ou é de teste")
        print("   Para testar com IA real, execute:")
        print("   export OPENAI_API_KEY='sua-chave-real'")
        print("   python test_real_ai_integration.py")
        return False
    
    print(f"✅ API Key detectada: {api_key[:10]}...")
    
    try:
        # Importar o sistema
        from src.ia.agents.agno_agent import VisionRefinerAgent, ProductVisionDTO
        from src.ia.services.vision_refine_service import VisionRefineService
        
        print("🔧 Criando agente com gpt-5-nano...")
        agent = VisionRefinerAgent(model_id='gpt-5-nano')
        
        # Criar adapter
        class AgentAdapter:
            def __init__(self, agent):
                self.agent = agent
            
            def run(self, payload):
                result = self.agent.refine(payload)
                if isinstance(result, ProductVisionDTO):
                    return result.dict()
                return result
        
        print("🔧 Criando serviço de refinamento...")
        adapted_agent = AgentAdapter(agent)
        service = VisionRefineService(adapted_agent)
        
        # Payload de teste
        test_payload = {
            'vision_statement': 'criar plataforma inovadora de aprendizado',
            'problem_statement': 'falta de personalização no ensino online',
            'target_audience': 'estudantes e educadores',
            'value_proposition': 'aprendizado personalizado com IA',
            'constraints': ['prazo de 6 meses', 'orçamento limitado']
        }
        
        print("🤖 Chamando IA real (gpt-5-nano)...")
        print("-" * 50)
        
        result = service.refine(test_payload)
        
        print("✅ SUCESSO! IA real respondeu")
        print("-" * 50)
        
        # Mostrar comparação
        print("\n📊 COMPARAÇÃO:")
        print("-" * 50)
        
        for field in ['vision_statement', 'problem_statement', 'target_audience', 'value_proposition']:
            original = test_payload.get(field, '')
            refined = result.get(field, '')
            
            print(f"\n{field.upper()}:")
            print(f"  Original: {original}")
            print(f"  Refinado: {refined}")
            
            if original != refined:
                print(f"  ✨ Modificado pela IA")
            else:
                print(f"  ⚫ Sem alteração")
        
        # Constraints
        print(f"\nCONSTRAINTS:")
        print(f"  Original: {test_payload.get('constraints', [])}")
        print(f"  Refinado: {result.get('constraints', [])}")
        
        if test_payload.get('constraints') != result.get('constraints'):
            print(f"  ✨ Modificado pela IA")
        else:
            print(f"  ⚫ Sem alteração")
        
        print("\n" + "=" * 50)
        print("🎉 Sistema de IA real está funcionando perfeitamente!")
        print("=" * 50)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        
        # Diagnóstico
        if "401" in str(e) or "invalid_api_key" in str(e):
            print("\n💡 Problema: API key inválida")
            print("   Verifique se sua chave está correta em https://platform.openai.com/api-keys")
        elif "model" in str(e).lower():
            print("\n💡 Problema: Modelo gpt-5-nano pode não estar disponível")
            print("   Considere usar 'gpt-4' ou 'gpt-3.5-turbo' em src/ia/agents/agno_agent.py")
        elif "rate" in str(e).lower():
            print("\n💡 Problema: Limite de taxa excedido")
            print("   Aguarde alguns segundos e tente novamente")
        else:
            import traceback
            print("\n📋 Stack trace completo:")
            traceback.print_exc()
        
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("🧪 TESTE DE INTEGRAÇÃO COM IA REAL")
    print("=" * 50)
    
    success = test_real_ai_integration()
    
    if success:
        sys.exit(0)
    else:
        sys.exit(1)