// Mermaid rendering and graph code generation

const FILE_TYPE_COLORS = {
    light: {
        "requirement": "#bbf",
        "spec": "#bfb",
        "design": "#bff",
        "task": "#ffb",
        "constitution": "#f9f",
        "default": "#ddd",
        "empty": "#f0f0f0",
        "stroke": "#333",
        "emptyStroke": "#999",
        "textColor": "#333"
    },
    dark: {
        "requirement": "#283593",
        "spec": "#2e7d32",
        "design": "#00695c",
        "task": "#f57f17",
        "constitution": "#6a1b6a",
        "default": "#37474f",
        "empty": "#263238",
        "stroke": "#90a4ae",
        "emptyStroke": "#607d8b",
        "textColor": "#fff"
    }
};

function getNodeColors() {
    const theme = document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
    return FILE_TYPE_COLORS[theme];
}

const EDGE_STYLES = {
    "explicit": "--o",
    "implicit": "-.-o",
    "link": "-->",
    "constitution": "-.-o"
};

function sanitizeNodeId(path) {
    return path.replace(/[^a-zA-Z0-9_]/g, "_");
}

function generateMermaidCode(graphData) {
    const lines = [];
    lines.push("graph BT");
    lines.push("");

    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    const lintIssues = graphData.lintIssues || {};

    const colors = getNodeColors();

    // Handle empty graph
    if (nodes.length === 0) {
        lines.push("    EMPTY[No documents found]");
        lines.push(`    style EMPTY fill:${colors.empty},stroke:${colors.emptyStroke},stroke-dasharray: 5 5`);
        return lines.join("\n");
    }

    // Check if CONSTITUTION exists
    const hasConstitution = nodes.some(node => node.id === "CONSTITUTION.md");
    if (!hasConstitution && nodes.length > 0) {
        lines.push("    CONSTITUTION[CONSTITUTION.md]");
        lines.push("");
    }

    // Generate node definitions with lint badges
    for (const node of nodes) {
        const nodeId = sanitizeNodeId(node.id);
        let title = (node.title || node.id).replace(/"/g, '\\"');

        // Add lint badge if issues exist for this node
        const nodeIssues = lintIssues[node.id] || [];
        if (nodeIssues.length > 0) {
            const errorCount = nodeIssues.filter(i => i.severity === "error").length;
            const warnCount = nodeIssues.filter(i => i.severity === "warning").length;
            const badge = [];
            if (errorCount > 0) badge.push(`E:${errorCount}`);
            if (warnCount > 0) badge.push(`W:${warnCount}`);
            if (badge.length > 0) title += ` [${badge.join(' ')}]`;
        }

        lines.push(`    ${nodeId}["${title}"]`);
    }

    lines.push("");

    // Generate edges
    const edgesAdded = new Set();
    for (const edge of edges) {
        const sourceId = sanitizeNodeId(edge.source);
        const targetId = sanitizeNodeId(edge.target);
        const edgeStyle = EDGE_STYLES[edge.type] || "-->";
        const edgeDef = `${sourceId} ${edgeStyle} ${targetId}`;
        if (!edgesAdded.has(edgeDef)) {
            lines.push(`    ${edgeDef}`);
            edgesAdded.add(edgeDef);
        }
    }

    // Add implicit edges from CONSTITUTION if not filtered
    if (!hasConstitution && nodes.length > 0) {
        // Collect nodes that have a parent (are sources of dependency edges)
        const nodesWithParent = new Set();
        for (const edge of edges) {
            nodesWithParent.add(edge.source);
        }

        // top-level requirements: CONSTITUTION -.-o requirement
        const requirementNodes = nodes.filter(node => node.file_type === "requirement");
        for (const node of requirementNodes) {
            if (nodesWithParent.has(node.id)) continue;
            const nodeId = sanitizeNodeId(node.id);
            const edgeDef = `${nodeId} -.-o CONSTITUTION`;
            if (!edgesAdded.has(edgeDef)) {
                lines.push(`    ${edgeDef}`);
                edgesAdded.add(edgeDef);
            }
        }

        // spec without a corresponding requirement: CONSTITUTION -.-o spec
        const requirementFeatureIds = new Set(requirementNodes.map(n => n.feature_id).filter(Boolean));
        const specNodes = nodes.filter(node => node.file_type === "spec");
        for (const node of specNodes) {
            if (nodesWithParent.has(node.id)) continue;
            if (!requirementFeatureIds.has(node.feature_id)) {
                const nodeId = sanitizeNodeId(node.id);
                const edgeDef = `${nodeId} -.-o CONSTITUTION`;
                if (!edgesAdded.has(edgeDef)) {
                    lines.push(`    ${edgeDef}`);
                    edgesAdded.add(edgeDef);
                }
            }
        }

        // orphan tasks (no link or explicit parent): CONSTITUTION -.-o task
        const taskNodes = nodes.filter(node => node.file_type === "task");
        for (const node of taskNodes) {
            if (nodesWithParent.has(node.id)) continue;
            const nodeId = sanitizeNodeId(node.id);
            const edgeDef = `${nodeId} -.-o CONSTITUTION`;
            if (!edgesAdded.has(edgeDef)) {
                lines.push(`    ${edgeDef}`);
                edgesAdded.add(edgeDef);
            }
        }
    }

    // Add ghost nodes for unresolved dependencies (max 10)
    const ghostNodes = new Set();
    for (const issues of Object.values(lintIssues)) {
        for (const issue of issues) {
            if (issue.rule === "unresolved-dependency") {
                // Extract unresolved ID from message
                const match = issue.message.match(/Unresolved depends-on reference: (.+)/);
                if (match) {
                    ghostNodes.add(match[1]);
                }
            }
            if (ghostNodes.size >= 10) break;
        }
        if (ghostNodes.size >= 10) break;
    }

    if (ghostNodes.size > 0) {
        lines.push("");
        lines.push("    %% Ghost nodes (unresolved dependencies)");
        for (const ghostId of ghostNodes) {
            const ghostNodeId = sanitizeNodeId("ghost_" + ghostId);
            lines.push(`    ${ghostNodeId}["${ghostId} ❓"]`);
        }

        // Add edges from source nodes to ghost nodes
        for (const [filePath, issues] of Object.entries(lintIssues)) {
            for (const issue of issues) {
                if (issue.rule === "unresolved-dependency") {
                    const match = issue.message.match(/Unresolved depends-on reference: (.+)/);
                    if (match && ghostNodes.has(match[1])) {
                        const sourceId = sanitizeNodeId(filePath);
                        const ghostNodeId = sanitizeNodeId("ghost_" + match[1]);
                        lines.push(`    ${sourceId} --x ${ghostNodeId}`);
                    }
                }
            }
        }
    }

    lines.push("");

    // Generate styles with lint-aware stroke colors
    for (const node of nodes) {
        const nodeId = sanitizeNodeId(node.id);
        let color;
        if (node.id === "CONSTITUTION.md") {
            color = colors.constitution;
        } else {
            color = colors[node.file_type] || colors.default;
        }

        // Check lint issues for this node to apply error/warning stroke
        const nodeIssues = lintIssues[node.id] || [];
        const hasError = nodeIssues.some(i => i.severity === "error");
        const hasWarning = nodeIssues.some(i => i.severity === "warning");

        let strokeColor = colors.stroke;
        let strokeWidth = "1px";
        if (hasError) {
            strokeColor = "#d32f2f";
            strokeWidth = "3px";
        } else if (hasWarning) {
            strokeColor = "#f9a825";
            strokeWidth = "2px";
        }

        lines.push(`    style ${nodeId} fill:${color},stroke:${strokeColor},stroke-width:${strokeWidth},color:${colors.textColor}`);
    }

    // Ghost node styles (dashed border, faded background)
    for (const ghostId of ghostNodes) {
        const ghostNodeId = sanitizeNodeId("ghost_" + ghostId);
        lines.push(`    style ${ghostNodeId} fill:${colors.empty},stroke:${colors.emptyStroke},stroke-dasharray: 5 5,color:${colors.textColor}`);
    }

    // Add CONSTITUTION style
    if (!hasConstitution && nodes.length > 0) {
        lines.push(`    style CONSTITUTION fill:${colors.constitution},stroke:${colors.stroke},stroke-width:1px,color:${colors.textColor}`);
    }

    return lines.join("\n");
}

function getMermaidTheme() {
    return document.documentElement.getAttribute('data-theme') === 'dark' ? 'dark' : 'default';
}

function initializeMermaid() {
    mermaid.initialize({
        startOnLoad: false,
        theme: getMermaidTheme(),
        themeVariables: {
            fontSize: '16px',
            fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif'
        },
        flowchart: {
            nodeSpacing: 80,
            rankSpacing: 100,
            padding: 20
        }
    });
}

// Common graph loading: fetch -> metadata -> parent map -> Mermaid render
async function loadGraphData(dataUrl, elementId, renderDivId, metadata) {
    const response = await fetch(dataUrl);
    if (!response.ok) throw new Error(`Failed to load: ${response.status}`);
    const graphData = await response.json();

    // Build node metadata
    const lintIssues = graphData.lintIssues || {};
    for (const node of graphData.nodes) {
        const nodeId = sanitizeNodeId(node.id);
        metadata[nodeId] = {
            title: node.title,
            path: node.id,
            directory: node.directory,
            featureId: node.feature_id || 'N/A',
            links: node.links || [],
            lintIssues: lintIssues[node.id] || []
        };
    }
    buildParentMap(graphData, metadata);

    // Mermaid render
    const mermaidCode = generateMermaidCode(graphData);
    const diagramElement = document.getElementById(elementId);
    diagramElement.textContent = mermaidCode;
    diagramElement.removeAttribute('data-processed');
    const { svg } = await mermaid.render(renderDivId, mermaidCode);
    diagramElement.innerHTML = svg;

    return graphData;
}

// Resolve parent node from SDD hierarchy (file_type + path structure)
function buildParentMap(graphData, metadata) {
    const nodes = graphData.nodes || [];
    const edges = graphData.edges || [];
    const requirementFeatureIds = new Set(
        nodes.filter(n => n.file_type === "requirement").map(n => n.feature_id).filter(Boolean)
    );
    // Build node lookup by id
    const nodeById = {};
    for (const n of nodes) nodeById[n.id] = n;

    for (const node of nodes) {
        const nodeId = sanitizeNodeId(node.id);
        if (!metadata[nodeId]) continue;

        if (node.file_type === "task") {
            // Task: resolve parents from link edges (can be multiple)
            const parents = findTaskParents(node, edges, nodeById);
            if (parents.length > 0) {
                metadata[nodeId].parent = parents.map(p => p.title || p.id).join(', ');
            }
        } else {
            const parent = findParentNode(node, nodes, requirementFeatureIds);
            if (parent) {
                metadata[nodeId].parent = parent.title || parent.id;
            }
        }
    }
}

function findTaskParents(node, edges, nodeById) {
    const candidates = [];
    const seen = new Set();
    for (const edge of edges) {
        if (edge.source === node.id && edge.type === "link") {
            const target = nodeById[edge.target];
            if (target && !seen.has(target.id)) {
                candidates.push(target);
                seen.add(target.id);
            }
        }
    }
    if (candidates.length <= 1) return candidates;

    // Remove ancestors: if A --> ... --> B exists among candidates, A is an ancestor of B -> remove A
    const candidateIds = new Set(candidates.map(c => c.id));
    const ancestors = new Set();
    for (const candidate of candidates) {
        // BFS: follow non-link edges from this candidate, check if we reach another candidate
        const visited = new Set();
        const queue = [candidate.id];
        while (queue.length > 0) {
            const current = queue.shift();
            if (visited.has(current)) continue;
            visited.add(current);
            for (const edge of edges) {
                if (edge.source === current && edge.type !== "link") {
                    if (candidateIds.has(edge.target) && edge.target !== candidate.id) {
                        ancestors.add(candidate.id);
                    }
                    queue.push(edge.target);
                }
            }
        }
    }
    return candidates.filter(c => !ancestors.has(c.id));
}

function findParentNode(node, allNodes, requirementFeatureIds) {
    const CONSTITUTION = { id: "CONSTITUTION.md", title: "CONSTITUTION.md" };

    if (node.file_type === "requirement") {
        // Nested requirement: parent is the index.md in the same directory
        const parts = node.id.split('/');
        if (parts.length > 2 && !node.id.endsWith('index.md')) {
            const parentDir = parts.slice(0, -1).join('/');
            const parentIndex = allNodes.find(n =>
                n.file_type === "requirement" &&
                n.id === parentDir + '/index.md'
            );
            if (parentIndex) return parentIndex;
        }
        return CONSTITUTION;
    }

    if (node.file_type === "spec") {
        // Parent is a requirement with the same feature_id, or CONSTITUTION
        const req = allNodes.find(n =>
            n.file_type === "requirement" && n.feature_id === node.feature_id
        );
        return req || CONSTITUTION;
    }

    if (node.file_type === "design") {
        // Parent is spec with the same feature_id
        const spec = allNodes.find(n =>
            n.file_type === "spec" && n.feature_id === node.feature_id
        );
        return spec || null;
    }

    return null;
}
