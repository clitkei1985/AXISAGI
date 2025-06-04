class ReasoningGraphVisualizer {
    constructor() {
        this.graph = null;
        this.currentTrace = null;
        this.animationFrame = null;
        this.isPlaying = false;
        this.currentStep = 0;
        this.ws = null;
        
        this.initializeWebSocket();
        this.initializeGraph();
        this.loadAvailableTraces();
        this.setupEventListeners();
    }
    
    initializeWebSocket() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/reasoning`);
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleRealtimeUpdate(data);
        };
        
        this.ws.onopen = () => {
            console.log('Connected to reasoning updates');
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    initializeGraph() {
        const elem = document.getElementById('reasoning-graph');
        
        this.graph = ForceGraph()(elem)
            .nodeId('id')
            .nodeLabel('label')
            .nodeColor(node => this.getNodeColor(node))
            .nodeVal(node => node.size || 20)
            .linkSource('source')
            .linkTarget('target')
            .linkColor(link => this.getLinkColor(link))
            .linkWidth(link => this.getLinkWidth(link))
            .linkDirectionalArrowLength(6)
            .linkDirectionalArrowRelPos(1)
            .onNodeClick((node, event) => this.showNodeInfo(node))
            .onNodeHover((node, prevNode) => this.handleNodeHover(node, prevNode))
            .d3Force('charge', d3.forceMany().strength(-300))
            .d3Force('link', d3.forceLink().distance(150));
    }
    
    getNodeColor(node) {
        const colors = {
            'source': '#4CAF50',
            'reasoning': '#2196F3',
            'answer': '#FF9800',
            'memory': '#9C27B0',
            'calculation': '#607D8B',
            'web_search': '#795548'
        };
        return colors[node.type] || '#999999';
    }
    
    getLinkColor(link) {
        if (link.confidence >= 0.8) return '#4CAF50';
        if (link.confidence >= 0.5) return '#FF9800';
        return '#F44336';
    }
    
    getLinkWidth(link) {
        if (link.confidence >= 0.8) return 3;
        if (link.confidence >= 0.5) return 2;
        return 1;
    }
    
    async loadAvailableTraces() {
        try {
            const response = await fetch('/api/analytics/reasoning-traces');
            const traces = await response.json();
            
            const select = document.getElementById('trace-select');
            select.innerHTML = '<option value="">Choose a reasoning trace...</option>';
            
            traces.forEach(trace => {
                const option = document.createElement('option');
                option.value = trace.trace_id;
                option.textContent = `${trace.query.substring(0, 50)}... (${trace.created_at})`;
                select.appendChild(option);
            });
        } catch (error) {
            console.error('Failed to load traces:', error);
        }
    }
    
    async loadTrace(traceId) {
        if (!traceId) return;
        
        this.showLoading(true);
        
        try {
            const response = await fetch(`/api/analytics/lineage/${traceId}`);
            const lineageData = await response.json();
            
            this.currentTrace = lineageData;
            this.renderGraph(lineageData);
            this.updateStats(lineageData);
            this.renderTimeline(lineageData);
            
        } catch (error) {
            console.error('Failed to load trace:', error);
        } finally {
            this.showLoading(false);
        }
    }
    
    renderGraph(lineageData) {
        const nodes = [];
        const links = [];
        
        // Add source nodes
        lineageData.trace.sources.forEach(source => {
            nodes.push({
                id: source.id,
                label: source.description,
                type: source.source_type,
                confidence: source.confidence,
                content: source.content,
                timestamp: source.timestamp,
                size: 15 + (source.confidence * 10)
            });
        });
        
        // Add reasoning nodes
        lineageData.trace.reasoning_steps.forEach(step => {
            nodes.push({
                id: step.id,
                label: step.step_type,
                type: 'reasoning',
                confidence: step.confidence,
                content: step.reasoning_text,
                output: step.output_data,
                timestamp: step.timestamp,
                model: step.model_used,
                size: 20 + (step.confidence * 15)
            });
            
            // Add links from input sources to reasoning step
            step.input_sources.forEach(sourceId => {
                links.push({
                    source: sourceId,
                    target: step.id,
                    confidence: step.confidence,
                    type: 'reasoning_input'
                });
            });
        });
        
        // Add final answer node
        if (lineageData.trace.final_answer) {
            const answerId = `${lineageData.trace.trace_id}_answer`;
            nodes.push({
                id: answerId,
                label: 'Final Answer',
                type: 'answer',
                confidence: 1.0,
                content: lineageData.trace.final_answer,
                timestamp: lineageData.trace.created_at,
                size: 30
            });
            
            // Connect reasoning steps to answer
            lineageData.trace.reasoning_steps.forEach(step => {
                links.push({
                    source: step.id,
                    target: answerId,
                    confidence: step.confidence,
                    type: 'reasoning_output'
                });
            });
        }
        
        // Update graph
        this.graph.graphData({ nodes, links });
    }
    
    updateStats(lineageData) {
        const sourceCount = lineageData.trace.sources.length;
        const reasoningCount = lineageData.trace.reasoning_steps.length;
        const totalNodes = sourceCount + reasoningCount + 1; // +1 for answer
        
        const allConfidences = [
            ...lineageData.trace.sources.map(s => s.confidence),
            ...lineageData.trace.reasoning_steps.map(r => r.confidence)
        ];
        const avgConfidence = allConfidences.length > 0 ? 
            allConfidences.reduce((a, b) => a + b, 0) / allConfidences.length : 0;
        
        document.getElementById('total-nodes').textContent = totalNodes;
        document.getElementById('source-count').textContent = sourceCount;
        document.getElementById('reasoning-count').textContent = reasoningCount;
        document.getElementById('confidence-avg').textContent = Math.round(avgConfidence * 100) + '%';
        
        // Calculate processing time if available
        if (lineageData.trace.reasoning_steps.length > 0) {
            const startTime = new Date(lineageData.trace.created_at);
            const endTime = new Date(lineageData.trace.reasoning_steps[lineageData.trace.reasoning_steps.length - 1].timestamp);
            const processingTime = endTime - startTime;
            document.getElementById('processing-time').textContent = processingTime + 'ms';
        }
    }
    
    renderTimeline(lineageData) {
        const timelineDiv = document.getElementById('timeline-chart');
        timelineDiv.innerHTML = '';
        
        // Create simple timeline visualization
        const events = [
            { time: lineageData.trace.created_at, label: 'Query Started', type: 'start' },
            ...lineageData.trace.sources.map(s => ({ 
                time: s.timestamp, 
                label: s.description, 
                type: 'source' 
            })),
            ...lineageData.trace.reasoning_steps.map(r => ({ 
                time: r.timestamp, 
                label: r.step_type, 
                type: 'reasoning' 
            }))
        ];
        
        events.sort((a, b) => new Date(a.time) - new Date(b.time));
        
        events.forEach((event, index) => {
            const eventDiv = document.createElement('div');
            eventDiv.style.cssText = `
                padding: 2px 5px;
                margin: 2px 0;
                background: ${event.type === 'source' ? '#4CAF50' : 
                            event.type === 'reasoning' ? '#2196F3' : '#FF9800'};
                color: white;
                border-radius: 3px;
                font-size: 10px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            `;
            eventDiv.textContent = `${index + 1}. ${event.label}`;
            timelineDiv.appendChild(eventDiv);
        });
    }
    
    showNodeInfo(node) {
        const nodeInfo = document.getElementById('node-info');
        const title = document.getElementById('node-title');
        const description = document.getElementById('node-description');
        const metadata = document.getElementById('node-metadata');
        
        title.textContent = node.label;
        description.textContent = node.content || 'No description available';
        
        metadata.innerHTML = `
            <p><strong>Type:</strong> ${node.type}</p>
            <p><strong>Confidence:</strong> ${Math.round(node.confidence * 100)}%</p>
            <p><strong>Timestamp:</strong> ${new Date(node.timestamp).toLocaleString()}</p>
            ${node.model ? `<p><strong>Model:</strong> ${node.model}</p>` : ''}
            ${node.output ? `<p><strong>Output:</strong> ${node.output.substring(0, 100)}...</p>` : ''}
        `;
        
        nodeInfo.style.display = 'block';
    }
    
    handleNodeHover(node, prevNode) {
        // Highlight connected nodes and links
        if (node) {
            this.graph.nodeColor(this.graph.nodeColor().map((color, i) => {
                const currentNode = this.graph.graphData().nodes[i];
                return currentNode.id === node.id ? '#ff0000' : color;
            }));
        }
    }
    
    handleRealtimeUpdate(data) {
        if (data.type === 'new_trace') {
            this.loadAvailableTraces();
        } else if (data.type === 'trace_update' && this.currentTrace && 
                  data.trace_id === this.currentTrace.trace.trace_id) {
            this.loadTrace(data.trace_id);
        }
    }
    
    setupEventListeners() {
        document.getElementById('trace-select').addEventListener('change', (e) => {
            this.loadTrace(e.target.value);
        });
        
        document.getElementById('layout-type').addEventListener('change', (e) => {
            this.updateLayout(e.target.value);
        });
        
        document.getElementById('node-size').addEventListener('input', (e) => {
            this.updateNodeSize(parseInt(e.target.value));
        });
        
        document.getElementById('link-distance').addEventListener('input', (e) => {
            this.updateLinkDistance(parseInt(e.target.value));
        });
    }
    
    updateLayout(layoutType) {
        // Implement different layout algorithms
        switch (layoutType) {
            case 'hierarchical':
                this.graph.d3Force('y', d3.forceY().strength(0.1));
                break;
            case 'circular':
                this.graph.d3Force('radial', d3.forceRadial(100));
                break;
            case 'tree':
                // Implement tree layout
                break;
            default:
                // Force directed (default)
                this.graph.d3Force('y', null);
                this.graph.d3Force('radial', null);
        }
        this.graph.d3ReheatSimulation();
    }
    
    updateNodeSize(size) {
        this.graph.nodeVal(node => node.size * (size / 20));
    }
    
    updateLinkDistance(distance) {
        this.graph.d3Force('link', d3.forceLink().distance(distance));
        this.graph.d3ReheatSimulation();
    }
    
    showLoading(show) {
        document.getElementById('loading').style.display = show ? 'block' : 'none';
    }
}

// Animation functions
function playReasoningAnimation() {
    // Implement step-by-step reasoning animation
    console.log('Playing reasoning animation...');
}

function pauseAnimation() {
    console.log('Pausing animation...');
}

function resetGraph() {
    console.log('Resetting graph...');
    location.reload();
}

// Initialize the visualizer
document.addEventListener('DOMContentLoaded', () => {
    window.reasoningViz = new ReasoningGraphVisualizer();
}); 