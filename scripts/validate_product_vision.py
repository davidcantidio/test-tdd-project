#!/usr/bin/env python3
"""
Script de Validação Didática da ProductVision Entity (TASK-1.2.1)

Este script executa testes detalhados da entidade ProductVision com logs
didáticos que mostram cada assert individualmente, facilitando a verificação
manual e o entendimento do que está sendo testado.
"""

import sys
import os
from datetime import datetime
from typing import Any, List, Tuple
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import the entity
from tdd_core.domain.entities.product_vision import ProductVision


# ANSI color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


class ProductVisionValidator:
    """Validador didático para ProductVision entity."""

    def __init__(self):
        self.test_count = 0
        self.passed_count = 0
        self.failed_count = 0
        self.results: List[Tuple[str, bool, str]] = []

    def log_test(self, test_name: str):
        """Log início de um teste."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}🧪 TESTE: {test_name}{Colors.ENDC}")

    def log_assert(self, description: str, expected: Any, actual: Any, passed: bool = None):
        """Log um assert com valores esperados e obtidos."""
        self.test_count += 1

        if passed is None:
            passed = expected == actual

        if passed:
            self.passed_count += 1
            status = f"{Colors.GREEN}✅ PASSOU{Colors.ENDC}"
        else:
            self.failed_count += 1
            status = f"{Colors.RED}❌ FALHOU{Colors.ENDC}"

        print(f"   {Colors.CYAN}➤ Assert {self.test_count}:{Colors.ENDC} {description}")
        print(f"      Esperado: {Colors.YELLOW}{repr(expected)}{Colors.ENDC}")
        print(f"      Obtido:   {Colors.YELLOW}{repr(actual)}{Colors.ENDC}")
        print(f"      {status}")

        self.results.append((description, passed, f"Expected: {expected}, Got: {actual}"))
        return passed

    def log_section(self, section_name: str):
        """Log uma seção de testes."""
        print(f"\n{Colors.HEADER}{'='*80}")
        print(f"{Colors.BOLD}📚 {section_name}{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")

    def get_valid_data(self):
        """Retorna dados válidos para criar uma ProductVision."""
        return {
            "name": "TDD Framework",
            "vision_statement": "Revolucionar desenvolvimento com TDD",
            "target_user": "Desenvolvedores Python",
            "user_problem": "Complexidade em implementar testes efetivos",
            "expected_benefits": "Qualidade de código e produtividade aumentadas",
            "product_description": "Framework completo para TDD com gamificação",
            "success_metrics": "98% cobertura, zero bugs críticos",
            "tech_requirements": "Python 3.11+, SQLite, Streamlit",
            "non_functional_requirements": "Performance <1ms, disponibilidade 99.9%",
            "compliance_requirements": "GDPR, SOC2, ISO 27001",
            "risks": "Curva de aprendizado inicial",
            "assumptions": "Equipe experiente em Python",
            "must_have": "Persistência explícita, validação completa",
            "cannot_have": "Campos genéricos sem semântica",
            "deliverables": "API REST, CLI, Interface Web",
            "market_opportunity": "10M desenvolvedores Python"
        }

    def test_creation_with_valid_fields(self):
        """Testa criação com todos os campos válidos."""
        self.log_test("Criação de ProductVision com campos válidos")

        # Create entity
        data = self.get_valid_data()
        pv = ProductVision(**data)

        # Test each field
        self.log_assert(
            "Verificando campo 'name'",
            "TDD Framework",
            pv.name
        )

        self.log_assert(
            "Verificando campo 'vision_statement'",
            "Revolucionar desenvolvimento com TDD",
            pv.vision_statement
        )

        self.log_assert(
            "Verificando campo 'target_user'",
            "Desenvolvedores Python",
            pv.target_user
        )

        self.log_assert(
            "Verificando campo 'user_problem'",
            "Complexidade em implementar testes efetivos",
            pv.user_problem
        )

        self.log_assert(
            "Verificando se is_valid() retorna True",
            True,
            pv.is_valid()
        )

        # Check timestamps
        self.log_assert(
            "Verificando se created_at foi inicializado",
            True,
            pv.created_at is not None
        )

        self.log_assert(
            "Verificando se created_at é datetime",
            True,
            isinstance(pv.created_at, datetime)
        )

    def test_validation_with_empty_fields(self):
        """Testa validação com campos vazios."""
        self.log_test("Validação com campos vazios")

        # Create entity with empty fields
        data = self.get_valid_data()
        data["name"] = ""
        data["vision_statement"] = "   "  # Only whitespace

        pv = ProductVision(**data)

        # Test validation
        errors = pv.validate()

        self.log_assert(
            "Verificando se há erros de validação",
            True,
            len(errors) > 0
        )

        self.log_assert(
            "Verificando número de erros",
            2,
            len(errors)
        )

        self.log_assert(
            "Verificando mensagem de erro para 'name'",
            True,
            "name is required and cannot be empty" in errors
        )

        self.log_assert(
            "Verificando se is_valid() retorna False",
            False,
            pv.is_valid()
        )

    def test_all_required_fields(self):
        """Testa que todos os 16 campos obrigatórios são validados."""
        self.log_test("Validação de todos os 16 campos obrigatórios")

        # Create entity with all empty strings
        required_fields = [
            "name", "vision_statement", "target_user", "user_problem",
            "expected_benefits", "product_description", "success_metrics",
            "tech_requirements", "non_functional_requirements",
            "compliance_requirements", "risks", "assumptions",
            "must_have", "cannot_have", "deliverables", "market_opportunity"
        ]

        data = {field: "" for field in required_fields}
        pv = ProductVision(**data)

        errors = pv.validate()

        self.log_assert(
            "Verificando número total de erros",
            16,
            len(errors)
        )

        # Check a few specific error messages
        for field in ["name", "vision_statement", "target_user"]:
            self.log_assert(
                f"Verificando erro para campo '{field}'",
                True,
                f"{field} is required and cannot be empty" in errors
            )

    def test_optional_fields(self):
        """Testa campos opcionais."""
        self.log_test("Campos opcionais (id, timestamps)")

        data = self.get_valid_data()
        pv = ProductVision(**data)

        self.log_assert(
            "Verificando se 'id' é None antes da persistência",
            None,
            pv.id
        )

        # Test with explicit id
        data["id"] = 123
        pv_with_id = ProductVision(**data)

        self.log_assert(
            "Verificando se 'id' pode ser definido explicitamente",
            123,
            pv_with_id.id
        )

    def test_special_characters_and_unicode(self):
        """Testa caracteres especiais e Unicode."""
        self.log_test("Suporte a caracteres especiais e Unicode")

        data = self.get_valid_data()
        data["name"] = "Projeto 日本語 🚀"
        data["target_user"] = "Développeurs français"
        data["risks"] = "Test with 'quotes' and \"double quotes\" & <tags>"

        pv = ProductVision(**data)

        self.log_assert(
            "Verificando Unicode em 'name'",
            "Projeto 日本語 🚀",
            pv.name
        )

        self.log_assert(
            "Verificando acentos em 'target_user'",
            "Développeurs français",
            pv.target_user
        )

        self.log_assert(
            "Verificando caracteres especiais em 'risks'",
            "Test with 'quotes' and \"double quotes\" & <tags>",
            pv.risks
        )

        self.log_assert(
            "Verificando se entidade com caracteres especiais é válida",
            True,
            pv.is_valid()
        )

    def test_field_modification(self):
        """Testa modificação de campos após criação."""
        self.log_test("Modificação de campos após criação")

        data = self.get_valid_data()
        pv = ProductVision(**data)

        # Modify fields
        original_name = pv.name
        pv.name = "Modified Name"
        pv.vision_statement = "Modified Vision"

        self.log_assert(
            "Verificando modificação do campo 'name'",
            "Modified Name",
            pv.name
        )

        self.log_assert(
            "Verificando modificação do campo 'vision_statement'",
            "Modified Vision",
            pv.vision_statement
        )

        self.log_assert(
            "Verificando se entidade modificada continua válida",
            True,
            pv.is_valid()
        )

    def test_validate_method_return_type(self):
        """Testa tipo de retorno do método validate()."""
        self.log_test("Tipo de retorno do método validate()")

        data = self.get_valid_data()
        pv = ProductVision(**data)

        errors = pv.validate()

        self.log_assert(
            "Verificando se validate() retorna uma lista",
            True,
            isinstance(errors, list)
        )

        self.log_assert(
            "Verificando se lista está vazia para entidade válida",
            0,
            len(errors)
        )

        # Test with invalid entity
        pv.name = ""
        errors = pv.validate()

        self.log_assert(
            "Verificando se erros são strings",
            True,
            all(isinstance(e, str) for e in errors)
        )

    def test_multiline_strings(self):
        """Testa strings multilinhas."""
        self.log_test("Suporte a strings multilinhas")

        data = self.get_valid_data()
        multiline = """Linha 1
        Linha 2
        Linha 3"""
        data["product_description"] = multiline

        pv = ProductVision(**data)

        self.log_assert(
            "Verificando string multilinha em 'product_description'",
            multiline,
            pv.product_description
        )

        self.log_assert(
            "Verificando se entidade com texto multilinha é válida",
            True,
            pv.is_valid()
        )

    def run_all_tests(self):
        """Executa todos os testes."""
        print(f"{Colors.BOLD}{Colors.HEADER}")
        print("="*80)
        print("🎯 VALIDAÇÃO DIDÁTICA DA PRODUCTVISION ENTITY (TASK-1.2.1)")
        print("="*80)
        print(f"{Colors.ENDC}")

        # Section 1: Creation and Basic Fields
        self.log_section("SEÇÃO 1: Criação e Campos Básicos")
        self.test_creation_with_valid_fields()
        self.test_optional_fields()

        # Section 2: Validation
        self.log_section("SEÇÃO 2: Validação de Campos")
        self.test_validation_with_empty_fields()
        self.test_all_required_fields()
        self.test_validate_method_return_type()

        # Section 3: Special Cases
        self.log_section("SEÇÃO 3: Casos Especiais")
        self.test_special_characters_and_unicode()
        self.test_multiline_strings()

        # Section 4: Modification
        self.log_section("SEÇÃO 4: Modificação de Campos")
        self.test_field_modification()

        # Final Report
        self.print_final_report()

    def print_final_report(self):
        """Imprime relatório final."""
        print(f"\n{Colors.HEADER}{'='*80}")
        print(f"{Colors.BOLD}📊 RELATÓRIO FINAL{Colors.ENDC}")
        print(f"{Colors.HEADER}{'='*80}{Colors.ENDC}")

        success_rate = (self.passed_count / self.test_count * 100) if self.test_count > 0 else 0

        print(f"\n{Colors.BOLD}Estatísticas:{Colors.ENDC}")
        print(f"  • Total de asserts: {Colors.CYAN}{self.test_count}{Colors.ENDC}")
        print(f"  • Passaram: {Colors.GREEN}{self.passed_count}{Colors.ENDC}")
        print(f"  • Falharam: {Colors.RED}{self.failed_count}{Colors.ENDC}")
        print(f"  • Taxa de sucesso: {Colors.YELLOW}{success_rate:.1f}%{Colors.ENDC}")

        if self.failed_count == 0:
            print(f"\n{Colors.GREEN}{Colors.BOLD}✅ TODOS OS TESTES PASSARAM!{Colors.ENDC}")
            print(f"{Colors.GREEN}A entidade ProductVision está implementada corretamente.{Colors.ENDC}")
        else:
            print(f"\n{Colors.RED}{Colors.BOLD}❌ ALGUNS TESTES FALHARAM{Colors.ENDC}")
            print(f"{Colors.RED}Verifique os erros acima para detalhes.{Colors.ENDC}")

        print(f"\n{Colors.CYAN}Implementação validada:")
        print(f"  • Arquivo: tdd_core/domain/entities/product_vision.py")
        print(f"  • Classe: ProductVision")
        print(f"  • Campos obrigatórios: 16")
        print(f"  • Métodos: validate(), is_valid()")
        print(f"  • Timestamps: Auto-inicializados{Colors.ENDC}")

        print(f"\n{Colors.HEADER}{'='*80}{Colors.ENDC}")


def main():
    """Função principal."""
    validator = ProductVisionValidator()

    try:
        validator.run_all_tests()
        sys.exit(0 if validator.failed_count == 0 else 1)
    except Exception as e:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ ERRO DURANTE EXECUÇÃO:{Colors.ENDC}")
        print(f"{Colors.RED}{str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(2)


if __name__ == "__main__":
    main()