// Admin Dashboard Application Logic
class AdminDashboard {
    constructor() {
        this.clients = new Map();
        this.ws = null;
        this.searchQuery = "";
        this.osFilter = "all";
        this.statusFilter = "all";
        this.viewMode = localStorage.getItem("admin_view_mode") || "grid_preview";
        this.activeTerminalClientId = null;
        this.activeProcessClientId = null;
        this.token = localStorage.getItem("admin_token") || "";

        this.checkAuthAndInit();
    }

    async checkAuthAndInit() {
        if (!this.token) {
            window.location.href = "/login";
            return;
        }

        try {
            const res = await fetch(`/api/auth/verify?token=${encodeURIComponent(this.token)}`);
            const data = await res.json();
            if (!data.authenticated) {
                localStorage.removeItem("admin_token");
                window.location.href = "/login";
                return;
            }
        } catch (e) {
            console.error("Auth verification error:", e);
        }

        this.updateViewModeButtons();
        this.initWebSocket();
        this.initEventListeners();
        this.fetchServerInfo();
        
        // Refresh server info every 10s
        setInterval(() => this.fetchServerInfo(), 10000);
    }

    async authFetch(url, options = {}) {
        options.headers = options.headers || {};
        if (this.token) {
            options.headers["Authorization"] = "Bearer " + this.token;
        }
        const res = await fetch(url, options);
        if (res.status === 401) {
            localStorage.removeItem("admin_token");
            window.location.href = "/login";
            throw new Error("Unauthorized");
        }
        return res;
    }

    initWebSocket() {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const wsUrl = `${protocol}//${window.location.host}/ws/admin/dashboard?token=${encodeURIComponent(this.token)}`;

        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
            console.log("[Dashboard] WebSocket connected.");
            document.getElementById("serverStatusBadge").innerHTML = `
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-emerald-500 mr-1.5 pulse-dot"></span>
                <span>Server Online</span>
            `;
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this.handleMessage(msg);
            } catch (e) {
                console.error("[Dashboard] Error parsing ws message:", e);
            }
        };

        this.ws.onclose = () => {
            console.log("[Dashboard] WebSocket disconnected. Reconnecting in 3s...");
            document.getElementById("serverStatusBadge").innerHTML = `
                <span class="inline-block w-2.5 h-2.5 rounded-full bg-rose-500 mr-1.5"></span>
                <span>Server Disconnected</span>
            `;
            setTimeout(() => this.initWebSocket(), 3000);
        };

        this.ws.onerror = (err) => {
            console.error("[Dashboard] WebSocket error:", err);
        };
    }

    handleMessage(msg) {
        if (msg.type === "initial_state") {
            this.clients.clear();
            (msg.clients || []).forEach(c => this.clients.set(c.device_id, c));
            this.renderDashboard();
        } else if (msg.type === "client_updated") {
            this.clients.set(msg.client.device_id, msg.client);
            this.renderDashboard();
        } else if (msg.type === "client_telemetry") {
            let client = this.clients.get(msg.client_id);
            if (!client) {
                // If client not yet in local map, create entry dynamically
                client = {
                    device_id: msg.client_id,
                    hostname: (msg.data && msg.data.hostname) || "Device",
                    username: (msg.data && msg.data.username) || "",
                    ip_address: (msg.data && msg.data.ip_address) || "127.0.0.1",
                    os_name: (msg.data && msg.data.os_name) || "Unknown OS",
                    os_type: (msg.data && msg.data.os_type) || "unknown",
                    status: msg.status || "online",
                    last_seen: Date.now() / 1000,
                    metrics: msg.data || {},
                    thumbnail: msg.thumbnail || "",
                    monitors: []
                };
                this.clients.set(msg.client_id, client);
            } else {
                client.metrics = msg.data;
                client.status = msg.status || "online";
                client.last_seen = Date.now() / 1000;
                if (msg.thumbnail) {
                    client.thumbnail = msg.thumbnail;
                }
                if (msg.data && msg.data.ip_address) client.ip_address = msg.data.ip_address;
                if (msg.data && msg.data.hostname) client.hostname = msg.data.hostname;
            }
            this.renderDashboard();
        } else if (msg.type === "client_status") {
            const client = this.clients.get(msg.client_id);
            if (client) {
                client.status = msg.status;
                this.renderDashboard();
            }
        } else if (msg.type === "client_disconnected") {
            const client = this.clients.get(msg.client_id);
            if (client) {
                client.status = "offline";
                this.renderDashboard();
            }
        }
    }

    async fetchServerInfo() {
        try {
            const res = await fetch("/api/server_info");
            const data = await res.json();
            document.getElementById("serverIpText").textContent = `${data.server_ip}:${data.port}`;
        } catch (e) {
            console.error("Error fetching server info:", e);
        }
    }

    initEventListeners() {
        // Search input
        document.getElementById("searchInput").addEventListener("input", (e) => {
            this.searchQuery = e.target.value.toLowerCase().trim();
            this.renderDashboard();
        });

        // OS Filter
        document.getElementById("osFilter").addEventListener("change", (e) => {
            this.osFilter = e.target.value;
            this.renderDashboard();
        });

        // Status Filter
        document.getElementById("statusFilter").addEventListener("change", (e) => {
            this.statusFilter = e.target.value;
            this.renderDashboard();
        });

        // Terminal command submit
        document.getElementById("terminalForm").addEventListener("submit", (e) => {
            e.preventDefault();
            this.sendTerminalCommand();
        });

        // Change Password Form
        const passForm = document.getElementById("changePasswordForm");
        if (passForm) {
            passForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.submitChangePassword();
            });
        }

        // Server Settings Form
        const serverForm = document.getElementById("serverSettingsForm");
        if (serverForm) {
            serverForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.submitServerSettings();
            });
        }

        // Device Note & Alias Form
        const noteForm = document.getElementById("noteForm");
        if (noteForm) {
            noteForm.addEventListener("submit", (e) => {
                e.preventDefault();
                this.submitNoteForm();
            });
        }
    }

    getFilteredClients() {
        const list = Array.from(this.clients.values());
        return list.filter(c => {
            // Search query (matches alias, note, hostname, IP, username, or device ID)
            const matchesSearch = !this.searchQuery || 
                (c.alias && c.alias.toLowerCase().includes(this.searchQuery)) ||
                (c.note && c.note.toLowerCase().includes(this.searchQuery)) ||
                (c.hostname && c.hostname.toLowerCase().includes(this.searchQuery)) ||
                (c.ip_address && c.ip_address.toLowerCase().includes(this.searchQuery)) ||
                (c.username && c.username.toLowerCase().includes(this.searchQuery)) ||
                (c.device_id && c.device_id.toLowerCase().includes(this.searchQuery));

            // OS Filter
            let matchesOS = true;
            if (this.osFilter === "windows") matchesOS = (c.os_type === "windows");
            if (this.osFilter === "linux") matchesOS = (c.os_type === "linux");

            // Status Filter
            let matchesStatus = true;
            if (this.statusFilter === "online") matchesStatus = (c.status === "online" || c.status === "in_session");
            if (this.statusFilter === "in_session") matchesStatus = (c.status === "in_session");
            if (this.statusFilter === "offline") matchesStatus = (c.status === "offline");

            return matchesSearch && matchesOS && matchesStatus;
        });
    }

    setViewMode(mode) {
        if (!["grid_preview", "grid_compact", "list"].includes(mode)) {
            mode = "grid_preview";
        }
        this.viewMode = mode;
        localStorage.setItem("admin_view_mode", mode);
        this.updateViewModeButtons();
        this.renderDashboard();
    }

    updateViewModeButtons() {
        const modes = [
            { id: "viewBtnGridPreview", mode: "grid_preview" },
            { id: "viewBtnGridCompact", mode: "grid_compact" },
            { id: "viewBtnList", mode: "list" }
        ];
        modes.forEach(m => {
            const btn = document.getElementById(m.id);
            if (!btn) return;
            if (this.viewMode === m.mode) {
                btn.className = "px-2.5 py-1.5 rounded-md text-xs font-semibold flex items-center space-x-1.5 bg-indigo-600 text-white shadow-sm transition";
            } else {
                btn.className = "px-2.5 py-1.5 rounded-md text-xs font-medium flex items-center space-x-1.5 text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition";
            }
        });
    }

    renderDashboard() {
        const allClients = Array.from(this.clients.values());
        const filtered = this.getFilteredClients();

        // Update Top Summary Stats
        const totalCount = allClients.length;
        const onlineCount = allClients.filter(c => c.status === "online" || c.status === "in_session").length;
        const inSessionCount = allClients.filter(c => c.status === "in_session").length;
        
        let totalCpu = 0, totalRam = 0, activeCount = 0;
        allClients.forEach(c => {
            if (c.status !== "offline" && c.metrics) {
                totalCpu += (c.metrics.cpu_percent || 0);
                totalRam += (c.metrics.ram_percent || 0);
                activeCount++;
            }
        });

        const avgCpu = activeCount > 0 ? (totalCpu / activeCount).toFixed(1) : "0";
        const avgRam = activeCount > 0 ? (totalRam / activeCount).toFixed(1) : "0";

        document.getElementById("statTotalClients").textContent = totalCount;
        document.getElementById("statOnlineClients").textContent = onlineCount;
        document.getElementById("statInSessionClients").textContent = inSessionCount;
        document.getElementById("statAvgUsage").textContent = `${avgCpu}% / ${avgRam}%`;

        // Render Client Grid / List Container
        const grid = document.getElementById("clientGrid");
        const emptyState = document.getElementById("emptyState");

        if (filtered.length === 0) {
            grid.innerHTML = "";
            emptyState.classList.remove("hidden");
            return;
        }

        emptyState.classList.add("hidden");

        // 3 View Modes
        if (this.viewMode === "grid_compact") {
            // Mode 2: Grid Minimalis (Nama, IP, Tombol Aksi)
            grid.className = "grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4";
            grid.innerHTML = filtered.map(c => this.generateClientCardCompactHtml(c)).join("");
        } else if (this.viewMode === "list") {
            // Mode 3: List / Tabel
            grid.className = "w-full";
            grid.innerHTML = this.generateClientListTableHtml(filtered);
        } else {
            // Mode 1 (Default): Grid dengan Live Screen Preview
            grid.className = "grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6";
            grid.innerHTML = filtered.map(c => this.generateClientCardPreviewHtml(c)).join("");
        }
    }

    generateClientCardPreviewHtml(c) {
        const m = c.metrics || {};
        const isOnline = c.status === "online" || c.status === "in_session";
        const isInSession = c.status === "in_session";

        // Status Badge
        let statusBadge = '';
        if (isInSession) {
            statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-900/80 text-indigo-300 border border-indigo-500/30">
                <span class="w-2 h-2 mr-1.5 rounded-full bg-indigo-400 animate-pulse"></span> In Session
            </span>`;
        } else if (isOnline) {
            statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-900/80 text-emerald-300 border border-emerald-500/30">
                <span class="w-2 h-2 mr-1.5 rounded-full bg-emerald-400"></span> Online
            </span>`;
        } else {
            statusBadge = `<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                <span class="w-2 h-2 mr-1.5 rounded-full bg-slate-500"></span> Offline
            </span>`;
        }

        // OS Badge & Icon
        let osIcon = '<i class="fa-brands fa-linux text-amber-400 text-lg"></i>';
        let osBadgeColor = "bg-amber-950/40 text-amber-300 border-amber-800/50";
        if (c.os_type === "windows") {
            osIcon = '<i class="fa-brands fa-windows text-blue-400 text-lg"></i>';
            osBadgeColor = "bg-blue-950/40 text-blue-300 border-blue-800/50";
        } else if (c.os_name && c.os_name.toLowerCase().includes("ubuntu")) {
            osIcon = '<i class="fa-brands fa-ubuntu text-orange-400 text-lg"></i>';
            osBadgeColor = "bg-orange-950/40 text-orange-300 border-orange-800/50";
        } else if (c.os_name && c.os_name.toLowerCase().includes("mint")) {
            osIcon = '<i class="fa-brands fa-linux text-emerald-400 text-lg"></i>';
            osBadgeColor = "bg-emerald-950/40 text-emerald-300 border-emerald-800/50";
        }

        // CPU & RAM percentage helpers
        const cpuPct = m.cpu_percent != null ? m.cpu_percent : 0;
        const ramPct = m.ram_percent != null ? m.ram_percent : 0;
        const diskPct = m.disk_percent != null ? m.disk_percent : 0;

        const cpuColor = cpuPct > 80 ? "bg-rose-500" : (cpuPct > 60 ? "bg-amber-500" : "bg-emerald-500");
        const ramColor = ramPct > 85 ? "bg-rose-500" : (ramPct > 65 ? "bg-amber-500" : "bg-indigo-500");

        // Screen thumbnail preview
        const thumbnailSrc = c.thumbnail ? c.thumbnail : "";
        const previewBlock = thumbnailSrc ? `
            <div class="relative w-full h-36 bg-slate-950 rounded-lg overflow-hidden border border-slate-800 mb-3 group cursor-pointer" onclick="app.openRemoteViewer('${c.device_id}')">
                <img src="${thumbnailSrc}" class="w-full h-full object-cover group-hover:scale-105 transition duration-300" alt="Screen Preview">
                <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition flex items-center justify-center">
                    <span class="px-3 py-1.5 bg-indigo-600/90 text-white rounded-md text-xs font-medium shadow-lg backdrop-blur">
                        <i class="fa-solid fa-display mr-1"></i> Remote Control
                    </span>
                </div>
            </div>
        ` : `
            <div class="w-full h-24 bg-slate-950/60 rounded-lg border border-slate-800/80 mb-3 flex items-center justify-center text-slate-500 text-xs">
                <i class="fa-solid fa-desktop mr-2 text-slate-600"></i> ${isOnline ? "Thumbnail waiting..." : "Client Offline"}
            </div>
        `;

        // Custom Alias & Note handling
        const aliasText = (c.alias || "").trim();
        const noteText = (c.note || "").trim();

        // Title and Hostname display
        let titleHtml = '';
        if (aliasText) {
            titleHtml = `
                <div>
                    <h3 class="text-base font-bold text-white tracking-wide flex items-center group">
                        <span class="text-indigo-400 mr-1.5"><i class="fa-solid fa-tag text-xs"></i></span>
                        <span class="truncate max-w-[170px]" title="${aliasText}">${aliasText}</span>
                        <button onclick="app.openNoteModal('${c.device_id}')" title="Edit Nama & Catatan" class="ml-2 text-slate-500 hover:text-indigo-400 text-xs transition">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                    </h3>
                    <p class="text-[11px] text-slate-400 flex items-center mt-0.5">
                        <span class="font-mono text-slate-300">${c.hostname || 'Device'}</span>
                        <span class="mx-1 text-slate-600">&bull;</span>
                        <span>${c.username || 'user'}</span>
                    </p>
                </div>
            `;
        } else {
            titleHtml = `
                <div>
                    <h3 class="text-base font-semibold text-white tracking-wide flex items-center">
                        <span class="truncate max-w-[170px]">${c.hostname || "Unknown Host"}</span>
                        <button onclick="app.openNoteModal('${c.device_id}')" title="Beri Nama / Catatan" class="ml-2 px-1.5 py-0.5 rounded text-[10px] bg-slate-800 hover:bg-slate-700 text-slate-400 hover:text-indigo-300 border border-slate-700 transition">
                            <i class="fa-solid fa-tag mr-1 text-[9px]"></i> + Note
                        </button>
                    </h3>
                    <p class="text-[11px] text-slate-400 mt-0.5">${c.username || 'user'}</p>
                </div>
            `;
        }

        // Note Banner if note exists
        let noteHtml = '';
        if (noteText) {
            noteHtml = `
                <div class="mb-3 px-2.5 py-1.5 rounded-lg bg-slate-950/70 border border-slate-800/90 text-slate-300 text-[11px] flex items-start justify-between gap-2">
                    <div class="flex items-start space-x-1.5 overflow-hidden">
                        <i class="fa-regular fa-note-sticky text-amber-400 mt-0.5 shrink-0"></i>
                        <span class="truncate" title="${noteText}">${noteText}</span>
                    </div>
                    <button onclick="app.openNoteModal('${c.device_id}')" title="Edit Catatan" class="text-slate-500 hover:text-amber-300 shrink-0">
                        <i class="fa-solid fa-pen-to-square text-[10px]"></i>
                    </button>
                </div>
            `;
        }

        return `
        <div class="client-card bg-slate-900/90 border border-slate-800 rounded-xl p-5 shadow-xl backdrop-blur-sm flex flex-col justify-between">
            <div>
                <!-- Card Header -->
                <div class="flex items-start justify-between mb-3">
                    <div class="flex items-center space-x-3">
                        <div class="p-2.5 rounded-lg bg-slate-800 border border-slate-700/60">
                            ${osIcon}
                        </div>
                        <div>
                            ${titleHtml}
                            <div class="flex items-center space-x-2 mt-0.5">
                                <span class="text-xs font-mono text-cyan-400 select-all">${c.ip_address}</span>
                                <button onclick="app.copyText('${c.ip_address}')" title="Copy IP" class="text-slate-500 hover:text-slate-300 text-xs">
                                    <i class="fa-regular fa-copy"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                    <div>
                        ${statusBadge}
                    </div>
                </div>

                <!-- Note Banner (if any) -->
                ${noteHtml}

                <!-- OS & Uptime sub-bar -->
                <div class="flex items-center justify-between text-xs text-slate-400 py-1.5 border-y border-slate-800/80 mb-3">
                    <span class="inline-flex items-center px-2 py-0.5 rounded text-[11px] border ${osBadgeColor}">
                        ${c.os_name || "Unknown"}
                    </span>
                    <span class="flex items-center" title="System Uptime">
                        <i class="fa-regular fa-clock mr-1 text-slate-500"></i>
                        ${m.uptime_str || "N/A"}
                    </span>
                </div>

                <!-- Screen Preview -->
                ${previewBlock}

                <!-- System Usage Gauges -->
                <div class="space-y-2.5 text-xs mb-4">
                    <!-- CPU -->
                    <div>
                        <div class="flex justify-between text-slate-300 mb-1">
                            <span class="flex items-center"><i class="fa-solid fa-microchip mr-1.5 text-slate-400"></i> CPU (${m.cpu_count || "?"} Cores)</span>
                            <span class="font-semibold">${cpuPct}%</span>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div class="${cpuColor} h-2 rounded-full transition-all duration-500" style="width: ${cpuPct}%"></div>
                        </div>
                    </div>

                    <!-- RAM -->
                    <div>
                        <div class="flex justify-between text-slate-300 mb-1">
                            <span class="flex items-center"><i class="fa-solid fa-memory mr-1.5 text-slate-400"></i> RAM</span>
                            <span><strong class="font-semibold">${ramPct}%</strong> (${m.ram_used_gb || 0} / ${m.ram_total_gb || 0} GB)</span>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div class="${ramColor} h-2 rounded-full transition-all duration-500" style="width: ${ramPct}%"></div>
                        </div>
                    </div>

                    <!-- Disk -->
                    <div>
                        <div class="flex justify-between text-slate-300 mb-1">
                            <span class="flex items-center"><i class="fa-solid fa-hard-drive mr-1.5 text-slate-400"></i> Storage</span>
                            <span><strong class="font-semibold">${diskPct}%</strong> (${m.disk_used_gb || 0} / ${m.disk_total_gb || 0} GB)</span>
                        </div>
                        <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                            <div class="bg-cyan-500 h-2 rounded-full transition-all duration-500" style="width: ${diskPct}%"></div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Action Buttons Footer -->
            <div class="pt-3 border-t border-slate-800 grid grid-cols-5 gap-1.5">
                <button onclick="app.openRemoteViewer('${c.device_id}')" 
                    ${!isOnline ? 'disabled' : ''} 
                    class="col-span-2 flex items-center justify-center px-2.5 py-2 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-md">
                    <i class="fa-solid fa-display mr-1"></i> Remote
                </button>
                
                <button onclick="app.openTerminal('${c.device_id}')" 
                    ${!isOnline ? 'disabled' : ''} 
                    title="Open Remote Terminal"
                    class="flex items-center justify-center p-2 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition border border-slate-700">
                    <i class="fa-solid fa-terminal"></i>
                </button>

                <button onclick="app.openProcessManager('${c.device_id}')" 
                    ${!isOnline ? 'disabled' : ''} 
                    title="Process / Task Manager"
                    class="flex items-center justify-center p-2 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition border border-slate-700">
                    <i class="fa-solid fa-list-check"></i>
                </button>

                <button onclick="app.openNoteModal('${c.device_id}')" 
                    title="Beri Nama & Catatan PC"
                    class="flex items-center justify-center p-2 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 transition border border-slate-700 hover:text-amber-300">
                    <i class="fa-solid fa-pen-to-square"></i>
                </button>
            </div>
            
            <!-- Power Controls Row -->
            <div class="mt-2 flex justify-between items-center text-[11px] text-slate-400 px-1">
                <span>Power:</span>
                <div class="flex space-x-2">
                    <button onclick="app.confirmPowerAction('${c.device_id}', 'lock')" ${!isOnline ? 'disabled' : ''} class="hover:text-amber-400 disabled:opacity-30" title="Lock Screen">
                        <i class="fa-solid fa-lock"></i> Lock
                    </button>
                    <button onclick="app.confirmPowerAction('${c.device_id}', 'reboot')" ${!isOnline ? 'disabled' : ''} class="hover:text-sky-400 disabled:opacity-30" title="Reboot System">
                        <i class="fa-solid fa-rotate-right"></i> Reboot
                    </button>
                    <button onclick="app.confirmPowerAction('${c.device_id}', 'shutdown')" ${!isOnline ? 'disabled' : ''} class="hover:text-rose-400 disabled:opacity-30" title="Shutdown System">
                        <i class="fa-solid fa-power-off"></i> Off
                    </button>
                </div>
            </div>
        </div>
        `;
    }

    generateClientCardHtml(c) {
        return this.generateClientCardPreviewHtml(c);
    }

    // --- Mode 2: Grid Minimalis (Nama, IP, dan Tombol Aksi) ---
    generateClientCardCompactHtml(c) {
        const m = c.metrics || {};
        const isOnline = c.status === "online" || c.status === "in_session";
        const isInSession = c.status === "in_session";

        // Status Badge
        let statusBadge = '';
        if (isInSession) {
            statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-indigo-900/80 text-indigo-300 border border-indigo-500/30">
                <span class="w-1.5 h-1.5 mr-1 rounded-full bg-indigo-400 animate-pulse"></span> In Session
            </span>`;
        } else if (isOnline) {
            statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-900/80 text-emerald-300 border border-emerald-500/30">
                <span class="w-1.5 h-1.5 mr-1 rounded-full bg-emerald-400"></span> Online
            </span>`;
        } else {
            statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                <span class="w-1.5 h-1.5 mr-1 rounded-full bg-slate-500"></span> Offline
            </span>`;
        }

        // OS Icon
        let osIcon = '<i class="fa-brands fa-linux text-amber-400 text-base"></i>';
        if (c.os_type === "windows") {
            osIcon = '<i class="fa-brands fa-windows text-blue-400 text-base"></i>';
        } else if (c.os_name && c.os_name.toLowerCase().includes("ubuntu")) {
            osIcon = '<i class="fa-brands fa-ubuntu text-orange-400 text-base"></i>';
        } else if (c.os_name && c.os_name.toLowerCase().includes("mint")) {
            osIcon = '<i class="fa-brands fa-linux text-emerald-400 text-base"></i>';
        }

        const cpuPct = m.cpu_percent != null ? m.cpu_percent : 0;
        const ramPct = m.ram_percent != null ? m.ram_percent : 0;

        const aliasText = (c.alias || "").trim();
        const noteText = (c.note || "").trim();

        let titleHtml = '';
        if (aliasText) {
            titleHtml = `
                <div class="min-w-0">
                    <h3 class="text-sm font-bold text-white tracking-wide flex items-center group">
                        <span class="text-indigo-400 mr-1 shrink-0"><i class="fa-solid fa-tag text-[10px]"></i></span>
                        <span class="truncate max-w-[140px]" title="${aliasText}">${aliasText}</span>
                        <button onclick="app.openNoteModal('${c.device_id}')" title="Edit Nama & Catatan" class="ml-1.5 text-slate-500 hover:text-indigo-400 text-[10px] transition shrink-0">
                            <i class="fa-solid fa-pen"></i>
                        </button>
                    </h3>
                    <p class="text-[10px] text-slate-400 truncate max-w-[140px]">${c.hostname || 'Device'}</p>
                </div>
            `;
        } else {
            titleHtml = `
                <div class="min-w-0">
                    <h3 class="text-sm font-semibold text-white tracking-wide flex items-center">
                        <span class="truncate max-w-[140px]" title="${c.hostname || 'Unknown'}">${c.hostname || "Unknown Host"}</span>
                        <button onclick="app.openNoteModal('${c.device_id}')" title="Beri Nama / Catatan" class="ml-1 text-slate-500 hover:text-indigo-400 text-[10px] transition shrink-0">
                            <i class="fa-solid fa-tag"></i>
                        </button>
                    </h3>
                    <p class="text-[10px] text-slate-400 truncate max-w-[140px]">${c.username || 'user'}</p>
                </div>
            `;
        }

        let noteHtml = '';
        if (noteText) {
            noteHtml = `
                <div class="mb-2 px-2 py-1 rounded bg-slate-950/70 border border-slate-800 text-amber-300/90 text-[10px] flex items-center justify-between gap-1.5">
                    <span class="truncate" title="${noteText}">
                        <i class="fa-regular fa-note-sticky text-amber-400 mr-1"></i>${noteText}
                    </span>
                    <button onclick="app.openNoteModal('${c.device_id}')" class="text-slate-500 hover:text-amber-300 shrink-0">
                        <i class="fa-solid fa-pen text-[9px]"></i>
                    </button>
                </div>
            `;
        }

        return `
        <div class="client-card bg-slate-900/90 border border-slate-800 hover:border-slate-700/80 rounded-xl p-3.5 shadow-md backdrop-blur-sm flex flex-col justify-between">
            <div>
                <!-- Header: OS Icon, Name, Status -->
                <div class="flex items-start justify-between gap-2 mb-2">
                    <div class="flex items-center space-x-2.5 min-w-0">
                        <div class="p-2 rounded-lg bg-slate-800 border border-slate-700/60 shrink-0">
                            ${osIcon}
                        </div>
                        ${titleHtml}
                    </div>
                    <div class="shrink-0">
                        ${statusBadge}
                    </div>
                </div>

                <!-- IP Address Box -->
                <div class="flex items-center justify-between text-xs py-1 px-2 bg-slate-950/80 rounded border border-slate-800/80 mb-2">
                    <div class="flex items-center space-x-1.5 min-w-0">
                        <i class="fa-solid fa-network-wired text-slate-500 text-[10px]"></i>
                        <span class="font-mono text-cyan-400 font-semibold truncate select-all text-xs">${c.ip_address}</span>
                    </div>
                    <button onclick="app.copyText('${c.ip_address}')" title="Copy IP" class="text-slate-500 hover:text-slate-300 text-xs px-0.5">
                        <i class="fa-regular fa-copy"></i>
                    </button>
                </div>

                <!-- Note (if any) -->
                ${noteHtml}

                <!-- Sub-info: OS Name & CPU/RAM usage -->
                <div class="flex items-center justify-between text-[10px] text-slate-400 mb-3 px-0.5">
                    <span class="truncate max-w-[110px]" title="${c.os_name || 'OS'}">
                        ${c.os_name ? c.os_name.replace('Microsoft ', '') : 'Unknown'}
                    </span>
                    <span class="font-mono text-slate-300">
                        <span class="${cpuPct > 80 ? 'text-rose-400 font-bold' : 'text-slate-400'}">C:${cpuPct}%</span>
                        <span class="text-slate-600 mx-0.5">/</span>
                        <span class="${ramPct > 85 ? 'text-rose-400 font-bold' : 'text-slate-400'}">R:${ramPct}%</span>
                    </span>
                </div>
            </div>

            <!-- Action Buttons Footer -->
            <div class="pt-2 border-t border-slate-800">
                <div class="grid grid-cols-4 gap-1.5">
                    <button onclick="app.openRemoteViewer('${c.device_id}')" 
                        ${!isOnline ? 'disabled' : ''} 
                        class="col-span-2 flex items-center justify-center px-2 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm">
                        <i class="fa-solid fa-display mr-1"></i> Remote
                    </button>
                    
                    <button onclick="app.openTerminal('${c.device_id}')" 
                        ${!isOnline ? 'disabled' : ''} 
                        title="Remote Terminal"
                        class="flex items-center justify-center p-1.5 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition border border-slate-700">
                        <i class="fa-solid fa-terminal"></i>
                    </button>

                    <button onclick="app.openProcessManager('${c.device_id}')" 
                        ${!isOnline ? 'disabled' : ''} 
                        title="Task Manager"
                        class="flex items-center justify-center p-1.5 rounded-lg text-xs font-medium text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition border border-slate-700">
                        <i class="fa-solid fa-list-check"></i>
                    </button>
                </div>

                <!-- Mini Power Controls -->
                <div class="mt-2 flex justify-between items-center text-[10px] text-slate-500 px-0.5">
                    <span class="font-mono text-[9px] text-slate-600 truncate max-w-[80px]" title="${c.device_id}">${c.device_id}</span>
                    <div class="flex items-center space-x-2">
                        <button onclick="app.confirmPowerAction('${c.device_id}', 'lock')" ${!isOnline ? 'disabled' : ''} class="hover:text-amber-400 disabled:opacity-30 transition" title="Lock Screen">
                            <i class="fa-solid fa-lock"></i>
                        </button>
                        <button onclick="app.confirmPowerAction('${c.device_id}', 'reboot')" ${!isOnline ? 'disabled' : ''} class="hover:text-sky-400 disabled:opacity-30 transition" title="Reboot System">
                            <i class="fa-solid fa-rotate-right"></i>
                        </button>
                        <button onclick="app.confirmPowerAction('${c.device_id}', 'shutdown')" ${!isOnline ? 'disabled' : ''} class="hover:text-rose-400 disabled:opacity-30 transition" title="Shutdown System">
                            <i class="fa-solid fa-power-off"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        `;
    }

    // --- Mode 3: List / Tabel View ---
    generateClientListTableHtml(clients) {
        const rowsHtml = clients.map(c => {
            const m = c.metrics || {};
            const isOnline = c.status === "online" || c.status === "in_session";
            const isInSession = c.status === "in_session";

            // Status Badge
            let statusBadge = '';
            if (isInSession) {
                statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-indigo-900/80 text-indigo-300 border border-indigo-500/30">
                    <span class="w-2 h-2 mr-1.5 rounded-full bg-indigo-400 animate-pulse"></span> In Session
                </span>`;
            } else if (isOnline) {
                statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-900/80 text-emerald-300 border border-emerald-500/30">
                    <span class="w-2 h-2 mr-1.5 rounded-full bg-emerald-400"></span> Online
                </span>`;
            } else {
                statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold bg-slate-800 text-slate-400 border border-slate-700">
                    <span class="w-2 h-2 mr-1.5 rounded-full bg-slate-500"></span> Offline
                </span>`;
            }

            // OS Icon
            let osIcon = '<i class="fa-brands fa-linux text-amber-400 text-base"></i>';
            if (c.os_type === "windows") {
                osIcon = '<i class="fa-brands fa-windows text-blue-400 text-base"></i>';
            } else if (c.os_name && c.os_name.toLowerCase().includes("ubuntu")) {
                osIcon = '<i class="fa-brands fa-ubuntu text-orange-400 text-base"></i>';
            } else if (c.os_name && c.os_name.toLowerCase().includes("mint")) {
                osIcon = '<i class="fa-brands fa-linux text-emerald-400 text-base"></i>';
            }

            const cpuPct = m.cpu_percent != null ? m.cpu_percent : 0;
            const ramPct = m.ram_percent != null ? m.ram_percent : 0;
            const diskPct = m.disk_percent != null ? m.disk_percent : 0;

            const aliasText = (c.alias || "").trim();
            const noteText = (c.note || "").trim();

            let titleHtml = '';
            if (aliasText) {
                titleHtml = `
                    <div class="flex items-center space-x-1.5">
                        <span class="text-indigo-400"><i class="fa-solid fa-tag text-xs"></i></span>
                        <span class="font-bold text-white text-sm hover:text-indigo-300 cursor-pointer" onclick="app.openNoteModal('${c.device_id}')">${aliasText}</span>
                        <span class="text-slate-400 text-xs">(${c.hostname || 'Device'})</span>
                    </div>
                `;
            } else {
                titleHtml = `
                    <div class="flex items-center space-x-1.5">
                        <span class="font-semibold text-white text-sm hover:text-indigo-300 cursor-pointer" onclick="app.openNoteModal('${c.device_id}')">${c.hostname || "Unknown Host"}</span>
                    </div>
                `;
            }

            let noteCell = '';
            if (noteText) {
                noteCell = `
                    <div class="flex items-center space-x-1 text-amber-300/90 text-xs group cursor-pointer" onclick="app.openNoteModal('${c.device_id}')">
                        <i class="fa-regular fa-note-sticky text-amber-400 mr-0.5"></i>
                        <span class="truncate max-w-[140px]" title="${noteText}">${noteText}</span>
                        <i class="fa-solid fa-pen text-[9px] text-slate-500 group-hover:text-amber-300 opacity-0 group-hover:opacity-100 transition"></i>
                    </div>
                `;
            } else {
                noteCell = `
                    <button onclick="app.openNoteModal('${c.device_id}')" class="text-slate-500 hover:text-indigo-400 text-xs transition">
                        <i class="fa-solid fa-plus text-[10px] mr-1"></i>Note
                    </button>
                `;
            }

            return `
            <tr class="hover:bg-slate-800/40 transition">
                <!-- Status -->
                <td class="py-3 px-4 whitespace-nowrap">
                    ${statusBadge}
                </td>

                <!-- Device & Name -->
                <td class="py-3 px-4">
                    <div class="flex items-center space-x-3">
                        <div class="p-2 rounded-lg bg-slate-800 border border-slate-700/60 shrink-0">
                            ${osIcon}
                        </div>
                        <div>
                            ${titleHtml}
                            <div class="text-[11px] text-slate-500 font-mono flex items-center space-x-1.5">
                                <span>${c.username || 'user'}</span>
                                <span>&bull;</span>
                                <span>${c.device_id}</span>
                            </div>
                        </div>
                    </div>
                </td>

                <!-- IP Address -->
                <td class="py-3 px-4 whitespace-nowrap">
                    <div class="flex items-center space-x-1.5">
                        <span class="font-mono text-cyan-400 font-semibold select-all text-xs">${c.ip_address}</span>
                        <button onclick="app.copyText('${c.ip_address}')" title="Copy IP" class="text-slate-500 hover:text-slate-300 text-xs">
                            <i class="fa-regular fa-copy"></i>
                        </button>
                    </div>
                </td>

                <!-- OS & Uptime -->
                <td class="py-3 px-4 whitespace-nowrap">
                    <div class="text-xs text-slate-300">${c.os_name || 'Unknown'}</div>
                    <div class="text-[11px] text-slate-500 flex items-center mt-0.5">
                        <i class="fa-regular fa-clock mr-1 text-slate-500"></i>
                        <span>${m.uptime_str || "N/A"}</span>
                    </div>
                </td>

                <!-- CPU / RAM / Disk -->
                <td class="py-3 px-4 whitespace-nowrap">
                    <div class="flex items-center space-x-2 text-xs">
                        <span class="${cpuPct > 80 ? 'text-rose-400 font-bold' : 'text-slate-300'}" title="CPU Usage">
                            <i class="fa-solid fa-microchip text-slate-500 mr-1"></i>${cpuPct}%
                        </span>
                        <span class="text-slate-600">|</span>
                        <span class="${ramPct > 85 ? 'text-rose-400 font-bold' : 'text-slate-300'}" title="RAM Usage (${m.ram_used_gb || 0}/${m.ram_total_gb || 0} GB)">
                            <i class="fa-solid fa-memory text-slate-500 mr-1"></i>${ramPct}%
                        </span>
                        <span class="text-slate-600">|</span>
                        <span class="text-slate-400" title="Storage Usage">
                            <i class="fa-solid fa-hard-drive text-slate-500 mr-1"></i>${diskPct}%
                        </span>
                    </div>
                </td>

                <!-- Catatan / Note -->
                <td class="py-3 px-4">
                    ${noteCell}
                </td>

                <!-- Aksi -->
                <td class="py-3 px-4 text-right whitespace-nowrap">
                    <div class="flex items-center justify-end space-x-1.5">
                        <button onclick="app.openRemoteViewer('${c.device_id}')" 
                            ${!isOnline ? 'disabled' : ''} 
                            class="px-2.5 py-1.5 rounded-lg text-xs font-semibold text-white bg-indigo-600 hover:bg-indigo-500 active:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed transition shadow-sm inline-flex items-center">
                            <i class="fa-solid fa-display mr-1"></i> Remote
                        </button>
                        
                        <button onclick="app.openTerminal('${c.device_id}')" 
                            ${!isOnline ? 'disabled' : ''} 
                            title="Remote Terminal"
                            class="p-1.5 rounded-lg text-xs text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition border border-slate-700">
                            <i class="fa-solid fa-terminal"></i>
                        </button>

                        <button onclick="app.openProcessManager('${c.device_id}')" 
                            ${!isOnline ? 'disabled' : ''} 
                            title="Task Manager"
                            class="p-1.5 rounded-lg text-xs text-slate-200 bg-slate-800 hover:bg-slate-700 active:bg-slate-600 disabled:opacity-40 disabled:cursor-not-allowed transition border border-slate-700">
                            <i class="fa-solid fa-list-check"></i>
                        </button>

                        <div class="flex items-center space-x-1 pl-1 border-l border-slate-800">
                            <button onclick="app.confirmPowerAction('${c.device_id}', 'lock')" ${!isOnline ? 'disabled' : ''} class="p-1 hover:text-amber-400 text-slate-400 text-xs disabled:opacity-30 transition" title="Lock Screen">
                                <i class="fa-solid fa-lock"></i>
                            </button>
                            <button onclick="app.confirmPowerAction('${c.device_id}', 'reboot')" ${!isOnline ? 'disabled' : ''} class="p-1 hover:text-sky-400 text-slate-400 text-xs disabled:opacity-30 transition" title="Reboot System">
                                <i class="fa-solid fa-rotate-right"></i>
                            </button>
                            <button onclick="app.confirmPowerAction('${c.device_id}', 'shutdown')" ${!isOnline ? 'disabled' : ''} class="p-1 hover:text-rose-400 text-slate-400 text-xs disabled:opacity-30 transition" title="Shutdown System">
                                <i class="fa-solid fa-power-off"></i>
                            </button>
                        </div>
                    </div>
                </td>
            </tr>
            `;
        }).join("");

        return `
        <div class="overflow-x-auto rounded-xl border border-slate-800 bg-slate-900/80 shadow-xl backdrop-blur">
            <table class="w-full text-left border-collapse text-xs whitespace-nowrap min-w-[700px]">
                <thead>
                    <tr class="border-b border-slate-800 bg-slate-950/80 text-slate-400 text-[11px] uppercase tracking-wider font-semibold">
                        <th class="py-3 px-4">Status</th>
                        <th class="py-3 px-4">Komputer / Device</th>
                        <th class="py-3 px-4">Alamat IP</th>
                        <th class="py-3 px-4">OS & Uptime</th>
                        <th class="py-3 px-4">CPU / RAM / Disk</th>
                        <th class="py-3 px-4">Catatan (Note)</th>
                        <th class="py-3 px-4 text-right">Aksi</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-800/60">
                    ${rowsHtml}
                </tbody>
            </table>
        </div>
        `;
    }

    // --- Action Handlers ---
    openRemoteViewer(clientId) {
        const client = this.clients.get(clientId);
        if (!client) {
            console.warn(`[Dashboard] Client ${clientId} not found in client map`);
            return;
        }
        if (window.remoteViewer) {
            window.remoteViewer.closeSession();
            window.remoteViewer.startSession(clientId, client);
        }
    }

    // --- Remote Terminal Modal ---
    openTerminal(clientId) {
        this.activeTerminalClientId = clientId;
        const client = this.clients.get(clientId);
        document.getElementById("terminalModal").classList.remove("hidden");
        const displayName = client.alias ? `${client.alias} (${client.hostname})` : (client.hostname || 'Device');
        document.getElementById("terminalTargetName").textContent = `${displayName} (${client.ip_address}) [${client.os_type === 'windows' ? 'cmd/powershell' : 'bash'}]`;
        document.getElementById("terminalOutput").textContent = `Connected to remote shell on ${displayName}...\nType commands and press Enter.\n\n`;
        document.getElementById("terminalInput").value = "";
        document.getElementById("terminalInput").focus();
    }

    closeTerminal() {
        this.activeTerminalClientId = null;
        document.getElementById("terminalModal").classList.add("hidden");
    }

    async sendTerminalCommand() {
        const input = document.getElementById("terminalInput");
        const cmd = input.value.trim();
        if (!cmd || !this.activeTerminalClientId) return;

        const out = document.getElementById("terminalOutput");
        out.textContent += `> ${cmd}\n`;
        input.value = "";
        input.disabled = true;

        try {
            const res = await this.authFetch(`/api/client/${this.activeTerminalClientId}/command`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ command: cmd })
            });
            const data = await res.json();
            
            if (data.result) {
                if (data.result.stdout) out.textContent += data.result.stdout + "\n";
                if (data.result.stderr) out.textContent += `[Error]: ${data.result.stderr}\n`;
            } else if (data.error) {
                out.textContent += `[Error]: ${data.error}\n`;
            }
        } catch (e) {
            out.textContent += `[Network Error]: ${e.message}\n`;
        } finally {
            input.disabled = false;
            input.focus();
            out.scrollTop = out.scrollHeight;
        }
    }

    // --- Process Manager Modal ---
    async openProcessManager(clientId) {
        this.activeProcessClientId = clientId;
        const client = this.clients.get(clientId);
        document.getElementById("processModal").classList.remove("hidden");
        const displayName = client.alias ? `${client.alias} (${client.hostname})` : (client.hostname || 'Device');
        document.getElementById("processTargetName").textContent = `${displayName} (${client.ip_address})`;
        await this.refreshProcessList();
    }

    closeProcessManager() {
        this.activeProcessClientId = null;
        document.getElementById("processModal").classList.add("hidden");
    }

    async refreshProcessList() {
        if (!this.activeProcessClientId) return;
        const tbody = document.getElementById("processTableBody");
        tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-slate-400"><i class="fa-solid fa-spinner fa-spin mr-2"></i> Loading running processes...</td></tr>`;

        try {
            const res = await this.authFetch(`/api/client/${this.activeProcessClientId}/processes?limit=60`);
            const data = await res.json();
            const procs = data.processes || [];

            if (procs.length === 0) {
                tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-slate-500">No processes retrieved.</td></tr>`;
                return;
            }

            tbody.innerHTML = procs.map(p => `
                <tr class="border-b border-slate-800/60 hover:bg-slate-800/40 text-xs">
                    <td class="py-2.5 px-3 font-mono text-slate-400">${p.pid}</td>
                    <td class="py-2.5 px-3 font-medium text-slate-200">${p.name}</td>
                    <td class="py-2.5 px-3 text-slate-400">${p.user || "-"}</td>
                    <td class="py-2.5 px-3 font-mono ${p.cpu > 50 ? 'text-rose-400 font-bold' : 'text-slate-300'}">${p.cpu}%</td>
                    <td class="py-2.5 px-3 font-mono text-slate-300">${p.ram}%</td>
                    <td class="py-2.5 px-3 text-right">
                        <button onclick="app.killProcess(${p.pid}, '${p.name}')" class="px-2 py-1 bg-rose-600/80 hover:bg-rose-500 text-white rounded text-[11px] transition">
                            Kill
                        </button>
                    </td>
                </tr>
            `).join("");

        } catch (e) {
            tbody.innerHTML = `<tr><td colspan="5" class="text-center py-6 text-rose-400">Failed to load processes: ${e.message}</td></tr>`;
        }
    }

    async killProcess(pid, name) {
        if (!confirm(`Are you sure you want to terminate process "${name}" (PID: ${pid})?`)) return;
        try {
            const res = await this.authFetch(`/api/client/${this.activeProcessClientId}/kill_process`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ pid: pid })
            });
            const data = await res.json();
            alert(data.message || (data.success ? "Process killed" : "Failed to kill process"));
            await this.refreshProcessList();
        } catch (e) {
            alert(`Error killing process: ${e.message}`);
        }
    }

    // --- Power Actions ---
    confirmPowerAction(clientId, action) {
        const client = this.clients.get(clientId);
        const name = client ? client.hostname : clientId;
        const msg = `Are you sure you want to perform "${action.toUpperCase()}" on "${name}"?`;
        if (confirm(msg)) {
            this.authFetch(`/api/client/${clientId}/power`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ action: action })
            })
            .then(res => res.json())
            .then(data => {
                alert(`Action "${action}" sent to ${name}.`);
            })
            .catch(err => {
                alert(`Error executing power action: ${err.message}`);
            });
        }
    }

    // --- Authentication & Settings Methods ---
    async logout() {
        if (!confirm("Are you sure you want to log out of the admin session?")) return;
        try {
            await fetch(`/api/auth/logout?token=${encodeURIComponent(this.token)}`, { method: "POST" });
        } catch (e) {}
        localStorage.removeItem("admin_token");
        window.location.href = "/login";
    }

    async openSettings() {
        document.getElementById("settingsModal").classList.remove("hidden");
        this.switchSettingsTab("security");
        await this.loadSettingsData();
    }

    closeSettings() {
        document.getElementById("settingsModal").classList.add("hidden");
    }

    switchSettingsTab(tab) {
        const tabSec = document.getElementById("tabContentSecurity");
        const tabSrv = document.getElementById("tabContentServer");
        const btnSec = document.getElementById("tabBtnSecurity");
        const btnSrv = document.getElementById("tabBtnServer");

        if (tab === "security") {
            tabSec.classList.remove("hidden");
            tabSrv.classList.add("hidden");
            btnSec.className = "py-3 px-4 font-semibold text-indigo-400 border-b-2 border-indigo-500 flex items-center";
            btnSrv.className = "py-3 px-4 font-medium text-slate-400 hover:text-slate-200 flex items-center";
        } else {
            tabSec.classList.add("hidden");
            tabSrv.classList.remove("hidden");
            btnSrv.className = "py-3 px-4 font-semibold text-indigo-400 border-b-2 border-indigo-500 flex items-center";
            btnSec.className = "py-3 px-4 font-medium text-slate-400 hover:text-slate-200 flex items-center";
        }
    }

    togglePassVisibility(inputId, iconId) {
        const inp = document.getElementById(inputId);
        const ico = document.getElementById(iconId);
        if (inp.type === "password") {
            inp.type = "text";
            ico.className = "fa-solid fa-eye-slash text-xs text-indigo-400";
        } else {
            inp.type = "password";
            ico.className = "fa-solid fa-eye text-xs";
        }
    }

    async loadSettingsData() {
        try {
            const res = await this.authFetch(`/api/settings?token=${encodeURIComponent(this.token)}`);
            const data = await res.json();
            document.getElementById("settingServerName").value = data.server_name || "";
            document.getElementById("settingActivePort").value = data.active_port || "";
            document.getElementById("settingUdpPort").value = data.active_udp_port || "";
            document.getElementById("settingTimeoutHours").value = data.session_timeout_hours || 24;
            document.getElementById("settingRememberDays").value = data.remember_days || 30;
        } catch (e) {
            console.error("Failed to load settings:", e);
        }
    }

    async submitChangePassword() {
        const curr = document.getElementById("currPass").value;
        const nw = document.getElementById("newPass").value;
        const conf = document.getElementById("confirmNewPass").value;
        const alertBox = document.getElementById("passwordAlert");

        if (nw.length < 4) {
            alertBox.textContent = "New password must be at least 4 characters.";
            alertBox.className = "p-3 rounded-lg text-xs font-medium bg-rose-950/60 border border-rose-800 text-rose-300";
            alertBox.classList.remove("hidden");
            return;
        }
        if (nw !== conf) {
            alertBox.textContent = "New passwords do not match.";
            alertBox.className = "p-3 rounded-lg text-xs font-medium bg-rose-950/60 border border-rose-800 text-rose-300";
            alertBox.classList.remove("hidden");
            return;
        }

        try {
            const res = await this.authFetch(`/api/auth/change_password?token=${encodeURIComponent(this.token)}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ current_password: curr, new_password: nw })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                alertBox.textContent = "Password updated successfully!";
                alertBox.className = "p-3 rounded-lg text-xs font-medium bg-emerald-950/60 border border-emerald-800 text-emerald-300";
                alertBox.classList.remove("hidden");
                document.getElementById("currPass").value = "";
                document.getElementById("newPass").value = "";
                document.getElementById("confirmNewPass").value = "";
            } else {
                alertBox.textContent = data.detail || data.message || "Failed to update password.";
                alertBox.className = "p-3 rounded-lg text-xs font-medium bg-rose-950/60 border border-rose-800 text-rose-300";
                alertBox.classList.remove("hidden");
            }
        } catch (e) {
            alertBox.textContent = e.message;
            alertBox.className = "p-3 rounded-lg text-xs font-medium bg-rose-950/60 border border-rose-800 text-rose-300";
            alertBox.classList.remove("hidden");
        }
    }

    async submitServerSettings() {
        const sName = document.getElementById("settingServerName").value;
        const timeout = parseInt(document.getElementById("settingTimeoutHours").value);
        const remDays = parseInt(document.getElementById("settingRememberDays").value);
        const alertBox = document.getElementById("serverAlert");

        try {
            const res = await this.authFetch(`/api/settings?token=${encodeURIComponent(this.token)}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    server_name: sName,
                    session_timeout_hours: timeout,
                    remember_days: remDays
                })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                alertBox.textContent = "Configuration saved successfully!";
                alertBox.className = "p-3 rounded-lg text-xs font-medium bg-emerald-950/60 border border-emerald-800 text-emerald-300";
                alertBox.classList.remove("hidden");
            } else {
                alertBox.textContent = data.detail || "Failed to save settings.";
                alertBox.className = "p-3 rounded-lg text-xs font-medium bg-rose-950/60 border border-rose-800 text-rose-300";
                alertBox.classList.remove("hidden");
            }
        } catch (e) {
            alertBox.textContent = e.message;
            alertBox.className = "p-3 rounded-lg text-xs font-medium bg-rose-950/60 border border-rose-800 text-rose-300";
            alertBox.classList.remove("hidden");
        }
    }

    // --- Device Note & Alias Modal ---
    openNoteModal(clientId) {
        const client = this.clients.get(clientId);
        if (!client) return;

        document.getElementById("noteClientId").value = clientId;
        document.getElementById("noteAliasInput").value = client.alias || "";
        document.getElementById("noteTextInput").value = client.note || "";
        document.getElementById("noteModalSubtitle").textContent = `${client.hostname || 'Device'} (${client.ip_address || '-'}) • ID: ${clientId}`;
        
        document.getElementById("noteModal").classList.remove("hidden");
        document.getElementById("noteAliasInput").focus();
    }

    closeNoteModal() {
        document.getElementById("noteModal").classList.add("hidden");
    }

    async submitNoteForm() {
        const clientId = document.getElementById("noteClientId").value;
        const alias = document.getElementById("noteAliasInput").value.trim();
        const note = document.getElementById("noteTextInput").value.trim();
        if (!clientId) return;

        try {
            const res = await this.authFetch(`/api/client/${clientId}/note?token=${encodeURIComponent(this.token)}`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ alias, note })
            });
            const data = await res.json();
            if (res.ok && data.success) {
                // Update local client map
                const client = this.clients.get(clientId);
                if (client) {
                    client.alias = alias;
                    client.note = note;
                }
                this.closeNoteModal();
                this.renderDashboard();
                this.showToast(alias ? `Nama PC diubah: "${alias}"` : "Catatan PC diperbarui!");
            } else {
                alert("Gagal menyimpan catatan: " + (data.detail || "Error"));
            }
        } catch (e) {
            console.error("Error updating note:", e);
            alert("Terjadi kesalahan saat menyimpan catatan: " + e.message);
        }
    }

    showToast(message, isError = false) {
        const toast = document.getElementById("toast");
        if (!toast) return;
        toast.textContent = message;
        toast.className = `fixed bottom-6 right-6 z-50 px-4 py-2.5 rounded-xl text-xs font-semibold shadow-2xl transition-all duration-300 ${
            isError ? "bg-rose-600 text-white" : "bg-indigo-600 text-white"
        }`;
        toast.classList.remove("opacity-0", "pointer-events-none");
        setTimeout(() => toast.classList.add("opacity-0", "pointer-events-none"), 2500);
    }

    copyText(text) {
        navigator.clipboard.writeText(text);
        this.showToast(`IP disalin: ${text}`);
    }
}

window.app = new AdminDashboard();
