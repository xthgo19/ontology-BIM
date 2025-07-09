export async function validateModel(formData) {
    const response = await fetch('/validate', { method: 'POST', body: formData });
    if (!response.ok) throw new Error(`Erro do servidor: ${response.status}`);
    const data = await response.json();
    if (data.error) throw new Error(data.error);
    return data;
}

export async function askChatbot(question) {
    const response = await fetch('/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
    });
    if (!response.ok) throw new Error('Erro na comunicação com o chatbot.');
    return await response.json();
}

export async function getGraphData(objectName) {
    const response = await fetch(`/graph-data?object=${encodeURIComponent(objectName)}`);
    if (!response.ok) throw new Error('Erro ao buscar dados do grafo.');
    return await response.json();
}

export async function getFullGraph() {
    const response = await fetch('/api/full-graph');
    if (!response.ok) throw new Error('Erro ao buscar o grafo completo.');
    return await response.json();
}

export async function getOntologySummary() {
    const response = await fetch('/ontology-summary');
    if (!response.ok) throw new Error('Erro ao buscar resumo da ontologia.');
    return await response.json();
}