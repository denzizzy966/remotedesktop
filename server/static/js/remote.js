// Remote Desktop Viewer & Input Handler
class RemoteDesktopViewer {
    constructor() {
        this.ws = null;
        this.currentClientId = null;
        this.canvas = document.getElementById("remoteCanvas");
        this.ctx = this.canvas.getContext("2d");
        this.active = false;
        this.viewOnly = false;
        
        // Metrics
        this.frameCount = 0;
        this.fps = 0;
        this.fpsTimer = null;
        this.latency = 0;
        this.targetWidth = 1920;
        this.targetHeight = 1080;
        
        // Stream settings
        this.scale = 0.75;
        this.quality = 60;
        this.targetFps = 25;
        this.currentMonitor = 1;

        // Image object for rendering
        this.img = new Image();
        this.img.onload = () => this.renderFrame();

        this.initEventListeners();
    }

    initEventListeners() {
        // Prevent context menu on canvas (allows right-click on remote machine)
        this.canvas.addEventListener("contextmenu", (e) => {
            e.preventDefault();
        });

        // Mouse events
        this.canvas.addEventListener("mousemove", (e) => this.handleMouseMove(e));
        this.canvas.addEventListener("mousedown", (e) => this.handleMouseDown(e));
        this.canvas.addEventListener("mouseup", (e) => this.handleMouseUp(e));
        this.canvas.addEventListener("dblclick", (e) => this.handleMouseDblClick(e));
        this.canvas.addEventListener("wheel", (e) => this.handleWheel(e), { passive: false });

        // Keyboard events on canvas
        window.addEventListener("keydown", (e) => {
            if (!this.active || this.viewOnly) return;
            // If typing in input or textarea (e.g. terminal or modal input), don't intercept
            if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
            
            // Prevent common browser shortcuts from breaking remote session
            if (["Tab", "F5", "F12"].includes(e.key) || (e.ctrlKey && ["w", "r", "t", "p", "f"].includes(e.key.toLowerCase()))) {
                e.preventDefault();
            }
            this.sendKeyEvent("down", e.key, e.code);
        });

        window.addEventListener("keyup", (e) => {
            if (!this.active || this.viewOnly) return;
            if (["INPUT", "TEXTAREA"].includes(document.activeElement.tagName)) return;
            this.sendKeyEvent("up", e.key, e.code);
        });
    }

    clearCanvasPlaceholder(text = "Connecting...") {
        if (!this.canvas || !this.ctx) return;
        this.ctx.save();
        this.ctx.fillStyle = "#020617";
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);
        this.ctx.fillStyle = "#818cf8";
        this.ctx.font = "bold 16px 'Inter', sans-serif";
        this.ctx.textAlign = "center";
        this.ctx.textBaseline = "middle";
        this.ctx.fillText(text, this.canvas.width / 2, this.canvas.height / 2);
        this.ctx.restore();
    }

    startSession(clientId, clientData) {
        // 1. Cleanly close any existing session or socket first
        this.closeSession();

        this.currentClientId = clientId;
        this.active = true;
        this.frameCount = 0;
        this.latency = 0;

        // 2. Open modal and update labels immediately
        const modal = document.getElementById("remoteModal");
        if (modal) modal.classList.remove("hidden");
        
        const displayName = clientData.alias 
            ? `${clientData.alias} (${clientData.hostname})` 
            : `${clientData.hostname || 'Device'} (${clientData.ip_address || 'LAN'})`;
        document.getElementById("remoteTargetName").textContent = displayName;
        document.getElementById("remoteTargetOS").textContent = clientData.os_name || "Unknown OS";
        document.getElementById("remoteResolution").textContent = "Connecting...";
        document.getElementById("remoteFps").textContent = "0 FPS";
        document.getElementById("remoteLatency").textContent = "-";

        // 3. Clear canvas immediately with placeholder so old screen is NEVER shown
        this.clearCanvasPlaceholder(`Menghubungkan ke ${clientData.hostname || clientId}...`);

        // Setup monitor selector
        const monitorSelect = document.getElementById("monitorSelect");
        monitorSelect.innerHTML = "";
        const monitors = clientData.monitors || [{ index: 1, name: "Primary Display" }];
        monitors.forEach(m => {
            const opt = document.createElement("option");
            opt.value = m.index;
            opt.textContent = `${m.name} (${m.width}x${m.height})`;
            monitorSelect.appendChild(opt);
        });

        // Calculate and display FPS periodically
        this.fpsTimer = setInterval(() => {
            if (!this.active) return;
            document.getElementById("remoteFps").textContent = `${this.frameCount} FPS`;
            document.getElementById("remoteLatency").textContent = this.latency ? `${this.latency}ms` : "-";
            this.frameCount = 0;
        }, 1000);

        // Connect WebSocket
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const token = localStorage.getItem("admin_token") || "";
        const wsUrl = `${protocol}//${window.location.host}/ws/admin/remote/${clientId}?token=${encodeURIComponent(token)}`;
        
        const socket = new WebSocket(wsUrl);
        this.ws = socket;

        socket.onopen = () => {
            if (this.ws !== socket) return; // Stale socket check
            console.log(`[Remote] Connected to remote session for client: ${clientId}`);
            this.sendStreamSettings();
            this.canvas.focus();
        };

        socket.onmessage = (event) => {
            if (this.ws !== socket || !this.active) return;
            try {
                const msg = JSON.parse(event.data);
                if (msg.type === "frame") {
                    // Check that the frame belongs to the active client
                    if (msg.device_id && msg.device_id !== this.currentClientId) {
                        return; // Ignore frames from an older device
                    }
                    this.onFrameReceived(msg);
                }
            } catch (e) {
                console.error("[Remote] Error decoding frame message:", e);
            }
        };

        socket.onclose = () => {
            if (this.ws === socket) {
                console.log("[Remote] Remote session closed by server or network");
                this.closeSession();
            }
        };

        socket.onerror = (err) => {
            console.error("[Remote] WebSocket error:", err);
        };
    }

    closeSession() {
        this.active = false;
        if (this.fpsTimer) {
            clearInterval(this.fpsTimer);
            this.fpsTimer = null;
        }

        // Cleanly detach and close WebSocket
        if (this.ws) {
            const socket = this.ws;
            this.ws = null;
            socket.onopen = null;
            socket.onmessage = null;
            socket.onerror = null;
            socket.onclose = null;
            try {
                if (socket.readyState === WebSocket.OPEN) {
                    socket.send(JSON.stringify({ type: "close_session" }));
                }
                socket.close();
            } catch (e) {}
        }

        // Wipe image memory and clear canvas
        this.img.src = "";
        this.clearCanvasPlaceholder("Sesi Remote Ditutup");
        this.currentClientId = null;

        const modal = document.getElementById("remoteModal");
        if (modal) {
            modal.classList.add("hidden");
        }
    }

    onFrameReceived(msg) {
        this.frameCount++;
        if (msg.timestamp) {
            this.latency = Math.max(1, Math.round((Date.now() / 1000 - msg.timestamp) * 1000));
        }

        this.targetWidth = msg.width || 1920;
        this.targetHeight = msg.height || 1080;

        document.getElementById("remoteResolution").textContent = `${this.targetWidth} x ${this.targetHeight}`;

        // Set canvas native resolution to match target screen aspect ratio
        if (this.canvas.width !== msg.rendered_w || this.canvas.height !== msg.rendered_h) {
            this.canvas.width = msg.rendered_w || this.targetWidth;
            this.canvas.height = msg.rendered_h || this.targetHeight;
        }

        // Trigger image render
        this.img.src = "data:image/jpeg;base64," + msg.data;
    }

    renderFrame() {
        if (!this.active) return;
        this.ctx.drawImage(this.img, 0, 0, this.canvas.width, this.canvas.height);
    }

    // --- Coordinate Translation ---
    getNormalizedCoords(e) {
        const rect = this.canvas.getBoundingClientRect();
        const clientX = e.clientX - rect.left;
        const clientY = e.clientY - rect.top;

        const normX = Math.max(0, Math.min(1, clientX / rect.width));
        const normY = Math.max(0, Math.min(1, clientY / rect.height));

        return { x: normX, y: normY };
    }

    getMouseButton(e) {
        if (e.button === 0) return "left";
        if (e.button === 2) return "right";
        if (e.button === 1) return "middle";
        return "left";
    }

    // --- Mouse Handlers ---
    handleMouseMove(e) {
        if (!this.active || this.viewOnly || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        const coords = this.getNormalizedCoords(e);
        this.ws.send(JSON.stringify({
            type: "input_mouse",
            data: {
                action: "move",
                x: coords.x,
                y: coords.y
            }
        }));
    }

    handleMouseDown(e) {
        if (!this.active || this.viewOnly || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        const coords = this.getNormalizedCoords(e);
        const button = this.getMouseButton(e);
        this.ws.send(JSON.stringify({
            type: "input_mouse",
            data: {
                action: "down",
                button: button,
                x: coords.x,
                y: coords.y
            }
        }));
    }

    handleMouseUp(e) {
        if (!this.active || this.viewOnly || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        const coords = this.getNormalizedCoords(e);
        const button = this.getMouseButton(e);
        this.ws.send(JSON.stringify({
            type: "input_mouse",
            data: {
                action: "up",
                button: button,
                x: coords.x,
                y: coords.y
            }
        }));
    }

    handleMouseDblClick(e) {
        if (!this.active || this.viewOnly || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        const coords = this.getNormalizedCoords(e);
        this.ws.send(JSON.stringify({
            type: "input_mouse",
            data: {
                action: "dblclick",
                button: "left",
                x: coords.x,
                y: coords.y
            }
        }));
    }

    handleWheel(e) {
        if (!this.active || this.viewOnly || !this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        e.preventDefault();
        const coords = this.getNormalizedCoords(e);
        this.ws.send(JSON.stringify({
            type: "input_mouse",
            data: {
                action: "wheel",
                deltaY: e.deltaY,
                x: coords.x,
                y: coords.y
            }
        }));
    }

    // --- Keyboard Handlers ---
    sendKeyEvent(action, key, code) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        this.ws.send(JSON.stringify({
            type: "input_key",
            data: {
                action: action,
                key: key,
                code: code
            }
        }));
    }

    sendShortcut(keys) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        this.ws.send(JSON.stringify({
            type: "input_key",
            data: {
                action: "shortcut",
                keys: keys
            }
        }));
    }

    wakeScreen() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        this.ws.send(JSON.stringify({ type: "wake_screen" }));
        if (window.app && window.app.showToast) {
            window.app.showToast("Wake display signal sent to remote PC", "info");
        }
    }

    sendCtrlAltDel() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        this.ws.send(JSON.stringify({ type: "ctrl_alt_del" }));
        if (window.app && window.app.showToast) {
            window.app.showToast("Sent Ctrl+Alt+Del / Unlock signal", "info");
        }
    }

    sendPasteText(text) {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN || !text) return;
        this.ws.send(JSON.stringify({
            type: "input_key",
            data: {
                action: "type",
                text: text
            }
        }));
    }

    // --- Settings / Quality ---
    setQualityProfile(profile) {
        if (profile === "performance") {
            this.scale = 0.5;
            this.quality = 40;
            this.targetFps = 30;
        } else if (profile === "balanced") {
            this.scale = 0.75;
            this.quality = 60;
            this.targetFps = 25;
        } else if (profile === "high") {
            this.scale = 1.0;
            this.quality = 80;
            this.targetFps = 20;
        }
        this.sendStreamSettings();
    }

    setMonitor(monitorIndex) {
        this.currentMonitor = parseInt(monitorIndex);
        this.sendStreamSettings();
    }

    sendStreamSettings() {
        if (!this.ws || this.ws.readyState !== WebSocket.OPEN) return;
        this.ws.send(JSON.stringify({
            type: "update_stream_settings",
            scale: this.scale,
            quality: this.quality,
            fps: this.targetFps,
            monitor: this.currentMonitor
        }));
    }

    toggleViewOnly() {
        this.viewOnly = !this.viewOnly;
        const btn = document.getElementById("viewOnlyBtn");
        if (this.viewOnly) {
            btn.classList.add("bg-amber-600", "text-white");
            btn.classList.remove("bg-slate-700", "text-slate-300");
            btn.innerHTML = '<i class="fa-solid fa-eye mr-1"></i> View Only (Active)';
        } else {
            btn.classList.remove("bg-amber-600", "text-white");
            btn.classList.add("bg-slate-700", "text-slate-300");
            btn.innerHTML = '<i class="fa-solid fa-gamepad mr-1"></i> Controlling';
        }
    }

    toggleFullscreen() {
        const elem = document.getElementById("remoteModalContent");
        if (!document.fullscreenElement) {
            elem.requestFullscreen().catch(err => {
                alert(`Error attempting to enable fullscreen: ${err.message}`);
            });
        } else {
            document.exitFullscreen();
        }
    }
}

window.remoteViewer = new RemoteDesktopViewer();
