#!/usr/bin/env python3
"""
Teste isolado para a extração de geometria IFC
"""

import os
import sys
import json
from pathlib import Path

# Adicionar o diretório do projeto ao path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_geometry_extraction_isolated():
    """Testa a extração de geometria IFC de forma isolada"""
    print("=== Teste Isolado de Extração de Geometria IFC ===")
    
    try:
        import ifcopenshell
        import ifcopenshell.geom
        
        # Verificar se existe algum arquivo IFC de teste
        uploads_dir = project_root / "uploads"
        ifc_files = list(uploads_dir.glob("*.ifc"))
        
        if not ifc_files:
            print("❌ Nenhum arquivo IFC encontrado na pasta uploads para teste")
            return False
        
        test_file = ifc_files[0]
        print(f"📁 Testando com arquivo: {test_file.name}")
        
        # Implementação da função de extração (copiada do routes_enhanced.py)
        def extract_ifc_geometry(ifc_file_path):
            try:
                model = ifcopenshell.open(ifc_file_path)
                settings = ifcopenshell.geom.settings()
                settings.set(settings.USE_WORLD_COORDS, True)
                settings.set(settings.WELD_VERTICES, True)
                
                elements_data = []
                
                # Processar todos os produtos IFC que têm representação geométrica
                for element in model.by_type("IfcProduct"):
                    if element.Representation:
                        try:
                            # Criar a forma geométrica
                            shape = ifcopenshell.geom.create_shape(settings, element)
                            geometry = shape.geometry
                            
                            # Extrair vértices e faces
                            verts = list(geometry.verts)
                            faces = list(geometry.faces)
                            
                            # Reorganizar vértices em grupos de 3 (x, y, z)
                            vertices = []
                            for i in range(0, len(verts), 3):
                                vertices.extend([verts[i], verts[i+1], verts[i+2]])
                            
                            # Reorganizar faces em grupos de 3 (triângulos)
                            indices = []
                            for i in range(0, len(faces), 3):
                                indices.extend([faces[i], faces[i+1], faces[i+2]])
                            
                            # Obter informações do elemento
                            element_data = {
                                \'globalId\': element.GlobalId,
                                \'type\': element.is_a(),
                                \'name\': element.Name or \'\',
                                \'description\': getattr(element, \'Description\', \'\') or \'\',
                                \'vertices\': vertices,
                                \'indices\': indices,
                                \'material\': None
                            }
                            
                            # Tentar obter informações de material se disponível
                            try:
                                if hasattr(element, \'HasAssociations\'):
                                    for association in element.HasAssociations:
                                        if association.is_a(\'IfcRelAssociatesMaterial\'):
                                            material = association.RelatingMaterial
                                            if hasattr(material, \'Name\'):
                                                element_data[\'material\'] = material.Name
                                            break
                            except:
                                pass
                            
                            elements_data.append(element_data)
                            
                        except Exception as e:
                            print(f"⚠️  Erro ao processar elemento {element.GlobalId}: {e}")
                            continue
                
                print(f"✅ Processados {len(elements_data)} elementos com geometria")
                return elements_data
                
            except Exception as e:
                print(f"❌ Erro ao extrair geometria IFC: {e}")
                return []
        
        # Extrair geometria
        elements_data = extract_ifc_geometry(str(test_file))
        
        if not elements_data:
            print("❌ Nenhum elemento de geometria extraído")
            return False
        
        print(f"✅ {len(elements_data)} elementos extraídos com sucesso")
        
        # Verificar estrutura dos dados
        first_element = elements_data[0]
        required_fields = [\'globalId\', \'type\', \'vertices\', \'indices\']
        
        for field in required_fields:
            if field not in first_element:
                print(f"❌ Campo obrigatório \'{field}\' não encontrado")
                return False
        
        print("✅ Estrutura de dados validada")
        
        # Verificar se há dados de geometria válidos
        valid_elements = [e for e in elements_data if e[\'vertices\'] and e[\'indices\']]
        print(f"✅ {len(valid_elements)} elementos com geometria válida")
        
        # Estatísticas dos tipos de elementos
        element_types = {}
        for element in elements_data:
            elem_type = element[\'type\']
            element_types[elem_type] = element_types.get(elem_type, 0) + 1
        
        print("\n📊 Tipos de elementos encontrados:")
        for elem_type, count in sorted(element_types.items()):
            print(f"  - {elem_type}: {count}")
        
        # Salvar dados de exemplo para debug
        sample_data = {
            \'total_elements\': len(elements_data),
            \'valid_elements\': len(valid_elements),
            \'element_types\': element_types,
            \'sample_element\': {
                \'globalId\': first_element[\'globalId\'],
                \'type\': first_element[\'type\'],
                \'name\': first_element[\'name\'],
                \'vertices_count\': len(first_element[\'vertices\']),
                \'indices_count\': len(first_element[\'indices\'])
            }
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

if __name__ == "__main__":
    success = test_geometry_extraction_isolated()
    if success:
        print("\n🎉 Teste de extração de geometria passou!")
    else:
        print("\n❌ Teste de extração de geometria falhou!")
    sys.exit(0 if success else 1)

