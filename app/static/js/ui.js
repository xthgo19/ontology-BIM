export function showStatus(message, isError = false, isLoading = false) {
    const statusArea = document.getElementById('status-area');
    let content = '';
    if (isLoading) {
        content = `<div class="flex justify-center items-center"><div class="spinner mr-3"></div><p>${message}</p></div>`;
    } else {
        content = `<p class="${isError ? 'text-red-600' : 'text-green-600'} font-semibold">${message}</p>`;
    }
    statusArea.innerHTML = content;
};

export function renderReport(results) {
    const reportContent = document.getElementById('report-content');
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
        if (el) reportContent.appendChild(el);
    });
};

export function addChatMessage(message, sender) {
    const chatWindow = document.getElementById('chat-window');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message p-3 rounded-lg max-w-2xl break-words shadow-sm ${sender === 'user' ? 'bg-indigo-500 text-white self-end ml-auto' : 'bg-gray-200 text-gray-800 self-start mr-auto'}`;
    messageDiv.innerHTML = message.replace(/\n/g, '<br>');
    chatWindow.appendChild(messageDiv);
    chatWindow.scrollTop = chatWindow.scrollHeight;
};

export async function populateOntologyExplorer() {
    const relationSelect = document.getElementById('relation-select');
    const objectSelect = document.getElementById('object-select');
    try {
        const data = await getOntologySummary();
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
    } catch (error) {
        console.error("Erro ao popular construtor:", error);
    }
};

export function checkSelections() {
    const relationSelect = document.getElementById('relation-select');
    const objectSelect = document.getElementById('object-select');
    const generateQueryBtn = document.getElementById('generate-query-btn');
    generateQueryBtn.disabled = !(relationSelect.value && objectSelect.value);
};

export function generateQuestion() {
    const relationSelect = document.getElementById('relation-select');
    const objectSelect = document.getElementById('object-select');
    const userInput = document.getElementById('user-input');
    const relation = relationSelect.value;
    const object = objectSelect.value;
    if (!relation || !object) return;
    userInput.value = `Qual a relação '${relation}' para o objeto '${object}'?`;
    userInput.focus();
};