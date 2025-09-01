#!/usr/bin/env python3
"""
AGV Context Extractor v5.0
Extrai contexto focado do Blueprint para alvos específicos, reduzindo contexto em 80%.
"""

import os
import sys
from pathlib import Path
from typing import Dict, List


class AGVContextExtractor:
    """Extrator inteligente de contexto para o Método AGV v5.0"""
    
    def __init__(self, blueprint_path: str, order_path: str):
        self.blueprint_path = Path(blueprint_path)
        self.order_path = Path(order_path)
        self.blueprint_content = self._read_file(self.blueprint_path)
        self.order_content = self._read_file(self.order_path)
    
    def _read_file(self, path: Path) -> str:
        """Lê arquivo com encoding UTF-8"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Erro ao ler {path}: {e}")
            return ""
    
    def extract_target_context(self, target_num: int) -> Dict[str, str]:
        """Extrai contexto focado para um alvo específico"""
        
        # 1. Mapear alvo para dependências e módulos
        target_deps = self._map_target_dependencies(target_num)
        
        # 2. Extrair seções relevantes do Blueprint
        relevant_sections = self._extract_blueprint_sections(target_deps)
        
        # 3. Extrair detalhes do alvo da ordem
        target_details = self._extract_target_details(target_num)
        
        # 4. Identificar arquivos de código necessários  
        code_dependencies = self._get_code_dependencies(target_deps)
        
        # 5. Calcular estatísticas de otimização
        original_size = len(self.blueprint_content.split('\n'))
        optimized_size = len(relevant_sections.split('\n'))
        reduction_pct = round((1 - optimized_size/original_size) * 100, 1)
        
        return {
            'target_number': str(target_num),
            'target_details': target_details,
            'blueprint_sections': relevant_sections,
            'code_dependencies': code_dependencies,
            'dependencies': target_deps,
            'optimization_stats': {
                'original_lines': original_size,
                'optimized_lines': optimized_size,
                'reduction_percentage': reduction_pct
            }
        }
    
    def _map_target_dependencies(self, target_num: int) -> Dict[str, List[str]]:
        """Mapeia alvo para seus módulos e dependências"""
        
        # TODO: Este mapeamento deve ser extraído automaticamente da Ordem de Implementação
        # Para projetos específicos, adapte os módulos e modelos conforme seu Blueprint
        target_map = {
            # Core e Multi-tenancy (1-4) - ADAPTE para seus módulos específicos
            1: {'modules': ['projeto.core'], 'models': ['Tenant', 'BaseTenantModel'], 'sections': ['3.1']},
            2: {'modules': ['projeto.core'], 'models': ['Tenant'], 'sections': ['settings.py']},
            3: {'modules': ['projeto.core'], 'models': ['Tenant'], 'sections': ['middleware']},
            4: {'modules': ['projeto.core'], 'models': ['Tenant'], 'sections': ['middleware']},
            
            # Users e Auth (5-8)
            5: {'modules': ['projeto.users', 'projeto.core'], 'models': ['User', 'Tenant'], 'sections': ['3.1', 'auth']},
            6: {'modules': ['projeto.users'], 'models': ['User'], 'sections': ['settings.py']},
            7: {'modules': ['projeto.users'], 'models': ['User'], 'sections': ['auth', 'JWT']},
            8: {'modules': ['projeto.users'], 'models': ['User'], 'sections': ['urls', 'auth']},
            
            # Customers (9-17)
            9: {'modules': ['projeto.customers', 'projeto.core'], 'models': ['Customer', 'BaseTenantModel'], 'sections': ['3.1']},
            10: {'modules': ['projeto.customers'], 'models': ['Customer'], 'sections': ['settings.py']},
            11: {'modules': ['projeto.customers'], 'models': ['Customer'], 'sections': ['factories', 'tests']},
            12: {'modules': ['projeto.customers'], 'models': ['Customer'], 'sections': ['3.1.1', 'DTOs']},
            13: {'modules': ['projeto.customers'], 'models': ['Customer'], 'sections': ['views', 'CRUD']},
            14: {'modules': ['projeto.customers'], 'models': ['Customer'], 'sections': ['urls']},
            15: {'modules': ['projeto.customers'], 'models': ['Customer'], 'sections': ['urls']},
            16: {'modules': ['DRF'], 'models': [], 'sections': ['18']},
            17: {'modules': ['DRF'], 'models': [], 'sections': ['18']},
            
            # Operations (18-26)
            18: {'modules': ['projeto.operations', 'projeto.customers'], 'models': ['Loan', 'Installment', 'Consultant'], 'sections': ['3.1']},
            19: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['settings.py']},
            20: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['factories', 'tests']},
            21: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['5', 'repositories']},
            22: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['5', 'services']},
            23: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['3.1.1', 'DTOs']},
            24: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['views']},
            25: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['urls']},
            26: {'modules': ['projeto.operations'], 'models': ['Loan'], 'sections': ['urls']},
            
            # Finance (27-31)
            27: {'modules': ['projeto.finance'], 'models': ['BankAccount', 'FinancialTransaction'], 'sections': ['3.1']},
            28: {'modules': ['projeto.finance'], 'models': ['BankAccount'], 'sections': ['settings.py']},
            29: {'modules': ['projeto.finance'], 'models': ['BankAccount'], 'sections': ['factories']},
            30: {'modules': ['projeto.finance'], 'models': ['BankAccount'], 'sections': ['CRUD']},
            31: {'modules': ['projeto.finance', 'projeto.operations'], 'models': ['FinancialTransaction', 'Loan'], 'sections': ['5', 'integration']},
            
            # Observability (32-35)
            32: {'modules': ['projeto.core'], 'models': [], 'sections': ['seed_data', 'factories']},
            33: {'modules': ['observability'], 'models': [], 'sections': ['14']},
            34: {'modules': ['observability'], 'models': [], 'sections': ['14', 'metrics']},
            35: {'modules': ['observability'], 'models': [], 'sections': ['14', 'health']},
            
            # Frontend (36-43)
            36: {'modules': ['frontend'], 'models': [], 'sections': ['4']},
            37: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'shared/ui']},
            38: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'shared/api']},
            39: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'entities']},
            40: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'features/auth']},
            41: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'features/customers']},
            42: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'features/loans']},
            43: {'modules': ['frontend'], 'models': [], 'sections': ['4', 'app/pages']},
        }
        
        return target_map.get(target_num, {'modules': [], 'models': [], 'sections': []})
    
    def _extract_blueprint_sections(self, target_deps: Dict) -> str:
        """Extrai apenas seções relevantes do Blueprint"""
        relevant_sections = []
        
        # Sempre incluir visão geral da arquitetura
        sections = self.blueprint_content.split('\n## ')
        relevant_sections.append(sections[0])  # Título e seção 1
        
        # Extrair seções específicas baseadas nas dependências
        for section_num in target_deps.get('sections', []):
            for section in sections[1:]:  # Pular primeira seção já incluída
                if section.startswith(section_num):
                    relevant_sections.append('## ' + section)
                elif section_num in section.lower():
                    relevant_sections.append('## ' + section)
        
        # Sempre incluir modelos relacionados
        if target_deps.get('models'):
            for section in sections[1:]:
                if 'modelos' in section.lower() or 'models' in section.lower():
                    # Extrair apenas modelos relevantes
                    model_section = self._extract_relevant_models(section, target_deps['models'])
                    if model_section:
                        relevant_sections.append('## ' + model_section)
        
        return '\n\n'.join(relevant_sections)
    
    def _extract_relevant_models(self, section: str, relevant_models: List[str]) -> str:
        """Extrai apenas modelos relevantes de uma seção"""
        lines = section.split('\n')
        relevant_lines = [lines[0]]  # Título da seção
        
        current_model = None
        include_lines = False
        
        for line in lines[1:]:
            # Detectar início de definição de modelo
            for model in relevant_models:
                if f'class {model}' in line:
                    current_model = model
                    include_lines = True
                    break
            
            # Incluir linhas se estivermos em um modelo relevante
            if include_lines:
                relevant_lines.append(line)
                
                # Parar quando chegar ao próximo modelo ou seção
                if line.startswith('class ') and current_model not in line:
                    include_lines = False
                elif line.startswith('# ') or line.startswith('## '):
                    include_lines = False
        
        return '\n'.join(relevant_lines) if len(relevant_lines) > 1 else ''
    
    def _extract_target_details(self, target_num: int) -> str:
        """Extrai detalhes específicos do alvo da ordem de implementação"""
        lines = self.order_content.split('\n')
        target_details = []
        
        # Encontrar linha do alvo
        target_found = False
        for i, line in enumerate(lines):
            if f'**Alvo {target_num}:**' in line:
                target_found = True
                target_details.append(line)
                
                # Incluir linhas seguintes até próximo alvo ou seção
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]
                    if '**Alvo ' in next_line or '>>>' in next_line:
                        break
                    target_details.append(next_line)
                break
        
        return '\n'.join(target_details) if target_found else f"Detalhes do Alvo {target_num} não encontrados"
    
    def _get_code_dependencies(self, target_deps: Dict) -> str:
        """Identifica arquivos de código que devem ser incluídos no contexto"""
        dependencies = []
        
        # Mapear módulos para possíveis arquivos de código
        for module in target_deps.get('modules', []):
            if 'projeto' in module:
                app_name = module.split('.')[-1]
                dependencies.append(f"- {app_name}/models.py (se existir)")
                dependencies.append(f"- {app_name}/serializers.py (se existir)")
                dependencies.append(f"- {app_name}/views.py (se existir)")
                dependencies.append(f"- {app_name}/tests/ (arquivos relevantes)")
            elif module == 'frontend':
                dependencies.append("- Estrutura de diretórios do frontend")
                dependencies.append("- Componentes e hooks relevantes")
            elif module == 'DRF':
                dependencies.append("- Configurações do Framework de API REST")
                dependencies.append("- Exception handlers customizados")
        
        return '\n'.join(dependencies) if dependencies else "Nenhuma dependência de código específica"


def main():
    """Função principal para execução via linha de comando"""
    target = os.getenv('TARGET')
    blueprint_path = os.getenv('BLUEPRINT_PATH', 'BLUEPRINT_ARQUITETURAL.md')
    order_path = os.getenv('ORDER_PATH', 'ORDEM_IMPLEMENTACAO.md')
    
    # Permitir TARGET via argumento da linha de comando
    if not target and len(sys.argv) > 1:
        target = sys.argv[1]
    
    if not target:
        print("Erro: Variável TARGET não definida")
        print("Uso: python agv_context_extractor.py <target_number>")
        sys.exit(1)
    
    try:
        target_num = int(target)
    except ValueError:
        print(f"Erro: TARGET deve ser um número. Recebido: {target}")
        sys.exit(1)
    
    extractor = AGVContextExtractor(blueprint_path, order_path)
    context = extractor.extract_target_context(target_num)
    
    # Salvar contexto otimizado em arquivo temporário
    output_file = f"agv_context_target_{target_num}.md"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"# CONTEXTO FOCADO - ALVO {target_num}\n\n")
        f.write(f"## Detalhes do Alvo\n{context['target_details']}\n\n")
        f.write(f"## Seções Relevantes do Blueprint\n{context['blueprint_sections']}\n\n")
        f.write(f"## Dependências de Código\n{context['code_dependencies']}\n\n")
        f.write("## Estatísticas de Otimização\n")
        f.write(f"- Contexto original: {context['optimization_stats']['original_lines']} linhas\n")
        f.write(f"- Contexto otimizado: {context['optimization_stats']['optimized_lines']} linhas\n")
        f.write(f"- Redução: {context['optimization_stats']['reduction_percentage']}%\n")
    
    print(f"Contexto focado extraído para Alvo {target_num}")
    print(f"Arquivo salvo: {output_file}")
    print(f"Redução de contexto: {context['optimization_stats']['reduction_percentage']}%")


if __name__ == '__main__':
    main()