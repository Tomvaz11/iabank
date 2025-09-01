#!/usr/bin/env python3
"""
AGV Focused Context Injector v5.0
Injeta contexto focado no prompt antes da execução de subagents.
"""

import os
import sys
from pathlib import Path


def inject_context_to_prompt():
    """Injeta contexto focado no prompt baseado no alvo especificado"""
    
    target = os.getenv('TARGET')
    if not target:
        print("Contexto não injetado - TARGET não especificado")
        return
    
    # Procurar arquivo de contexto gerado
    context_file = f"agv_context_target_{target}.md"
    
    if not Path(context_file).exists():
        print(f"Arquivo de contexto não encontrado: {context_file}")
        return
    
    # Ler contexto focado
    try:
        with open(context_file, 'r', encoding='utf-8') as f:
            focused_context = f.read()
    except Exception as e:
        print(f"Erro ao ler contexto: {e}")
        return
    
    # Criar prompt otimizado
    optimized_prompt = f"""
# CONTEXTO AGV OTIMIZADO AUTOMATICAMENTE INJETADO

{focused_context}

---

# INSTRUÇÕES PARA O SUBAGENT

Você recebeu contexto OTIMIZADO e FOCADO para implementar este alvo específico.

**IMPORTANTE:**
- Este contexto foi reduzido de 1000+ linhas para apenas as seções relevantes
- Todas as informações necessárias estão presentes
- Implemente APENAS o que está especificado para este alvo
- Siga rigorosamente as diretrizes do Blueprint fornecido

**VALIDAÇÕES OBRIGATÓRIAS:**
1. Gere testes unitários para TODO código de produção
2. Mantenha conformidade com arquitetura em camadas
3. Garanta isolamento multi-tenant em todos os dados
4. Documente todo código com docstrings apropriadas

Proceda com a implementação focada usando este contexto otimizado.

---

"""
    
    # Salvar prompt otimizado
    output_file = f"agv_optimized_prompt_target_{target}.md"
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(optimized_prompt)
        
        print("Contexto focado injetado com sucesso")
        print(f"Prompt otimizado salvo em: {output_file}")
        
        # Exibir estatísticas
        lines = focused_context.count('\n')
        print(f"Contexto injetado: ~{lines} linhas (vs 1000+ original)")
        
    except Exception as e:
        print(f"Erro ao salvar prompt otimizado: {e}")


def validate_context_injection():
    """Valida se a injeção de contexto foi bem-sucedida"""
    
    target = os.getenv('TARGET')
    if not target:
        return False
    
    context_file = f"agv_context_target_{target}.md"
    prompt_file = f"agv_optimized_prompt_target_{target}.md"
    
    # Verificar se arquivos existem
    if not Path(context_file).exists():
        print(f"❌ Arquivo de contexto não encontrado: {context_file}")
        return False
    
    if not Path(prompt_file).exists():
        print(f"❌ Prompt otimizado não encontrado: {prompt_file}")
        return False
    
    # Verificar tamanho dos arquivos
    try:
        context_size = Path(context_file).stat().st_size
        prompt_size = Path(prompt_file).stat().st_size
        
        if context_size == 0 or prompt_size == 0:
            print("❌ Arquivos de contexto estão vazios")
            return False
        
        print("✅ Contexto injetado com sucesso")
        print(f"   - Contexto: {context_size} bytes")
        print(f"   - Prompt: {prompt_size} bytes")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao validar injeção: {e}")
        return False


def cleanup_context_files():
    """Remove arquivos temporários de contexto"""
    
    # Encontrar todos os arquivos de contexto AGV
    context_pattern = "agv_context_target_*.md"
    prompt_pattern = "agv_optimized_prompt_target_*.md"
    
    removed_files = []
    
    for pattern in [context_pattern, prompt_pattern]:
        for file_path in Path('.').glob(pattern):
            try:
                file_path.unlink()
                removed_files.append(str(file_path))
            except Exception as e:
                print(f"Erro ao remover {file_path}: {e}")
    
    if removed_files:
        print(f"[CLEAN] Arquivos temporários removidos: {len(removed_files)}")
        for file in removed_files:
            print(f"   - {file}")
    else:
        print("[CLEAN] Nenhum arquivo temporário encontrado")


def main():
    """Função principal"""
    
    # Verificar modo de operação
    mode = os.getenv('INJECTION_MODE', 'inject')
    
    # Permitir modo via argumento
    if len(sys.argv) > 1:
        mode = sys.argv[1]
    
    if mode == 'inject':
        inject_context_to_prompt()
    elif mode == 'validate':
        success = validate_context_injection()
        sys.exit(0 if success else 1)
    elif mode == 'cleanup':
        cleanup_context_files()
    else:
        print(f"Modo desconhecido: {mode}")
        print("Modos disponíveis: inject, validate, cleanup")
        sys.exit(1)


if __name__ == '__main__':
    main()