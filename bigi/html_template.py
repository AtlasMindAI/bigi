HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BiGI - Impact Graph Visualization</title>
    <!-- Google Fonts & Mermaid.js -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10.2.4/dist/mermaid.min.js"></script>
    <style>
        :root {
            --bg-color: #060913;
            --panel-bg: rgba(10, 15, 30, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
            --accent-rule: #6366f1; /* Indigo */
            --accent-func: #10b981; /* Emerald */
            --accent-unres: #f43f5e; /* Rose */
            --accent-glow: rgba(99, 102, 241, 0.15);
            --panel-blur: blur(20px);
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }

        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: radial-gradient(circle at 50% 50%, #080d1a 0%, #03050a 100%);
            color: var(--text-main);
            overflow: hidden;
            height: 100vh;
            display: flex;
        }

        #canvas-container {
            flex-grow: 1;
            height: 100%;
            position: relative;
            cursor: grab;
        }

        #canvas-container:active {
            cursor: grabbing;
        }

        canvas {
            display: block;
            width: 100%;
            height: 100%;
        }

        /* UI Panels */
        .panel {
            position: absolute;
            background: rgba(8, 12, 24, 0.75);
            backdrop-filter: blur(25px);
            -webkit-backdrop-filter: blur(25px);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 24px;
            box-shadow: 0 20px 50px -10px rgba(0, 0, 0, 0.8), inset 0 1px 1px rgba(255, 255, 255, 0.05);
            z-index: 10;
            max-height: 90vh;
            overflow-y: auto;
            transition: transform 0.4s cubic-bezier(0.16, 1, 0.3, 1), opacity 0.4s, border-color 0.3s;
        }

        .panel::-webkit-scrollbar {
            width: 6px;
        }
        .panel::-webkit-scrollbar-track {
            background: transparent;
        }
        .panel::-webkit-scrollbar-thumb {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 3px;
        }

        #left-panel {
            top: 20px;
            left: 20px;
            width: 320px;
            display: flex;
            flex-direction: column;
            gap: 18px;
        }

        #left-panel.collapsed {
            transform: translateX(-350px);
            opacity: 0;
            pointer-events: none;
        }

        #right-panel {
            top: 20px;
            right: 20px;
            width: 350px;
            transform: translateX(380px);
            opacity: 0;
            pointer-events: none;
        }

        #right-panel.active {
            transform: translateX(0);
            opacity: 1;
            pointer-events: all;
        }

        /* Floating panel toggle buttons */
        .fab-btn {
            position: absolute;
            top: 30px;
            width: 36px;
            height: 36px;
            border-radius: 50%;
            background: rgba(17, 24, 39, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            z-index: 11;
            transition: all 0.4s cubic-bezier(0.16, 1, 0.3, 1);
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
            font-size: 0.85rem;
        }

        .fab-btn:hover {
            background: #1f2937;
            border-color: rgba(255, 255, 255, 0.2);
            transform: scale(1.05);
        }

        #toggle-left {
            left: 360px;
        }

        #toggle-left.collapsed {
            left: 20px;
        }

        .panel-close-btn {
            float: right;
            background: transparent;
            border: none;
            color: var(--text-muted);
            font-size: 1.2rem;
            cursor: pointer;
            transition: color 0.2s;
            line-height: 1;
        }

        .panel-close-btn:hover {
            color: var(--text-main);
        }

        h2 {
            font-family: 'Outfit', sans-serif;
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin-bottom: 5px;
            color: #ffffff;
            display: inline-block;
        }

        .subtitle {
            font-size: 0.7rem;
            color: var(--text-muted);
            margin-top: -3px;
            margin-bottom: 5px;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        /* Search input */
        .search-box {
            position: relative;
            width: 100%;
        }

        .search-box input {
            width: 100%;
            background: rgba(0, 0, 0, 0.3);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 10px 14px;
            color: var(--text-main);
            font-size: 0.85rem;
            outline: none;
            transition: all 0.2s;
        }

        .search-box input:focus {
            border-color: var(--accent-rule);
            background: rgba(0, 0, 0, 0.5);
            box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
        }

        /* Legend */
        .legend-item {
            display: flex;
            align-items: center;
            gap: 12px;
            font-size: 0.8rem;
            margin-bottom: 10px;
        }

        .legend-color {
            width: 10px;
            height: 10px;
            border-radius: 50%;
        }

        .color-rule { background-color: var(--accent-rule); box-shadow: 0 0 8px var(--accent-rule); }
        .color-func { background-color: var(--accent-func); box-shadow: 0 0 8px var(--accent-func); }
        .color-unres { background-color: var(--accent-unres); box-shadow: 0 0 8px var(--accent-unres); }

        /* Node List */
        .node-list-container {
            display: flex;
            flex-direction: column;
            gap: 5px;
            max-height: 220px;
            overflow-y: auto;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 8px;
            background: rgba(0, 0, 0, 0.25);
        }

        .node-item {
            padding: 8px 12px;
            border-radius: 6px;
            font-size: 0.8rem;
            cursor: pointer;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: all 0.2s;
            border: 1px solid transparent;
        }

        .node-item:hover {
            background: rgba(255, 255, 255, 0.04);
            border-color: rgba(255, 255, 255, 0.05);
        }

        .badge {
            font-size: 0.6rem;
            padding: 2px 6px;
            border-radius: 4px;
            font-weight: 600;
            letter-spacing: 0.02em;
        }

        .badge-rule { background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.2); }
        .badge-func { background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.2); }
        .badge-unres { background: rgba(244, 63, 94, 0.15); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.2); }

        /* Details Panel Content */
        .detail-header {
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 16px;
            margin-bottom: 16px;
        }

        .detail-title {
            font-size: 1.05rem;
            font-weight: 700;
            word-break: break-all;
            color: #ffffff;
        }

        .detail-meta {
            font-size: 0.65rem;
            color: var(--text-muted);
            margin-top: 5px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
        }

        .section-title {
            font-size: 0.75rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--text-muted);
            margin-top: 20px;
            margin-bottom: 10px;
        }

        .detail-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 6px;
            font-size: 0.78rem;
        }

        .detail-list li {
            background: rgba(255, 255, 255, 0.02);
            border: 1px solid var(--border-color);
            padding: 10px 14px;
            border-radius: 8px;
            word-break: break-all;
        }

        .code-container {
            background: #090d16 !important;
            border: 1px solid rgba(255, 255, 255, 0.08) !important;
            border-radius: 6px;
            padding: 10px;
            font-family: monospace;
            font-size: 0.72rem;
            color: #a7f3d0;
            overflow-x: auto;
            max-height: 250px;
            margin-top: 10px;
            white-space: pre;
            line-height: 1.4;
        }

        /* Tabbed navigation styling */
        .tabs {
            display: flex;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 16px;
            gap: 4px;
        }
        .tab-btn {
            padding: 8px 12px;
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            user-select: none;
        }
        .tab-btn:hover {
            color: var(--text-main);
        }
        .tab-btn.active {
            color: #818cf8;
            border-bottom-color: #818cf8;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }

        /* Left Panel tabbed navigation styling */
        .left-tabs {
            display: flex;
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 14px;
            margin-top: 14px;
            gap: 4px;
        }
        .left-tab-btn {
            flex: 1;
            text-align: center;
            padding: 8px 6px;
            font-size: 0.72rem;
            font-weight: 600;
            color: var(--text-muted);
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s ease;
            user-select: none;
        }
        .left-tab-btn:hover {
            color: var(--text-main);
        }
        .left-tab-btn.active {
            color: var(--highlight-color);
            border-bottom-color: var(--highlight-color);
        }
        .git-item {
            cursor: pointer;
            transition: all 0.15s ease;
        }
        .git-item:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
            border-color: rgba(249, 115, 22, 0.4) !important;
        }

        .detail-edge-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .btn {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--border-color);
            color: var(--text-main);
            padding: 8px 14px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.8rem;
            transition: all 0.2s;
        }

        .btn:hover {
            background: rgba(255, 255, 255, 0.08);
            border-color: rgba(255, 255, 255, 0.15);
        }

        #controls {
            position: absolute;
            bottom: 20px;
            left: 20px;
            display: flex;
            gap: 10px;
            z-index: 10;
        }

        #path-tracing-hud {
            display: none;
            position: absolute;
            top: 20px;
            left: 50%;
            transform: translateX(-50%);
            align-items: center;
            gap: 12px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(99, 102, 241, 0.45);
            border-radius: 20px;
            padding: 6px 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            backdrop-filter: blur(12px);
            z-index: 20;
            font-size: 0.8rem;
            pointer-events: auto;
            animation: slideDown 0.3s ease-out;
            color: #cbd5e1;
        }

        @keyframes slideDown {
            from { transform: translate(-50%, -20px); opacity: 0; }
            to { transform: translate(-50%, 0); opacity: 1; }
        }
    </style>
</head>
<body>
    <div id="canvas-container">
        <canvas id="graphCanvas"></canvas>
    </div>

    <!-- Path Tracing HUD Overlay -->
    <div id="path-tracing-hud">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 0.9rem;">🏁</span>
            <span style="color: var(--text-muted); font-size: 0.72rem;">Start:</span>
            <span id="path-start-name" style="color: #a5b4fc; font-weight: 600; font-family: monospace;">-</span>
        </div>
        <div style="color: rgba(255,255,255,0.25); font-weight: 300;">🡒</div>
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 0.9rem;">🎯</span>
            <span style="color: var(--text-muted); font-size: 0.72rem;">End:</span>
            <span id="path-end-name" style="color: #f472b6; font-weight: 600; font-family: monospace;">-</span>
        </div>
        <div style="width: 1px; height: 16px; background: rgba(255,255,255,0.15); margin: 0 4px;"></div>
        <button class="btn" style="padding: 2px 8px; font-size: 0.65rem; background: rgba(244, 63, 94, 0.15); border: 1px solid rgba(244, 63, 94, 0.3); color: #fda4af;" onclick="clearPathTracing()">Clear</button>
    </div>

    <!-- Controls -->
    <div id="controls">
        <button class="btn" id="btn-pause">Pause Physics</button>
        <button class="btn" id="btn-reset">Reset Layout</button>
        <button class="btn" id="btn-layout">Layout: Swimlanes</button>
        <button class="btn" id="btn-export">Export PNG</button>
    </div>

    <!-- Minimap overlay -->
    <div id="minimap-container" style="position: absolute; bottom: 20px; right: 20px; width: 150px; height: 100px; background: rgba(10, 15, 30, 0.75); border: 1px solid var(--border-color); border-radius: 8px; backdrop-filter: blur(10px); z-index: 10; overflow: hidden; pointer-events: none;">
        <canvas id="minimapCanvas" style="width: 100%; height: 100%; display: block;"></canvas>
    </div>

    <!-- Toggle Left Panel button -->
    <button id="toggle-left" class="fab-btn">◀</button>

    <!-- Left Panel: Legend & Search & Info -->
    <div class="panel" id="left-panel">
        <div>
            <button class="panel-close-btn" id="close-left-btn">×</button>
            <h2 style="display: flex; align-items: center; gap: 8px; font-size: 1.1rem; letter-spacing: -0.01em;">
                <span style="font-size: 1.25rem;">🧬</span> BiGI Impact Graph
            </h2>
            <div class="subtitle" style="font-size: 0.65rem; color: #6366f1; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; margin-top: 3px;">Cross-Layer Genomic Index</div>
        </div>

        <div class="left-tabs">
            <div id="left-tab-btn-search" class="left-tab-btn active" style="--highlight-color: #818cf8;" onclick="switchLeftTab('search')">🔍 Search</div>
            <div id="left-tab-btn-git" class="left-tab-btn" style="--highlight-color: #fdba74; position: relative;" onclick="switchLeftTab('git')">
                🍊 Git Risk
                <span id="git-changes-badge" style="display: none; background: #f97316; color: white; font-size: 0.58rem; font-weight: bold; padding: 1px 5px; border-radius: 10px; margin-left: 4px; box-shadow: 0 0 5px rgba(249, 115, 22, 0.4);">0</span>
            </div>
        </div>

        <div id="left-content-search" style="display: block;">
            <div class="search-box">
                <input type="text" id="search-input" placeholder="Search rules or functions...">
            </div>

            <div>
                <div class="section-title">Modalities</div>
                <div class="legend-item">
                    <div class="legend-color color-rule"></div>
                    <span>Pipeline Rule</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color color-func"></div>
                    <span>R Function Definition</span>
                </div>
                <div class="legend-item">
                    <div class="legend-color color-unres"></div>
                    <span>External / Unresolved</span>
                </div>
            </div>

            <div>
                <div class="section-title">Filters</div>
                <div class="legend-item">
                    <input type="checkbox" id="hide-unresolved-cb" checked style="margin-right: 8px; cursor: pointer;">
                    <label for="hide-unresolved-cb" style="cursor: pointer; font-size: 0.8rem; user-select: none;">Hide Unresolved Links</label>
                </div>
                <div class="legend-item" style="margin-top: 8px;">
                    <input type="checkbox" id="focus-mode-cb" style="margin-right: 8px; cursor: pointer;">
                    <label for="focus-mode-cb" style="cursor: pointer; font-size: 0.8rem; user-select: none; color: #818cf8; font-weight: 500; display: flex; align-items: center; gap: 4px;">🎯 Focus Mode (Selected thread)</label>
                </div>
                <div class="legend-item" id="git-filter-container" style="display: none; margin-top: 8px;">
                    <input type="checkbox" id="git-impact-cb" style="margin-right: 8px; cursor: pointer;">
                    <label for="git-impact-cb" style="cursor: pointer; font-size: 0.8rem; user-select: none; color: #fdba74; display: flex; align-items: center; gap: 4px; font-weight: 500;">🍊 Git Changes Impact</label>
                </div>
            </div>

            <div>
                <div class="section-title">Index Nodes</div>
                <div class="node-list-container" id="node-list">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>

        <div id="left-content-git" style="display: none;">
            <div id="git-dashboard-intro" style="font-size: 0.72rem; color: var(--text-muted); line-height: 1.45; margin-bottom: 12px; padding: 8px; background: rgba(249, 115, 22, 0.05); border: 1px dashed rgba(249, 115, 22, 0.2); border-radius: 6px;">
                ⚠️ No modified files detected in Git. Modify rules or functions in your repository to calculate downstream risk propagation.
            </div>
            
            <div id="git-dashboard-active" style="display: none;">
                <div style="display: flex; flex-direction: column; gap: 10px; margin-bottom: 15px;">
                    <div style="display:flex; justify-content:space-between; align-items:center; background: rgba(0,0,0,0.25); border: 1px solid var(--border-color); padding: 8px 12px; border-radius: 6px;">
                        <span style="font-size:0.7rem; color: var(--text-muted);">Impact Pruned View:</span>
                        <div style="display: flex; align-items: center; cursor: pointer;">
                            <input type="checkbox" id="git-dashboard-toggle-cb" style="cursor: pointer; margin-right: 6px;">
                            <label for="git-dashboard-toggle-cb" style="font-size: 0.7rem; color: #fdba74; font-weight: 600; cursor: pointer; user-select:none;">Only Show Risk Radius</label>
                        </div>
                    </div>
                </div>

                <div class="section-title" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span>Modified Entrypoints</span>
                    <span id="git-modified-count" style="font-size: 0.65rem; padding: 2px 6px; background: rgba(239, 68, 68, 0.2); color: #f87171; border-radius: 10px; font-weight: 700;">0</span>
                </div>
                <div id="git-entrypoints-list" style="display: flex; flex-direction: column; gap: 6px; margin-bottom: 15px; max-height: 160px; overflow-y: auto; padding: 2px;">
                    <!-- Populated by JS -->
                </div>

                <div class="section-title" style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span>Downstream Blast Radius</span>
                    <span id="git-impacted-count" style="font-size: 0.65rem; padding: 2px 6px; background: rgba(249, 115, 22, 0.2); color: #fdba74; border-radius: 10px; font-weight: 700;">0</span>
                </div>
                <div id="git-impacted-list" style="display: flex; flex-direction: column; gap: 6px; max-height: 240px; overflow-y: auto; padding: 2px;">
                    <!-- Populated by JS -->
                </div>
            </div>
        </div>
    </div>

    <!-- Right Panel: Node details Inspector -->
    <div class="panel" id="right-panel">
        <button class="panel-close-btn" id="close-right-btn">×</button>
        <div id="detail-content">
            <!-- Populated by JS -->
        </div>
    </div>

    <script>
        // Inject data here from Python
        const graphData = // __DATA__;
        const WASM_BASE64 = "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IANJIggbIQYgASACSSEHIAAgBCAIGyEIAkAgACgCECIBDQAgACgCFCEBCyADIAYgBxshAyAEIAggBxshBCABIQAgAQ0ACwsgBEUNAAJAQQAoApSJwIAAIgAgAkkNACADIAAgAmtPDQELIAQoAhghBgJAAkACQCAEKAIMIgAgBEcNACAEQRRBECAEKAIUIgAbaigCACIBDQFBACEADAILIAQoAggiASAANgIMIAAgATYCCAwBCyAEQRRqIARBEGogABshBwNAIAchCCABIgBBFGogAEEQaiAAKAIUIgEbIQcgAEEUQRAgARtqKAIAIgENAAsgCEEANgIACwJAIAZFDQACQAJAAkAgBCAEKAIcQQJ0QfSFwIAAaiIBKAIARg0AAkAgBigCECAERg0AIAYgADYCFCAADQIMBAsgBiAANgIQIAANAQwDCyABIAA2AgAgAEUNAQsgACAGNgIYAkAgBCgCECIBRQ0AIAAgATYCECABIAA2AhgLIAQoAhQiAUUNASAAIAE2AhQgASAANgIYDAELQQBBACgCkInAgABBfiAEKAIcd3E2ApCJwIAACwJAAkAgA0EQSQ0AIAQgAkEDcjYCBCAEIAJqIgAgA0EBcjYCBCAAIANqIAM2AgACQCADQYACSQ0AIAAgAxCogICAAAwCCwJAAkBBACgCjInAgAAiAUEBIANBA3Z0IgdxDQBBACABIAdyNgKMicCAACADQfgBcUGEh8CAAGoiAyEBDAELIANB+AFxIgNBhIfAgABqIQEgA0GMh8CAAGooAgAhAwsgASAANgIIIAMgADYCDCAAIAE2AgwgACADNgIIDAELIAQgAyACaiIAQQNyNgIEIAQgAGoiACAAKAIEQQFyNgIECyAEQQhqIgANAQtBACgClInAgAAiACACTw0BAkBBACgCmInAgAAiACACSw0AAkAgAkGvgARqIgRBEHZAACIDQX9HDQBBAA8LQQAhACADQRB0IgFFDQFBAEEAKAKkicCAACAEQYCAfHEiAEFwaiAAIAFBACAAa0YbIghqIgA2AqSJwIAAQQAgAEEAKAKoicCAACIDIAAgA0sbNgKoicCAAAJAAkACQAJAAkBBACgCoInAgAAiA0UNAEH0hsCAACEAA0AgACgCACIEIAAoAgQiB2ogAUYNAiAAKAIIIgANAAwDCwsCQAJAQQAoArCJwIAAIgBF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IAAgA2ogAzYCAAJAIANBgAJJDQAgACADEKiAgIAADAgLAkACQEEAKAKMicCAACICQQEgA0EDdnQiBHENAEEAIAIgBHI2AoyJwIAAIANB+AFxQYSHwIAAaiIDIQIMAQsgA0H4AXEiA0GEh8CAAGohAiADQYyHwIAAaigCACEDCyACIAA2AgggAyAANgIMIAAgAjYCDCAAIAM2AggMBwsgACAHIAhqNgIEQQBBACgCoInAgAAiAEEPakF4cSIDQXhqIgQ2AqCJwIAAQQAgACADa0EAKAKYicCAACAIaiIDakEIaiIBNgKYicCAACAEIAFBAXI2AgQgACADakEoNgIEQQBBgICAATYCrInAgAALQQAhAEEAKAKYicCAACIDIAJNDQFBACADIAJrIgM2ApiJwIAAQQBBACgCoInAgAAiACACaiIENgKgicCAACAEIANBAXI2AgQgACACQQNyNgIEIABBCGoPC0EAIAAgAmsiAzYCmInAgABBAEEAKAKgicCAACIAIAJqIgQ2AqCJwIAAIAQgA0EBcjYCBCAAIAJBA3I2AgQgAEEIaiEACyAADwtBACgCnInAgAAhAwJAAkAgACACayIEQQ9LDQBBAEEANgKcicCAAEEAQQA2ApSJwIAAIAMgAEEDcjYCBCADIABqIgAgACgCBEEBcjYCBAwBC0EAIAQ2ApSJwIAAQQAgAyACaiIBNgKcicCAACABIARBAXI2AgQgAyAAaiAENgIAIAMgAkEDcjYCBAsgA0EIag8LQQAgADYCoInAgABBAEEAKAKYicCAACADaiIDNgKYicCAACAAIANBAXI2AgQMAQtBACAANgKcicCAAEEAQQAoApSJwIAAIANqIgM2ApSJwIAAIAAgA0EBcjYCBCAAIANqIAM2AgALIAFBCGoLmQIBBH8jgICAgABBEGsiAySAgICAAAJAAkACQCABRQ0AIAJBAnQhAUEAIQQCQCACQf////8DSw0AIAFB/P///wdLDQACQCABDQBBACEFQQQhBgwDCyACIQUgARCIgICAACIGDQJBBCEECyAEIAEQg4CAgAAACyADQQRqIAJBAUEEQQQQhoCAgAAgAygCCCEFAkAgAygCBEEBRg0AIAMoAgwhBgwCCyAFIAMoAgwQg4CAgAAACwJAAkAgAkECSQ0AIAJBf2ohBCAGIQEDQCABQX82AgAgAUEE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AgwgA0EBOwEcIAMgAjYCGCADIANBDGo2AhQgA0EUahCkgICAAAAL1AYBBX8gAEF4aiIBIABBfGooAgAiAkF4cSIAaiEDAkACQCACQQFxDQAgAkECcUUNASABKAIAIgIgAGohAAJAIAEgAmsiAUEAKAKcicCAAEcNACADKAIEQQNxQQNHDQFBACAANgKUicCAACADIAMoAgRBfnE2AgQgASAAQQFyNgIEIAMgADYCAA8LIAEgAhCggICAAAsCQAJAAkACQAJAAkAgAygCBCICQQJxDQAgA0EAKAKgicCAAEYNAiADQQAoApyJwIAARg0DIAMgAkF4cSICEKCAgIAAIAEgAiAAaiIAQQFyNgIEIAEgAGogADYCACABQQAoApyJwIAARw0BQQAgADYClInAgAAPCyADIAJBfnE2AgQgASAAQQFyNgIEIAEgAGogADYCAAsgAEGAAkkNAiABIAAQqICAgABBACEBQQBBACgCtInAgABBf2oiADYCtInAgAAgAA0EAkBBACgC/IbAgAAiAEUNAEEAIQEDQCABQQFqIQEgACgCCCIADQALC0EAIAFB/x8gAUH/H0sbNgK0icCAAA8LQQAgATYCoInAgABBAEEAKAKYicCAACAAaiIANgKYicCAACABIABBAXI2AgQCQCABQQAoApyJwIAARw0AQQBBADYClInAgABBAEEANgKcicCAAAsgAEEAKAKsicCAACIETQ0DQQAoAqCJwIAAIgBFDQNBACECQQAoApiJwIAAIgVBKUkNAkH0hsCAACEBA0ACQCABKAIAIgMgAEsNACAAIAMgASgCBGpJDQQLIAEoAgghAQwACwtBACABNgKcicCAAEEAQQAoApSJwIAAIABqIgA2ApSJwIAAIAEgAEEBcjYCBCABIABqIAA2AgAPCwJAAkBBACgCjInAgAAiA0EBIABBA3Z0IgJxDQBBACADIAJyNgKMicCAACAAQfgBcUGEh8CAAGoiACEDDAELIABB+AFxIgBBhIfAgABqIQMgAEGMh8CAAGooAgAhAAsgAyABNgIIIAAgATYCDCABIAM2AgwgASAANgIIDwsCQEEAKAL8hsCAACIBRQ0AQQAhAgNAIAJBAWohAiABKAIIIgENAAsLQQAgAkH/HyACQf8fSxs2ArSJwIAAIAUgBE0NAEEAQX82AqyJwIAACwsQACAAQd0A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aiEAIAUgByADKAIQEYCAgIAAgICAgABFDQAMAwsLQQEhBiADIAogCyAFKAIMEYGAgIAAgICAgAANASABIA03AghBACEGDAELQQEhBiABKAIAIgAgASgCBCIDIAQgCRCigICAAA0AIAAgCiALIAMoAgwRgYCAgACAgICAACEGCyACQRBqJICAgIAAIAYPC0F+QQpBqITAgAAQmYCAgAAACzgCAX8BfiOAgICAAEEQayIBJICAgIAAIAApAgAhAiABIAA2AgwgASACNwIEIAFBBGoQqYCAgAAACwkAIABBADYCAAuZAQECfyOAgICAAEEQayIEJICAgIAAQQBBACgCxInAgAAiBUEBajYCxInAgAACQCAFQQBIDQACQAJAQQAtAMCJwIAADQBBAEEAKAK8icCAAEEBajYCvInAgABBACgCyInAgABBf0oNAQwCCyAEQQhqIAAgARGCgICAAICAgIAAAAtBAEEAOgDAicCAACACRQ0AEKeAgIAAAAsACwMAAAvDAgEEf0EfIQICQCABQf///wdLDQAgAUEmIAFBCHZnIgJrdkEBcSACQQF0a0E+aiECCyAAQgA3AhAgACACNgIcIAJBAnRB9IXAgABqIQMCQEEAKAKQicCAAEEBIAJ0IgRxDQAgAyAANgIAIAAgAzYCGCAAIAA2AgwgACAANgIIQQBBACgCkInAgAAgBHI2ApCJwIAADwsCQAJAAkAgAygCACIEKAIEQXhxIAFHDQAgBCECDAELIAFBAEEZIAJBAXZrIAJBH0YbdCEDA0AgBCADQR12QQRxaiIFKAIQIgJFDQIgA0EBdCEDIAIhBCACKAIEQXhxIAFHDQALCyACKAIIIgMgADYCDCACIAA2AgggAEEANgIYIAAgAjYCDCAAIAM2AggPCyAFQRBqIAA2AgAgACAENgIYIAAgADYCDCAAIAA2AggLCwAgABCqgICAAAALjwEBA38jgICAgABBEGsiASSAgICAAAJAIAAoAgAiAigCBCIDQQFxDQAgAUGAgICAeDYCACABIAA2AgwgAUGCgICAACAAKAIIIgAtAAggAC0ACRCmgICAAAALIAIoAgAhAiABIANBAXY2AgQgASACNgIAIAFBg4CAgAAgACgCCCIALQAIIAAtAAkQpoCAgAAACwwAIAAgASkCADcDAAsNACAAIAEQrYCAgAAACw4AQQBBAToAuInAgAAACwvOBQIAQYCAwAALuAUgaW5kZXggb3V0IG9mIGJvdW5kczogdGhlIGxlbiBpcyDAEiBidXQgdGhlIGluZGV4IGlzIMAAbGlicmFyeS9jb3JlL3NyYy9mbXQvbnVtLnJzAGxpYnJhcnkvYWxsb2Mvc3JjL3Jhd192ZWMvbW9kLnJzAC9ydXN0L2RlcHMvZGxtYWxsb2MtMC4yLjExL3NyYy9kbG1hbGxvYy5ycwBzcmMvbGliLnJzAAAAnwAQAAoAAACkAAAAFAAAAJ8AEAAKAAAAswAAACoAAACfABAACgAAALoAAAArAAAAnwAQAAoAAACXAAAAFAAAAJ8AEAAKAAAAngAAABsAAACfABAACgAAAO8AAAAQAAAAnwAQAAoAAADkAAAAEAAAAJ8AEAAKAAAAzQAAABQAAACfABAACgAAAM0AAAAqAAAAY2FwYWNpdHkgb3ZlcmZsb3cAAABTABAAIAAAABwAAAAFAAAAMDAwMTAyMDMwNDA1MDYwNzA4MDkxMDExMTIxMzE0MTUxNjE3MTgxOTIwMjEyMjIzMjQyNTI2MjcyODI5MzAzMTMyMzMzNDM1MzYzNzM4Mzk0MDQxNDI0MzQ0NDU0NjQ3NDg0OTUwNTE1MjUzNTQ1NTU2NTc1ODU5NjA2MTYyNjM2NDY1NjY2NzY4Njk3MDcxNzI3Mzc0NzU3Njc3Nzg3OTgwODE4MjgzODQ4NTg2ODc4ODg5OTA5MTkyOTM5NDk1OTY5Nzk4OTk3ABAAGwAAAFcCAAAFAAAAYXNzZXJ0aW9uIGZhaWxlZDogcHNpemUgPj0gc2l6ZSArIG1pbl9vdmVyaGVhZAAAdAAQACoAAACxBAAACQAAAGFzc2VydGlvbiBmYWlsZWQ6IHBzaXplIDw9IHNpemUgKyBtYXhfb3ZlcmhlYWQAAHQAEAAqAAAAtwQAAA0AAAAAQbiFwAALBBXNWwcAzhEEbmFtZQASEXBoeXNpY3Nfd2FzbS53YXNtAYsRLgBFX1pONWFsbG9jM3ZlYzE2VmVjJExUJFQkQyRBJEdUJDE2aW50b19ib3hlZF9zbGljZTE3aDVhOTQ5OWU3NTdlOWU3M2JFASxfUk52Q3NkQmV6ekR3bWE1MV83X19fcnVzdGMxNF9fX3J1c3RfZGVhbGxvYwIsX1JOdkNzZEJlenpEd21hNTFfN19fX3J1c3RjMTRfX19ydXN0X3JlYWxsb2MDM19aTjVhbGxvYzdyYXdfdmVjMTJoYW5kbGVfZXJyb3IxN2gxZTEyOWVhNTkzMmQ4YWE4RQRFX1pONWFsbG9jM3ZlYzE2VmVjJExUJFQkQyRBJEdUJDE2aW50b19ib3hlZF9zbGljZTE3aDlkYTFlOTU3YzZiMzk4MjBFBStfWk41YWxsb2MzdmVjOWZyb21fZWxlbTE3aDBhZmI0NDlkMzU1NTU1NTBFBkxfWk41YWxsb2M3cmF3X3ZlYzIwUmF3VmVjSW5uZXIkTFQkQSRHVCQxNXRyeV9hbGxvY2F0ZV9pbjE3aDFlMDg3ZjQyMjE3NWE2NGRFBytfWk41YWxsb2MzdmVjOWZyb21fZWxlbTE3aDhkMDI0MWFjNjYyODU0ZDJFCENfWk44ZGxtYWxsb2M4ZGxtYWxsb2MxN0RsbWFsbG9jJExUJEEkR1QkNm1hbGxvYzE3aDYxOTEwNjdiN2NmMjkwYTdFCStfWk41YWxsb2MzdmVjOWZyb21fZWxlbTE3aDliMGQzN2Y5N2RjODcyZmRFCgthbGxvY19saW5rcwsLYWxsb2Nfbm9kZXMMDmdldF9hY3RpdmVfcHRyDQ5nZXRfaGVpZ2h0X3B0cg4TZ2V0X2xpbmtfYWN0aXZlX3B0cg8OZ2V0X3JhZGl1c19wdHIQC2dldF9zcmNfcHRyEQtnZXRfdGd0X3B0chIMZ2V0X3R5cGVfcHRyEwpnZXRfdnhfcHRyFApnZXRfdnlfcHRyFQ1nZXRfd2lkdGhfcHRyFglnZXRfeF9wdHIXCWdldF95X3B0chgPc3RlcF9zaW11bGF0aW9uGTpfWk40Y29yZTlwYW5pY2tpbmcxOHBhbmljX2JvdW5kc19jaGVjazE3aDJlNGUwYmYxNWZlMjBlZDZFGjdfWk41YWxsb2M1YWxsb2MxOGhhbmRsZV9hbGxvY19lcnJvcjE3aDdhYjFhM2RlZDA1ZWM3NzFFGzhfUk52Q3NkQmV6ekR3bWE1MV83X19fcnVzdGMyNl9fX3J1c3RfYWxsb2NfZXJyb3JfaGFuZGxlchw4X1pONWFsbG9jN3Jhd192ZWMxN2NhcGFjaXR5X292ZXJmbG93MTdoZGRlNmNkYTU3ODMyZmZjMkUdMF9aTjRjb3JlOXBhbmlja2luZzlwYW5pY19mbXQxN2g4MDZlNjQ3NzE1OTkwMTM4RR5BX1pOOGRsbWFsbG9jOGRsbWFsbG9jMTdEbG1hbGxvYyRMVCRBJEdUJDRmcmVlMTdoMjU3YjRiZDA3NTliNGJmYkUfLF9aTjRjb3JlOXBhbmlja2luZzVwYW5pYzE3aDRiMzQyOTg2NTA4MDRmM2ZFIEpfWk44ZGxtYWxsb2M4ZGxtYWxsb2MxN0RsbWFsbG9jJExUJEEkR1QkMTJ1bmxpbmtfY2h1bmsxN2g4ODM5M2NmM2ZkOTJjNWQ2RSFLX1pOOGRsbWFsbG9jOGRsbWFsbG9jMTdEbG1hbGxvYyRMVCRBJEdUJDEzZGlzcG9zZV9jaHVuazE3aGEzN2Y5NmQxNTcyMzEyYjlFIkZfWk40Y29yZTNmbXQ5Rm9ybWF0dGVyMTJwYWRfaW50ZWdyYWwxMndyaXRlX3ByZWZpeDE3aDgyZDIwODNjYzgxNTNmNWZFI2RfWk40Y29yZTNmbXQzbnVtM2ltcDU0XyRMVCRpbXBsJHUyMCRjb3JlLi5mbXQuLkRpc3BsYXkkdTIwJGZvciR1MjAkdXNpemUkR1QkM2ZtdDE3aDNiMGVjN2E5Yzc1NzYzYzBFJC5fUk52Q3NkQmV6ekR3bWE1MV83X19fcnVzdGMxN3J1c3RfYmVnaW5fdW53aW5kJTdfWk40Y29yZTVwYW5pYzEyUGFuaWNQYXlsb2FkNmFzX3N0cjE3aDAzYWRmZDY1ODRhNjhkZjhFJjZfWk4zc3RkOXBhbmlja2luZzE1cGFuaWNfd2l0aF9ob29rMTdoNTFjNWVkZWViNDhlNjlkM0UnJ19STnZDc2RCZXp6RHdtYTUxXzdfX19ydXN0YzEwcnVzdF9wYW5pYyhQX1pOOGRsbWFsbG9jOGRsbWFsbG9jMTdEbG1hbGxvYyRMVCRBJEdUJDE4aW5zZXJ0X2xhcmdlX2NodW5rMTdoNzg4ZGU2NGM2MjAwNzYzOEUpRV9aTjNzdGQzc3lzOWJhY2t0cmFjZTI2X19ydXN0X2VuZF9zaG9ydF9iYWNrdHJhY2UxN2g4ODAyMGNjZjc2ZDJkNjYxRSpSX1pOM3N0ZDlwYW5pY2tpbmcxM3BhbmljX2hhbmRsZXIyOF8kdTdiJCR1N2IkY2xvc3VyZSR1N2QkJHU3ZCQxN2hkZjhkNjU4NzkwY2NlZTRjRSt9X1pOOTNfJExUJHN0ZC4ucGFuaWNraW5nLi5wYW5pY19oYW5kbGVyLi5TdGF0aWNTdHJQYXlsb2FkJHUyMCRhcyR1MjAkY29yZS4ucGFuaWMuLlBhbmljUGF5bG9hZCRHVCQ2YXNfc3RyMTdoY2E5ZDdjZTgxOGNjYmVmOUUsKl9aTjNzdGQ1YWxsb2M4cnVzdF9vb20xN2gyZDcwODY3YTAxMmNhOGI4RS1FX1pOM3N0ZDNzeXM5YmFja3RyYWNlMjZfX3J1c3RfZW5kX3Nob3J0X2JhY2t0cmFjZTE3aDhmYTY5MWUyM2JlOWExYWRFBxIBAA9fX3N0YWNrX3BvaW50ZXIJEQIABy5yb2RhdGEBBS5kYXRhAE0JcHJvZHVjZXJzAghsYW5ndWFnZQEEUnVzdAAMcHJvY2Vzc2VkLWJ5AQVydXN0Yx0xLjkzLjEgKDAxZjZkZGY3NSAyMDI2LTAyLTExKQCUAQ90YXJnZXRfZmVhdHVyZXMIKwtidWxrLW1lbW9yeSsPYnVsay1tZW1vcnktb3B0KxZjYWxsLWluZGlyZWN0LW92ZXJsb25nKwptdWx0aXZhbHVlKw9tdXRhYmxlLWdsb2JhbHMrE25vbnRyYXBwaW5nLWZwdG9pbnQrD3JlZmVyZW5jZS10eXBlcysIc2lnbi1leHQ="; // __WASM_BASE64__

        // Setup Wasm Physics Fallback/Engine
        let wasmLoaded = false;
        let wasmInstance = null;
        let wasmExports = null;

        function base64ToUint8Array(base64) {
            const binaryString = atob(base64);
            const len = binaryString.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryString.charCodeAt(i);
            }
            return bytes;
        }

        function initWasmPhysics() {
            if (!WASM_BASE64) return;
            try {
                const wasmBytes = base64ToUint8Array(WASM_BASE64);
                WebAssembly.instantiate(wasmBytes, {}).then(result => {
                    wasmInstance = result.instance;
                    wasmExports = wasmInstance.exports;
                    
                    // Pre-allocate memory sizes
                    wasmExports.alloc_nodes(nodes.length);
                    wasmExports.alloc_links(links.length);
                    
                    // Setup type array pointers (static mapping)
                    const typeArray = new Int32Array(wasmExports.memory.buffer, wasmExports.get_type_ptr(), nodes.length);
                    nodes.forEach((n, idx) => {
                        typeArray[idx] = n.type === 'rule' ? 1 : n.type === 'function' ? 0 : 2;
                    });

                    // Setup links src/tgt indices
                    const srcArray = new Int32Array(wasmExports.memory.buffer, wasmExports.get_src_ptr(), links.length);
                    const tgtArray = new Int32Array(wasmExports.memory.buffer, wasmExports.get_tgt_ptr(), links.length);
                    const nodeIdToIndex = new Map(nodes.map((n, idx) => [n.id, idx]));
                    links.forEach((l, idx) => {
                        let sIdx = nodeIdToIndex.get(l.source);
                        let tIdx = nodeIdToIndex.get(l.target);
                        srcArray[idx] = sIdx !== undefined ? sIdx : -1;
                        tgtArray[idx] = tIdx !== undefined ? tIdx : -1;
                    });
                    
                    wasmLoaded = true;
                    console.log("BiGI Hybrid Wasm Physics Solver active (using spatial hash grid).");
                }).catch(err => {
                    console.warn("Could not instantiate Wasm Physics solver. Using JS fallback.", err);
                });
            } catch (e) {
                console.warn("Wasm not supported or error in decoding. Using JS fallback.", e);
            }
        }

        function runWasmSimulation(layoutMode, hideUnresolved, isFocusMode, selectedNodeActivePaths, selectedNode, hoveredNode, collapsedGroups, groups, draggedNode) {
            if (!wasmLoaded || !wasmExports) return false;
            if (!isSimulating) return true;
            
            const memBuffer = wasmExports.memory.buffer;
            
            const xArray = new Float32Array(memBuffer, wasmExports.get_x_ptr(), nodes.length);
            const yArray = new Float32Array(memBuffer, wasmExports.get_y_ptr(), nodes.length);
            const vxArray = new Float32Array(memBuffer, wasmExports.get_vx_ptr(), nodes.length);
            const vyArray = new Float32Array(memBuffer, wasmExports.get_vy_ptr(), nodes.length);
            const wArray = new Float32Array(memBuffer, wasmExports.get_width_ptr(), nodes.length);
            const hArray = new Float32Array(memBuffer, wasmExports.get_height_ptr(), nodes.length);
            const radArray = new Float32Array(memBuffer, wasmExports.get_radius_ptr(), nodes.length);
            const activeArray = new Uint8Array(memBuffer, wasmExports.get_active_ptr(), nodes.length);
            const linkActiveArray = new Uint8Array(memBuffer, wasmExports.get_link_active_ptr(), links.length);

            // Write inputs to Wasm
            nodes.forEach((n, idx) => {
                let vx = n.vx;
                let vy = n.vy;
                
                // Incorporate dynamic mouse repulsion in velocity vector before sending to Wasm
                if (mouseSim.x !== null && mouseSim.y !== null && n.width >= 1.0) {
                    let dx = n.x - mouseSim.x;
                    let dy = n.y - mouseSim.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 120 && dist > 1) {
                        let force = (120 - dist) * 0.12;
                        vx += (dx / dist) * force;
                        vy += (dy / dist) * force;
                    }
                }

                xArray[idx] = n.x;
                yArray[idx] = n.y;
                vxArray[idx] = vx;
                vyArray[idx] = vy;
                wArray[idx] = n.width;
                hArray[idx] = n.height;
                radArray[idx] = n.radius;
                
                let isActive = 1;
                if (hideUnresolved && n.type === 'unresolved') isActive = 0;
                else if (isFocusMode && !selectedNodeActivePaths.has(n.id)) isActive = 0;
                else if (n.width < 1.0) isActive = 0;
                activeArray[idx] = isActive;
            });

            links.forEach((l, idx) => {
                let isLActive = 1;
                const sNode = nodeIdMap[l.source];
                const tNode = nodeIdMap[l.target];
                if (!sNode || !tNode) {
                    isLActive = 0;
                } else if (hideUnresolved && (sNode.type === 'unresolved' || tNode.type === 'unresolved')) {
                    isLActive = 0;
                } else if (isFocusMode && (!selectedNodeActivePaths.has(l.source) || !selectedNodeActivePaths.has(l.target))) {
                    isLActive = 0;
                }
                linkActiveArray[idx] = isLActive;
            });

            // Step in Wasm
            const layoutModeVal = layoutMode === 'swimlane' ? 1 : 0;
            wasmExports.step_simulation(layoutModeVal, width, height);

            // Read coordinates back
            nodes.forEach((n, idx) => {
                if (activeArray[idx] === 1 && n !== draggedNode) {
                    n.x = xArray[idx];
                    n.y = yArray[idx];
                    n.vx = vxArray[idx];
                    n.vy = vyArray[idx];
                }
            });

            return true;
        }

        const canvas = document.getElementById("graphCanvas");
        const ctx = canvas.getContext("2d");
        const container = document.getElementById("canvas-container");

        let width = canvas.width = container.clientWidth;
        let height = canvas.height = container.clientHeight;

        window.addEventListener("resize", () => {
            width = canvas.width = container.clientWidth;
            height = canvas.height = container.clientHeight;
        });

        const rawNodes = graphData.nodes;
        const rawEdges = graphData.edges;

        const nodes = [];
        const nodeIdMap = {};

        // Convert dict nodes to array with layout properties
        // Pre-measure text widths to scale bounding box capsules
        Object.entries(rawNodes).forEach(([id, n]) => {
            // Measure text width using a temp estimation or standard canvas rules
            // (We will measure dynamically in canvas after font load, but initialize here)
            const nameLen = n.name.length;
            const w = Math.max(nameLen * 6.2 + 20, 60);
            const h = 20;
            const defaultRad = w / 2; // collision radius is half-width
            const node = {
                id: id,
                name: n.name,
                type: n.type,
                file: n.file,
                inputs: n.inputs || [],
                outputs: n.outputs || [],
                line_range: n.line_range || [],
                x: width / 2 + (Math.random() - 0.5) * 400,
                y: height / 2 + (Math.random() - 0.5) * 400,
                vx: 0,
                vy: 0,
                width: w,
                height: h,
                baseWidth: w,
                baseHeight: h,
                targetWidth: w,
                targetHeight: h,
                radius: defaultRad,
                baseRadius: defaultRad,
                targetRadius: defaultRad,
                code: n.code || "",
                git_modified: n.git_modified || false
            };
            nodes.push(node);
            nodeIdMap[id] = node;
        });

        function initNodeSizes() {
            ctx.font = "9px sans-serif";
            nodes.forEach(n => {
                const textWidth = ctx.measureText(n.name).width;
                const w = Math.max(textWidth + 24, 70);
                n.width = w;
                n.baseWidth = w;
                n.targetWidth = w;
                n.radius = w / 2;
                n.baseRadius = w / 2;
                n.targetRadius = w / 2;
            });
        }
        initNodeSizes();
        if (document.fonts) {
            document.fonts.ready.then(() => {
                initNodeSizes();
            });
        }

        // Convert edges
        const links = rawEdges.map(e => ({
            source: e.source,
            target: e.target,
            confidence: e.confidence,
            type: e.type,
            label: e.label,
            detail: e.detail
        })).filter(l => nodeIdMap[l.source] && nodeIdMap[l.target]);

        // State variables
        let selectedNode = null;
        let selectedNodeActivePaths = new Set();
        let selectedNodeActiveLinks = new Set();
        let collapsedGroups = new Set();
        let hoveredNode = null;
        let isSimulating = true;
        let transform = { x: 0, y: 0, k: 1 };
        let isDraggingCanvas = false;
        let dragStart = { x: 0, y: 0 };
        let draggedNode = null;
        let mouseSim = { x: null, y: null };
        let layoutMode = 'swimlane'; // 'swimlane' or 'free'

        // Git Changes Impact Tracker State
        let gitRiskScores = {}; // Map of node.id -> shortest path distance from modified node (0 is modified, 1 is direct downstream, etc.)
        let gitImpactNodes = new Set();
        let hasGitChanges = false;
        let gitImpactOnly = false;

        // Interactive Path Tracing State
        let pathStartNode = null;
        let pathEndNode = null;
        let pathTracingNodes = new Set();
        let pathTracingLinks = new Set();

        function calculateGitImpact() {
            const modifiedIds = [];
            let gitModifiedCount = 0;
            nodes.forEach(n => {
                if (n.git_modified) {
                    modifiedIds.push(n.id);
                    hasGitChanges = true;
                    gitModifiedCount++;
                }
            });

            if (hasGitChanges) {
                document.getElementById("git-filter-container").style.display = "flex";
                const badge = document.getElementById("git-changes-badge");
                if (badge) {
                    badge.style.display = "inline-flex";
                    badge.textContent = gitModifiedCount;
                }
                const dashIntro = document.getElementById("git-dashboard-intro");
                const dashActive = document.getElementById("git-dashboard-active");
                if (dashIntro && dashActive) {
                    dashIntro.style.display = "none";
                    dashActive.style.display = "block";
                }
            } else {
                const badge = document.getElementById("git-changes-badge");
                if (badge) badge.style.display = "none";
                const dashIntro = document.getElementById("git-dashboard-intro");
                const dashActive = document.getElementById("git-dashboard-active");
                if (dashIntro && dashActive) {
                    dashIntro.style.display = "block";
                    dashActive.style.display = "none";
                }
            }

            const adj = {};
            links.forEach(l => {
                adj[l.source] = adj[l.source] || [];
                adj[l.source].push(l.target);
            });

            gitRiskScores = {};
            const queue = [];
            modifiedIds.forEach(id => {
                gitRiskScores[id] = 0;
                queue.push(id);
            });

            while (queue.length > 0) {
                const curr = queue.shift();
                const currDist = gitRiskScores[curr];
                const children = adj[curr] || [];
                children.forEach(child => {
                    if (!(child in gitRiskScores)) {
                        gitRiskScores[child] = currDist + 1;
                        queue.push(child);
                    }
                });
            }
            gitImpactNodes = new Set(Object.keys(gitRiskScores));
        }
        calculateGitImpact();
        initWasmPhysics();

        // Left Panel Tab Switching
        function switchLeftTab(tabId) {
            document.querySelectorAll('.left-tab-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById(`left-tab-btn-${tabId}`).classList.add('active');
            
            if (tabId === 'search') {
                document.getElementById('left-content-search').style.display = 'block';
                document.getElementById('left-content-git').style.display = 'none';
            } else {
                document.getElementById('left-content-search').style.display = 'none';
                document.getElementById('left-content-git').style.display = 'block';
                populateGitDashboard();
            }
        }

        // Populate Git Risk / Blast Radius Dashboard
        function populateGitDashboard() {
            const entrypointList = document.getElementById("git-entrypoints-list");
            const impactedList = document.getElementById("git-impacted-list");
            if (!entrypointList || !impactedList) return;

            entrypointList.innerHTML = "";
            impactedList.innerHTML = "";

            const modifiedNodes = [];
            const impactedNodes = [];

            nodes.forEach(n => {
                if (n.git_modified) {
                    modifiedNodes.push(n);
                } else if (gitImpactNodes.has(n.id)) {
                    impactedNodes.push(n);
                }
            });

            // Sort lists
            modifiedNodes.sort((a, b) => a.name.localeCompare(b.name));
            impactedNodes.sort((a, b) => {
                const distA = gitRiskScores[a.id] || 999;
                const distB = gitRiskScores[b.id] || 999;
                if (distA !== distB) return distA - distB;
                return a.name.localeCompare(b.name);
            });

            // Update header counts
            document.getElementById("git-modified-count").textContent = modifiedNodes.length;
            document.getElementById("git-impacted-count").textContent = impactedNodes.length;

            if (modifiedNodes.length === 0) {
                entrypointList.innerHTML = `<div style="color:var(--text-muted); font-size:0.65rem; text-align:center; padding:10px;">No entrypoints</div>`;
            } else {
                modifiedNodes.forEach(n => {
                    const item = document.createElement("div");
                    item.className = "git-item";
                    item.style.cssText = "background: rgba(239, 68, 68, 0.05); border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 6px; padding: 8px; cursor: pointer; transition: all 0.15s ease; margin-bottom: 4px;";
                    item.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 3px;">
                            <span style="font-weight: 600; font-size: 0.72rem; color: #f3f4f6;">\${n.name}</span>
                            <span style="font-size:0.55rem; text-transform:uppercase; padding: 1px 4px; border-radius: 4px; background: rgba(239, 68, 68, 0.2); color: #f87171; font-weight:700;">\${n.type}</span>
                        </div>
                        <div style="font-size:0.6rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">📁 \${n.file || "No file info"}</div>
                    `;
                    item.onclick = () => window.selectNodeById(n.id);
                    entrypointList.appendChild(item);
                });
            }

            if (impactedNodes.length === 0) {
                impactedList.innerHTML = `<div style="color:var(--text-muted); font-size:0.65rem; text-align:center; padding:10px;">No downstream impact</div>`;
            } else {
                impactedNodes.forEach(n => {
                    const dist = gitRiskScores[n.id];
                    let degreeText = `\${dist}th Degree`;
                    let badgeColor = "rgba(234, 179, 8, 0.2)";
                    let textColor = "#fde047";
                    if (dist === 1) {
                        degreeText = "1st Degree Direct";
                        badgeColor = "rgba(249, 115, 22, 0.2)";
                        textColor = "#fdba74";
                    } else if (dist === 2) {
                        degreeText = "2nd Degree Secondary";
                        badgeColor = "rgba(234, 179, 8, 0.15)";
                        textColor = "#fef08a";
                    }

                    const item = document.createElement("div");
                    item.className = "git-item";
                    item.style.cssText = "background: rgba(249, 115, 22, 0.03); border: 1px solid rgba(249, 115, 22, 0.15); border-radius: 6px; padding: 8px; cursor: pointer; transition: all 0.15s ease; margin-bottom: 4px;";
                    item.innerHTML = `
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 3px;">
                            <span style="font-weight: 600; font-size: 0.72rem; color: #e2e8f0;">\${n.name}</span>
                            <span style="font-size:0.55rem; padding: 1px 4px; border-radius: 4px; background: \${badgeColor}; color: \${textColor}; font-weight:700;">\${degreeText}</span>
                        </div>
                        <div style="font-size:0.6rem; color: var(--text-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">📁 \${n.file || "No file info"}</div>
                    `;
                    item.onclick = () => window.selectNodeById(n.id);
                    impactedList.appendChild(item);
                });
            }
        }

        function computeActivePaths(node) {
            selectedNodeActivePaths.clear();
            selectedNodeActiveLinks.clear();
            if (!node) return;
            
            selectedNodeActivePaths.add(node.id);
            let queue = [node.id];
            while (queue.length > 0) {
                let curr = queue.shift();
                links.forEach(l => {
                    if (l.target === curr && !selectedNodeActivePaths.has(l.source)) {
                        selectedNodeActivePaths.add(l.source);
                        selectedNodeActiveLinks.add(l);
                        queue.push(l.source);
                    }
                });
            }
            queue = [node.id];
            while (queue.length > 0) {
                let curr = queue.shift();
                links.forEach(l => {
                    if (l.source === curr && !selectedNodeActivePaths.has(l.target)) {
                        selectedNodeActivePaths.add(l.target);
                        selectedNodeActiveLinks.add(l);
                        queue.push(l.target);
                    }
                });
            }
        }

        // Calculate degree centrality for visual sizing and analysis
        function calculateCentrality() {
            nodes.forEach(n => {
                n.inDegree = 0;
                n.outDegree = 0;
            });
            links.forEach(l => {
                if (nodeIdMap[l.source]) nodeIdMap[l.source].outDegree++;
                if (nodeIdMap[l.target]) nodeIdMap[l.target].inDegree++;
            });
            nodes.forEach(n => {
                n.centrality = n.inDegree + n.outDegree;
            });
            const maxCent = Math.max(...nodes.map(n => n.centrality), 1);
            nodes.forEach(n => {
                n.centralityScore = n.centrality / maxCent;
            });
        }
        calculateCentrality();



        // Tab Switching Logic
        let activeTabId = "overview";
        function switchTab(tabId) {
            activeTabId = tabId;
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            const btn = document.getElementById(`tab-btn-${tabId}`);
            if (btn) btn.classList.add('active');
            
            const content = document.getElementById(`tab-content-${tabId}`);
            if (content) content.classList.add('active');
        }

        // Generate Mermaid.js code for transitive sub-graph
        function generateMermaidCode(node, activePaths) {
            let mStr = "graph TD\n";
            mStr += "  classDef rule fill:#6366f1,stroke:#a5b4fc,color:#fff,rx:6px,ry:6px;\n";
            mStr += "  classDef func fill:#10b981,stroke:#34d399,color:#fff,rx:6px,ry:6px;\n";
            mStr += "  classDef unres fill:#f43f5e,stroke:#fda4af,color:#fff,stroke-dasharray:3 3,rx:6px,ry:6px;\n\n";

            const pathNodeIds = activePaths && activePaths.size > 0 ? activePaths : new Set([node.id]);
            
            nodes.forEach(n => {
                if (pathNodeIds.has(n.id)) {
                    const cleanId = n.id.replace(/[^a-zA-Z0-9_]/g, "_");
                    mStr += `  ${cleanId}["${n.name}"]:::${n.type === 'rule' ? 'rule' : n.type === 'unresolved' ? 'unres' : 'func'}\n`;
                }
            });

            links.forEach(l => {
                if (pathNodeIds.has(l.source) && pathNodeIds.has(l.target)) {
                    const cleanSrc = l.source.replace(/[^a-zA-Z0-9_]/g, "_");
                    const cleanTgt = l.target.replace(/[^a-zA-Z0-9_]/g, "_");
                    if (l.label) {
                        mStr += `  ${cleanSrc} -->|"${l.label}"| ${cleanTgt}\n`;
                    } else {
                        mStr += `  ${cleanSrc} --> ${cleanTgt}\n`;
                    }
                }
            });
            return mStr;
        }

        // Clipboard utility for Mermaid copy action
        function copyMermaidToClipboard() {
            const codeEl = document.getElementById("mermaid-code-block");
            if (!codeEl) return;
            navigator.clipboard.writeText(codeEl.textContent).then(() => {
                const copyBtn = document.getElementById("mermaid-copy-btn");
                if (copyBtn) {
                    copyBtn.textContent = "📋 Copied!";
                    setTimeout(() => { copyBtn.textContent = "📋 Copy Code"; }, 2000);
                }
            }).catch(err => {
                console.error("Failed to copy text: ", err);
            });
        }

        // Popout Mermaid flowchart in a new window
        function openMermaidInNewWindow() {
            const container = document.getElementById("mermaid-rendered-flowchart");
            const svgElement = container ? container.querySelector("svg") : null;
            if (!svgElement) {
                alert("No flowchart rendered yet to open!");
                return;
            }
            
            const win = window.open("", "_blank");
            if (!win) {
                alert("Popup blocker blocked the new window. Please allow popups for this site.");
                return;
            }
            
            const svgHtml = svgElement.outerHTML;
            const nodeName = selectedNode ? selectedNode.name : "Sub-graph";
            
            win.document.write(`
<!DOCTYPE html>
<html>
<head>
    <title>Mermaid Flowchart - \${nodeName}</title>
    <style>
        :root {
            --bg-color: #0f172a;
            --border-color: #334155;
            --text-color: #cbd5e1;
            --accent-color: #c084fc;
        }
        body {
            margin: 0;
            padding: 20px;
            background: var(--bg-color);
            color: var(--text-color);
            font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            min-height: 100vh;
            box-sizing: border-box;
            overflow: auto;
        }
        .header {
            width: 100%;
            max-width: 1200px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 12px;
            margin-bottom: 20px;
        }
        h1 {
            font-size: 1.25rem;
            font-weight: 600;
            margin: 0;
            color: #f3f4f6;
        }
        .subtitle {
            font-size: 0.8rem;
            color: #94a3b8;
        }
        .btn {
            background: rgba(192, 132, 252, 0.15);
            border: 1px solid rgba(192, 132, 252, 0.4);
            color: #e9d5ff;
            padding: 6px 12px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 0.75rem;
            font-weight: 500;
            transition: all 0.15s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }
        .btn:hover {
            background: rgba(192, 132, 252, 0.25);
            border-color: rgba(192, 132, 252, 0.6);
            box-shadow: 0 0 12px rgba(192, 132, 252, 0.15);
        }
        .chart-container {
            background: rgba(0, 0, 0, 0.25);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 24px;
            display: flex;
            justify-content: center;
            align-items: center;
            max-width: 100%;
            overflow: auto;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.3);
        }
        svg {
            max-width: 100%;
            height: auto;
        }
    </style>
</head>
<body>
    <div class="header">
        <div>
            <h1>Flowchart: \${nodeName}</h1>
            <div class="subtitle">Genomics impact graph generated by BiGI</div>
        </div>
        <button class="btn" onclick="window.print()">🖨️ Print / Save PDF</button>
    </div>
    <div class="chart-container">
        \${svgHtml}
    </div>
    <script>
        document.querySelectorAll(".node").forEach(nodeEl => {
            const idClass = Array.from(nodeEl.classList).find(c => c.startsWith("flowchart-") && !c.includes("-"));
            let targetId = null;
            if (idClass) {
                targetId = idClass.replace("flowchart-", "");
            } else {
                const idAttr = nodeEl.id;
                if (idAttr) {
                    const match = idAttr.match(/^(?:flowchart-)?([a-zA-Z0-9_]+)-\\d+$/);
                    if (match) targetId = match[1];
                }
            }
            
            if (targetId) {
                nodeEl.style.cursor = "pointer";
                nodeEl.addEventListener("click", (evt) => {
                    if (window.opener && !window.opener.closed) {
                        window.opener.selectNodeByIdSanitized(targetId);
                        window.opener.focus();
                    }
                });
            }
        });
    <\/script>
</body>
</html>
            `);
            win.document.close();
        }

        // Advanced search matching
        function nodeMatchesSearch(n) {
            const search = document.getElementById("search-input").value.trim().toLowerCase();
            if (!search) return true;
            
            let searchType = null;
            let searchFile = null;
            let plainSearch = search;
            
            if (search.includes("type:")) {
                const match = search.match(/type:(\w+)/);
                if (match) {
                    searchType = match[1];
                    plainSearch = plainSearch.replace(/type:\w+/, "").trim();
                }
            }
            if (search.includes("file:")) {
                const match = search.match(/file:([^\s]+)/);
                if (match) {
                    searchFile = match[1].toLowerCase();
                    plainSearch = plainSearch.replace(/file:[^\s]+/, "").trim();
                }
            }
            
            if (searchType && n.type !== searchType) return false;
            if (searchFile && (!n.file || !n.file.toLowerCase().includes(searchFile))) return false;
            if (plainSearch) {
                const matchesName = n.name.toLowerCase().includes(plainSearch);
                const matchesFile = n.file && n.file.toLowerCase().includes(plainSearch);
                if (!matchesName && !matchesFile) return false;
            }
            return true;
        }

        // Collapsible sidebar elements
        const leftPanel = document.getElementById("left-panel");
        const rightPanel = document.getElementById("right-panel");
        const toggleLeftBtn = document.getElementById("toggle-left");
        const closeLeftBtn = document.getElementById("close-left-btn");
        const closeRightBtn = document.getElementById("close-right-btn");

        function setLeftPanelCollapsed(collapsed) {
            if (collapsed) {
                leftPanel.classList.add("collapsed");
                toggleLeftBtn.classList.add("collapsed");
                toggleLeftBtn.textContent = "▶";
            } else {
                leftPanel.classList.remove("collapsed");
                toggleLeftBtn.classList.remove("collapsed");
                toggleLeftBtn.textContent = "◀";
            }
        }

        toggleLeftBtn.onclick = () => {
            const isCollapsed = leftPanel.classList.contains("collapsed");
            setLeftPanelCollapsed(!isCollapsed);
        };
        closeLeftBtn.onclick = () => setLeftPanelCollapsed(true);
        
        closeRightBtn.onclick = () => {
            selectedNode = null;
            rightPanel.classList.remove("active");
        };

        // Populate left panel node list
        const nodeListEl = document.getElementById("node-list");
        function populateNodeList(filterText = "") {
            nodeListEl.innerHTML = "";
            const hideUnresolved = document.getElementById("hide-unresolved-cb").checked;
            const gitImpactCb = document.getElementById("git-impact-cb");
            const gitImpactOnly = gitImpactCb ? gitImpactCb.checked : false;
            const focusModeCb = document.getElementById("focus-mode-cb");
            const isFocusModeActive = focusModeCb && focusModeCb.checked && selectedNode;
            
            const sortedNodes = [...nodes].sort((a, b) => {
                if (a.type !== b.type) return a.type.localeCompare(b.type);
                return a.name.localeCompare(b.name);
            });

            sortedNodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') {
                    return;
                }
                if (gitImpactOnly && !gitImpactNodes.has(n.id)) {
                    return;
                }
                if (isFocusModeActive && !selectedNodeActivePaths.has(n.id)) {
                    return;
                }
                if (!nodeMatchesSearch(n)) {
                    return;
                }
                const div = document.createElement("div");
                div.className = "node-item";
                if (n.git_modified) {
                    div.style.borderLeft = "3px solid #f97316";
                    div.style.background = "rgba(249, 115, 22, 0.03)";
                }
                
                let badgeClass = "badge-func";
                let badgeText = "FUNC";
                if (n.type === "rule") {
                    badgeClass = "badge-rule";
                    badgeText = "RULE";
                } else if (n.type === "unresolved") {
                    badgeClass = "badge-unres";
                    badgeText = "UNRES";
                }

                div.innerHTML = `
                    <span style="font-weight: 500; display:flex; align-items:center; gap:4px;">
                        ${n.git_modified ? "📝 " : ""}${n.name}
                    </span>
                    <span class="badge ${badgeClass}">${badgeText}</span>
                `;
                div.onclick = () => selectNode(n);
                nodeListEl.appendChild(div);
            });
        }
        populateNodeList();

        document.getElementById("search-input").addEventListener("input", (e) => {
            populateNodeList(e.target.value);
            draw();
        });

        document.getElementById("hide-unresolved-cb").addEventListener("change", () => {
            populateNodeList(document.getElementById("search-input").value);
            draw();
        });

        const focusModeCb = document.getElementById("focus-mode-cb");
        if (focusModeCb) {
            focusModeCb.addEventListener("change", () => {
                populateNodeList(document.getElementById("search-input").value);
                isSimulating = true; // wake physics
                draw();
            });
        }

        document.getElementById("git-impact-cb").addEventListener("change", (e) => {
            gitImpactOnly = e.target.checked;
            const dashToggle = document.getElementById("git-dashboard-toggle-cb");
            if (dashToggle) dashToggle.checked = e.target.checked;
            populateNodeList(document.getElementById("search-input").value);
            draw();
        });

        const dashToggle = document.getElementById("git-dashboard-toggle-cb");
        if (dashToggle) {
            dashToggle.addEventListener("change", (e) => {
                const gitImpactCb = document.getElementById("git-impact-cb");
                if (gitImpactCb) {
                    gitImpactCb.checked = e.target.checked;
                    gitImpactCb.dispatchEvent(new Event("change"));
                }
            });
        }

        // Pause / Play Physics
        const pauseBtn = document.getElementById("btn-pause");
        pauseBtn.onclick = () => {
            isSimulating = !isSimulating;
            pauseBtn.textContent = isSimulating ? "Pause Physics" : "Resume Physics";
        };

        // Reset positions
        document.getElementById("btn-reset").onclick = () => {
            nodes.forEach(n => {
                n.x = width / 2 + (Math.random() - 0.5) * 400;
                n.y = height / 2 + (Math.random() - 0.5) * 400;
                n.vx = 0;
                n.vy = 0;
            });
            transform = { x: 0, y: 0, k: 1 };
            if (!isSimulating) {
                isSimulating = true;
                pauseBtn.textContent = "Pause Physics";
            }
        };

        // Layout Mode toggle
        const layoutBtn = document.getElementById("btn-layout");
        layoutBtn.onclick = () => {
            layoutMode = layoutMode === 'swimlane' ? 'free' : 'swimlane';
            layoutBtn.textContent = layoutMode === 'swimlane' ? 'Layout: Swimlanes' : 'Layout: Free';
            if (!isSimulating) {
                isSimulating = true;
                pauseBtn.textContent = "Pause Physics";
            }
        };

        // Export PNG capture
        document.getElementById("btn-export").onclick = () => {
            const dataURL = canvas.toDataURL("image/png");
            const link = document.createElement("a");
            link.download = `bigi_impact_graph_${selectedNode ? selectedNode.name : 'export'}.png`;
            link.href = dataURL;
            link.click();
        };

        function escapeHtml(str) {
            if (!str) return "";
            return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }

        function highlightCode(code) {
            if (!code) return "";
            let esc = escapeHtml(code);
            
            const placeholders = [];
            
            // 1. Temporarily extract block comments /* ... */
            esc = esc.replace(/(\/\*[\s\S]*?\*\/)/g, (match) => {
                const id = `__COMMENT_${placeholders.length}__`;
                placeholders.push({ id: id, html: `<span style="color: #6b7280; font-style: italic;">${match}</span>` });
                return id;
            });

            // 2. Temporarily extract single-line comments (# or //)
            esc = esc.replace(/((?:#[^\n]*)|(?:\/\/[^\n]*))/g, (match) => {
                const id = `__COMMENT_${placeholders.length}__`;
                placeholders.push({ id: id, html: `<span style="color: #6b7280; font-style: italic;">${match}</span>` });
                return id;
            });
            
            // 3. Temporarily extract double-quoted strings
            esc = esc.replace(/("(?:\\.|[^"\\])*")/g, (match) => {
                const id = `__STRING_${placeholders.length}__`;
                placeholders.push({ id: id, html: `<span style="color: #fb7185;">${match}</span>` });
                return id;
            });
            
            // 4. Temporarily extract single-quoted strings
            esc = esc.replace(/('(?:\\.|[^'\\])*')/g, (match) => {
                const id = `__STRING_${placeholders.length}__`;
                placeholders.push({ id: id, html: `<span style="color: #fb7185;">${match}</span>` });
                return id;
            });

            // 5. Highlight variables assignment / arrows
            esc = esc.replace(/(&lt;-|=|=&gt;|-&gt;)/g, '<span style="color: #34d399;">$1</span>');

            // 6. Highlight keywords
            const keywords = /\b(function|if|else|for|while|return|library|require|in|next|break|def|func|fn|sub|const|let|var|class|import|export|from|as|package|struct|impl|use|using|end)\b/g;
            esc = esc.replace(keywords, '<span style="color: #f472b6; font-weight: bold;">$1</span>');

            // 7. Highlight function calls
            esc = esc.replace(/\b([a-zA-Z0-9_\.\:]+)\s*(?=\()/g, '<span style="color: #60a5fa;">$1</span>');

            // 8. Restore comments and strings (in reverse order to handle nesting)
            for (let i = placeholders.length - 1; i >= 0; i--) {
                esc = esc.replace(placeholders[i].id, placeholders[i].html);
            }

            return esc;
        }

        function renderMermaidFlowchart(node, mermaidCode) {
            const element = document.getElementById("mermaid-rendered-flowchart");
            if (!element) return;
            if (!window.mermaid) {
                element.innerHTML = `<div style="color: var(--accent-unres); font-size: 0.75rem; text-align: center; padding: 20px 0;">Mermaid library failed to load (offline or CDN blocked). Copy code below.</div>`;
                return;
            }
            
            try {
                const chartId = "mermaid-chart-" + Math.floor(Math.random() * 1000000);
                mermaid.render(chartId, mermaidCode).then(({ svg, bindFunctions }) => {
                    element.innerHTML = svg;
                    if (bindFunctions) bindFunctions(element);
                    
                    // Bind click handlers to nodes in the flowchart
                    element.querySelectorAll(".node").forEach(nodeEl => {
                        const idClass = Array.from(nodeEl.classList).find(c => c.startsWith("flowchart-") && !c.includes("-"));
                        let targetId = null;
                        if (idClass) {
                            targetId = idClass.replace("flowchart-", "");
                        } else {
                            const idAttr = nodeEl.id;
                            if (idAttr) {
                                const match = idAttr.match(/^(?:flowchart-)?([a-zA-Z0-9_]+)-\d+$/);
                                if (match) targetId = match[1];
                            }
                        }
                        
                        if (targetId) {
                            nodeEl.style.cursor = "pointer";
                            nodeEl.addEventListener("click", (evt) => {
                                evt.stopPropagation();
                                const origNode = nodes.find(n => n.id.replace(/[^a-zA-Z0-9_]/g, "_") === targetId);
                                if (origNode) {
                                    selectNodeById(origNode.id);
                                }
                            });
                        }
                    });
                }).catch(err => {
                    console.error("Mermaid Render Error: ", err);
                    element.innerHTML = `<div style="color: var(--accent-unres); font-size: 0.75rem; text-align: center; padding: 20px 0;">Mermaid render error. Copy code below.</div>`;
                });
            } catch (e) {
                console.error(e);
                element.innerHTML = `<div style="color: var(--accent-unres); font-size: 0.75rem; text-align: center; padding: 20px 0;">Mermaid render initialization error.</div>`;
            }
        }

        // Selection display updater
        function selectNode(node) {
            selectedNode = node;
            const content = document.getElementById("detail-content");

            if (!node) {
                rightPanel.classList.remove("active");
                selectedNodeActivePaths.clear();
                selectedNodeActiveLinks.clear();
                return;
            }

            rightPanel.classList.add("active");
            computeActivePaths(node);
            
            // Highlight connections
            const incoming = [];
            const outgoing = [];
            links.forEach(l => {
                if (l.target === node.id) {
                    incoming.push({ 
                        node: nodeIdMap[l.source], 
                        conf: l.confidence,
                        type: l.type,
                        label: l.label,
                        detail: l.detail 
                    });
                }
                if (l.source === node.id) {
                    outgoing.push({ 
                        node: nodeIdMap[l.target], 
                        conf: l.confidence,
                        type: l.type,
                        label: l.label,
                        detail: l.detail 
                    });
                }
            });

            let criticalityBadge = "";
            if (node.centralityScore > 0.6) {
                criticalityBadge = `<span class="badge" style="background: rgba(239, 68, 68, 0.2); color: #fca5a5; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 6px; font-weight:bold; font-size:0.65rem;">🔥 CRITICAL HUB</span>`;
            } else if (node.centralityScore > 0.3) {
                criticalityBadge = `<span class="badge" style="background: rgba(245, 158, 11, 0.2); color: #fde047; border: 1px solid rgba(245, 158, 11, 0.4); padding: 2px 6px; font-weight:bold; font-size:0.65rem;">⚡ HIGH CONFLICT</span>`;
            } else {
                criticalityBadge = `<span class="badge" style="background: rgba(148, 163, 184, 0.15); color: #cbd5e1; border: 1px solid rgba(148, 163, 184, 0.3); padding: 2px 6px; font-size:0.65rem;">Normal Linkage</span>`;
            }

            let specificDetails = "";
            if (node.type === "rule") {
                const absPath = `${graphData.pipeline_dir}/${node.file}`;
                const fileUri = `file://${absPath}`;
                specificDetails = `
                    <div class="section-title">Rule Configuration</div>
                    <div style="font-size: 0.78rem; margin-bottom: 8px; color: var(--text-muted); display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <strong>File:</strong> <a href="${fileUri}" target="_blank" style="color: #818cf8; text-decoration: underline; font-family: monospace; font-size: 0.75rem;">${node.file}</a>
                        <a href="vscode://file${absPath}:1" 
                           title="Open in VS Code" 
                           style="display: inline-flex; align-items: center; justify-content: center; background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.3); color: #a5b4fc; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-decoration: none; cursor: pointer;">
                           💻 Open in Editor
                        </a>
                    </div>
                    <div class="section-title">Inputs</div>
                    <ul class="detail-list">
                        ${node.inputs.map(i => `<li>${i}</li>`).join("") || "<li style='color: var(--text-muted); italic;'>None</li>"}
                    </ul>
                    <div class="section-title">Outputs</div>
                    <ul class="detail-list">
                        ${node.outputs.map(o => `<li>${o}</li>`).join("") || "<li style='color: var(--text-muted); italic;'>None</li>"}
                    </ul>
                `;
            } else if (node.type === "unresolved") {
                let pkgName = "";
                let funcName = node.name;
                if (node.name.includes("::")) {
                    const parts = node.name.split("::");
                    pkgName = parts[0];
                    funcName = parts[1];
                }
                
                specificDetails = `
                    <div class="section-title">External Function Context</div>
                    <div style="font-size: 0.78rem; margin-bottom: 8px; color: var(--text-muted);">
                        This is an external library or package function.
                    </div>
                    ${pkgName ? `
                    <div style="margin-bottom: 12px;">
                        <span class="badge badge-unres" style="font-size: 0.7rem; background: rgba(244, 63, 94, 0.2); color: #fb7185; border: 1px solid rgba(244, 63, 94, 0.4); padding: 4px 8px;">Package: ${pkgName}</span>
                    </div>` : ""}
                    <div style="font-size: 0.78rem; margin-top: 8px; display: flex; gap: 8px;">
                        <a href="https://rdrr.io/search/?q=${node.name}" target="_blank" style="color: #6366f1; text-decoration: underline; font-weight: 500;">Search Rdrr.io Docs</a>
                        ${pkgName ? `• <a href="https://rdrr.io/cran/${pkgName}/man/${funcName}.html" target="_blank" style="color: #6366f1; text-decoration: underline; font-weight: 500;">Direct Page</a>` : ""}
                    </div>
                `;
            } else {
                const absPath = `${graphData.pipeline_dir}/${node.file}`;
                const fileUri = `file://${absPath}` + (node.line_range.length ? `#L${node.line_range[0]}` : "");
                specificDetails = `
                    <div class="section-title">Function Context</div>
                    <div style="font-size: 0.78rem; margin-bottom: 8px; color: var(--text-muted); display: flex; align-items: center; gap: 8px; flex-wrap: wrap;">
                        <strong>File:</strong> <a href="${fileUri}" target="_blank" style="color: #818cf8; text-decoration: underline; font-family: monospace; font-size: 0.75rem;">${node.file}</a>
                        <a href="vscode://file${absPath}:${node.line_range.length ? node.line_range[0] : 1}" 
                           title="Open in VS Code" 
                           style="display: inline-flex; align-items: center; justify-content: center; background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.3); color: #a5b4fc; padding: 2px 6px; border-radius: 4px; font-size: 0.65rem; font-weight: 600; text-decoration: none; cursor: pointer;">
                           💻 Open in Editor
                        </a>
                    </div>
                    ${node.line_range.length ? `<div style="font-size: 0.78rem; color: var(--text-muted);"><strong>Line range:</strong> ${node.line_range[0]} - ${node.line_range[1]}</div>` : ""}
                `;
            }

            // Preserve the tab if it is still valid, else default to 'overview'
            if (activeTabId === 'code' && !node.code) {
                activeTabId = 'overview';
            }

            const mermaidCode = generateMermaidCode(node, selectedNodeActivePaths);

            content.innerHTML = `
                <div class="detail-header">
                    <div style="display: flex; align-items: center; justify-content: space-between; width: 100%; flex-wrap: wrap; gap: 6px;">
                        <div class="detail-title">${node.name}</div>
                        ${node.git_modified ? `<span class="badge" style="background: rgba(249, 115, 22, 0.2); color: #fdba74; border: 1px solid rgba(249, 115, 22, 0.4); font-weight: bold; font-size: 0.65rem;">📝 GIT MODIFIED</span>` : ""}
                    </div>
                    <span class="badge ${node.type === 'rule' ? 'badge-rule' : node.type === 'unresolved' ? 'badge-unres' : 'badge-func'}" style="margin-top:5px; display:inline-block;">${node.type.toUpperCase()}</span>
                    
                    <!-- Path Tracing Controls -->
                    <div style="margin-top: 10px; display: flex; gap: 8px; flex-wrap: wrap;">
                        <button class="btn" style="padding: 4px 8px; font-size: 0.68rem; background: rgba(99, 102, 241, 0.15); border: 1px solid rgba(99, 102, 241, 0.35); color: #c7d2fe; display: flex; align-items: center; gap: 4px; border-radius: 6px;" onclick="setPathStart('${node.id}')">
                            🏁 Set as Start
                        </button>
                        <button class="btn" style="padding: 4px 8px; font-size: 0.68rem; background: rgba(236, 72, 153, 0.15); border: 1px solid rgba(236, 72, 153, 0.35); color: #fbcfe8; display: flex; align-items: center; gap: 4px; border-radius: 6px;" onclick="setPathEnd('${node.id}')">
                            🎯 Set as End
                        </button>
                    </div>
                </div>
                
                <div class="tabs">
                    <div class="tab-btn ${activeTabId === 'overview' ? 'active' : ''}" id="tab-btn-overview" onclick="switchTab('overview')">Overview</div>
                    <div class="tab-btn ${activeTabId === 'trace' ? 'active' : ''}" id="tab-btn-trace" onclick="switchTab('trace')">Graph Trace</div>
                    ${node.code ? `<div class="tab-btn ${activeTabId === 'code' ? 'active' : ''}" id="tab-btn-code" onclick="switchTab('code')">Source Code</div>` : ""}
                    <div class="tab-btn ${activeTabId === 'mermaid' ? 'active' : ''}" id="tab-btn-mermaid" onclick="switchTab('mermaid')">Mermaid Flow</div>
                </div>

                <div id="tab-content-overview" class="tab-content ${activeTabId === 'overview' ? 'active' : ''}">
                    ${specificDetails}
                    <div class="section-title">Criticality Analysis</div>
                    <div style="font-size: 0.78rem; display: flex; align-items: center; gap: 8px;">
                        <strong>Linkage Strength:</strong> ${criticalityBadge}
                    </div>
                    <div style="font-size: 0.72rem; color: var(--text-muted); margin-top: 6px; line-height: 1.35;">
                        Degree score: <strong>${node.centrality}</strong> active connections.
                    </div>
                </div>

                <div id="tab-content-trace" class="tab-content ${activeTabId === 'trace' ? 'active' : ''}">
                    <div class="section-title">Dependencies (Upstream)</div>
                    <ul class="detail-list" style="padding-left:0;">
                        ${incoming.map(i => {
                            let connDesc = "";
                            if (i.type === "pipeline_dep") {
                                connDesc = `Depends on outputs of rule <code>${i.node.name}</code> (matched via <code>${i.label}</code>)`;
                            } else if (i.type === "r_call") {
                                if (node.type === "rule") {
                                    connDesc = `Executed inside rule's script (calls function <code>${i.node.name}()</code>)`;
                                } else {
                                    connDesc = `Calls function <code>${i.node.name}()</code>`;
                                }
                            }
                            return `
                                <li style="display:flex; flex-direction:column; gap:4px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); padding: 10px 14px; border-radius: 8px; margin-bottom: 6px; list-style:none;">
                                    <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                                        <span style="color: #818cf8; cursor:pointer; font-weight: 600;" onclick="selectNodeById('${i.node.id}')">${i.node.name}</span>
                                        <span class="badge ${i.conf === 'HIGH' ? 'badge-func' : i.conf === 'AMBIGUOUS' ? 'badge-rule' : 'badge-unres'}">${i.conf}</span>
                                    </div>
                                    <div style="font-size:0.75rem; color:var(--text-main); margin-top:2px;">
                                        ${connDesc}
                                    </div>
                                    ${i.detail ? `<div style="font-size:0.7rem; color:var(--text-muted); font-style:italic;">Note: ${i.detail}</div>` : ""}
                                </li>
                            `;
                        }).join("") || "<li style='color: var(--text-muted); list-style:none;'>None</li>"}
                    </ul>

                    <div class="section-title">Downstream Impact (What breaks if changed)</div>
                    <ul class="detail-list" style="padding-left:0;">
                        ${outgoing.map(o => {
                            let connDesc = "";
                            if (o.type === "pipeline_dep") {
                                connDesc = `Feeds outputs into rule <code>${o.node.name}</code> (matched via <code>${o.label}</code>)`;
                            } else if (o.type === "r_call") {
                                if (o.node.type === "rule") {
                                    connDesc = `Called inside script run by Snakemake rule <code>${o.node.name}</code> (<code>${o.node.file}</code>)`;
                                } else {
                                    connDesc = `Called inside body of function <code>${o.node.name}()</code>`;
                                }
                            }
                            return `
                                <li style="display:flex; flex-direction:column; gap:4px; background: rgba(255,255,255,0.02); border: 1px solid var(--border-color); padding: 10px 14px; border-radius: 8px; margin-bottom: 6px; list-style:none;">
                                    <div style="display:flex; justify-content:space-between; align-items:center; width:100%;">
                                        <span style="color: #818cf8; cursor:pointer; font-weight: 600;" onclick="selectNodeById('${o.node.id}')">${o.node.name}</span>
                                        <span class="badge ${o.conf === 'HIGH' ? 'badge-func' : o.conf === 'AMBIGUOUS' ? 'badge-rule' : 'badge-unres'}">${o.conf}</span>
                                    </div>
                                    <div style="font-size:0.75rem; color:var(--text-main); margin-top:2px;">
                                        ${connDesc}
                                    </div>
                                    ${o.detail ? `<div style="font-size:0.7rem; color:var(--text-muted); font-style:italic;">Note: ${o.detail}</div>` : ""}
                                </li>
                            `;
                        }).join("") || "<li style='color: var(--text-muted); list-style:none;'>None</li>"}
                    </ul>
                </div>

                ${node.code ? `
                <div id="tab-content-code" class="tab-content ${activeTabId === 'code' ? 'active' : ''}">
                    <div class="section-title">Source Code Preview</div>
                    <pre class="code-container"><code>${highlightCode(node.code)}</code></pre>
                </div>
                ` : ""}

                <div id="tab-content-mermaid" class="tab-content ${activeTabId === 'mermaid' ? 'active' : ''}">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                        <span class="section-title" style="margin-top:0; margin-bottom:0;">Interactive Flowchart</span>
                        <button id="mermaid-open-btn" class="btn" style="padding: 4px 10px; font-size: 0.65rem;" onclick="openMermaidInNewWindow()">↗️ Open in New Window</button>
                    </div>
                    <div id="mermaid-rendered-flowchart" style="background: rgba(0,0,0,0.3); border: 1px solid var(--border-color); border-radius: 8px; padding: 12px; margin-bottom: 16px; display: flex; justify-content: center; overflow-x: auto; min-height: 120px;">
                        <div style="color: var(--text-muted); font-size: 0.75rem; text-align: center; width: 100%; padding: 20px 0;">Generating Flowchart...</div>
                    </div>
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 10px;">
                        <span class="section-title" style="margin-top:0; margin-bottom:0;">Mermaid Flowchart Code</span>
                        <button id="mermaid-copy-btn" class="btn" style="padding: 4px 10px; font-size: 0.65rem;" onclick="copyMermaidToClipboard()">📋 Copy Code</button>
                    </div>
                    <pre class="code-container" style="color: #c084fc; max-height: 200px;"><code id="mermaid-code-block">${escapeHtml(mermaidCode)}</code></pre>
                    <div style="font-size: 0.7rem; color: var(--text-muted); margin-top: 10px; line-height: 1.45;">
                        💡 Click nodes in the visual flow above to quickly focus the main graph canvas on that node!
                    </div>
                </div>
            `;

            renderMermaidFlowchart(node, mermaidCode);
            isSimulating = true; // Wake physics to focus/re-layout
            populateNodeList(document.getElementById("search-input").value);
        }

        window.selectNodeById = function(id) {
            const node = nodeIdMap[id];
            if (node) {
                selectNode(node);
                // Center camera smoothly on selected node
                transform.x = width / 2 - node.x * transform.k;
                transform.y = height / 2 - node.y * transform.k;
            }
        };

        window.selectNodeByIdSanitized = function(sanitizedId) {
            const node = nodes.find(n => n.id.replace(/[^a-zA-Z0-9_]/g, "_") === sanitizedId);
            if (node) {
                window.selectNodeById(node.id);
            }
        };

        window.setPathStart = function(id) {
            const node = nodeIdMap[id];
            if (node) {
                pathStartNode = node;
                document.getElementById("path-start-name").textContent = node.name;
                updatePathTracingHUD();
            }
        };

        window.setPathEnd = function(id) {
            const node = nodeIdMap[id];
            if (node) {
                pathEndNode = node;
                document.getElementById("path-end-name").textContent = node.name;
                updatePathTracingHUD();
            }
        };

        window.clearPathTracing = function() {
            pathStartNode = null;
            pathEndNode = null;
            pathTracingNodes.clear();
            pathTracingLinks.clear();
            document.getElementById("path-tracing-hud").style.display = "none";
            isSimulating = true; // Wake up physics
        };

        function updatePathTracingHUD() {
            const hud = document.getElementById("path-tracing-hud");
            hud.style.display = "flex";
            
            if (pathStartNode && pathEndNode) {
                computePathTracing();
                
                const startLabel = document.getElementById("path-start-name");
                const endLabel = document.getElementById("path-end-name");
                
                let hasPath = pathTracingNodes.has(pathStartNode.id) && pathTracingNodes.has(pathEndNode.id) && pathTracingNodes.size >= 2;
                if (pathStartNode.id === pathEndNode.id) hasPath = true;
                
                if (!hasPath) {
                    hud.style.borderColor = "rgba(244, 63, 94, 0.6)";
                    endLabel.style.color = "#f43f5e";
                    endLabel.textContent = pathEndNode.name + " (⚠️ No path)";
                } else {
                    hud.style.borderColor = "rgba(99, 102, 241, 0.45)";
                    endLabel.style.color = "#f472b6";
                    endLabel.textContent = pathEndNode.name;
                }
            }
            isSimulating = true; // Wake up physics to layout/render
        }

        function computePathTracing() {
            pathTracingNodes.clear();
            pathTracingLinks.clear();
            
            if (!pathStartNode || !pathEndNode) return;
            
            // 1. Forward traversal from StartNode
            const reachableFromStart = new Set();
            const queueStart = [pathStartNode.id];
            reachableFromStart.add(pathStartNode.id);
            
            // Create adjacency lists
            const adjForward = {};
            const adjBackward = {};
            links.forEach(l => {
                adjForward[l.source] = adjForward[l.source] || [];
                adjForward[l.source].push(l.target);
                
                adjBackward[l.target] = adjBackward[l.target] || [];
                adjBackward[l.target].push(l.source);
            });
            
            while (queueStart.length > 0) {
                const curr = queueStart.shift();
                const neighbors = adjForward[curr] || [];
                neighbors.forEach(nxt => {
                    if (!reachableFromStart.has(nxt)) {
                        reachableFromStart.add(nxt);
                        queueStart.push(nxt);
                    }
                });
            }
            
            // 2. Backward traversal from EndNode (using reverse edges)
            const canReachEnd = new Set();
            const queueEnd = [pathEndNode.id];
            canReachEnd.add(pathEndNode.id);
            
            while (queueEnd.length > 0) {
                const curr = queueEnd.shift();
                const neighbors = adjBackward[curr] || [];
                neighbors.forEach(nxt => {
                    if (!canReachEnd.has(nxt)) {
                        canReachEnd.add(nxt);
                        queueEnd.push(nxt);
                    }
                });
            }
            
            // 3. Find intersection of reachable sets
            nodes.forEach(n => {
                if (reachableFromStart.has(n.id) && canReachEnd.has(n.id)) {
                    pathTracingNodes.add(n.id);
                }
            });
            
            // 4. Find links connecting these nodes
            links.forEach(l => {
                if (pathTracingNodes.has(l.source) && pathTracingNodes.has(l.target)) {
                    pathTracingLinks.add(l);
                }
            });
        }

        // Graph Simulation Loop
        function runSimulation() {
            const hideUnresolved = document.getElementById("hide-unresolved-cb").checked;
            const focusModeCb = document.getElementById("focus-mode-cb");
            const isFocusMode = focusModeCb && focusModeCb.checked && selectedNode;
            
            // Script groups grouping calculations
            const groups = {};
            nodes.forEach(n => {
                if (n.type === 'function' && n.file) {
                    groups[n.file] = groups[n.file] || [];
                    groups[n.file].push(n);
                }
            });

            // Group collapsing layout handler
            Object.entries(groups).forEach(([filename, groupNodes]) => {
                if (groupNodes.length < 2) return;
                
                if (collapsedGroups.has(filename)) {
                    let avgX = 0, avgY = 0, activeCount = 0;
                    groupNodes.forEach(gn => {
                        if (isFocusMode && !selectedNodeActivePaths.has(gn.id)) return;
                        avgX += gn.x;
                        avgY += gn.y;
                        activeCount++;
                    });
                    
                    if (activeCount > 0) {
                        avgX /= activeCount;
                        avgY /= activeCount;
                    } else {
                        avgX = width / 2;
                        avgY = height / 2;
                    }
                    
                    groupNodes.forEach(gn => {
                        gn.x += (avgX - gn.x) * 0.35;
                        gn.y += (avgY - gn.y) * 0.35;
                        gn.vx = 0;
                        gn.vy = 0;
                        gn.width = 0.1;
                        gn.height = 0.1;
                        gn.radius = 0.1;
                    });
                    
                    const primary = groupNodes.find(gn => !isFocusMode || selectedNodeActivePaths.has(gn.id)) || groupNodes[0];
                    if (primary) {
                        primary.width = Math.max(primary.baseWidth, 90);
                        primary.height = primary.baseHeight;
                        primary.radius = primary.width / 2;
                    }
                } else {
                    groupNodes.forEach(gn => {
                        if (gn.width < 1.0) {
                            gn.width = gn.baseWidth;
                            gn.height = gn.baseHeight;
                            gn.radius = gn.baseWidth / 2;
                        }
                    });
                }
            });

            // Target dimensions and sizing configurations (stable pill shape at all times)
            nodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') return;
                if (isFocusMode && !selectedNodeActivePaths.has(n.id)) return;
                
                const isSelected = selectedNode && selectedNode.id === n.id;
                const isHovered = hoveredNode && hoveredNode.id === n.id;
                
                // Keep base sizes unless collapsed
                const isColGroup = n.file && collapsedGroups.has(n.file);
                const isPrimary = isColGroup && groups[n.file] && (groups[n.file].find(gn => !isFocusMode || selectedNodeActivePaths.has(gn.id)) || groups[n.file][0]) === n;
                
                if (isColGroup && !isPrimary) {
                    // Do not resize if collapsed secondary node
                    return;
                }
                
                let tW = isColGroup ? Math.max(n.baseWidth, 90) : n.baseWidth;
                let tH = n.baseHeight;
                
                if (isSelected || isHovered) {
                    tW = tW * 1.15;
                    tH = tH * 1.15;
                }
                
                n.targetWidth = tW;
                n.targetHeight = tH;
                
                // Interpolate width and height for smooth transitions
                n.width += (n.targetWidth - n.width) * 0.18;
                n.height += (n.targetHeight - n.height) * 0.18;
                
                // Set radius to half-width for general physics repulsion sizing
                n.targetRadius = n.width / 2;
                n.radius += (n.targetRadius - n.radius) * 0.18;
            });

            // If Wasm is loaded, route physics through WebAssembly engine
            if (wasmLoaded && runWasmSimulation(layoutMode, hideUnresolved, isFocusMode, selectedNodeActivePaths, selectedNode, hoveredNode, collapsedGroups, groups, draggedNode)) {
                return;
            }

            // Layered Layout Swimlane gravity (Rules on top, functions in middle, unresolved at bottom)
            if (layoutMode === 'swimlane') {
                nodes.forEach(n => {
                    if (hideUnresolved && n.type === 'unresolved') return;
                    if (isFocusMode && !selectedNodeActivePaths.has(n.id)) return;
                    
                    let targetY = height / 2;
                    if (n.type === 'rule') {
                        targetY = height * 0.23;
                    } else if (n.type === 'function') {
                        targetY = height * 0.53;
                    } else if (n.type === 'unresolved') {
                        targetY = height * 0.83;
                    }
                    
                    n.vy += (targetY - n.y) * 0.008;
                });
            }

            if (!isSimulating) return;

            // Pre-filter active nodes once to avoid O(N^2) conditional checks inside nested loop
            const activeNodes = [];
            for (let i = 0; i < nodes.length; i++) {
                const n = nodes[i];
                if (hideUnresolved && n.type === 'unresolved') continue;
                if (isFocusMode && !selectedNodeActivePaths.has(n.id)) continue;
                if (n.width < 1.0) continue;
                activeNodes.push(n);
            }

            // Repulsion forces between nodes
            if (activeNodes.length <= 150) {
                // Low overhead O(N^2) loop for small graphs (maintains absolute precision and layout characteristics)
                for (let i = 0; i < activeNodes.length; i++) {
                    const nodeI = activeNodes[i];
                    nodeI.index = i;
                    
                    for (let j = i + 1; j < activeNodes.length; j++) {
                        const nodeJ = activeNodes[j];
                        
                        let dx = nodeJ.x - nodeI.x;
                        let dy = nodeJ.y - nodeI.y;
                        let distSq = dx*dx + dy*dy;
                        
                        if (distSq > 90000) continue; // 300px threshold
                        
                        let dist = Math.sqrt(distSq);
                        if (dist < 1) dist = 1;

                        let strength = 950;
                        let force = strength / distSq;
                        
                        if (dist < 55) {
                            force += (55 - dist) * 0.85;
                        }

                        let fx = (dx / dist) * force;
                        let fy = (dy / dist) * force;

                        nodeI.vx -= fx;
                        nodeI.vy -= fy;
                        nodeJ.vx += fx;
                        nodeJ.vy += fy;

                        // AABB Collision Solver
                        const hWidthI = nodeI.width / 2;
                        const hHeightI = nodeI.height / 2;
                        const hWidthJ = nodeJ.width / 2;
                        const hHeightJ = nodeJ.height / 2;
                        const padX = 14;
                        const padY = 12;
                        const minDistanceX = hWidthI + hWidthJ + padX;
                        const minDistanceY = hHeightI + hHeightJ + padY;

                        const overlapX = minDistanceX - Math.abs(dx);
                        const overlapY = minDistanceY - Math.abs(dy);

                        if (overlapX > 0 && overlapY > 0) {
                            if (overlapX < overlapY) {
                                const sign = dx > 0 ? 1 : -1;
                                const pushForce = overlapX * 0.12 * sign;
                                nodeI.vx -= pushForce;
                                nodeJ.vx += pushForce;
                            } else {
                                const sign = dy > 0 ? 1 : -1;
                                const pushForce = overlapY * 0.12 * sign;
                                nodeI.vy -= pushForce;
                                nodeJ.vy += pushForce;
                            }
                        }
                    }
                }
            } else {
                // High-performance Flat Array Spatial Hash Grid for large graphs (O(N) complexity scaling)
                const cellSize = 220; // Cells matching typical capsule bounds (150px) + margin
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;
                
                for (let i = 0; i < activeNodes.length; i++) {
                    const n = activeNodes[i];
                    n.index = i; // Assign integer index for lookup safety
                    if (n.x < minX) minX = n.x;
                    if (n.x > maxX) maxX = n.x;
                    if (n.y < minY) minY = n.y;
                    if (n.y > maxY) maxY = n.y;
                }
                
                minX -= 10;
                minY -= 10;
                
                const cols = Math.ceil((maxX - minX) / cellSize) + 2;
                const rows = Math.ceil((maxY - minY) / cellSize) + 2;
                const grid = new Array(cols * rows);
                
                // Populate grid cells
                for (let i = 0; i < activeNodes.length; i++) {
                    const n = activeNodes[i];
                    const col = Math.floor((n.x - minX) / cellSize);
                    const row = Math.floor((n.y - minY) / cellSize);
                    const cellIdx = col + row * cols;
                    if (!grid[cellIdx]) {
                        grid[cellIdx] = [];
                    }
                    grid[cellIdx].push(n);
                    n.col = col;
                    n.row = row;
                }

                // Calculate forces via neighbor grid cell lookup (9 cells per node)
                for (let i = 0; i < activeNodes.length; i++) {
                    const nodeI = activeNodes[i];
                    const col = nodeI.col;
                    const row = nodeI.row;
                    
                    for (let dRow = -1; dRow <= 1; dRow++) {
                        const r = row + dRow;
                        if (r < 0 || r >= rows) continue;
                        const rowOffset = r * cols;
                        
                        for (let dCol = -1; dCol <= 1; dCol++) {
                            const c = col + dCol;
                            if (c < 0 || c >= cols) continue;
                            
                            const cellIdx = c + rowOffset;
                            const cellNodes = grid[cellIdx];
                            if (!cellNodes) continue;
                            
                            for (let j = 0; j < cellNodes.length; j++) {
                                const nodeJ = cellNodes[j];
                                if (nodeI.index >= nodeJ.index) continue; // Avoid double counting
                                
                                let dx = nodeJ.x - nodeI.x;
                                let dy = nodeJ.y - nodeI.y;
                                let distSq = dx*dx + dy*dy;
                                
                                // Skip if beyond 220px boundary
                                if (distSq > 48400) continue;
                                
                                let dist = Math.sqrt(distSq);
                                if (dist < 1) dist = 1;

                                let strength = 950;
                                let force = strength / distSq;
                                
                                if (dist < 55) {
                                    force += (55 - dist) * 0.85;
                                }

                                let fx = (dx / dist) * force;
                                let fy = (dy / dist) * force;

                                nodeI.vx -= fx;
                                nodeI.vy -= fy;
                                nodeJ.vx += fx;
                                nodeJ.vy += fy;

                                // AABB Collision Solver
                                const hWidthI = nodeI.width / 2;
                                const hHeightI = nodeI.height / 2;
                                const hWidthJ = nodeJ.width / 2;
                                const hHeightJ = nodeJ.height / 2;
                                const padX = 14;
                                const padY = 12;
                                const minDistanceX = hWidthI + hWidthJ + padX;
                                const minDistanceY = hHeightI + hHeightJ + padY;

                                const overlapX = minDistanceX - Math.abs(dx);
                                const overlapY = minDistanceY - Math.abs(dy);

                                if (overlapX > 0 && overlapY > 0) {
                                    if (overlapX < overlapY) {
                                        const sign = dx > 0 ? 1 : -1;
                                        const pushForce = overlapX * 0.12 * sign;
                                        nodeI.vx -= pushForce;
                                        nodeJ.vx += pushForce;
                                    } else {
                                        const sign = dy > 0 ? 1 : -1;
                                        const pushForce = overlapY * 0.12 * sign;
                                        nodeI.vy -= pushForce;
                                        nodeJ.vy += pushForce;
                                    }
                                }
                            }
                        }
                    }
                }
            }

            // Spring forces along links (skip unresolved if hidden)
            links.forEach(l => {
                let source = nodeIdMap[l.source];
                let target = nodeIdMap[l.target];
                if (!source || !target) return;
                if (hideUnresolved && (source.type === 'unresolved' || target.type === 'unresolved')) return;
                if (isFocusMode && (!selectedNodeActivePaths.has(l.source) || !selectedNodeActivePaths.has(l.target))) return;

                let dx = target.x - source.x;
                let dy = target.y - source.y;
                let dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < 1) dist = 1;

                let restLength = 140; // Increased link rest length for more spacious layouts
                let k = 0.07;
                let force = (dist - restLength) * k;

                let fx = (dx / dist) * force;
                let fy = (dy / dist) * force;

                source.vx += fx;
                source.vy += fy;
                target.vx -= fx;
                target.vy -= fy;
            });

            // Interactive Cursor Repulsion (skip unresolved if hidden)
            if (mouseSim.x !== null && mouseSim.y !== null) {
                nodes.forEach(n => {
                    if (hideUnresolved && n.type === 'unresolved') return;
                    if (isFocusMode && !selectedNodeActivePaths.has(n.id)) return;
                    if (n.width < 1.0) return;
                    
                    let dx = n.x - mouseSim.x;
                    let dy = n.y - mouseSim.y;
                    let dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist < 120 && dist > 1) {
                        let force = (120 - dist) * 0.12; // push node gently away from cursor
                        n.vx += (dx / dist) * force;
                        n.vy += (dy / dist) * force;
                    }
                });
            }

            // Subtle continuous Brownian motion / drift so graph feels organic and "alive"
            nodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') return;
                if (isFocusMode && !selectedNodeActivePaths.has(n.id)) return;
                if (n.width < 1.0) return;
                n.vx += (Math.random() - 0.5) * 0.08;
                n.vy += (Math.random() - 0.5) * 0.08;
            });

            // Gravity towards screen center & apply velocity (skip unresolved if hidden)
            nodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') return;
                if (isFocusMode && !selectedNodeActivePaths.has(n.id)) return;
                
                let dx = width / 2 - n.x;
                let dy = height / 2 - n.y;
                n.vx += dx * 0.001; // Dampened from 0.0035 to 0.001 so nodes disperse naturally
                n.vy += dy * 0.001;

                // Velocity cap to prevent numerical simulation explosion
                const maxSpeed = 30;
                const speed = Math.sqrt(n.vx * n.vx + n.vy * n.vy);
                if (speed > maxSpeed) {
                    n.vx = (n.vx / speed) * maxSpeed;
                    n.vy = (n.vy / speed) * maxSpeed;
                }

                n.vx *= 0.72; // friction decay
                n.vy *= 0.72;

                // Guard against NaN values
                if (isNaN(n.vx) || isNaN(n.vy)) {
                    n.vx = 0;
                    n.vy = 0;
                }
                if (isNaN(n.x) || isNaN(n.y)) {
                    n.x = width / 2 + (Math.random() - 0.5) * 200;
                    n.y = height / 2 + (Math.random() - 0.5) * 200;
                }

                if (n !== draggedNode) {
                    n.x += n.vx;
                    n.y += n.vy;
                }
            });
        }

        // Draw grid background helper
        function drawGrid() {
            ctx.save();
            ctx.strokeStyle = "rgba(255, 255, 255, 0.015)";
            ctx.lineWidth = 0.8;
            
            const gridSize = 45;
            
            // Start points in simulation coordinates
            const startSim = toSimCoords(0, 0);
            const endSim = toSimCoords(width, height);
            
            const startX = Math.floor(startSim.x / gridSize) * gridSize;
            const endX = Math.ceil(endSim.x / gridSize) * gridSize;
            const startY = Math.floor(startSim.y / gridSize) * gridSize;
            const endY = Math.ceil(endSim.y / gridSize) * gridSize;
            
            // Draw grid lines
            ctx.beginPath();
            for (let x = startX; x <= endX; x += gridSize) {
                ctx.moveTo(x, startY);
                ctx.lineTo(x, endY);
            }
            for (let y = startY; y <= endY; y += gridSize) {
                ctx.moveTo(startX, y);
                ctx.lineTo(endX, y);
            }
            ctx.stroke();
            
            // Draw secondary grid lines for a fine-grain blueprint style
            ctx.strokeStyle = "rgba(255, 255, 255, 0.005)";
            ctx.lineWidth = 0.5;
            const subGridSize = 15;
            ctx.beginPath();
            for (let x = startX; x <= endX; x += subGridSize) {
                if (x % gridSize === 0) continue;
                ctx.moveTo(x, startY);
                ctx.lineTo(x, endY);
            }
            for (let y = startY; y <= endY; y += subGridSize) {
                if (y % gridSize === 0) continue;
                ctx.moveTo(startX, y);
                ctx.lineTo(endX, y);
            }
            ctx.stroke();
            ctx.restore();
        }

        // Draw Loop (with dynamic filtering of unresolved links/nodes for massive performance gains)
        function draw() {
            ctx.clearRect(0, 0, width, height);

            // Draw dynamic background engineering grid first
            drawGrid();

            ctx.save();
            ctx.translate(transform.x, transform.y);
            ctx.scale(transform.k, transform.k);

            // Viewport Frustum Culling bounds calculation in simulation coordinates
            const tl = toSimCoords(0, 0);
            const br = toSimCoords(width, height);
            
            // Add safety margin (e.g. 150px) around visible simulation area
            const minSimX = tl.x - 150;
            const maxSimX = br.x + 150;
            const minSimY = tl.y - 150;
            const maxSimY = br.y + 150;

            const hideUnresolved = document.getElementById("hide-unresolved-cb").checked;
            const gitImpactCb = document.getElementById("git-impact-cb");
            const gitImpactOnly = gitImpactCb ? gitImpactCb.checked : false;
            const search = document.getElementById("search-input").value.trim().toLowerCase();
            const focusModeCb = document.getElementById("focus-mode-cb");
            const isFocusMode = focusModeCb && focusModeCb.checked && selectedNode;

            // 1. Build active paths sets (computed in selectNode)
            const activePaths = selectedNodeActivePaths;
            const activeLinks = selectedNodeActiveLinks;

            // 2. Draw script background grouping cards (Visual Script Clustering)
            const groups = {};
            nodes.forEach(n => {
                if (n.type === 'function' && n.file) {
                    groups[n.file] = groups[n.file] || [];
                    groups[n.file].push(n);
                }
            });
            
            ctx.save();
            Object.entries(groups).forEach(([filename, groupNodes]) => {
                if (groupNodes.length < 2) return;
                
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;
                groupNodes.forEach(n => {
                    if (isFocusMode && !activePaths.has(n.id)) return;
                    minX = Math.min(minX, n.x - n.width/2);
                    maxX = Math.max(maxX, n.x + n.width/2);
                    minY = Math.min(minY, n.y - n.height/2);
                    maxY = Math.max(maxY, n.y + n.height/2);
                });
                
                if (minX === Infinity) return; // Skip if no nodes visible in focus mode
                
                // Viewport culling check: skip group folder card if completely off-screen
                if (maxX < minSimX || minX > maxSimX || maxY < minSimY || minY > maxSimY) return;
                
                // Hide or dim visual clustering cards if they do not match search query
                const matchesSearch = !search || filename.toLowerCase().includes(search) || groupNodes.some(n => n.name.toLowerCase().includes(search));
                const hasGitActiveNodes = !gitImpactOnly || groupNodes.some(n => gitImpactNodes.has(n.id));
                const cardOpacity = matchesSearch && hasGitActiveNodes ? 1.0 : 0.05;

                const pad = 12;
                const rx = minX - pad;
                const ry = minY - pad - 12;
                const rw = (maxX - minX) + pad*2;
                const rh = (maxY - minY) + pad*2 + 12;
                
                const isCollapsed = collapsedGroups.has(filename);
                if (isCollapsed) {
                    // Draw collapsed folder card
                    ctx.fillStyle = `rgba(15, 23, 42, ${0.6 * cardOpacity})`;
                    ctx.strokeStyle = `rgba(99, 102, 241, ${0.45 * cardOpacity})`;
                    ctx.lineWidth = 1.5;
                    ctx.setLineDash([]);
                } else {
                    ctx.fillStyle = `rgba(30, 41, 59, ${0.15 * cardOpacity})`;
                    ctx.strokeStyle = `rgba(255, 255, 255, ${0.05 * cardOpacity})`;
                    ctx.lineWidth = 1;
                    ctx.setLineDash([4, 4]);
                }
                
                ctx.beginPath();
                const cardRadius = 8;
                ctx.moveTo(rx + cardRadius, ry);
                ctx.lineTo(rx + rw - cardRadius, ry);
                ctx.quadraticCurveTo(rx + rw, ry, rx + rw, ry + cardRadius);
                ctx.lineTo(rx + rw, ry + rh - cardRadius);
                ctx.quadraticCurveTo(rx + rw, ry + rh, rx + rw - cardRadius, ry + rh);
                ctx.lineTo(rx + cardRadius, ry + rh);
                ctx.quadraticCurveTo(rx, ry + rh, rx, ry + rh - cardRadius);
                ctx.lineTo(rx, ry + cardRadius);
                ctx.quadraticCurveTo(rx, ry, rx + cardRadius, ry);
                ctx.closePath();
                ctx.fill();
                ctx.stroke();
                ctx.setLineDash([]);
                
                ctx.fillStyle = isCollapsed ? `rgba(165, 180, 252, ${0.85 * cardOpacity})` : `rgba(148, 163, 184, ${0.5 * cardOpacity})`;
                ctx.font = isCollapsed ? "bold italic 7.5px sans-serif" : "italic 7px sans-serif";
                ctx.textAlign = "left";
                ctx.textBaseline = "top";
                ctx.fillText((isCollapsed ? "📂 [Collapsed Folder] " : "") + filename, rx + 8, ry + 6);
            });
            ctx.restore();

            // Draw link paths (skip unresolved if hidden)
            links.forEach(l => {
                const s = nodeIdMap[l.source];
                const t = nodeIdMap[l.target];
                if (!s || !t) return;
                if (hideUnresolved && (s.type === 'unresolved' || t.type === 'unresolved')) return;
                if (isFocusMode && (!activePaths.has(l.source) || !activePaths.has(l.target))) return;

                // Viewport culling check: skip link if both endpoints are off-screen
                const sVisible = s.x >= minSimX && s.x <= maxSimX && s.y >= minSimY && s.y <= maxSimY;
                const tVisible = t.x >= minSimX && t.x <= maxSimX && t.y >= minSimY && t.y <= maxSimY;
                if (!sVisible && !tVisible) return;

                const matchesSearch = nodeMatchesSearch(s) || nodeMatchesSearch(t);
                const isPathActive = pathStartNode && pathEndNode && pathTracingNodes.has(pathStartNode.id) && pathTracingNodes.has(pathEndNode.id);
                
                let isLinkHighlighted;
                if (isPathActive) {
                    isLinkHighlighted = pathTracingLinks.has(l);
                } else {
                    isLinkHighlighted = matchesSearch && (!selectedNode || activeLinks.has(l)) && (!gitImpactOnly || (gitImpactNodes.has(l.source) && gitImpactNodes.has(l.target)));
                }
                
                const edgeOpacity = isLinkHighlighted ? 1.0 : 0.015;

                const isLinkSelected = selectedNode && (selectedNode.id === s.id || selectedNode.id === t.id);
                
                if (transform.k < 0.22 && !isLinkSelected && !isPathActive) {
                    // Straight lines without gradients/curves when zoomed out for extreme rendering speedups
                    ctx.beginPath();
                    ctx.moveTo(s.x, s.y);
                    ctx.lineTo(t.x, t.y);
                    ctx.strokeStyle = isLinkHighlighted ? "rgba(165, 180, 252, 0.15)" : "rgba(255, 255, 255, 0.035)";
                    ctx.lineWidth = 0.6;
                    ctx.stroke();
                    return;
                }

                // Calculate curved control point (quadratic Bezier) to prevent straight line overlaps
                let dx = t.x - s.x;
                let dy = t.y - s.y;
                let dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < 1) dist = 1;
                
                // Perpendicular vector for curving
                let nx = -dy / dist;
                let ny = dx / dist;
                let curveOffset = dist * 0.12; 
                let qx = (s.x + t.x) / 2 + nx * curveOffset;
                let qy = (s.y + t.y) / 2 + ny * curveOffset;

                // Define node type colors for gradients
                let sColor = s.type === 'rule' ? '#6366f1' : s.type === 'unresolved' ? '#f43f5e' : '#10b981';
                let tColor = t.type === 'rule' ? '#6366f1' : t.type === 'unresolved' ? '#f43f5e' : '#10b981';
                
                if (isPathActive && pathTracingLinks.has(l)) {
                    sColor = '#a5b4fc'; // Start path is purple
                    tColor = '#f472b6'; // End path is pink
                }
                
                ctx.beginPath();
                ctx.moveTo(s.x, s.y);
                ctx.quadraticCurveTo(qx, qy, t.x, t.y);

                // Edge gradient color blending (represents information flow direction)
                let grad = ctx.createLinearGradient(s.x, s.y, t.x, t.y);
                let alpha = isLinkSelected ? 0.75 : 0.16;
                if (isPathActive && pathTracingLinks.has(l)) {
                    alpha = 0.85; // High contrast highlight for paths
                }
                
                // If change propagation risk is active, color downstream edges amber/orange
                if (hasGitChanges && l.source in gitRiskScores) {
                    const sourceRisk = gitRiskScores[l.source];
                    if (sourceRisk === 0) {
                        sColor = '#ef4444'; // direct modified is red
                    } else if (sourceRisk === 1) {
                        sColor = '#f97316'; // first degree is orange
                    } else {
                        sColor = '#fbbf24'; // secondary degree is amber
                    }
                }

                grad.addColorStop(0, hexToRgba(sColor, alpha * edgeOpacity));
                grad.addColorStop(1, hexToRgba(tColor, alpha * edgeOpacity));

                ctx.strokeStyle = grad;
                ctx.lineWidth = isLinkSelected ? 2.2 : 1.2;
                ctx.stroke();

                // Draw edge arrows aligned with the curve tangent at target
                const angle = Math.atan2(t.y - qy, t.x - qx);
                const arrowLength = 6;
                
                // Ellipse boundary intersection for rectangular nodes
                const cos = Math.cos(angle);
                const sin = Math.sin(angle);
                const halfW = t.width / 2;
                const halfH = t.height / 2;
                const arrowOffset = Math.sqrt((halfW * cos)**2 + (halfH * sin)**2) + 3;
                
                const arrowX = t.x - arrowOffset * Math.cos(angle);
                const arrowY = t.y - arrowOffset * Math.sin(angle);

                ctx.beginPath();
                ctx.moveTo(arrowX, arrowY);
                ctx.lineTo(arrowX - arrowLength * Math.cos(angle - Math.PI/6), arrowY - arrowLength * Math.sin(angle - Math.PI/6));
                ctx.lineTo(arrowX - arrowLength * Math.cos(angle + Math.PI/6), arrowY - arrowLength * Math.sin(angle + Math.PI/6));
                ctx.closePath();
                ctx.fillStyle = isLinkSelected ? hexToRgba(tColor, 0.8 * edgeOpacity) : hexToRgba(tColor, 0.25 * edgeOpacity);
                ctx.fill();

                // Draw rotated connection labels along the edge (only drawn if selected/hovered)
                const isLinkHovered = hoveredNode && (hoveredNode.id === s.id || hoveredNode.id === t.id);
                const showLabels = isLinkSelected || isLinkHovered;
                if (l.label && showLabels && isLinkHighlighted) {
                    const mx = 0.25 * s.x + 0.5 * qx + 0.25 * t.x;
                    const my = 0.25 * s.y + 0.5 * qy + 0.25 * t.y;

                    let textAngle = Math.atan2(t.y - s.y, t.x - s.x);
                    if (textAngle > Math.PI / 2 || textAngle < -Math.PI / 2) {
                        textAngle += Math.PI; // orient text to always be readable
                    }

                    ctx.save();
                    ctx.translate(mx, my);
                    ctx.rotate(textAngle);
                    
                    ctx.font = isLinkSelected ? "bold 7px sans-serif" : "7px sans-serif";
                    
                    const labelText = l.label;
                    const textWidth = ctx.measureText(labelText).width;
                    
                    // Capsule mask background for readability
                    ctx.fillStyle = "rgba(6, 9, 19, 0.88)";
                    ctx.beginPath();
                    ctx.rect(-textWidth/2 - 4, -5, textWidth + 8, 10);
                    ctx.fill();
                    
                    ctx.strokeStyle = isLinkSelected ? hexToRgba(tColor, 0.4) : "rgba(255, 255, 255, 0.05)";
                    ctx.lineWidth = 0.5;
                    ctx.stroke();

                    ctx.fillStyle = isLinkSelected ? "#ffffff" : "rgba(156, 163, 175, 0.6)";
                    ctx.textAlign = "center";
                    ctx.textBaseline = "middle";
                    ctx.fillText(labelText, 0, 0);
                    ctx.restore();
                }
            });

            // Draw animated pulse indicators gliding along curved edges (skip unresolved if hidden)
            const pulseTime = Date.now() * 0.0012;
            links.forEach(l => {
                const s = nodeIdMap[l.source];
                const t = nodeIdMap[l.target];
                if (!s || !t) return;
                if (hideUnresolved && (s.type === 'unresolved' || t.type === 'unresolved')) return;
                if (isFocusMode && (!activePaths.has(l.source) || !activePaths.has(l.target))) return;

                // Viewport culling check: skip link pulse if both endpoints are off-screen
                const sVisible = s.x >= minSimX && s.x <= maxSimX && s.y >= minSimY && s.y <= maxSimY;
                const tVisible = t.x >= minSimX && t.x <= maxSimX && t.y >= minSimY && t.y <= maxSimY;
                if (!sVisible && !tVisible) return;

                const matchesSearch = !search || s.name.toLowerCase().includes(search) || t.name.toLowerCase().includes(search);
                const isPathActive = pathStartNode && pathEndNode && pathTracingNodes.has(pathStartNode.id) && pathTracingNodes.has(pathEndNode.id);
                
                let isLinkHighlighted;
                if (isPathActive) {
                    isLinkHighlighted = pathTracingLinks.has(l);
                } else {
                    isLinkHighlighted = matchesSearch && (!selectedNode || activeLinks.has(l));
                }
                
                // Prune pulse indicators on non-highlighted links for clean presentation
                if (!isLinkHighlighted) return;

                // Skip pulse animation when zoomed out to conserve GPU/CPU rendering resources
                const isLinkSelected = selectedNode && (selectedNode.id === s.id || selectedNode.id === t.id);
                if (transform.k < 0.22 && !isLinkSelected && !isPathActive) return;

                let dx = t.x - s.x;
                let dy = t.y - s.y;
                let dist = Math.sqrt(dx*dx + dy*dy);
                if (dist < 1) dist = 1;
                
                let nx = -dy / dist;
                let ny = dx / dist;
                let curveOffset = dist * 0.12; 
                let qx = (s.x + t.x) / 2 + nx * curveOffset;
                let qy = (s.y + t.y) / 2 + ny * curveOffset;

                const offset = (s.x + s.y) * 0.003;
                const progress = (pulseTime + offset) % 1.0;
                
                // Calculate coordinate along quadratic Bezier curve
                const px = (1-progress)*(1-progress)*s.x + 2*(1-progress)*progress*qx + progress*progress*t.x;
                const py = (1-progress)*(1-progress)*s.y + 2*(1-progress)*progress*qy + progress*progress*t.y;

                let pulseColor = "rgba(255, 255, 255, 0.4)";
                if (isPathActive && pathTracingLinks.has(l)) {
                    pulseColor = "#f472b6"; // Hot pink flow indicator for active path tracing
                } else if (selectedNode && (selectedNode.id === s.id || selectedNode.id === t.id)) {
                    pulseColor = l.confidence === 'HIGH' ? "#10b981" : 
                                 l.confidence === 'AMBIGUOUS' ? "#6366f1" : "#f43f5e";
                }

                ctx.beginPath();
                ctx.arc(px, py, 2.2, 0, 2 * Math.PI);
                ctx.fillStyle = pulseColor;
                ctx.shadowColor = pulseColor;
                ctx.shadowBlur = 4;
                ctx.fill();
                ctx.shadowBlur = 0;
            });

            // Draw Nodes (represented as clean glassmorphic pill badges matching biological pathway standards, skip unresolved if hidden)
            nodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') return;
                if (isFocusMode && !activePaths.has(n.id)) return;

                // Collapsed script group visual reduction
                const isColGroup = n.file && collapsedGroups.has(n.file);
                if (isColGroup) {
                    const primary = groups[n.file] && (groups[n.file].find(gn => !isFocusMode || activePaths.has(gn.id)) || groups[n.file][0]);
                    if (primary !== n) return; // Skip drawing secondary collapsed nodes
                }

                // Viewport culling check: skip node if it is off-screen
                if (n.x < minSimX || n.x > maxSimX || n.y < minSimY || n.y > maxSimY) return;

                const isSelected = selectedNode && selectedNode.id === n.id;
                const isHovered = hoveredNode && hoveredNode.id === n.id;

                const matchesSearch = nodeMatchesSearch(n);
                const isPathActive = pathStartNode && pathEndNode && pathTracingNodes.has(pathStartNode.id) && pathTracingNodes.has(pathEndNode.id);
                
                let isHighlighted;
                if (isPathActive) {
                    isHighlighted = pathTracingNodes.has(n.id);
                } else {
                    isHighlighted = matchesSearch && (!selectedNode || activePaths.has(n.id)) && (!gitImpactOnly || gitImpactNodes.has(n.id));
                }
                
                const nodeOpacity = isHighlighted ? 1.0 : 0.03;

                let baseColor = "#10b981"; // FUNC
                if (n.type === "rule") {
                    baseColor = "#6366f1"; // RULE
                } else if (n.type === "unresolved") {
                    baseColor = "#f43f5e"; // UNRES
                }
                
                if (isPathActive) {
                    if (n.id === pathStartNode.id) {
                        baseColor = "#a5b4fc"; // Purple start node
                    } else if (n.id === pathEndNode.id) {
                        baseColor = "#f472b6"; // Pink end node
                    } else if (pathTracingNodes.has(n.id)) {
                        baseColor = "#818cf8"; // Lavender path connection node
                    }
                }

                const w = n.width;
                const h = n.height;
                const rx = n.x - w/2;
                const ry = n.y - h/2;

                ctx.beginPath();
                const radius = 6; // rounded corner radius
                ctx.moveTo(rx + radius, ry);
                ctx.lineTo(rx + w - radius, ry);
                ctx.quadraticCurveTo(rx + w, ry, rx + w, ry + radius);
                ctx.lineTo(rx + w, ry + h - radius);
                ctx.quadraticCurveTo(rx + w, ry + h, rx + w - radius, ry + h);
                ctx.lineTo(rx + radius, ry + h);
                ctx.quadraticCurveTo(rx, ry + h, rx, ry + h - radius);
                ctx.lineTo(rx, ry + radius);
                ctx.quadraticCurveTo(rx, ry, rx + radius, ry);
                ctx.closePath();

                // Glassmorphic node fill
                let fillAlpha = isSelected ? 0.35 : isHovered ? 0.22 : 0.10;
                ctx.fillStyle = hexToRgba(baseColor, fillAlpha * nodeOpacity);
                ctx.fill();

                // Border outline
                ctx.strokeStyle = isSelected ? hexToRgba("#ffffff", nodeOpacity) : isHovered ? hexToRgba(baseColor, 0.95 * nodeOpacity) : hexToRgba(baseColor, 0.55 * nodeOpacity);
                ctx.lineWidth = isSelected ? 2.0 : isHovered ? 1.5 : 1.0;
                
                // Represent unresolved node borders as dashed lines
                if (n.type === "unresolved") {
                    ctx.setLineDash([3, 3]);
                } else {
                    ctx.setLineDash([]);
                }
                ctx.stroke();
                ctx.setLineDash([]); // reset

                // Draw dynamic change propagation warnings (neon risk halos)
                if (hasGitChanges && n.id in gitRiskScores && isHighlighted) {
                    ctx.save();
                    const riskDist = gitRiskScores[n.id];
                    let glowColor = "rgba(249, 115, 22, 0.4)"; // Orange (1st degree)
                    let pulseFreq = 0.003;
                    if (riskDist === 0) {
                        glowColor = "rgba(239, 68, 68, 0.6)"; // Red (modified source)
                        pulseFreq = 0.005;
                    } else if (riskDist === 1) {
                        glowColor = "rgba(249, 115, 22, 0.45)"; // Orange (direct consumer)
                        pulseFreq = 0.003;
                    } else {
                        glowColor = "rgba(234, 179, 8, 0.25)"; // Yellow (secondary blast radius)
                        pulseFreq = 0.002;
                    }
                    
                    const pulseFactor = 0.5 + 0.5 * Math.sin(Date.now() * pulseFreq);
                    const padPulse = 3 + 4 * pulseFactor;
                    
                    ctx.shadowColor = glowColor;
                    ctx.shadowBlur = 10 * pulseFactor;
                    ctx.strokeStyle = glowColor;
                    ctx.lineWidth = isSelected ? 2.5 : isHovered ? 2.0 : 1.5;
                    
                    ctx.beginPath();
                    const rX = rx - padPulse/2;
                    const rY = ry - padPulse/2;
                    const rW = w + padPulse;
                    const rH = h + padPulse;
                    const rRadius = radius + padPulse/2;
                    
                    ctx.moveTo(rX + rRadius, rY);
                    ctx.lineTo(rX + rW - rRadius, rY);
                    ctx.quadraticCurveTo(rX + rW, rY, rX + rW, rY + rRadius);
                    ctx.lineTo(rX + rW, rY + rH - rRadius);
                    ctx.quadraticCurveTo(rX + rW, rY + rH, rX + rW - rRadius, rY + rH);
                    ctx.lineTo(rX + rRadius, rY + rH);
                    ctx.quadraticCurveTo(rX, rY + rH, rX, rY + rH - rRadius);
                    ctx.lineTo(rX, rY + rRadius);
                    ctx.quadraticCurveTo(rX, rY, rX + rRadius, rY);
                    ctx.closePath();
                    ctx.stroke();
                    ctx.restore();
                }

                // Draw orange highlight border for Git modified files (source)
                if (n.git_modified && isHighlighted) {
                    ctx.save();
                    ctx.shadowColor = "#f97316";
                    ctx.shadowBlur = 8;
                    ctx.strokeStyle = hexToRgba("#f97316", nodeOpacity);
                    ctx.lineWidth = isSelected ? 2.5 : isHovered ? 2.0 : 1.5;
                    ctx.beginPath();
                    ctx.moveTo(rx + radius, ry);
                    ctx.lineTo(rx + w - radius, ry);
                    ctx.quadraticCurveTo(rx + w, ry, rx + w, ry + radius);
                    ctx.lineTo(rx + w, ry + h - radius);
                    ctx.quadraticCurveTo(rx + w, ry + h, rx + w - radius, ry + h);
                    ctx.lineTo(rx + radius, ry + h);
                    ctx.quadraticCurveTo(rx, ry + h, rx, ry + h - radius);
                    ctx.lineTo(rx, ry + radius);
                    ctx.quadraticCurveTo(rx, ry, rx + radius, ry);
                    ctx.closePath();
                    ctx.stroke();
                    ctx.restore();
                }

                // Draw drop-shadow halo glows for active selections
                if (isSelected) {
                    ctx.save();
                    ctx.shadowColor = baseColor;
                    ctx.shadowBlur = 15;
                    ctx.beginPath();
                    ctx.moveTo(rx + radius, ry);
                    ctx.lineTo(rx + w - radius, ry);
                    ctx.quadraticCurveTo(rx + w, ry, rx + w, ry + radius);
                    ctx.lineTo(rx + w, ry + h - radius);
                    ctx.quadraticCurveTo(rx + w, ry + h, rx + w - radius, ry + h);
                    ctx.lineTo(rx + radius, ry + h);
                    ctx.quadraticCurveTo(rx, ry + h, rx, ry + h - radius);
                    ctx.lineTo(rx, ry + radius);
                    ctx.quadraticCurveTo(rx, ry, rx + radius, ry);
                    ctx.closePath();
                    ctx.strokeStyle = hexToRgba(baseColor, nodeOpacity);
                    ctx.stroke();
                    ctx.restore();
                }

                // Draw text inside the default pill badge capsule (no canvas card expansion, clean UI)
                ctx.font = isSelected ? "bold 9px sans-serif" : "9px sans-serif";
                ctx.fillStyle = isSelected ? hexToRgba("#ffffff", nodeOpacity) : isHovered ? hexToRgba("#f3f4f6", nodeOpacity) : hexToRgba("#cbd5e1", nodeOpacity);
                ctx.textAlign = "center";
                ctx.textBaseline = "middle";
                
                // Show folder name if group collapsed
                const displayName = isColGroup ? `📂 [Folder] ${n.file}` : n.name;
                ctx.fillText(displayName, n.x, n.y);
            });

            ctx.restore();
        }

        // Color brightness adjustment helper
        function adjustColorBrightness(hex, percent) {
            let num = parseInt(hex.replace("#",""), 16),
                amt = Math.round(2.55 * percent),
                R = (num >> 16) + amt,
                G = (num >> 8 & 0x00FF) + amt,
                B = (num & 0x0000FF) + amt;
            return "#" + (0x1000000 + (R<255?R<0?0:R:255)*0x10000 + (G<255?G<0?0:G:255)*0x100 + (B<255?B<0?0:B:255)).toString(16).slice(1);
        }

        // Color hex to RGBA converter for custom transparent curved edges
        function hexToRgba(hex, alpha) {
            let r = parseInt(hex.slice(1, 3), 16),
                g = parseInt(hex.slice(3, 5), 16),
                b = parseInt(hex.slice(5, 7), 16);
            return `rgba(${r}, ${g}, ${b}, ${alpha})`;
        }

        const minimapCanvas = document.getElementById("minimapCanvas");
        const mmCtx = minimapCanvas.getContext("2d");
        minimapCanvas.width = 150;
        minimapCanvas.height = 100;

        function drawMinimap() {
            mmCtx.clearRect(0, 0, 150, 100);
            
            const hideUnresolved = document.getElementById("hide-unresolved-cb").checked;
            
            // 1. Calculate bounding box of all active nodes
            let minX = Infinity, maxX = -Infinity;
            let minY = Infinity, maxY = -Infinity;
            nodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') return;
                minX = Math.min(minX, n.x);
                maxX = Math.max(maxX, n.x);
                minY = Math.min(minY, n.y);
                maxY = Math.max(maxY, n.y);
            });
            
            if (minX === Infinity) return;
            
            // Add padding around bounds
            const pad = 60;
            minX -= pad; maxX += pad;
            minY -= pad; maxY += pad;
            
            const boundsW = maxX - minX;
            const boundsH = maxY - minY;
            
            // Fit bounds into minimap aspect ratio
            const scaleX = 150 / boundsW;
            const scaleY = 100 / boundsH;
            const scale = Math.min(scaleX, scaleY) * 0.9;
            
            const dx = (150 - boundsW * scale) / 2;
            const dy = (100 - boundsH * scale) / 2;
            
            const toMinimap = (x, y) => ({
                x: (x - minX) * scale + dx,
                y: (y - minY) * scale + dy
            });
            
            // 2. Draw nodes on minimap
            nodes.forEach(n => {
                if (hideUnresolved && n.type === 'unresolved') return;
                const p = toMinimap(n.x, n.y);
                let color = "#10b981"; // FUNC
                if (n.type === "rule") color = "#6366f1"; // RULE
                else if (n.type === "unresolved") color = "#f43f5e"; // UNRES
                
                mmCtx.fillStyle = color;
                mmCtx.beginPath();
                mmCtx.arc(p.x, p.y, 2, 0, 2 * Math.PI);
                mmCtx.fill();
            });
            
            // 3. Draw viewport box on minimap
            const tl = toSimCoords(0, 0);
            const br = toSimCoords(width, height);
            
            const mTl = toMinimap(tl.x, tl.y);
            const mBr = toMinimap(br.x, br.y);
            
            mmCtx.strokeStyle = "rgba(255, 255, 255, 0.4)";
            mmCtx.lineWidth = 1;
            mmCtx.fillStyle = "rgba(255, 255, 255, 0.05)";
            mmCtx.beginPath();
            mmCtx.rect(mTl.x, mTl.y, mBr.x - mTl.x, mBr.y - mTl.y);
            mmCtx.fill();
            mmCtx.stroke();
        }

        // Animation loop
        function tick() {
            runSimulation();
            draw();
            drawMinimap();
            requestAnimationFrame(tick);
        }
        tick();

        // Screen Coordinates to Simulation coordinates converter
        function toSimCoords(x, y) {
            return {
                x: (x - transform.x) / transform.k,
                y: (y - transform.y) / transform.k
            };
        }

        // Double click to collapse/expand group cards
        canvas.addEventListener("dblclick", (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            const simMouse = toSimCoords(mouseX, mouseY);
            
            // Check if clicked inside a group card bounds
            let clickedGroup = null;
            
            const localGroups = {};
            nodes.forEach(n => {
                if (n.type === 'function' && n.file) {
                    localGroups[n.file] = localGroups[n.file] || [];
                    localGroups[n.file].push(n);
                }
            });
            
            const focusModeCb = document.getElementById("focus-mode-cb");
            const isFocusMode = focusModeCb && focusModeCb.checked && selectedNode;
            
            Object.entries(localGroups).forEach(([filename, groupNodes]) => {
                if (groupNodes.length < 2) return;
                let minX = Infinity, maxX = -Infinity;
                let minY = Infinity, maxY = -Infinity;
                groupNodes.forEach(n => {
                    if (isFocusMode && !selectedNodeActivePaths.has(n.id)) return;
                    minX = Math.min(minX, n.x - n.width/2);
                    maxX = Math.max(maxX, n.x + n.width/2);
                    minY = Math.min(minY, n.y - n.height/2);
                    maxY = Math.max(maxY, n.y + n.height/2);
                });
                if (minX === Infinity) return;
                
                const pad = 12;
                const rx = minX - pad;
                const ry = minY - pad - 12;
                const rw = (maxX - minX) + pad*2;
                const rh = (maxY - minY) + pad*2 + 12;
                
                if (simMouse.x >= rx && simMouse.x <= rx + rw &&
                    simMouse.y >= ry && simMouse.y <= ry + rh) {
                    clickedGroup = filename;
                }
            });
            
            if (clickedGroup) {
                if (collapsedGroups.has(clickedGroup)) {
                    collapsedGroups.delete(clickedGroup);
                } else {
                    collapsedGroups.add(clickedGroup);
                }
                isSimulating = true; // wake up physics to re-layout
                draw();
            }
        });

        // Mouse Interactions
        canvas.addEventListener("mousedown", (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            const simMouse = toSimCoords(mouseX, mouseY);
            
            const hideUnresolved = document.getElementById("hide-unresolved-cb").checked;
            const focusModeCb = document.getElementById("focus-mode-cb");
            const isFocusMode = focusModeCb && focusModeCb.checked && selectedNode;

            const localGroups = {};
            nodes.forEach(n => {
                if (n.type === 'function' && n.file) {
                    localGroups[n.file] = localGroups[n.file] || [];
                    localGroups[n.file].push(n);
                }
            });

            let clickedNode = null;
            for (let n of nodes) {
                if (hideUnresolved && n.type === 'unresolved') continue;
                if (isFocusMode && !selectedNodeActivePaths.has(n.id)) continue;
                
                // If collapsed group, skip secondary nodes
                if (n.file && collapsedGroups.has(n.file)) {
                    const primary = localGroups[n.file] && (localGroups[n.file].find(gn => !isFocusMode || selectedNodeActivePaths.has(gn.id)) || localGroups[n.file][0]);
                    if (primary !== n) continue;
                }

                const dx = n.x - simMouse.x;
                const dy = n.y - simMouse.y;
                const dist = Math.sqrt(dx*dx + dy*dy);
                if (dist <= n.radius + 5) {
                    clickedNode = n;
                    break;
                }
            }

            if (clickedNode) {
                draggedNode = clickedNode;
                selectNode(clickedNode);
            } else {
                isDraggingCanvas = true;
                dragStart.x = e.clientX - transform.x;
                dragStart.y = e.clientY - transform.y;
            }
        });

        canvas.addEventListener("mousemove", (e) => {
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            const simMouse = toSimCoords(mouseX, mouseY);

            mouseSim.x = simMouse.x;
            mouseSim.y = simMouse.y;

            const hideUnresolved = document.getElementById("hide-unresolved-cb").checked;
            const focusModeCb = document.getElementById("focus-mode-cb");
            const isFocusMode = focusModeCb && focusModeCb.checked && selectedNode;

            const localGroups = {};
            nodes.forEach(n => {
                if (n.type === 'function' && n.file) {
                    localGroups[n.file] = localGroups[n.file] || [];
                    localGroups[n.file].push(n);
                }
            });

            if (draggedNode) {
                draggedNode.x = simMouse.x;
                draggedNode.y = simMouse.y;
                draggedNode.vx = 0;
                draggedNode.vy = 0;
            } else if (isDraggingCanvas) {
                transform.x = e.clientX - dragStart.x;
                transform.y = e.clientY - dragStart.y;
            } else {
                // Hover detection
                let curHover = null;
                for (let n of nodes) {
                    if (hideUnresolved && n.type === 'unresolved') continue;
                    if (isFocusMode && !selectedNodeActivePaths.has(n.id)) continue;
                    
                    // If collapsed group, skip secondary nodes
                    if (n.file && collapsedGroups.has(n.file)) {
                        const primary = localGroups[n.file] && (localGroups[n.file].find(gn => !isFocusMode || selectedNodeActivePaths.has(gn.id)) || localGroups[n.file][0]);
                        if (primary !== n) continue;
                    }

                    const dx = n.x - simMouse.x;
                    const dy = n.y - simMouse.y;
                    const dist = Math.sqrt(dx*dx + dy*dy);
                    if (dist <= n.radius + 5) {
                        curHover = n;
                        break;
                    }
                }
                hoveredNode = curHover;
            }
        });

        canvas.addEventListener("mouseup", () => {
            draggedNode = null;
            isDraggingCanvas = false;
        });

        canvas.addEventListener("mouseleave", () => {
            draggedNode = null;
            isDraggingCanvas = false;
            mouseSim.x = null;
            mouseSim.y = null;
        });

        // Zoom mapping
        canvas.addEventListener("wheel", (e) => {
            e.preventDefault();
            const rect = canvas.getBoundingClientRect();
            const mouseX = e.clientX - rect.left;
            const mouseY = e.clientY - rect.top;
            const simMouse = toSimCoords(mouseX, mouseY);

            const zoomFactor = 1.12;
            const nextK = e.deltaY < 0 ? transform.k * zoomFactor : transform.k / zoomFactor;

            if (nextK < 0.1 || nextK > 10) return;

            transform.x = mouseX - simMouse.x * nextK;
            transform.y = mouseY - simMouse.y * nextK;
            transform.k = nextK;
        }, { passive: false });
        
        populateNodeList();
        if (graphData.selected_node_id) {
            setTimeout(() => {
                selectNodeById(graphData.selected_node_id);
            }, 100);
        }
    </script>
</body>
</html>
"""
