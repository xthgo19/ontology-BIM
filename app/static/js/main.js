import { drawGraph, resetGraph } from './graph.js';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

document.addEventListener('DOMContentLoaded', () => {
    // Seletores de Elementos DOM
    const uploadForm = document.getElementById('upload-form');
    const validateBtn = document.getElementById('validate-btn');
    const statusArea = document.getElementById('status-area');
    const reportContent = document.getElementById('report-content');
    const mainContent = document.getElementById('main-content');
    const chatWindow = document.getElementById('chat-window');
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');
    const resetBtn = document.getElementById('reset-btn');
    const fullGraphBtn = document.getElementById('full-graph-btn');
    const relationSelect = document.getElementById('relation-select');
    const objectSelect = document.getElementById('object-select');
    const generateQueryBtn = document.getElementById('generate-query-btn');
    const viewerContainer = document.getElementById('viewer-container');

    // Estado da Aplicação
    let conflictMessages = {};
    let scene, camera, renderer, controls;
    let guidToMeshMap = new Map();
    let ifcModel = null;

    const setupThreeJs = () => {
        if (renderer) { 
            renderer.domElement.remove(); 
            renderer.dispose(); 
        }
        
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x222222);
        
        camera = new THREE.PerspectiveCamera(75, viewerContainer.clientWidth / viewerContainer.clientHeight || 1, 0.1, 1000);
        camera.position.set(15, 15, 15);
        
        // Iluminação
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
        directionalLight.position.set(0, 10, 5);
        scene.add(directionalLight);
        
        // Grid helper
        const gridHelper = new THREE.GridHelper(100, 100, 0x555555, 0x333333);
        scene.add(gridHelper);
        
        // Renderer
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
        viewerContainer.appendChild(renderer.domElement);
        
        // Controles
        controls = new OrbitControls(camera, renderer.domElement);
        
        // Loop de animação
        const animate = () => { 
            requestAnimationFrame(animate); 
            controls.update(); 
            renderer.render(scene, camera); 
        };
        animate();
    };

    const loadProcessedIFCModel = (elements3dData) => {
        // Remover modelo anterior se existir
        if (ifcModel) {
            scene.remove(ifcModel);
            ifcModel = null;
        }
        
        // Limpar mapeamento anterior
        guidToMeshMap.clear();
        
        const group = new THREE.Group(); // Para agrupar todos os meshes do modelo
        
        // Materiais
        const defaultMaterial = new THREE.MeshLambertMaterial({ color: 0xcccccc });
        const wallMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x8090a0, 
            transparent: true, 
            opacity: 0.7 
        });

        let processedCount = 0;
        
        elements3dData.forEach(elementData => {
            try {
                // Criar geometria
                const geometry = new THREE.BufferGeometry();
                
                // Verificar se temos dados de geometria válidos
                if (!elementData.vertices || !elementData.indices || 
                    elementData.vertices.length === 0 || elementData.indices.length === 0) {
                    console.warn(`Elemento ${elementData.globalId} não tem geometria válida`);
                    return;
                }
                
                // Configurar vértices
                geometry.setAttribute('position', new THREE.Float32BufferAttribute(elementData.vertices, 3));
                
                // Configurar índices
                geometry.setIndex(new THREE.Uint32BufferAttribute(elementData.indices, 1));
                
                // Calcular normais para iluminação
                geometry.computeVertexNormals();
                
                // Escolher material baseado no tipo
                let material = defaultMaterial;
                if (elementData.type === 'IfcWall' || elementData.type === 'IfcWallStandardCase') {
                    material = wallMaterial;
                }
                
                // Criar mesh
                const mesh = new THREE.Mesh(geometry, material);
                
                // Armazenar metadados
                mesh.userData.globalId = elementData.globalId;
                mesh.userData.type = elementData.type;
                mesh.userData.name = elementData.name;
                mesh.userData.description = elementData.description;
                mesh.userData.material = elementData.material;
                
                // Adicionar ao grupo
                group.add(mesh);
                
                // Mapear GlobalId para mesh
                guidToMeshMap.set(elementData.globalId, mesh);
                
                processedCount++;
                
            } catch (error) {
                console.error(`Erro ao processar elemento ${elementData.globalId}:`, error);
            }
        });

        if (processedCount === 0) {
            addChatMessage('Nenhum elemento 3D foi processado com sucesso.', 'bot');
            return;
        }

        ifcModel = group;
        scene.add(ifcModel);

        // Ajustar câmera para o novo modelo
        const box = new THREE.Box3().setFromObject(ifcModel);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());
        
        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / 2 / Math.tan(fov / 2));
        cameraZ *= 1.5; // Afastar um pouco mais
        
        camera.position.set(center.x + cameraZ, center.y + cameraZ, center.z + cameraZ);
        camera.lookAt(center);
        controls.target.copy(center);
        controls.update();

        addChatMessage(`Modelo 3D carregado com sucesso! ${processedCount} elementos processados.`, 'bot');
        
        // Atualizar tamanho do renderer
        renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
        camera.aspect = viewerContainer.clientWidth / viewerContainer.clientHeight;
        camera.updateProjectionMatrix();
    };

    const highlightValidationErrors = (validationResults) => {
        if (!validationResults || validationResults.length === 0) return;
        
        const highlightMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
        let highlightedCount = 0;
        
        validationResults.forEach(result => {
            if (result.type === 'CONFLITO' && result.element) {
                // Remover prefixo 'ifc:' se presente
                const guid = result.element.replace('ifc:', '');
                const mesh = guidToMeshMap.get(guid);
                
                if (mesh) {
                    // Armazenar material original se ainda não foi armazenado
                    if (!mesh.userData.originalMaterial) {
                        mesh.userData.originalMaterial = mesh.material;
                    }
                    
                    // Aplicar material de destaque
                    mesh.material = highlightMaterial;
                    highlightedCount++;
                    
                    console.log(`Destacado elemento com erro: ${guid}`);
                } else {
                    console.warn(`Elemento não encontrado para destaque: ${guid}`);
                }
            }
        });
        
        if (highlightedCount > 0) {
            addChatMessage(`Foram destacados ${highlightedCount} elementos com conflitos em vermelho.`, 'bot');
        }
    };

    uploadForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const formData = new FormData(uploadForm);
        showStatus('A validar e a processar o modelo...', false, true);
        validateBtn.disabled = true;
        mainContent.classList.add('hidden');
        conflictMessages = {};
        guidToMeshMap.clear();

        try {
            setupThreeJs();
            addChatMessage('A validar e a processar o modelo...', 'bot');
            
            const response = await fetch('/validate', { method: 'POST', body: formData });
            if (!response.ok) throw new Error(`Erro do servidor: ${response.status}`);
            
            const data = await response.json();
            if (data.error) throw new Error(data.error);

            console.log('Dados recebidos do backend:', data);

            // Verificar se temos dados de geometria 3D
            if (data.elements_3d_data && data.elements_3d_data.length > 0) {
                addChatMessage(`Processamento concluído. Carregando ${data.elements_3d_data.length} elementos 3D...`, 'bot');
                
                // Carregar modelo usando dados processados pelo backend
                loadProcessedIFCModel(data.elements_3d_data);
                
                // Processar conflitos para destaque
                if (data.validation) {
                    data.validation.forEach(item => {
                        if (item.type === 'CONFLITO' && item.element) {
                            conflictMessages[item.element] = item.message;
                        }
                    });
                    
                    // Destacar elementos com erros
                    highlightValidationErrors(data.validation);
                }
                
            } else {
                addChatMessage('Nenhum dado de geometria 3D foi recebido do backend.', 'bot');
            }

            showStatus('Validação e carregamento concluídos!', false);
            renderReport(data.validation);
            mainContent.classList.remove('hidden');
            
            loadFullGraph();
            populateOntologyExplorer();

        } catch (error) {
            showStatus(`Erro: ${error.message}`, true);
            console.error(error);
            addChatMessage(`Falha crítica: ${error.message}. Verifique o console.`, 'bot');
        } finally {
            validateBtn.disabled = false;
        }
    });

    const addChatMessage = (message, sender) => {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message p-3 rounded-lg max-w-2xl break-words shadow-sm ${sender === 'user' ? 'bg-indigo-500 text-white self-end ml-auto' : 'bg-gray-200 text-gray-800 self-start mr-auto'}`;
        messageDiv.innerHTML = message.replace(/\n/g, '<br>');
        chatWindow.appendChild(messageDiv);
        chatWindow.scrollTop = chatWindow.scrollHeight;
    };
    
    const sendMessage = async () => {
        const message = userInput.value.trim();
        if (!message) return;
        addChatMessage(message, 'user');
        userInput.value = '';
        try {
            const response = await fetch('/ask', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ question: message }) });
            const data = await response.json();
            addChatMessage(data.answer, 'bot');
            if (data.object) {
                const graphResponse = await fetch(`/graph-data?object=${encodeURIComponent(data.object)}`);
                const graphData = await graphResponse.json();
                drawGraph(graphData, conflictMessages, addChatMessage);
            }
        } catch (error) {
            addChatMessage('Ocorreu um erro ao comunicar com o servidor.', 'bot');
        }
    };
    
    const showStatus = (message, isError = false, isLoading = false) => {
        let content = '';
        if (isLoading) {
            content = `<div class="flex justify-center items-center"><div class="spinner mr-3"></div><p>${message}</p></div>`;
        } else {
            content = `<p class="${isError ? 'text-red-600' : 'text-green-600'} font-semibold">${message}</p>`;
        }
        statusArea.innerHTML = content;
    };

    const renderReport = (results) => {
        reportContent.innerHTML = '';
        if (!results || results.length === 0) {
            reportContent.innerHTML = '<p>Nenhum resultado.</p>';
            return;
        }
        results.forEach(item => {
            let el = document.createElement('div');
            if (item.type === 'SUCESSO') {
                el.className = 'p-4 bg-green-50 border-l-4 border-green-500 text-green-800 rounded';
                el.innerHTML = `<p class="font-bold">Sucesso</p><p>${item.message}</p>`;
            } else if (item.type === 'CONFLITO') {
                el.className = 'p-4 bg-red-50 border-l-4 border-red-500 text-red-800 rounded';
                el.innerHTML = `<p class="font-bold">Conflito</p><p><strong>Elemento:</strong> <code>${item.element}</code></p><p><strong>Mensagem:</strong> ${item.message}</p><p class="mt-2 pt-2 border-t border-red-200"><strong>Sugestão IA:</strong> <span class="italic">${item.suggestion_llm}</span></p>`;
            } else if (item.type === 'ERRO') {
                el.className = 'p-4 bg-yellow-50 border-l-4 border-yellow-500 text-yellow-800 rounded';
                el.innerHTML = `<p class="font-bold">Aviso</p><p>${item.message}</p>`;
            }
            if (el.innerHTML) reportContent.appendChild(el);
        });
    };

    const populateOntologyExplorer = async () => {
        try {
            const response = await fetch('/ontology-summary');
            const data = await response.json();
            relationSelect.innerHTML = '<option value="">-- Selecione a Relação --</option>';
            data.relations.forEach(rel => {
                const option = document.createElement('option');
                option.value = rel;
                option.textContent = rel;
                relationSelect.appendChild(option);
            });
            objectSelect.innerHTML = '<option value="">-- Selecione o Objeto --</option>';
            data.types.forEach(type => {
                const optgroup = document.createElement('optgroup');
                optgroup.label = type.type;
                type.examples.forEach(ex => {
                    const option = document.createElement('option');
                    option.value = ex;
                    option.textContent = ex;
                    optgroup.appendChild(option);
                });
                objectSelect.appendChild(optgroup);
            });
        } catch (error) { console.error("Erro ao popular construtor:", error); }
    };

    const loadFullGraph = async () => {
        addChatMessage('A gerar o grafo completo...', 'bot');
        try {
            const response = await fetch('/api/full-graph');
            const graphData = await response.json();
            if (graphData.error) throw new Error(graphData.error);
            if (graphData.nodes.length >= 500) addChatMessage('Aviso: Grafo grande, a exibir as primeiras 500 relações.', 'bot');
            drawGraph(graphData, conflictMessages, addChatMessage);
            if (Object.keys(conflictMessages).length > 0) addChatMessage(`Conflitos encontrados destacados no grafo.`, 'bot');
        } catch (error) {
            addChatMessage(`Ocorreu um erro ao gerar o grafo: ${error.message}`, 'bot');
        }
    };
    
    const checkSelections = () => {
        generateQueryBtn.disabled = !(relationSelect.value && objectSelect.value);
    };
    
    const generateQuestion = () => {
        const relation = relationSelect.value;
        const object = objectSelect.value;
        if (!relation || !object) return;
        userInput.value = `Qual a relação '${relation}' para o objeto '${object}'?`;
        userInput.focus();
    };

    // INÍCIO DO CÓDIGO DE INTERATIVIDADE
    const raycaster = new THREE.Raycaster();
    const mouse = new THREE.Vector2();
    let selectedObject = null;
    const originalMaterials = new Map();

    function onMouseClick(event) {
        // Calcular posição do mouse relativa ao canvas
        const rect = renderer.domElement.getBoundingClientRect();
        mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
        mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

        raycaster.setFromCamera(mouse, camera);
        const intersects = raycaster.intersectObjects(scene.children, true);

        if (intersects.length > 0) {
            const firstIntersected = intersects[0].object;

            // Restaura o material do objeto previamente selecionado
            if (selectedObject && originalMaterials.has(selectedObject)) {
                selectedObject.material = originalMaterials.get(selectedObject);
            }

            // Armazena o novo objeto selecionado e seu material original
            selectedObject = firstIntersected;
            if (!originalMaterials.has(selectedObject)) {
                originalMaterials.set(selectedObject, selectedObject.material);
            }

            // Cria um material de destaque para o objeto selecionado
            const highlightMaterial = selectedObject.material.clone();
            highlightMaterial.emissive = new THREE.Color(0xffff00); // Destaque amarelo
            selectedObject.material = highlightMaterial;

            // Mostrar informações do objeto
            let info = `Objeto selecionado: ${selectedObject.name || 'Sem nome'}`;
            if (selectedObject.userData.globalId) {
                info += `\nGlobalId: ${selectedObject.userData.globalId}`;
            }
            if (selectedObject.userData.type) {
                info += `\nTipo: ${selectedObject.userData.type}`;
            }
            if (selectedObject.userData.material) {
                info += `\nMaterial: ${selectedObject.userData.material}`;
            }
            
            addChatMessage(info, 'bot');

        } else {
            // Se clicar fora, restaura o último objeto selecionado
            if (selectedObject && originalMaterials.has(selectedObject)) {
                selectedObject.material = originalMaterials.get(selectedObject);
                selectedObject = null;
            }
        }
    }

    // Adiciona o listener de clique ao container do visualizador
    viewerContainer.addEventListener('click', onMouseClick);

    // Event listeners
    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
    resetBtn.addEventListener('click', () => resetGraph());
    fullGraphBtn.addEventListener('click', loadFullGraph);
    relationSelect.addEventListener('change', checkSelections);
    objectSelect.addEventListener('change', checkSelections);
    generateQueryBtn.addEventListener('click', generateQuestion);
    
    // Redimensionamento da janela
    window.addEventListener('resize', () => {
        if (renderer && camera) {
            camera.aspect = viewerContainer.clientWidth / viewerContainer.clientHeight;
            camera.updateProjectionMatrix();
            renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
        }
    });
});

