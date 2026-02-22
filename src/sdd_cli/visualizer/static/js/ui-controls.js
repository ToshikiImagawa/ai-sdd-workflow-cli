// UI controls: zoom, pan, theme, download, node detail

// Zoom constants
const zoomStep = 0.2;
const minZoom = 0.3;
const maxZoom = 4.0;

// Theme management
function getInitialTheme() {
    const saved = localStorage.getItem('sdd-theme');
    if (saved) return saved;
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

function applyTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('sdd-theme', theme);

    const checkbox = document.getElementById('theme-checkbox');
    if (checkbox) {
        checkbox.checked = theme === 'dark';
    }
}

function toggleTheme() {
    const checkbox = document.getElementById('theme-checkbox');
    const next = checkbox.checked ? 'dark' : 'light';
    applyTheme(next);
    rerenderAllDiagrams();
}

// Zoom functionality
function getActiveZoomKeys() {
    return activeTab === 'single' ? ['single'] : ['split1', 'split2'];
}

function applyZoomToSvg(selector, zoomValue) {
    const svg = document.querySelector(selector);
    if (svg) {
        svg.style.transform = `scale(${zoomValue})`;
        svg.style.transformOrigin = 'top left';
    }
}

function updateZoom() {
    if (activeTab === 'single') {
        applyZoomToSvg('#mermaid-diagram svg', zoomState.single);
        document.getElementById('zoom-level').textContent = Math.round(zoomState.single * 100) + '%';
    } else {
        applyZoomToSvg('#mermaid-diagram-1 svg', zoomState.split1);
        applyZoomToSvg('#mermaid-diagram-2 svg', zoomState.split2);
        document.getElementById('zoom-level').textContent =
            `PRD: ${Math.round(zoomState.split1 * 100)}% | Direct: ${Math.round(zoomState.split2 * 100)}%`;
    }
}

function zoomIn() {
    for (const key of getActiveZoomKeys()) {
        if (zoomState[key] < maxZoom) zoomState[key] += zoomStep;
    }
    updateZoom();
}

function zoomOut() {
    for (const key of getActiveZoomKeys()) {
        if (zoomState[key] > minZoom) zoomState[key] -= zoomStep;
    }
    updateZoom();
}

function resetZoom() {
    for (const key of getActiveZoomKeys()) {
        zoomState[key] = 1.0;
    }
    updateZoom();
}

// Pan functionality
function setupPanZoom(containerId) {
    let isPanning = false;
    let startX, startY;
    let scrollLeft, scrollTop;

    const container = document.getElementById(containerId);
    if (!container) return;

    container.addEventListener('mousedown', (e) => {
        isPanning = true;
        startX = e.pageX - container.offsetLeft;
        startY = e.pageY - container.offsetTop;
        scrollLeft = container.scrollLeft;
        scrollTop = container.scrollTop;
    });

    container.addEventListener('mouseleave', () => {
        isPanning = false;
    });

    container.addEventListener('mouseup', () => {
        isPanning = false;
    });

    container.addEventListener('mousemove', (e) => {
        if (!isPanning) return;
        e.preventDefault();
        const x = e.pageX - container.offsetLeft;
        const y = e.pageY - container.offsetTop;
        const walkX = (x - startX) * 1.5;
        const walkY = (y - startY) * 1.5;
        container.scrollLeft = scrollLeft - walkX;
        container.scrollTop = scrollTop - walkY;
    });

    // Mouse wheel zoom
    container.addEventListener('wheel', (e) => {
        e.preventDefault();
        if (e.deltaY < 0) {
            zoomIn();
        } else {
            zoomOut();
        }
    });
}

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.key === '+' || e.key === '=') {
        e.preventDefault();
        zoomIn();
    } else if (e.key === '-') {
        e.preventDefault();
        zoomOut();
    } else if (e.key === '0') {
        e.preventDefault();
        resetZoom();
    } else if (e.key === 'Escape') {
        closeNodeDetail();
    }
});

// Download functionality
function downloadSVG() {
    const svgElement = activeTab === 'single'
        ? document.querySelector('#mermaid-diagram svg')
        : document.querySelector('#mermaid-diagram-1 svg');
    if (!svgElement) {
        alert('Diagram not loaded yet');
        return;
    }

    const svgData = new XMLSerializer().serializeToString(svgElement);
    const blob = new Blob([svgData], { type: 'image/svg+xml' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = 'dependency-graph.svg';
    link.click();
    URL.revokeObjectURL(url);
}

// Node detail functionality
function showNodeDetail(nodeId, nodeData) {
    const parentHtml = nodeData.parent
        ? nodeData.parent.split(', ').map(p => `<span class="parent-tag">${p}</span>`).join(' ')
        : 'N/A';

    const linksHtml = nodeData.links && nodeData.links.length > 0
        ? nodeData.links.map(l => `<span class="parent-tag">${l}</span>`).join(' ')
        : 'N/A';

    const detailContent = document.getElementById('detail-content');
    detailContent.innerHTML = `
        <h2>${nodeData.title || nodeId}</h2>
        <div class="detail-item">
            <div class="detail-label">File Path</div>
            <div class="detail-value">${nodeData.path || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Directory</div>
            <div class="detail-value">${nodeData.directory || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Feature ID</div>
            <div class="detail-value">${nodeData.featureId || 'N/A'}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Links</div>
            <div class="detail-value">${linksHtml}</div>
        </div>
        <div class="detail-item">
            <div class="detail-label">Parent</div>
            <div class="detail-value">${parentHtml}</div>
        </div>
    `;
    document.getElementById('overlay').classList.add('active');
    document.getElementById('node-detail').classList.add('active');
}

function closeNodeDetail() {
    document.getElementById('overlay').classList.remove('active');
    document.getElementById('node-detail').classList.remove('active');
}
