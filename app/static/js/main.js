import { drawGraph, resetGraph } from './graph.js';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

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

    const setupThreeJs = () => {
        if (renderer) { renderer.domElement.remove(); renderer.dispose(); }
        scene = new THREE.Scene();
        scene.background = new THREE.Color(0x222222);
        camera = new THREE.PerspectiveCamera(75, viewerContainer.clientWidth / viewerContainer.clientHeight || 1, 0.1, 1000);
        camera.position.set(15, 15, 15);
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.8);
        scene.add(ambientLight);
        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
        directionalLight.position.set(0, 10, 5);
        scene.add(directionalLight);
        const gridHelper = new THREE.GridHelper(100, 100, 0x555555, 0x333333);
        scene.add(gridHelper);
        renderer = new THREE.WebGLRenderer({ antialias: true });
        renderer.setPixelRatio(window.devicePixelRatio);
        viewerContainer.appendChild(renderer.domElement);
        controls = new OrbitControls(camera, renderer.domElement);
        const animate = () => { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); };
        animate();
    };

    const highlightElements = () => {
        if (Object.keys(conflictMessages).length === 0) return;
        const highlightMaterial = new THREE.MeshBasicMaterial({ color: 0xff0000 });
        let highlightedCount = 0;
        
        Object.keys(conflictMessages).forEach(guidWithPrefix => {
            const guid = guidWithPrefix.replace('ifc:', '');
            const mesh = guidToMeshMap.get(guid);
            if (mesh) {
                mesh.material = highlightMaterial;
                highlightedCount++;
            }
        });
        if (highlightedCount > 0) addChatMessage(`Foram destacados ${highlightedCount} elementos com conflitos.`, 'bot');
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

            addChatMessage('Processamento concluído. A carregar modelo 3D...', 'bot');

            const loader = new GLTFLoader();
            const gltf = await loader.loadAsync(data.model_path);
            const model = gltf.scene;

            console.log("Iniciando processamento do modelo 3D...");
            console.log("Metadados recebidos:", data.metadata);

            const wallMaterial = new THREE.MeshStandardMaterial({
            color: 0x8090a0,
            transparent: true,
            opacity: 0.2, // Opacidade mais baixa para ver melhor o interior
            side: THREE.DoubleSide,
            depthWrite: false // Impede que objetos transparentes "briguem" na renderização
        });

            const defaultMaterial = new THREE.MeshStandardMaterial({ color: 0xcccccc, side: THREE.DoubleSide });

        
            console.log("Iniciando processamento do modelo 3D...");
            console.log("Metadados recebidos:", data.metadata);
            let foundAnyMatch = false;

            model.traverse(child => {
                if (child.isMesh) {
                    // Extrai o GUID do nome do objeto. Ex: "product-GUID-body" -> "GUID"
                    const match = child.name.match(/product-([a-f0-9\-]+)-body/);
                
                    if (match && match[1]) {
                        const extractedGuid = match[1];
                    
                        // Procura o GUID extraído nos metadados
                        if (data.metadata[extractedGuid]) {
                            const meta = data.metadata[extractedGuid];
                            foundAnyMatch = true;
                        
                            // Aplica o material correto baseado no tipo de objeto
                            if (meta.type === 'IfcWall' || meta.type === 'IfcWallStandardCase') {
                                child.material = wallMaterial;
                            } else {
                                child.material = defaultMaterial;
                            }
                        
                            // Mapeia o GUID para a malha para uso posterior (destaque de conflitos)
                            guidToMeshMap.set(extractedGuid, child);

                        } else {
                            // Se o GUID extraído não estiver nos metadados, usa o material padrão
                            child.material = defaultMaterial;
                        }
                    } else {
                        // Se o nome do objeto não seguir o padrão esperado, usa o material padrão
                        child.material = defaultMaterial;
                    }
                }
            });

            if (foundAnyMatch) {
                console.log("%cSUCESSO: Correspondência entre modelo e metadados realizada!", 'color: #00ff00; font-weight: bold;');
            } else {
                console.error("FALHA CRÍTICA: Nenhuma correspondência encontrada. Verifique o formato dos nomes no GLB e os GUIDs nos metadados.");
            }

            scene.add(model);

            const box = new THREE.Box3().setFromObject(model);
            const size = box.getSize(new THREE.Vector3());
            const center = box.getCenter(new THREE.Vector3());
            const maxDim = Math.max(size.x, size.y, size.z);
            let cameraZ = Math.abs(maxDim / 2 / Math.tan(camera.fov * (Math.PI / 180) / 2));
            cameraZ = isFinite(cameraZ) && cameraZ > 0 ? cameraZ * 2.0 : 20;
            camera.position.set(center.x, center.y + size.y, center.z + cameraZ);
            controls.target.copy(center);
            controls.update();
            
            addChatMessage('Modelo 3D carregado. Pronto!', 'bot');
            if (data.validation) {
                data.validation.forEach(item => {
                    if (item.type === 'CONFLITO' && item.element) {
                        conflictMessages[item.element] = item.message;
                    }
                });
            }
            showStatus('Validação e carregamento concluídos!', false);
            renderReport(data.validation);
            mainContent.classList.remove('hidden');

            renderer.setSize(viewerContainer.clientWidth, viewerContainer.clientHeight);
            camera.aspect = viewerContainer.clientWidth / viewerContainer.clientHeight;
            camera.updateProjectionMatrix();
            
            highlightElements();
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
        // Normaliza as coordenadas do mouse para o range do Three.js (-1 a +1)
        mouse.x = (event.clientX / renderer.domElement.clientWidth) * 2 - 1;
        mouse.y = - (event.clientY / renderer.domElement.clientHeight) * 2 + 1;

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

            // Alterna a transparência do objeto selecionado
            const isTransparent = selectedObject.material.transparent;
            selectedObject.material.transparent = !isTransparent;
            selectedObject.material.opacity = isTransparent ? 1.0 : 0.3;

            addChatMessage(`Objeto selecionado: ${selectedObject.name}. Transparência: ${selectedObject.material.transparent ? 'Ativada' : 'Desativada'}.`, 'bot');

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

    sendBtn.addEventListener('click', sendMessage);
    userInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(); });
    resetBtn.addEventListener('click', () => resetGraph());
    fullGraphBtn.addEventListener('click', loadFullGraph);
    relationSelect.addEventListener('change', checkSelections);
    objectSelect.addEventListener('change', checkSelections);
    generateQueryBtn.addEventListener('click', generateQuestion);
});