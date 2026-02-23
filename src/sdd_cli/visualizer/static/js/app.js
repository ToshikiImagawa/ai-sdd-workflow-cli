// Entry point, tab switching, data loading

// Global variables
let nodeMetadata = {};
let nodeMetadata1 = {};
let nodeMetadata2 = {};
const zoomState = { single: 1.0, split1: 1.0, split2: 1.0 };

// Current active tab
let activeTab = 'single';
let splitDataLoaded = false;
let singleDataLoaded = false;

// Apply initial theme and initialize Mermaid
applyTheme(getInitialTheme());
initializeMermaid();

// Re-render all diagrams (called from ui-controls on theme change)
async function rerenderAllDiagrams() {
    initializeMermaid();

    if (singleDataLoaded) {
        singleDataLoaded = false;
        await loadSingleData();
    }
    if (splitDataLoaded) {
        splitDataLoaded = false;
        await loadSplitData();
    }
}

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(`tab-${tabName}`).classList.add('active');

    activeTab = tabName;

    // Load data if not loaded yet
    if (tabName === 'single' && !singleDataLoaded) {
        loadSingleData();
    } else if (tabName === 'split' && !splitDataLoaded) {
        loadSplitData();
    }

    // Update header based on active tab
    if (tabName === 'single') {
        document.getElementById('graph-title').textContent = 'SDD Dependency Graph';
        document.getElementById('graph-subtitle').textContent = 'Interactive dependency graph visualization';
    } else {
        document.getElementById('graph-title').textContent = 'SDD Dependency Graph (Split View)';
        document.getElementById('graph-subtitle').textContent = 'PRD-based and Direct (without PRD) documents';
    }

    // Update zoom display
    updateZoom();
}

// Setup tab click handlers
document.querySelectorAll('.tab-button').forEach(button => {
    button.addEventListener('click', () => {
        const tabName = button.dataset.tab;
        switchTab(tabName);
    });
});

// Single graph mode
async function loadSingleData() {
    try {
        nodeMetadata = {};
        const graphData = await loadGraphData('/dependency-graph.json', 'mermaid-diagram', 'graphDiv', nodeMetadata);

        // Set title
        document.getElementById('graph-title').textContent = graphData.title || 'SDD Dependency Graph';
        document.getElementById('graph-subtitle').textContent = graphData.subtitle || 'Interactive dependency graph visualization';
        document.getElementById('single-title').textContent = graphData.title || 'SDD Dependency Graph';

        singleDataLoaded = true;
        initializeAfterLoad('mermaid-diagram', nodeMetadata);
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById('mermaid-diagram').innerHTML =
            `<div class="error-message">Error loading diagram: ${error.message}</div>`;
        document.getElementById('graph-subtitle').textContent = 'Error loading data';
    }
}

// Split graph mode
async function loadSplitData() {
    try {
        document.getElementById('graph-title').textContent = 'SDD Dependency Graph (Split View)';
        document.getElementById('graph-subtitle').textContent = 'PRD-based and Direct (without PRD) documents';

        // Graph 1: PRD-based
        nodeMetadata1 = {};
        await loadGraphData('/prd-based-graph.json', 'mermaid-diagram-1', 'graphDiv1', nodeMetadata1);
        initializeAfterLoad('mermaid-diagram-1', nodeMetadata1, 1);

        // Graph 2: Direct
        nodeMetadata2 = {};
        await loadGraphData('/direct-graph.json', 'mermaid-diagram-2', 'graphDiv2', nodeMetadata2);
        initializeAfterLoad('mermaid-diagram-2', nodeMetadata2, 2);

        splitDataLoaded = true;
        updateSplitNodeCount();
    } catch (error) {
        console.error('Error loading split data:', error);
        document.getElementById('graph-subtitle').textContent = 'Error loading data';
    }
}

function updateSplitNodeCount() {
    const nodes1 = document.querySelectorAll('#mermaid-diagram-1 .node').length;
    const edges1 = document.querySelectorAll('#mermaid-diagram-1 .flowchart-link, #mermaid-diagram-1 path.edge').length;
    const nodes2 = document.querySelectorAll('#mermaid-diagram-2 .node').length;
    const edges2 = document.querySelectorAll('#mermaid-diagram-2 .flowchart-link, #mermaid-diagram-2 path.edge').length;

    document.getElementById('node-count').textContent =
        `PRD: ${nodes1} nodes, ${edges1} edges | Direct: ${nodes2} nodes, ${edges2} edges`;
}

function initializeAfterLoad(elementId, metadata, graphIndex) {
    setTimeout(() => {
        updateZoom();

        const nodes = document.querySelectorAll(`#${elementId} .node`);

        if (activeTab === 'single') {
            // Single mode: update node count
            const edges = document.querySelectorAll(`#${elementId} .flowchart-link, #${elementId} .edge-pattern, #${elementId} path.edge`);
            const edgeCount = edges.length > 0 ? edges.length : document.querySelectorAll(`#${elementId} marker`).length / 2;
            document.getElementById('node-count').textContent =
                `${nodes.length} nodes, ${Math.floor(edgeCount)} edges`;
        }

        // Add click handlers to nodes
        nodes.forEach((node) => {
            node.style.cursor = 'pointer';
            node.addEventListener('click', () => {
                let nodeId = node.id || 'unknown';

                if (nodeId.startsWith('flowchart-')) {
                    nodeId = nodeId.substring('flowchart-'.length);
                    nodeId = nodeId.replace(/-\d+$/, '');
                }

                console.log('Node clicked:', nodeId, 'Available metadata keys:', Object.keys(metadata));

                const nodeData = metadata[nodeId] || {
                    title: node.textContent,
                    path: 'N/A',
                    directory: 'N/A',
                    featureId: 'N/A'
                };
                showNodeDetail(nodeId, nodeData);
            });
        });
    }, 1000);
}

// Setup pan/zoom for containers after page load
window.addEventListener('load', () => {
    setTimeout(() => {
        setupPanZoom('mermaid-diagram');
        setupPanZoom('mermaid-diagram-1');
        setupPanZoom('mermaid-diagram-2');
    }, 1500);
});

// Initialize on page load
async function init() {
    await loadSingleData();
}

window.addEventListener('load', init);
