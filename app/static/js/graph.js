let network = null;

const applyConflictHighlighting = (graphData, conflictMessages) => {
    if (Object.keys(conflictMessages).length > 0 && graphData && graphData.nodes) {
        const conflictingIds = new Set(
            Object.keys(conflictMessages).map(nodeId => {
                const parts = nodeId.split(/[:#]/);
                return parts[parts.length - 1];
            })
        );

        graphData.nodes.forEach(node => {
            const graphNodeId = node.id.substring(node.id.lastIndexOf('#') + 1) || node.id.substring(node.id.lastIndexOf('/') + 1);
            if (conflictingIds.has(graphNodeId)) {
                node.color = { background: '#fecaca', border: '#ef4444' };
                
                const originalUri = Object.keys(conflictMessages).find(key => key.endsWith(graphNodeId));
                if (originalUri) {
                    const message = conflictMessages[originalUri];
                    
                    const tooltipElement = document.createElement('div');
                    tooltipElement.style.whiteSpace = 'normal';
                    tooltipElement.style.overflowWrap = 'break-word';
                    tooltipElement.style.wordWrap = 'break-word';
                    tooltipElement.innerHTML = `<div style="font-weight: bold; margin-bottom: 5px; color: #dc2626;">⚠️ Conflito de Validação</div><div>${message}</div>`;
                    node.title = tooltipElement;
                }
            }
        });
    }
    return graphData;
};

export const drawGraph = (graphData, conflictMessages, addChatMessageCallback) => {
    const graphContainer = document.getElementById('graph-container');
    if (network) { network.destroy(); network = null; }
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0) {
         graphContainer.innerHTML = '<p class="p-4 text-gray-500 text-center">Nenhum dado para visualizar.</p>';
         return;
    }

    const highlightedGraphData = applyConflictHighlighting(graphData, conflictMessages);
    const data = { nodes: new vis.DataSet(highlightedGraphData.nodes), edges: new vis.DataSet(highlightedGraphData.edges) };
    
    const options = {
        nodes: { shape: 'box', margin: 15, widthConstraint: { minimum: 150 } },
        edges: {
            font: { align: 'middle', size: 12, color: '#4b5563', background: 'rgba(255, 255, 255, 0.8)', strokeWidth: 0 },
            smooth: { type: 'continuous' },
            color: {
                color: '#a0aec0',
                highlight: '#4f46e5',
                inherit: false
            }
        },
        physics: { solver: 'barnesHut', barnesHut: { gravitationalConstant: -60000, centralGravity: 0.25, springLength: 400, springConstant: 0.02, damping: 0.3, avoidOverlap: 1 }, },
        interaction: { hover: true, navigationButtons: true, keyboard: true, tooltipDelay: 200 }
    };
    graphContainer.innerHTML = '';
    network = new vis.Network(graphContainer, data, options);
    network.on("stabilizationIterationsDone", () => network.setOptions({ physics: false }));
    network.on("doubleClick", async (params) => {
        if (params.nodes.length > 0) {
            const nodeId = params.nodes[0];
            const nodeObject = data.nodes.get(nodeId);
            addChatMessageCallback(`Explorando: '${nodeObject.label}'`, 'user');
            const graphResponse = await fetch(`/graph-data?object=${encodeURIComponent(nodeObject.label)}`);
            const newGraphData = await graphResponse.json();
            drawGraph(newGraphData, conflictMessages, addChatMessageCallback);
        }
    });
};

export const resetGraph = () => {
    const graphContainer = document.getElementById('graph-container');
    if (network) { network.destroy(); network = null; }
    graphContainer.innerHTML = '<p class="p-4 text-gray-500 text-center">Grafo reiniciado. Faça uma consulta para visualizar.</p>';
};

export const highlightNodeInGraph = (globalId) => {
    if (!network || !globalId) {
        return;
    }

    const nodes = network.body.data.nodes.get({
        filter: function (item) {
            return item.id.endsWith(globalId);
        }
    });

    if (nodes && nodes.length > 0) {
        const nodeId = nodes[0].id;

        network.setSelection({ nodes: [nodeId], edges: [] });

        network.focus(nodeId, {
            scale: 1.5,
            animation: {
                duration: 1000,
                easingFunction: 'easeInOutQuad'
            }
        });
    }
};