#!/usr/bin/env python3
"""
Script de teste para a solução aprimorada do visualizador 3D IFC
Testa o processamento de geometria no backend e a integração com o frontend
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configurar o ambiente Flask
os.environ["FLASK_APP"] = "run.py"
os.environ["FLASK_ENV"] = "development"

def test_geometry_extraction():
    """Testa a extração de geometria IFC"""
    print("=== Teste de Extração de Geometria IFC ===")
    
    try:
        # Importar a função de extração
        from app.routes_enhanced import extract_ifc_geometry
        
        # Verificar se existe algum arquivo IFC de teste
        uploads_dir = project_root / "uploads"
        ifc_files = list(uploads_dir.glob("*.ifc"))
        
        if not ifc_files:
            print("❌ Nenhum arquivo IFC encontrado na pasta uploads para teste")
            return False
        
        test_file = ifc_files[0]
        print(f"📁 Testando com arquivo: {test_file.name}")
        
        # Extrair geometria
        elements_data = extract_ifc_geometry(str(test_file))
        
        if not elements_data:
            print("❌ Nenhum elemento de geometria extraído")
            return False
        
        print(f"✅ {len(elements_data)} elementos extraídos com sucesso")
        
        # Verificar estrutura dos dados
        first_element = elements_data[0]
        required_fields = ["globalId", "type", "vertices", "indices"]
        
        for field in required_fields:
            if field not in first_element:
                print(f"❌ Campo obrigatório \'{field}\' não encontrado")
                return False
        
        print("✅ Estrutura de dados validada")
        
        # Verificar se há dados de geometria válidos
        valid_elements = [e for e in elements_data if e["vertices"] and e["indices"]]
        print(f"✅ {len(valid_elements)} elementos com geometria válida")
        
        # Salvar dados de exemplo para debug
        sample_data = {
            "total_elements": len(elements_data),
            "valid_elements": len(valid_elements),
            "sample_element": first_element,
            "element_types": list(set(e["type"] for e in elements_data))
        }
        
        with open(project_root / "geometry_test_output.json", "w") as f:
            json.dump(sample_data, f, indent=2)
        
        print("✅ Dados de exemplo salvos em geometry_test_output.json")
        return True
        
    except Exception as e:
        print(f"❌ Erro durante teste: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_backend_integration():
    """Testa a integração do backend"""
    print("\n=== Teste de Integração do Backend ===")
    
    try:
        # Importar e configurar a aplicação Flask
        from app import app
        from config import Config
        
        # Configurar para teste
        app.config["TESTING"] = True
        app.config["UPLOAD_FOLDER"] = str(project_root / "uploads")
        
        with app.test_client() as client:
            # Testar rota principal
            response = client.get("/")
            if response.status_code != 200:
                print(f"❌ Rota principal falhou: {response.status_code}")
                return False
            
            print("✅ Rota principal funcionando")
            
            # Verificar se existe arquivo IFC para teste
            uploads_dir = Path(app.config["UPLOAD_FOLDER"])
            ifc_files = list(uploads_dir.glob("*.ifc"))
            
            if ifc_files:
                print(f"✅ {len(ifc_files)} arquivo(s) IFC disponível(is) para teste")
            else:
                print("⚠️  Nenhum arquivo IFC disponível para teste completo")
            
            return True
            
    except Exception as e:
        print(f"❌ Erro na integração do backend: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_files():
    """Testa se os arquivos do frontend estão corretos"""
    print("\n=== Teste dos Arquivos Frontend ===")
    
    try:
        # Verificar arquivos essenciais
        essential_files = [
            "app/templates/index_enhanced.html",
            "app/static/js/main_enhanced.js",
            "app/static/js/graph.js",
            "app/static/css/style.css"
        ]
        
        for file_path in essential_files:
            full_path = project_root / file_path
            if not full_path.exists():
                print(f"❌ Arquivo essencial não encontrado: {file_path}")
                return False
            print(f"✅ {file_path}")
        
        # Verificar se o main_enhanced.js contém as funções necessárias
        main_js_path = project_root / "app/static/js/main_enhanced.js"
        with open(main_js_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        required_functions = [
            "loadProcessedIFCModel",
            "highlightValidationErrors",
            "setupThreeJs"
        ]
        
        for func in required_functions:
            if func not in content:
                print(f"❌ Função necessária não encontrada: {func}")
                return False
        
        print("✅ Todas as funções necessárias encontradas no frontend")
        return True
        
    except Exception as e:
        print(f"❌ Erro ao verificar arquivos frontend: {e}")
        return False

def create_backup():
    """Cria backup dos arquivos originais"""
    print("\n=== Criando Backup dos Arquivos Originais ===")
    
    try:
        backup_dir = project_root / "backup_original"
        backup_dir.mkdir(exist_ok=True)
        
        files_to_backup = [
            "app/routes.py",
            "app/templates/index.html",
            "app/static/js/main.js"
        ]
        
        for file_path in files_to_backup:
            src = project_root / file_path
            if src.exists():
                dst = backup_dir / Path(file_path).name
                shutil.copy2(src, dst)
                print(f"✅ Backup criado: {dst}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erro ao criar backup: {e}")
        return False

def main():
    """Função principal de teste"""
    print("🚀 Iniciando testes da solução aprimorada do visualizador 3D IFC")
    print("=" * 60)
    
    # Criar backup
    if not create_backup():
        print("⚠️  Falha ao criar backup, continuando mesmo assim...")
    
    # Executar testes
    tests = [
        ("Arquivos Frontend", test_frontend_files),
        ("Integração Backend", test_backend_integration),
        ("Extração de Geometria", test_geometry_extraction)
    ]
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n🔍 Executando: {test_name}")
        results[test_name] = test_func()
    
    # Resumo dos resultados
    print("\n" + "=" * 60)
    print("📊 RESUMO DOS TESTES")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASSOU" if result else "❌ FALHOU"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! A solução está pronta para uso.")
        print("\nPróximos passos:")
        print("1. Substitua app/routes.py por app/routes_enhanced.py")
        print("2. Substitua app/templates/index.html por app/templates/index_enhanced.html")
        print("3. Substitua app/static/js/main.js por app/static/js/main_enhanced.js")
        print("4. Reinicie o servidor Flask")
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

