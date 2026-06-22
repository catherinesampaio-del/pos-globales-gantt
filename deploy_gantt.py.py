#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════════════════════════
DEPLOY AUTOMÁTICO - GANTT CHART GITHUB PAGES
═══════════════════════════════════════════════════════════════════════════════
"""

import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ═══════════════════════════════════════════════════════════════════════════
# CONFIGURAÇÕES
# ═══════════════════════════════════════════════════════════════════════════

GITHUB_USERNAME = "SEU_USUARIO"  # ← EDITE AQUI
REPO_NAME = "pos-globales-gantt"
BRANCH = "main"

# ═══════════════════════════════════════════════════════════════════════════

class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text):
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")

def run_command(cmd, show_output=False):
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            check=True,
            capture_output=not show_output,
            text=True
        )
        return True, result.stdout if not show_output else ""
    except subprocess.CalledProcessError as e:
        return False, e.stderr if not show_output else ""

def check_git_installed():
    success, _ = run_command("git --version")
    if not success:
        print_error("Git não está instalado!")
        print_info("Instale: https://git-scm.com/downloads")
        return False
    return True

def check_python_packages():
    try:
        import plotly
        import pandas
        print_success("Pacotes Python OK (plotly, pandas)")
        return True
    except ImportError as e:
        print_error(f"Pacote faltando: {e.name}")
        print_info("Execute: pip install plotly pandas")
        return False

def generate_gantt():
    print_info("Gerando HTML do Gantt Chart...")
    
    try:
        # Importar e executar o gantt_manager
        import gantt_manager
        result = gantt_manager.generate_gantt()
        
        if result.get('sucesso'):
            print_success("HTML gerado com sucesso!")
            return True
        else:
            print_error(f"Erro ao gerar Gantt: {result.get('erro')}")
            return False
    except FileNotFoundError:
        print_error("gantt_manager.py não encontrado!")
        return False
    except Exception as e:
        print_error(f"Erro: {e}")
        return False

def git_status():
    success, output = run_command("git status --short")
    if success and output.strip():
        print_info("Arquivos modificados:")
        for line in output.strip().split('\n'):
            print(f"   {line}")
        return True
    return False

def git_commit_push():
    print_info("Adicionando arquivos...")
    success, _ = run_command("git add .")
    if not success:
        print_error("Falha ao adicionar arquivos")
        return False
    
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    commit_msg = f"🚀 Atualização Gantt - {timestamp}"
    
    print_info(f"Commit: {commit_msg}")
    success, output = run_command(f'git commit -m "{commit_msg}"')
    if not success:
        if "nothing to commit" in output:
            print_info("Nenhuma alteração para commit")
            return True
        print_error("Falha no commit")
        return False
    
    print_info("Enviando para GitHub...")
    success, _ = run_command(f"git push origin {BRANCH}", show_output=True)
    if not success:
        print_error("Falha no push")
        return False
    
    print_success("Push concluído!")
    return True

def show_url():
    url = f"https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/"
    print(f"\n{Colors.BOLD}🌐 SEU GANTT CHART:{Colors.END}")
    print(f"   {Colors.GREEN}{url}{Colors.END}")
    print(f"\n{Colors.YELLOW}⏳ Aguarde 1-2 minutos para atualização{Colors.END}\n")

def setup_mode():
    print_header("CONFIGURAÇÃO INICIAL - GITHUB PAGES")
    
    print("Siga estes passos:\n")
    
    print(f"{Colors.BOLD}1. Criar repositório no GitHub:{Colors.END}")
    print(f"   https://github.com/new")
    print(f"   Nome: {REPO_NAME}")
    print(f"   ✓ Public")
    print(f"   ✓ Add README\n")
    
    print(f"{Colors.BOLD}2. Clonar repositório:{Colors.END}")
    print(f"   git clone https://github.com/{GITHUB_USERNAME}/{REPO_NAME}.git")
    print(f"   cd {REPO_NAME}\n")
    
    print(f"{Colors.BOLD}3. Copiar arquivos:{Colors.END}")
    print(f"   • gantt_manager.py")
    print(f"   • gantt_data.json")
    print(f"   • index.html (renomeie gantt_globales_v2_moderno.html)")
    print(f"   • deploy_gantt.py")
    print(f"   • README.md\n")
    
    print(f"{Colors.BOLD}4. Primeiro commit:{Colors.END}")
    print(f"   git add .")
    print(f'   git commit -m "Setup inicial"')
    print(f"   git push origin {BRANCH}\n")
    
    print(f"{Colors.BOLD}5. Ativar GitHub Pages:{Colors.END}")
    print(f"   Settings → Pages → Source: {BRANCH} / (root) → Save\n")
    
    print(f"{Colors.BOLD}6. Acessar:{Colors.END}")
    print(f"   https://{GITHUB_USERNAME}.github.io/{REPO_NAME}/\n")

def deploy_mode():
    print_header("DEPLOY GANTT CHART")
    
    # Verificações
    if not check_git_installed():
        return 1
    
    if not check_python_packages():
        return 1
    
    # Gerar HTML
    if not generate_gantt():
        return 1
    
    # Verificar mudanças
    if not git_status():
        print_info("Nenhuma alteração detectada")
        return 0
    
    # Commit e Push
    if not git_commit_push():
        return 1
    
    # Mostrar URL
    show_url()
    print_success("DEPLOY CONCLUÍDO!")
    
    return 0

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--setup":
        setup_mode()
    else:
        exit_code = deploy_mode()
        sys.exit(exit_code)

if __name__ == "__main__":
    main()
