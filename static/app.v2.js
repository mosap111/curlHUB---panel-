
window.customConfirm = function(message, title = "تأكيد الإجراء") {
    return new Promise((resolve) => {
        const modal = document.getElementById("confirm-modal");
        const titleEl = document.getElementById("confirm-modal-title");
        const msgEl = document.getElementById("confirm-modal-message");
        const btnCancel = document.getElementById("btn-confirm-cancel");
        const btnOk = document.getElementById("btn-confirm-ok");

        titleEl.textContent = title;
        msgEl.textContent = message;
        
        modal.classList.remove("hidden");

        const cleanup = () => {
            modal.classList.add("hidden");
            btnCancel.removeEventListener("click", onCancel);
            btnOk.removeEventListener("click", onOk);
        };

        const onCancel = () => { cleanup(); resolve(false); };
        const onOk = () => { cleanup(); resolve(true); };

        btnCancel.addEventListener("click", onCancel);
        btnOk.addEventListener("click", onOk);
    });
};

/**
 * Server Console & File Management Dashboard
 * Client Application Logic
 */

document.addEventListener('DOMContentLoaded', () => {

    // Global Helpers
    function escapeHtml(str) {
        if (str === null || str === undefined) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    // Global State
    let authToken = getCookie('session_token') || localStorage.getItem('server_token') || sessionStorage.getItem('server_token') || null;
    let currentUser = getCookie('session_user') || localStorage.getItem('server_user') || sessionStorage.getItem('server_user') || 'admin';
    let currentPath = '/root';
    let currentEditingFile = null;
    let editorUnsaved = false;
    let termSocket = null;
    let term = null;
    let fitAddon = null;
    let editor = null;
    let statsInterval = null;
    let arabicFixEnabled = true;

    // Theme Management
    const themeToggleBtn = document.getElementById('theme-toggle-btn');
    const loginThemeBtn = document.getElementById('login-theme-btn');
    const themeIcon = document.getElementById('theme-icon');
    let isLightMode = localStorage.getItem('theme_light') === 'true';

    function applyTheme() {
        if (isLightMode) {
            document.body.classList.add('light-theme');
            if (themeIcon) themeIcon.innerHTML = '<path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>';
            if (loginThemeBtn) loginThemeBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>';
        } else {
            document.body.classList.remove('light-theme');
            if (themeIcon) themeIcon.innerHTML = '<circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>';
            if (loginThemeBtn) loginThemeBtn.innerHTML = '<svg viewBox="0 0 24 24" width="18" height="18" stroke="currentColor" stroke-width="2" fill="none"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>';
        }
        if (editor) {
            editor.setTheme(isLightMode ? "ace/theme/github" : "ace/theme/dracula");
        }
        if (term) {
            term.options.theme = isLightMode 
                ? { background: '#f8fafc', foreground: '#0f172a', cursor: '#0f172a' }
                : { background: '#020617', foreground: '#e2e8f0', cursor: '#38bdf8' };
        }
    }
    applyTheme();

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            isLightMode = !isLightMode;
            localStorage.setItem('theme_light', isLightMode);
            applyTheme();
        });
    }

    if (loginThemeBtn) {
        loginThemeBtn.addEventListener('click', (e) => {
            e.preventDefault();
            isLightMode = !isLightMode;
            localStorage.setItem('theme_light', isLightMode);
            applyTheme();
        });
    }

    const loginLangBtn = document.getElementById('login-lang-btn');
    if (loginLangBtn) {
        const loginDict = {
            en: {
                title: "Server Login",
                subtitle: "Welcome back! Please login to continue",
                username: "Username",
                usernamePh: "Enter username",
                password: "Password",
                remember: "Remember me on this device",
                forgot: "Forgot password?",
                loginBtn: "Login to Dashboard",
                lang: "AR"
            },
            ar: {
                title: "تسجيل الدخول للسيرفر",
                subtitle: "أهلاً بك مجدداً! قم بتسجيل الدخول للمتابعة",
                username: "اسم المستخدم",
                usernamePh: "أدخل اسم المستخدم",
                password: "كلمة المرور",
                remember: "تذكرني على هذا الجهاز",
                forgot: "نسيت الكلمة؟",
                loginBtn: "دخول إلى اللوحة",
                lang: "EN"
            }
        };

        loginLangBtn.addEventListener('click', (e) => {
            e.preventDefault();
            const toEn = loginLangBtn.textContent === 'EN';
            const lang = toEn ? 'en' : 'ar';
            
            document.documentElement.dir = toEn ? 'ltr' : 'rtl';
            document.documentElement.lang = lang;
            loginLangBtn.textContent = loginDict[lang].lang;

            document.getElementById('login-title').textContent = loginDict[lang].title;
            document.getElementById('login-subtitle').textContent = loginDict[lang].subtitle;
            document.getElementById('lbl-username').textContent = loginDict[lang].username;
            document.getElementById('username').placeholder = loginDict[lang].usernamePh;
            document.getElementById('lbl-password').textContent = loginDict[lang].password;
            document.getElementById('lbl-remember').textContent = loginDict[lang].remember;
            document.getElementById('lbl-forgot').textContent = loginDict[lang].forgot;
            document.getElementById('lbl-login-btn').textContent = loginDict[lang].loginBtn;
        });
    }

    // DOM Elements
    const loginScreen = document.getElementById('login-screen');
    const appContainer = document.getElementById('app-container');
    const loginForm = document.getElementById('login-form');
    const loginError = document.getElementById('login-error');
    const currentUsernameSpan = document.getElementById('current-username');
    const logoutBtn = document.getElementById('logout-btn');
    const navTabs = document.querySelectorAll('.nav-tab');
    const tabPanes = document.querySelectorAll('.tab-pane');

    // Stats Elements
    const statCpu = document.getElementById('stat-cpu');
    const barCpu = document.getElementById('bar-cpu');
    const statRam = document.getElementById('stat-ram');
    const barRam = document.getElementById('bar-ram');
    const statSwap = document.getElementById('stat-swap');
    const barSwap = document.getElementById('bar-swap');
    const statDisk = document.getElementById('stat-disk');
    const barDisk = document.getElementById('bar-disk');

    // Terminal Elements
    const terminalEl = document.getElementById('terminal');
    const arabicFixToggle = document.getElementById('arabic-fix-toggle');
    const btnTermReconnect = document.getElementById('btn-term-reconnect');
    const btnTermClear = document.getElementById('btn-term-clear');
    const btnTermFullscreen = document.getElementById('btn-term-fullscreen');
    const quickCmdButtons = document.querySelectorAll('.cmd-pill');

    // Files Elements
    const filesListBody = document.getElementById('files-list-body');
    const filesBreadcrumbs = document.getElementById('files-breadcrumbs');
    const btnFilesUp = document.getElementById('btn-files-up');
    const btnFilesRefresh = document.getElementById('btn-files-refresh');
    const filesFilterInput = document.getElementById('files-filter');
    const btnUploadFile = document.getElementById('btn-upload-file');
    const fileUploadInput = document.getElementById('file-upload-input');
    const btnNewFile = document.getElementById('btn-new-file');
    const btnNewFolder = document.getElementById('btn-new-folder');
    const dropZone = document.getElementById('drop-zone');
    const dropOverlay = document.getElementById('drop-overlay');
    const jumpButtons = document.querySelectorAll('.jump-btn');

    // Editor Elements
    const editorActiveFilename = document.getElementById('editor-active-filename');
    const editorUnsavedDot = document.getElementById('editor-unsaved-dot');
    const editorModeSelect = document.getElementById('editor-mode-select');
    const btnEditorSave = document.getElementById('btn-editor-save');
    const btnEditorClose = document.getElementById('btn-editor-close');
    const editorCursorPos = document.getElementById('editor-cursor-pos');
    const editorFilePath = document.getElementById('editor-file-path');

    // Modal Elements
    const promptModal = document.getElementById('prompt-modal');
    const modalTitle = document.getElementById('modal-title');
    const modalLabel = document.getElementById('modal-label');
    const modalInput = document.getElementById('modal-input');
    const btnModalCancel = document.getElementById('btn-modal-cancel');
    const btnModalConfirm = document.getElementById('btn-modal-confirm');
    let modalCallback = null;

    // Toast Container
    const toastContainer = document.getElementById('toast-container');

    // Settings
    const changePassForm = document.getElementById('change-pass-form');

    // Booster & Clean Elements
    const btnQuickClean = document.getElementById('btn-quick-clean');
    const btnCleanFromMonitor = document.getElementById('btn-clean-from-monitor');
    const cleanModal = document.getElementById('clean-modal');
    const btnCloseCleanModal = document.getElementById('btn-close-clean-modal');
    const cleanRamFreed = document.getElementById('clean-ram-freed');
    const cleanDiskFreed = document.getElementById('clean-disk-freed');
    const cleanTasksList = document.getElementById('clean-tasks-list');
    const cleanModalSubtitle = document.getElementById('clean-modal-subtitle');

    // Monitor Elements
    const monHostname = document.getElementById('mon-hostname');
    const monOs = document.getElementById('mon-os');
    const monUptime = document.getElementById('mon-uptime');
    const monLoadavg = document.getElementById('mon-loadavg');
    const monNetIo = document.getElementById('mon-net-io');
    const monRefreshInterval = document.getElementById('mon-refresh-interval');
    const btnMonRefresh = document.getElementById('btn-mon-refresh');
    const monCpuVal = document.getElementById('mon-cpu-val');
    const monCpuBar = document.getElementById('mon-cpu-bar');
    const monCpuLoad = document.getElementById('mon-cpu-load');
    const monCpuCoresBadge = document.getElementById('mon-cpu-cores-badge');
    const monRamVal = document.getElementById('mon-ram-val');
    const monRamBar = document.getElementById('mon-ram-bar');
    const monRamPercentBadge = document.getElementById('mon-ram-percent-badge');
    const monRamCache = document.getElementById('mon-ram-cache');
    const monRamFree = document.getElementById('mon-ram-free');
    const monProcTotalBadge = document.getElementById('mon-proc-total-badge');
    const monProcRunning = document.getElementById('mon-proc-running');
    const monProcRunCount = document.getElementById('mon-proc-run-count');
    const monProcSleepCount = document.getElementById('mon-proc-sleep-count');
    const monProcZombieCount = document.getElementById('mon-proc-zombie-count');
    const monTopConsumer = document.getElementById('mon-top-consumer');
    const monPortsCountBadge = document.getElementById('mon-ports-count-badge');
    const monPortsVal = document.getElementById('mon-ports-val');
    const monNetSent = document.getElementById('mon-net-sent');
    const monNetRecv = document.getElementById('mon-net-recv');
    const procsCountLabel = document.getElementById('procs-count-label');
    const procSearchInput = document.getElementById('proc-search-input');
    const procSortSelect = document.getElementById('proc-sort-select');
    const procsTableBody = document.getElementById('procs-table-body');
    const portsCountLabel = document.getElementById('ports-count-label');
    const portsSearchInput = document.getElementById('ports-search-input');
    const portsTableBody = document.getElementById('ports-table-body');
    const servicesCountLabel = document.getElementById('services-count-label');
    const servicesSearchInput = document.getElementById('services-search-input');
    const servicesTableBody = document.getElementById('services-table-body');

    let monitorInterval = null;
    let cachedProcesses = [];
    let cachedPorts = [];
    let cachedServices = [];

    // --- TOAST NOTIFICATIONS ---
    window.showToast = function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.style.opacity = '0';
            setTimeout(() => toast.remove(), 300);
        }, 3500);
    }

    // --- API HELPER ---
    window.apiRequest = async function apiRequest(endpoint, options = {}) {
        options.headers = options.headers || {};
        if (options.body && typeof options.body === 'string' && options.body.startsWith('{') && !options.headers['Content-Type']) {
            options.headers['Content-Type'] = 'application/json';
        }
        if (authToken) {
            options.headers['Authorization'] = `Bearer ${authToken}`;
        }
        try {
            const response = await fetch(endpoint, options);
            if (response.status === 401) {
                handleLogout();
                throw new Error('انتهت الجلسة، يرجى إعادة تسجيل الدخول');
            }
            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.detail || 'حدث خطأ غير متوقع');
            }
            return data;
        } catch (err) {
            throw err;
        }
    }

    // --- AUTHENTICATION ---
    async function checkAuth() {
        if (!authToken) {
            showLogin();
            return;
        }
        try {
            const res = await apiRequest('/api/auth/check');
            currentUser = res.username;
            currentUsernameSpan.textContent = currentUser;
            showApp();
        } catch (e) {
            showLogin();
        }
    }

    function showLogin() {
        loginScreen.classList.remove('hidden');
        appContainer.classList.add('hidden');
        if (statsInterval) clearInterval(statsInterval);
    }

    function showApp() {
        loginScreen.classList.add('hidden');
        appContainer.classList.remove('hidden');
        currentUsernameSpan.textContent = currentUser;

        // Initialize components
        initTerminal();
        initEditor();
        loadFiles(currentPath);
        startStatsPolling();
    }

    loginForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        loginError.classList.add('hidden');
        const user = document.getElementById('username').value.trim();
        const pass = document.getElementById('password').value;

        try {
            const res = await apiRequest('/api/auth/login', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: user, password: pass, remember: document.getElementById('remember-me').checked })
            });
            authToken = res.token;
            currentUser = res.username;
            
            // Backend handles session_token (HttpOnly). We just store the username for UI purposes.
            if (document.getElementById('remember-me').checked) {
                const d = new Date();
                d.setTime(d.getTime() + (7*24*60*60*1000));
                document.cookie = `session_user=${currentUser}; expires=${d.toUTCString()}; path=/; SameSite=Lax`;
            } else {
                document.cookie = `session_user=${currentUser}; path=/; SameSite=Lax`;
            }
            showApp();
            showToast('تم تسجيل الدخول بنجاح', 'success');
        } catch (err) {
            loginError.textContent = err.message;
            loginError.classList.remove('hidden');
        }
    });

    logoutBtn.addEventListener('click', async () => {
        try {
            await apiRequest('/api/auth/logout', { method: 'POST' });
        } catch (e) {}
        handleLogout();
    });

    function handleLogout() {
        authToken = null;
        currentUser = '';
        localStorage.removeItem('server_token');
        localStorage.removeItem('server_user');
        sessionStorage.removeItem('server_token');
        sessionStorage.removeItem('server_user');
        document.cookie = "session_token=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        document.cookie = "session_user=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;";
        if (statsInterval) clearInterval(statsInterval);
        if (termSocket) termSocket.close();
        showLogin();
    }

    // --- TAB SWITCHING ---
    navTabs.forEach(tab => {
        tab.addEventListener('click', () => {
            const target = tab.getAttribute('data-tab');
            navTabs.forEach(t => t.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));

            tab.classList.add('active');
            const targetPane = document.getElementById(target);
            if (targetPane) targetPane.classList.add('active');

            // Refit terminal or editor if activated
            if (target === 'tab-terminal' && fitAddon) {
                stopMonitorPolling();
                if (!termSocket || termSocket.readyState !== WebSocket.OPEN) {
                    connectTerminalWebSocket();
                }
                setTimeout(() => {
                    if (fitAddon) fitAddon.fit();
                    if (termSocket && termSocket.readyState === WebSocket.OPEN && term) {
                        termSocket.send(JSON.stringify({ resize: [term.cols, term.rows] }));
                    }
                    if (term) term.focus();
                }, 50);
            } else if (target === 'tab-bots') {
                stopMonitorPolling();
                loadBotsList();
            } else if (target === 'tab-editor' && editor) {
                stopMonitorPolling();
                setTimeout(() => editor.resize(), 50);
            } else if (target === 'tab-monitor') {
                startMonitorPolling();
            } else if (target === 'tab-security') {
                stopMonitorPolling();
                loadSecurityData();
            } else if (target === 'tab-backups') {
                stopMonitorPolling();
                loadBackups();
            } else if (target === 'tab-db') {
                stopMonitorPolling();
                loadDatabases();
            } else if (target === 'tab-logs') {
                stopMonitorPolling();
                loadLogView();
            } else if (target === 'tab-settings') {
                stopMonitorPolling();
                loadTelegramSettings();
            } else {
                stopMonitorPolling();
            }
        });
    });

    // --- SYSTEM STATS POLLING ---
    function startStatsPolling() {
        fetchStats();
        if (statsInterval) clearInterval(statsInterval);
        statsInterval = setInterval(fetchStats, 3000);
    }

    async function fetchStats() {
        if (!authToken) return;
        try {
            const stats = await apiRequest('/api/system/stats');
            
            // CPU
            statCpu.textContent = `${stats.cpu.percent}%`;
            barCpu.style.width = `${Math.min(stats.cpu.percent, 100)}%`;
            barCpu.style.background = stats.cpu.percent > 80 ? 'var(--accent-danger)' : 'var(--accent-primary)';

            // RAM
            statRam.textContent = `${stats.memory.used_gb}/${stats.memory.total_gb}G`;
            barRam.style.width = `${stats.memory.percent}%`;
            barRam.style.background = stats.memory.percent > 85 ? 'var(--accent-danger)' : 'var(--accent-primary)';

            // Swap
            statSwap.textContent = `${stats.swap.used_gb}/${stats.swap.total_gb}G`;
            barSwap.style.width = `${stats.swap.percent}%`;

            // Disk
            statDisk.textContent = `${stats.disk.percent}%`;
            barDisk.style.width = `${stats.disk.percent}%`;
        } catch (e) {}
    }

    // --- TAB 1: TERMINAL LOGIC WITH ARABIC SUPPORT ---
    function initTerminal() {
        if (term) return;

        term = new Terminal({
            cursorBlink: true,
            cursorStyle: 'block',
            fontSize: 14,
            fontFamily: "ui-monospace, 'Fira Code', 'JetBrains Mono', 'DejaVu Sans Mono', Menlo, Consolas, 'Courier New', monospace",
            letterSpacing: 0,
            lineHeight: 1.2,
            allowProposedApi: true,
            windowsMode: false,
            scrollback: 5000,
            theme: {
                background: '#06090f',
                foreground: '#e2e8f0',
                cursor: '#38bdf8',
                selectionBackground: 'rgba(56, 189, 248, 0.3)',
                black: '#0f172a',
                red: '#ef4444',
                green: '#10b981',
                yellow: '#f59e0b',
                blue: '#3b82f6',
                magenta: '#8b5cf6',
                cyan: '#06b6d4',
                white: '#f8fafc',
                brightBlack: '#475569',
                brightRed: '#f87171',
                brightGreen: '#34d399',
                brightYellow: '#fbbf24',
                brightBlue: '#60a5fa',
                brightMagenta: '#a78bfa',
                brightCyan: '#22d3ee',
                brightWhite: '#ffffff'
            }
        });

        fitAddon = new FitAddon.FitAddon();
        term.loadAddon(fitAddon);
        if (window.WebLinksAddon) {
            term.loadAddon(new WebLinksAddon.WebLinksAddon());
        }
        if (window.Unicode11Addon) {
            const unicode11 = new Unicode11Addon.Unicode11Addon();
            term.loadAddon(unicode11);
            term.unicode.activeVersion = '11';
        }

        term.open(terminalEl);
        fitAddon.fit();

        connectTerminalWebSocket();

        // Keyboard input -> WebSocket
        term.onData(data => {
            if (termSocket && termSocket.readyState === WebSocket.OPEN) {
                termSocket.send(data);
            }
        });

        // Window resize
        window.addEventListener('resize', () => {
            if (fitAddon) {
                fitAddon.fit();
                if (termSocket && termSocket.readyState === WebSocket.OPEN) {
                    termSocket.send(JSON.stringify({ resize: [term.cols, term.rows] }));
                }
            }
        });

        // Quick commands
        quickCmdButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const cmd = btn.getAttribute('data-cmd');
                if (termSocket && termSocket.readyState === WebSocket.OPEN) {
                    termSocket.send(cmd + '\r');
                    term.focus();
                }
            });
        });

        // Terminal Special Keys Handler (Ctrl+C, ESC, TAB, Arrows, etc.)
        const termKeyButtons = document.querySelectorAll('.term-key-btn');
        const keyMap = {
            'ctrl-c': '\x03',
            'ctrl-z': '\x1a',
            'ctrl-d': '\x04',
            'ctrl-l': '\x0c',
            'ctrl-a': '\x01',
            'ctrl-e': '\x05',
            'esc': '\x1b',
            'tab': '\t',
            'enter': '\r',
            'arrow-up': '\x1b[A',
            'arrow-down': '\x1b[B',
            'arrow-right': '\x1b[C',
            'arrow-left': '\x1b[D'
        };

        termKeyButtons.forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const keyType = btn.getAttribute('data-key');
                const sequence = keyMap[keyType];
                if (sequence && termSocket && termSocket.readyState === WebSocket.OPEN) {
                    termSocket.send(sequence);
                    if (term) term.focus();
                }
            });
        });

        const btnTermReset = document.getElementById('btn-term-reset');
        let terminalPingInterval = null;

        if (btnTermReset) {
            btnTermReset.addEventListener('click', async () => {
                if (!(await window.customConfirm('هل تريد إنهاء جلسة الطرفية الحالية وبدء صدفة (Shell)) جديدة ونظيفة؟')) {
                    return;
                }
                try {
                    await apiRequest('/api/terminal/reset', { method: 'POST' });
                    if (term) term.clear();
                    showToast('تمت إعادة تعيين الجلسة وبدء جلسة طرفية جديدة 🔄', 'success');
                    connectTerminalWebSocket();
                } catch (err) {
                    showToast(err.message, 'error');
                }
            });
        }

        btnTermClear.addEventListener('click', () => {
            if (term) term.clear();
        });
        btnTermReconnect.addEventListener('click', () => {
            showToast('جاري إعادة الاتصال بالجلسة الحالية...', 'info');
            connectTerminalWebSocket();
        });
        
        btnTermFullscreen.addEventListener('click', () => {
            const wrap = document.getElementById('terminal-wrapper');
            if (!document.fullscreenElement) {
                wrap.requestFullscreen().catch(err => {});
            } else {
                document.exitFullscreen();
            }
        });

        if (arabicFixToggle) {
            arabicFixToggle.addEventListener('change', (e) => {
                arabicFixEnabled = e.target.checked;
                showToast(arabicFixEnabled ? 'تم تفعيل تصحيح النصوص العربية' : 'تم تعطيل تصحيح النصوص العربية');
            });
        }
    }

    function connectTerminalWebSocket() {
        if (termSocket) {
            try {
                termSocket.close();
            } catch (e) {}
            termSocket = null;
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws/terminal?token=${encodeURIComponent(authToken)}`;

        termSocket = new WebSocket(wsUrl);
        termSocket.binaryType = 'arraybuffer';

        termSocket.onopen = () => {
            if (fitAddon) {
                fitAddon.fit();
                termSocket.send(JSON.stringify({ resize: [term.cols, term.rows] }));
            }
            // Keepalive ping every 15s so idle connections never time out
            if (terminalPingInterval) clearInterval(terminalPingInterval);
            terminalPingInterval = setInterval(() => {
                if (termSocket && termSocket.readyState === WebSocket.OPEN) {
                    termSocket.send('__ping__');
                }
            }, 15000);
        };

        termSocket.onmessage = (event) => {
            let data = event.data;
            if (typeof data === 'string' && data === '__pong__') {
                return;
            }
            if (data instanceof ArrayBuffer) {
                const decoder = new TextDecoder('utf-8');
                data = decoder.decode(data);
            }

            // Apply Arabic Reshaping and BiDi if enabled
            if (arabicFixEnabled && window.ArabicShaper) {
                data = window.ArabicShaper.process(data);
            }

            term.write(data);
        };

        termSocket.onclose = () => {
            if (terminalPingInterval) {
                clearInterval(terminalPingInterval);
                terminalPingInterval = null;
            }
            // Auto reconnect seamlessly if user is logged in
            if (authToken) {
                setTimeout(() => {
                    if (authToken && (!termSocket || termSocket.readyState === WebSocket.CLOSED)) {
                        connectTerminalWebSocket();
                    }
                }, 2500);
            }
        };

        termSocket.onerror = () => {};
    }

    // --- TAB 2: FILE MANAGER LOGIC ---
    async function loadFiles(path) {
        try {
            filesListBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">جاري تحميل الملفات...</td></tr>';
            const data = await apiRequest(`/api/files/list?path=${encodeURIComponent(path)}`);
            currentPath = data.current_path;
            renderBreadcrumbs(currentPath);
            renderFilesList(data.items);
        } catch (err) {
            showToast(err.message, 'error');
            filesListBody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: var(--accent-danger); padding: 20px;">${err.message}</td></tr>`;
        }
    }

    function renderBreadcrumbs(path) {
        filesBreadcrumbs.innerHTML = '';
        const parts = path.split('/').filter(Boolean);
        
        // Root item
        const rootItem = document.createElement('span');
        rootItem.className = 'breadcrumb-item';
        rootItem.textContent = '/';
        rootItem.addEventListener('click', () => loadFiles('/'));
        filesBreadcrumbs.appendChild(rootItem);

        let accPath = '';
        parts.forEach(part => {
            accPath += '/' + part;
            const currentAcc = accPath;
            const item = document.createElement('span');
            item.className = 'breadcrumb-item';
            item.textContent = part;
            item.addEventListener('click', () => loadFiles(currentAcc));
            filesBreadcrumbs.appendChild(item);
        });
    }

    function renderFilesList(items) {
        filesListBody.innerHTML = '';

        if (items.length === 0) {
            filesListBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">هذا المجلد فارغ</td></tr>';
            return;
        }

        items.forEach(item => {
            const tr = document.createElement('tr');
            tr.className = `file-row ${item.is_dir ? 'is-dir' : 'is-file'}`;

            // Icon & Name Cell
            const nameTd = document.createElement('td');
            nameTd.className = 'file-name-cell';
            
            let iconSvg = item.is_dir 
                ? '<svg viewBox="0 0 24 24" width="18" height="18" stroke="#38bdf8" stroke-width="2" fill="rgba(56, 189, 248, 0.2)"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"></path></svg>'
                : '<svg viewBox="0 0 24 24" width="18" height="18" stroke="#94a3b8" stroke-width="2" fill="none"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline></svg>';

            nameTd.innerHTML = `${iconSvg} <span class="file-name-text">${escapeHtml(item.name)}</span>`;
            
            // Double click / Click behavior
            nameTd.addEventListener('click', () => {
                if (item.is_dir) {
                    loadFiles(item.path);
                } else {
                    openFileInEditor(item.path);
                }
            });

            // Size
            const sizeTd = document.createElement('td');
            sizeTd.textContent = item.is_dir ? '--' : formatBytes(item.size);

            // Mod Date
            const dateTd = document.createElement('td');
            dateTd.textContent = new Date(item.mtime * 1000).toLocaleString('ar-EG', { dateStyle: 'short', timeStyle: 'short' });

            // Permissions
            const permTd = document.createElement('td');
            permTd.textContent = item.permissions;
            permTd.style.fontFamily = 'var(--font-code)';

            // Actions Cell
            const actionsTd = document.createElement('td');
            actionsTd.className = 'file-actions-cell';

            if (!item.is_dir) {
                // Edit
                const editBtn = document.createElement('button');
                editBtn.className = 'action-btn-sm';
                editBtn.title = 'تعديل الملف';
                editBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>';
                editBtn.addEventListener('click', (e) => { e.stopPropagation(); openFileInEditor(item.path); });
                actionsTd.appendChild(editBtn);

                // Download
                const dlBtn = document.createElement('button');
                dlBtn.className = 'action-btn-sm';
                dlBtn.title = 'تحميل الملف';
                dlBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>';
                dlBtn.addEventListener('click', (e) => { e.stopPropagation(); downloadFile(item.path); });
                actionsTd.appendChild(dlBtn);
            } else {
                // Download Folder
                const dlBtn = document.createElement('button');
                dlBtn.className = 'action-btn-sm';
                dlBtn.title = 'ضغط وتنزيل المجلد';
                dlBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>';
                dlBtn.addEventListener('click', (e) => { e.stopPropagation(); downloadFolder(item.path); });
                actionsTd.appendChild(dlBtn);
            }

            // Compress
            const compressBtn = document.createElement('button');
            compressBtn.className = 'action-btn-sm';
            compressBtn.title = 'ضغط في نفس المسار';
            compressBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path><polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline><line x1="12" y1="22.08" x2="12" y2="12"></line></svg>';
            compressBtn.addEventListener('click', (e) => { e.stopPropagation(); compressItem(item.path); });
            actionsTd.appendChild(compressBtn);

            // Chmod
            const chmodBtn = document.createElement('button');
            chmodBtn.className = 'action-btn-sm';
            chmodBtn.title = 'تعديل الصلاحيات';
            chmodBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>';
            chmodBtn.addEventListener('click', (e) => { e.stopPropagation(); promptChmod(item); });
            actionsTd.appendChild(chmodBtn);

            // Rename
            const renameBtn = document.createElement('button');
            renameBtn.className = 'action-btn-sm';
            renameBtn.title = 'إعادة التسمية';
            renameBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>';
            renameBtn.addEventListener('click', (e) => { e.stopPropagation(); promptRename(item); });
            actionsTd.appendChild(renameBtn);

            // Delete
            const delBtn = document.createElement('button');
            delBtn.className = 'action-btn-sm delete';
            delBtn.title = 'حذف';
            delBtn.innerHTML = '<svg viewBox="0 0 24 24" width="15" height="15" stroke="currentColor" stroke-width="2" fill="none"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>';
            delBtn.addEventListener('click', (e) => { e.stopPropagation(); confirmDelete(item); });
            actionsTd.appendChild(delBtn);

            tr.appendChild(nameTd);
            tr.appendChild(sizeTd);
            tr.appendChild(dateTd);
            tr.appendChild(permTd);
            tr.appendChild(actionsTd);

            filesListBody.appendChild(tr);
        });
    }

    // Filter Files in list
    filesFilterInput.addEventListener('input', (e) => {
        const term = e.target.value.toLowerCase();
        const rows = filesListBody.querySelectorAll('.file-row');
        rows.forEach(row => {
            const name = row.querySelector('.file-name-text').textContent.toLowerCase();
            row.style.display = name.includes(term) ? '' : 'none';
        });
    });

    btnFilesUp.addEventListener('click', () => {
        const parts = currentPath.split('/').filter(Boolean);
        if (parts.length > 0) {
            parts.pop();
            const parent = '/' + parts.join('/');
            loadFiles(parent || '/');
        }
    });

    btnFilesRefresh.addEventListener('click', () => loadFiles(currentPath));

    jumpButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            loadFiles(btn.getAttribute('data-path'));
        });
    });

    // Upload Files
    btnUploadFile.addEventListener('click', () => fileUploadInput.click());
    fileUploadInput.addEventListener('change', () => {
        if (fileUploadInput.files.length > 0) {
            uploadFiles(fileUploadInput.files);
        }
    });

    // Drag and drop upload
    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropOverlay.classList.remove('hidden');
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            dropOverlay.classList.add('hidden');
        }, false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files && files.length > 0) {
            uploadFiles(files);
        }
    });

    async function uploadFiles(fileList) {
        const formData = new FormData();
        formData.append('destination', currentPath);
        for (let i = 0; i < fileList.length; i++) {
            formData.append('files', fileList[i]);
        }

        showToast(`جاري رفع ${fileList.length} ملف...`, 'info');
        try {
            const res = await fetch('/api/files/upload', {
                method: 'POST',
                headers: { 'Authorization': `Bearer ${authToken}` },
                body: formData
            });
            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || 'فشل رفع الملفات');
            showToast('تم رفع الملفات بنجاح', 'success');
            loadFiles(currentPath);
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    function downloadFile(path) {
        window.open(`/api/files/download?path=${encodeURIComponent(path)}&token=${encodeURIComponent(authToken)}`, '_blank');
    }

    function downloadFolder(path) {
        window.open(`/api/files/download_folder?path=${encodeURIComponent(path)}&token=${encodeURIComponent(authToken)}`, '_blank');
    }

    // Modal Prompt Helper
    function showPrompt(title, label, defaultValue, callback) {
        modalTitle.textContent = title;
        modalLabel.textContent = label;
        modalInput.value = defaultValue || '';
        promptModal.classList.remove('hidden');
        modalInput.focus();
        modalCallback = callback;
    }

    btnModalCancel.addEventListener('click', () => {
        promptModal.classList.add('hidden');
        modalCallback = null;
    });

    btnModalConfirm.addEventListener('click', () => {
        const val = modalInput.value.trim();
        if (val && modalCallback) {
            modalCallback(val);
        }
        promptModal.classList.add('hidden');
    });

    btnNewFile.addEventListener('click', () => {
        showPrompt('إنشاء ملف جديد', 'اسم الملف:', 'new_script.py', async (name) => {
            try {
                await apiRequest('/api/files/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parent_path: currentPath, name: name, is_dir: false })
                });
                showToast(`تم إنشاء الملف ${name}`, 'success');
                loadFiles(currentPath);
            } catch (e) { showToast(e.message, 'error'); }
        });
    });

    btnNewFolder.addEventListener('click', () => {
        showPrompt('إنشاء مجلد جديد', 'اسم المجلد:', 'new_folder', async (name) => {
            try {
                await apiRequest('/api/files/create', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ parent_path: currentPath, name: name, is_dir: true })
                });
                showToast(`تم إنشاء المجلد ${name}`, 'success');
                loadFiles(currentPath);
            } catch (e) { showToast(e.message, 'error'); }
        });
    });

    async function compressItem(path) {
        try {
            const res = await apiRequest('/api/files/compress', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: path })
            });
            showToast(res.message, 'success');
            loadFiles(currentPath);
        } catch (e) { showToast(e.message, 'error'); }
    }

    function promptChmod(item) {
        showPrompt('تعديل الصلاحيات', 'أدخل رقم الصلاحية (مثال: 755):', '755', async (perms) => {
            if (!/^[0-7]{3,4}$/.test(perms)) {
                showToast('الصلاحيات غير صالحة', 'error');
                return;
            }
            try {
                const res = await apiRequest('/api/files/chmod', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ path: item.path, permissions: perms })
                });
                showToast(res.message, 'success');
                loadFiles(currentPath);
            } catch (e) { showToast(e.message, 'error'); }
        });
    }

    function promptRename(item) {
        showPrompt('إعادة التسمية', 'الاسم الجديد:', item.name, async (newName) => {
            if (newName === item.name) return;
            const parent = item.path.substring(0, item.path.lastIndexOf('/')) || '/';
            const newPath = (parent === '/' ? '' : parent) + '/' + newName;
            try {
                await apiRequest('/api/files/rename', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ old_path: item.path, new_path: newPath })
                });
                showToast('تمت إعادة التسمية بنجاح', 'success');
                loadFiles(currentPath);
            } catch (e) { showToast(e.message, 'error'); }
        });
    }

    async function confirmDelete(item) {
        const type = item.is_dir ? 'المجلد' : 'الملف';
        if (!(await window.customConfirm(`هل أنت متأكد من رغبتك في حذف ${type} "${item.name}" نهائياً؟`))) {
            return;
        }
        try {
            await apiRequest('/api/files/delete', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: item.path })
            });
            showToast('تم الحذف بنجاح', 'success');
            loadFiles(currentPath);
        } catch (e) { showToast(e.message, 'error'); }
    }

    // --- TAB 3: CODE EDITOR LOGIC ---
    function initEditor() {
        if (editor) return;

        editor = ace.edit('code-editor-container');
        editor.setTheme(isLightMode ? "ace/theme/github" : "ace/theme/dracula");
        editor.session.setMode('ace/mode/python');
        editor.setFontSize(14);
        editor.setShowPrintMargin(false);
        editor.setOptions({
            enableBasicAutocompletion: true,
            enableLiveAutocompletion: true,
            enableSnippets: true,
            tabSize: 4,
            useSoftTabs: true
        });

        editor.selection.on('changeCursor', () => {
            const cursor = editor.getCursorPosition();
            editorCursorPos.textContent = `السطر: ${cursor.row + 1}, العمود: ${cursor.column + 1}`;
        });

        editor.session.on('change', () => {
            if (currentEditingFile) {
                editorUnsaved = true;
                editorUnsavedDot.classList.remove('hidden');
            }
        });

        // Ctrl+S / Cmd+S shortcut
        editor.commands.addCommand({
            name: 'saveFile',
            bindKey: { win: 'Ctrl-S', mac: 'Command-S' },
            exec: () => saveCurrentFile()
        });

        btnEditorSave.addEventListener('click', () => saveCurrentFile());
        
        btnEditorClose.addEventListener('click', async () => {
            if (editorUnsaved && !(await window.customConfirm('لديك تعديلات غير محفوظة، هل أنت متأكد من الإغلاق؟'))) return;
            currentEditingFile = null;
            editorUnsaved = false;
            editorUnsavedDot.classList.add('hidden');
            editorActiveFilename.textContent = 'لم يتم فتح أي ملف';
            editorFilePath.textContent = 'المسار: --';
            editor.setValue('', -1);
            // Switch to files tab
            document.querySelector('.nav-tab[data-tab="tab-files"]').click();
        });

        editorModeSelect.addEventListener('change', (e) => {
            editor.session.setMode(`ace/mode/${e.target.value}`);
        });
    }

    async function openFileInEditor(path) {
        try {
            showToast('جاري فتح الملف...', 'info');
            const data = await apiRequest(`/api/files/read?path=${encodeURIComponent(path)}`);
            
            currentEditingFile = data.path;
            editorActiveFilename.textContent = data.name;
            editorFilePath.textContent = `المسار: ${data.path}`;
            editor.setValue(data.content, -1);
            editorUnsaved = false;
            editorUnsavedDot.classList.add('hidden');

            // Detect mode
            const ext = data.name.split('.').pop().toLowerCase();
            const modeMap = {
                'py': 'python', 'js': 'javascript', 'html': 'html', 'css': 'css',
                'sh': 'sh', 'bash': 'sh', 'json': 'json', 'yaml': 'yaml',
                'yml': 'yaml', 'conf': 'nginx', 'txt': 'text', 'log': 'text'
            };
            const mode = modeMap[ext] || 'text';
            editorModeSelect.value = mode;
            editor.session.setMode(`ace/mode/${mode}`);

            // Switch to editor tab
            document.querySelector('.nav-tab[data-tab="tab-editor"]').click();
            showToast(`تم فتح ${data.name}`, 'success');
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    async function saveCurrentFile() {
        if (!currentEditingFile) {
            showToast('لا يوجد ملف مفتوح للحفظ', 'error');
            return;
        }
        try {
            const content = editor.getValue();
            await apiRequest('/api/files/save', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: currentEditingFile, content: content })
            });
            editorUnsaved = false;
            editorUnsavedDot.classList.add('hidden');
            showToast('تم حفظ الملف بنجاح 💾', 'success');
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // --- TAB 4: SETTINGS LOGIC ---
    changePassForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const oldPass = document.getElementById('old-pass').value;
        const newPass = document.getElementById('new-pass').value;
        const confirmPass = document.getElementById('confirm-new-pass').value;

        if (newPass !== confirmPass) {
            showToast('كلمة المرور الجديدة غير متطابقة', 'error');
            return;
        }

        try {
            await apiRequest('/api/auth/change-password', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ old_password: oldPass, new_password: newPass })
            });
            showToast('تم تغيير كلمة المرور بنجاح!', 'success');
            changePassForm.reset();
        } catch (err) {
            showToast(err.message, 'error');
        }
    });

    // Helpers
    function formatBytes(bytes, decimals = 2) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(dm)) + ' ' + sizes[i];
    }

    // ==========================================
    // --- TAB: SYSTEM & PORTS MONITOR LOGIC ---
    // ==========================================
    async function loadMonitorData() {
        if (!authToken) return;
        try {
            const data = await apiRequest('/api/system/monitor');
            renderMonitorStats(data);
        } catch (err) {
            console.error('Monitor fetch error:', err);
        }
    }

    function renderMonitorStats(data) {
        if (!data) return;

        // Banner info
        if (monHostname) monHostname.textContent = data.system.hostname || 'server';
        if (monOs) monOs.textContent = data.system.os || 'Linux';
        if (monUptime) monUptime.textContent = data.system.uptime_str || '--';
        if (monLoadavg) monLoadavg.textContent = `${data.system.load_1} / ${data.system.load_5} / ${data.system.load_15}`;
        if (monNetIo) monNetIo.textContent = `↑ ${data.network.bytes_sent_mb} MB | ↓ ${data.network.bytes_recv_mb} MB`;

        // KPI: CPU
        if (monCpuVal) monCpuVal.textContent = `${data.cpu.percent}%`;
        if (monCpuBar) {
            monCpuBar.style.width = `${Math.min(data.cpu.percent, 100)}%`;
            monCpuBar.style.background = data.cpu.percent > 80 ? 'var(--accent-danger)' : (data.cpu.percent > 50 ? 'var(--accent-warning)' : 'linear-gradient(90deg, #0284c7, #38bdf8)');
        }
        if (monCpuCoresBadge) monCpuCoresBadge.textContent = `${data.cpu.cores} Cores (${data.cpu.physical_cores} Physical)`;
        if (monCpuLoad) monCpuLoad.textContent = `${data.system.load_1} (1m) / ${data.system.load_5} (5m)`;

        // KPI: RAM
        if (monRamVal) monRamVal.textContent = `${data.memory.used_gb} / ${data.memory.total_gb} GB`;
        if (monRamPercentBadge) monRamPercentBadge.textContent = `${data.memory.percent}%`;
        if (monRamBar) {
            monRamBar.style.width = `${data.memory.percent}%`;
            monRamBar.style.background = data.memory.percent > 85 ? 'var(--accent-danger)' : 'linear-gradient(90deg, #8b5cf6, #c084fc)';
        }
        if (monRamCache) monRamCache.textContent = `${data.memory.cached_mb} MB`;
        if (monRamFree) monRamFree.textContent = `${data.memory.free_gb} GB`;

        // KPI: Processes
        if (monProcTotalBadge) monProcTotalBadge.textContent = `${data.proc_summary.total} عملية`;
        if (monProcRunning) monProcRunning.textContent = `${data.proc_summary.running} نشطة تعمل الآن`;
        if (monProcRunCount) monProcRunCount.textContent = data.proc_summary.running;
        if (monProcSleepCount) monProcSleepCount.textContent = data.proc_summary.sleeping;
        if (monProcZombieCount) monProcZombieCount.textContent = data.proc_summary.zombie;

        // Top consumer
        if (data.processes && data.processes.length > 0 && monTopConsumer) {
            const top = data.processes[0];
            monTopConsumer.textContent = `${top.name} (PID: ${top.pid} - ${top.cpu_percent}% CPU, ${top.memory_mb}MB)`;
        }

        // KPI: Ports
        if (monPortsCountBadge) monPortsCountBadge.textContent = `${data.ports.length} بورت`;
        if (monPortsVal) monPortsVal.textContent = `${data.ports.length} منفذ يستمع للطلبات`;
        if (monNetSent) monNetSent.textContent = `${data.network.bytes_sent_mb} MB`;
        if (monNetRecv) monNetRecv.textContent = `${data.network.bytes_recv_mb} MB`;

        // Store cached lists for searching / sorting
        cachedProcesses = data.processes || [];
        cachedPorts = data.ports || [];
        cachedServices = data.services || [];

        renderFilteredProcesses();
        renderFilteredPorts();
        renderFilteredServices();
    }

    function renderFilteredProcesses() {
        if (!procsTableBody) return;
        const q = (procSearchInput ? procSearchInput.value : '').toLowerCase().trim();
        const sortBy = procSortSelect ? procSortSelect.value : 'cpu';

        let list = [...cachedProcesses];

        if (q) {
            list = list.filter(p => 
                p.name.toLowerCase().includes(q) || 
                String(p.pid).includes(q) || 
                p.user.toLowerCase().includes(q) ||
                p.cmdline.toLowerCase().includes(q)
            );
        }

        if (sortBy === 'cpu') {
            list.sort((a, b) => b.cpu_percent - a.cpu_percent || b.memory_mb - a.memory_mb);
        } else if (sortBy === 'ram') {
            list.sort((a, b) => b.memory_mb - a.memory_mb || b.cpu_percent - a.cpu_percent);
        } else if (sortBy === 'pid') {
            list.sort((a, b) => a.pid - b.pid);
        }

        if (procsCountLabel) procsCountLabel.textContent = `${list.length} معروض`;

        if (list.length === 0) {
            procsTableBody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 24px; color: var(--text-muted);">لا توجد عمليات تطابق البحث</td></tr>';
            return;
        }

        procsTableBody.innerHTML = '';
        list.forEach(p => {
            const tr = document.createElement('tr');

            // CPU badge class
            let cpuClass = 'badge-cpu-low';
            if (p.cpu_percent > 60) cpuClass = 'badge-cpu-high';
            else if (p.cpu_percent > 20) cpuClass = 'badge-cpu-med';

            tr.innerHTML = `
                <td><span class="badge-pid">${p.pid}</span></td>
                <td>
                    <div style="display: flex; flex-direction: column;">
                        <strong style="color: var(--text-primary); font-size: 13px;">${escapeHtml(p.name)}</strong>
                        <span style="font-size: 11px; color: var(--text-muted); max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(p.cmdline)}">${escapeHtml(p.cmdline)}</span>
                    </div>
                </td>
                <td><span style="color: var(--text-secondary); font-size: 12px;">${escapeHtml(p.user)}</span></td>
                <td><span class="${cpuClass}">${p.cpu_percent}%</span></td>
                <td><strong style="color: #c084fc;">${p.memory_mb} MB</strong> <span style="font-size: 11px; color: var(--text-muted);">(${p.memory_percent}%)</span></td>
                <td><span style="font-size: 12px; color: var(--text-secondary);">${p.threads}</span></td>
                <td><span class="badge-status ${p.status === 'running' ? 'status-running' : 'status-sleeping'}">${p.status}</span></td>
                <td style="text-align: center;">
                    <button class="btn-kill-proc" data-pid="${p.pid}" data-name="${escapeHtml(p.name)}" title="إنهاء العملية فوراً">إنهاء (Kill)</button>
                </td>
            `;

            const btnKill = tr.querySelector('.btn-kill-proc');
            btnKill.addEventListener('click', () => killProcess(p.pid, p.name));

            procsTableBody.appendChild(tr);
        });
    }

    function renderFilteredPorts() {
        if (!portsTableBody) return;
        const q = (portsSearchInput ? portsSearchInput.value : '').toLowerCase().trim();

        let list = [...cachedPorts];
        if (q) {
            list = list.filter(item => 
                String(item.port).includes(q) || 
                item.process_name.toLowerCase().includes(q) || 
                item.ip.toLowerCase().includes(q) ||
                item.proto.toLowerCase().includes(q) ||
                String(item.pid).includes(q)
            );
        }

        if (portsCountLabel) portsCountLabel.textContent = `${list.length} بورت نشط`;

        if (list.length === 0) {
            portsTableBody.innerHTML = '<tr><td colspan="6" style="text-align: center; padding: 24px; color: var(--text-muted);">لا توجد منافذ تطابق البحث</td></tr>';
            return;
        }

        portsTableBody.innerHTML = '';
        list.forEach(p => {
            const tr = document.createElement('tr');

            const isPublic = p.ip === '0.0.0.0' || p.ip === '::';
            const protoClass = p.proto === 'TCP' ? 'tcp' : 'udp';

            tr.innerHTML = `
                <td><span class="badge-port">:${p.port}</span></td>
                <td><span class="badge-proto ${protoClass}">${p.proto}</span></td>
                <td>
                    <strong style="color: #38bdf8; font-size: 13px;">${escapeHtml(p.process_name)}</strong>
                </td>
                <td><span class="badge-pid">${p.pid || '--'}</span></td>
                <td>
                    <span class="badge-ip ${isPublic ? 'public' : 'local'}">
                        ${p.ip} ${isPublic ? '(متاح عام 🌐)' : '(محلي 🔒)'}
                    </span>
                </td>
                <td><span class="badge-status status-running">${p.status}</span></td>
            `;

            portsTableBody.appendChild(tr);
        });
    }

    function renderFilteredServices() {
        if (!servicesTableBody) return;
        const q = (servicesSearchInput ? servicesSearchInput.value : '').toLowerCase().trim();

        let list = [...cachedServices];
        if (q) {
            list = list.filter(s => 
                s.name.toLowerCase().includes(q) || 
                s.unit.toLowerCase().includes(q) || 
                s.desc.toLowerCase().includes(q)
            );
        }

        if (servicesCountLabel) servicesCountLabel.textContent = `${list.length} خدمة`;

        if (list.length === 0) {
            servicesTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 24px; color: var(--text-muted);">لا توجد خدمات تطابق البحث</td></tr>';
            return;
        }

        servicesTableBody.innerHTML = '';
        list.forEach(s => {
            const tr = document.createElement('tr');

            const isRunning = s.status === 'active' || s.sub_status === 'running';
            const isFailed = s.status === 'failed' || s.sub_status === 'failed';
            const statusClass = isRunning ? 'status-running' : (isFailed ? 'status-zombie' : 'status-sleeping');

            tr.innerHTML = `
                <td>
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span class="badge-dot" style="background: ${isRunning ? '#10b981' : (isFailed ? '#ef4444' : '#94a3b8')};"></span>
                        <strong style="color: #38bdf8; font-family: 'JetBrains Mono', monospace; font-size: 13px;">${escapeHtml(s.name)}</strong>
                    </div>
                </td>
                <td><span style="font-size: 12px; color: var(--text-secondary); max-width: 320px; display: inline-block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(s.desc)}">${escapeHtml(s.desc)}</span></td>
                <td><span class="badge-status ${statusClass}">${s.status}</span></td>
                <td><span style="font-size: 11px; color: var(--text-muted); font-family: monospace;">${s.sub_status}</span></td>
                <td style="text-align: center;">
                    <div class="srv-action-group">
                        <button class="btn-srv restart" data-srv="${escapeHtml(s.unit)}" data-act="restart" title="إعادة تشغيل الخدمة">🔄 إعادة تشغيل</button>
                        ${isRunning ? 
                            `<button class="btn-srv stop" data-srv="${escapeHtml(s.unit)}" data-act="stop" title="إيقاف الخدمة">⏹️ إيقاف</button>` : 
                            `<button class="btn-srv start" data-srv="${escapeHtml(s.unit)}" data-act="start" title="تشغيل الخدمة">▶️ تشغيل</button>`
                        }
                    </div>
                </td>
            `;

            const btnRestart = tr.querySelector('.btn-srv.restart');
            if (btnRestart) {
                btnRestart.addEventListener('click', () => handleServiceAction(s.unit, 'restart'));
            }
            const btnStop = tr.querySelector('.btn-srv.stop');
            if (btnStop) {
                btnStop.addEventListener('click', () => handleServiceAction(s.unit, 'stop'));
            }
            const btnStart = tr.querySelector('.btn-srv.start');
            if (btnStart) {
                btnStart.addEventListener('click', () => handleServiceAction(s.unit, 'start'));
            }

            servicesTableBody.appendChild(tr);
        });
    }

    async function handleServiceAction(serviceUnit, action) {
        const actLabels = { restart: 'إعادة تشغيل', stop: 'إيقاف', start: 'تشغيل' };
        if (!(await window.customConfirm(`هل أنت متأكد من رغبتك في ${actLabels[action] || action} الخدمة ${serviceUnit}؟`))) {
            return;
        }
        showToast(`جاري ${actLabels[action] || action} الخدمة ${serviceUnit}...`, 'info');
        try {
            const res = await apiRequest('/api/system/service/action', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ service: serviceUnit, action: action })
            });
            showToast(res.message || 'تم تنفيذ الإجراء بنجاح', 'success');
            loadMonitorData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    async function killProcess(pid, name) {
        if (!(await window.customConfirm(`هل أنت متأكد من رغبتك في إنهاء وإيقاف العملية ${name} (PID: ${pid}))؟`)) {
            return;
        }
        try {
            const res = await apiRequest('/api/system/process/kill', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ pid: pid })
            });
            showToast(res.message || 'تم إنهاء العملية بنجاح', 'success');
            loadMonitorData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // Server Cleaner Execution
    async function cleanServer() {
        showToast('⚡ جاري تنظيف السيرفر وتفريغ الذاكرة المؤقتة...', 'info');
        try {
            const res = await apiRequest('/api/system/clean', { method: 'POST' });
            
            if (cleanRamFreed) cleanRamFreed.textContent = `+${res.ram_freed_mb} MB`;
            if (cleanDiskFreed) cleanDiskFreed.textContent = `+${res.disk_freed_mb} MB`;
            if (cleanModalSubtitle) cleanModalSubtitle.textContent = `الرام الحالية: ${res.current_ram_percent}% | القرص: ${res.current_disk_percent}%`;

            if (cleanTasksList && res.actions) {
                cleanTasksList.innerHTML = '';
                res.actions.forEach(act => {
                    const li = document.createElement('li');
                    li.textContent = act;
                    cleanTasksList.appendChild(li);
                });
            }

            if (cleanModal) cleanModal.classList.remove('hidden');
            showToast(`تم تنظيف السيرفر بنجاح! تم تحرير ${res.ram_freed_mb}MB من الرام`, 'success');
            
            fetchStats();
            loadMonitorData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    function startMonitorPolling() {
        stopMonitorPolling();
        loadMonitorData();
        const interval = monRefreshInterval ? parseInt(monRefreshInterval.value, 10) : 3000;
        if (interval > 0) {
            monitorInterval = setInterval(loadMonitorData, interval);
        }
    }

    function stopMonitorPolling() {
        if (monitorInterval) {
            clearInterval(monitorInterval);
            monitorInterval = null;
        }
    }

    // Monitor Events
    if (procSearchInput) procSearchInput.addEventListener('input', renderFilteredProcesses);
    if (procSortSelect) procSortSelect.addEventListener('change', renderFilteredProcesses);
    if (portsSearchInput) portsSearchInput.addEventListener('input', renderFilteredPorts);
    if (servicesSearchInput) servicesSearchInput.addEventListener('input', renderFilteredServices);

    if (btnMonRefresh) btnMonRefresh.addEventListener('click', () => {
        loadMonitorData();
        showToast('تم تحديث بيانات الأداء والمنافذ والخدمات', 'info');
    });

    if (monRefreshInterval) {
        monRefreshInterval.addEventListener('change', () => {
            startMonitorPolling();
            const val = monRefreshInterval.value;
            if (val === '0') showToast('تم إيقاف التحديث التلقائي');
            else showToast(`تم ضبط التحديث التلقائي كل ${parseInt(val)/1000} ثوانٍ`);
        });
    }

    if (btnQuickClean) btnQuickClean.addEventListener('click', cleanServer);
    if (btnCloseCleanModal) btnCloseCleanModal.addEventListener('click', () => cleanModal.classList.add('hidden'));
    // --- TAB: SECURITY SHIELD & ATTACK MONITOR ---
    const secKpiTotal = document.getElementById('sec-kpi-total');
    const secKpiBanned = document.getElementById('sec-kpi-banned');
    const secKpiScanners = document.getElementById('sec-kpi-scanners');
    const secKpiBrute = document.getElementById('sec-kpi-brute');
    const secBannedBadge = document.getElementById('sec-banned-badge');
    const secBannedTableBody = document.getElementById('sec-banned-table-body');
    const secLogsBadge = document.getElementById('sec-logs-badge');
    const secLogsTableBody = document.getElementById('sec-logs-table-body');
    const secLogsSearch = document.getElementById('sec-logs-search');
    const secFilterType = document.getElementById('sec-filter-type');
    const btnSecRefresh = document.getElementById('btn-sec-refresh');
    const btnSecClearLogs = document.getElementById('btn-sec-clear-logs');
    const btnSecBanManual = document.getElementById('btn-sec-ban-manual');
    const banModal = document.getElementById('ban-modal');
    const btnCloseBanModal = document.getElementById('btn-close-ban-modal');
    const btnCancelBanModal = document.getElementById('btn-cancel-ban-modal');
    const banIpForm = document.getElementById('ban-ip-form');
    const banIpInput = document.getElementById('ban-ip-input');
    const banReasonInput = document.getElementById('ban-reason-input');
    const banDurationSelect = document.getElementById('ban-duration-select');

    let securityCachedLogs = [];
    let securityCachedBanned = [];

    async function loadSecurityData() {
        if (!authToken) return;
        try {
            const [statsRes, logsRes, f2bRes] = await Promise.all([
                apiRequest('/api/security/stats'),
                apiRequest('/api/security/logs'),
                apiRequest('/api/security/fail2ban').catch(() => ({ status: 'error', jails: {}, all_banned_ips: [] }))
            ]);
            
            securityCachedBanned = statsRes.banned_ips || [];
            securityCachedLogs = logsRes.logs || [];

            renderSecurityStats(statsRes);
            renderSecurityBannedTable(securityCachedBanned);
            renderFilteredSecurityLogs();
            renderFail2banSystemJails(f2bRes);
        } catch (err) {
            showToast('تعذر تحميل بيانات الأمان: ' + err.message, 'error');
        }
    }

    function renderFail2banSystemJails(f2b) {
        const jailsContainer = document.getElementById('f2b-jails-container');
        const bannedBody = document.getElementById('f2b-banned-table-body');
        const jailsBadge = document.getElementById('fail2ban-jails-badge');
        if (!jailsContainer || !bannedBody) return;

        jailsContainer.innerHTML = '';
        const jails = f2b.jails || {};
        const jailKeys = Object.keys(jails);
        if (jailsBadge) jailsBadge.textContent = `${jailKeys.length} سجون نظام نشطة`;

        if (jailKeys.length === 0) {
            jailsContainer.innerHTML = '<div style="color: var(--text-muted); font-size: 13px;">لا توجد سجون Fail2Ban نشطة حالياً</div>';
        } else {
            jailKeys.forEach(jk => {
                const j = jails[jk];
                const div = document.createElement('div');
                div.className = 'f2b-jail-card';
                div.innerHTML = `
                    <div class="f2b-jail-header">
                        <strong>🛡️ ${escapeHtml(jk)}</strong>
                        <span class="badge-status ${j.currently_banned > 0 ? 'status-sleeping' : 'status-running'}">${j.currently_banned} محظور</span>
                    </div>
                    <div class="f2b-jail-stats">
                        <span>المحاولات الفاشلة: <strong>${j.currently_failed}</strong></span> &bull; 
                        <span>الإجمالي: <strong>${j.total_banned}</strong></span>
                    </div>
                `;
                jailsContainer.appendChild(div);
            });
        }

        bannedBody.innerHTML = '';
        const allBanned = f2b.all_banned_ips || [];
        if (allBanned.length === 0) {
            bannedBody.innerHTML = '<tr><td colspan="3" style="text-align: center; padding: 18px; color: #34d399;">لا توجد عناوين محظورة حالياً في سجون النظام 🛡️</td></tr>';
        } else {
            allBanned.forEach(item => {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td><strong style="color: #f87171; font-family: 'JetBrains Mono', monospace; font-size: 13px;">${escapeHtml(item.ip)}</strong></td>
                    <td><span class="badge-proto" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">${escapeHtml(item.jail)}</span></td>
                    <td style="text-align: center;">
                        <button class="btn-srv restart btn-unban-f2b" data-ip="${escapeHtml(item.ip)}" data-jail="${escapeHtml(item.jail)}">🔓 فك الحظر</button>
                    </td>
                `;
                bannedBody.appendChild(tr);
            });

            bannedBody.querySelectorAll('.btn-unban-f2b').forEach(btn => {
                btn.addEventListener('click', async () => {
                    const ip = btn.getAttribute('data-ip');
                    const jail = btn.getAttribute('data-jail');
                    if (!(await window.customConfirm(`هل تريد فك الحظر عن ${ip} في سجن ${jail}؟`))) return;
                    try {
                        const res = await apiRequest('/api/security/fail2ban/unban', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ ip, jail })
                        });
                        showToast(res.message, 'success');
                        loadSecurityData();
                    } catch (e) {
                        showToast(e.message, 'error');
                    }
                });
            });
        }
    }

    function renderSecurityStats(data) {
        const stats = data.stats || {};
        if (secKpiTotal) secKpiTotal.textContent = (stats.total_blocked || 0).toLocaleString();
        if (secKpiBanned) secKpiBanned.textContent = (data.banned_count || 0).toLocaleString();
        if (secKpiScanners) secKpiScanners.textContent = ((stats.scanners_blocked || 0) + (stats.honeypot_trapped || 0)).toLocaleString();
        if (secKpiBrute) secKpiBrute.textContent = (stats.brute_force_blocked || 0).toLocaleString();
        if (secBannedBadge) secBannedBadge.textContent = `${data.banned_count || 0} محظور`;
        if (secLogsBadge) secLogsBadge.textContent = `${data.total_events_count || securityCachedLogs.length} حدث`;
    }

    function renderSecurityBannedTable(bannedIps) {
        if (!secBannedTableBody) return;
        secBannedTableBody.innerHTML = '';

        if (!bannedIps || bannedIps.length === 0) {
            secBannedTableBody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 24px; color: #34d399;">لا توجد عناوين محظورة حالياً - السيرفر آمن تماماً 🛡️</td></tr>';
            return;
        }

        bannedIps.forEach(b => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong style="color: #f87171; font-family: 'JetBrains Mono', monospace; font-size: 13px;">${escapeHtml(b.ip)}</strong></td>
                <td><span style="color: var(--text-primary); font-size: 12px;">${escapeHtml(b.reason)}</span></td>
                <td><span style="color: var(--text-muted); font-size: 12px; font-family: 'JetBrains Mono', monospace;">${escapeHtml(b.banned_at)}</span></td>
                <td><span style="color: #fbbf24; font-size: 12px; font-weight: 600;">${b.remaining_minutes > 0 ? b.remaining_minutes + ' دقيقة' : b.remaining_seconds + ' ثانية'}</span></td>
                <td style="text-align: center;">
                    <button class="btn-srv restart btn-unban-ip" data-ip="${escapeHtml(b.ip)}" title="إلغاء وفك الحظر فوراً">🔓 فك الحظر</button>
                </td>
            `;
            secBannedTableBody.appendChild(tr);
        });

        secBannedTableBody.querySelectorAll('.btn-unban-ip').forEach(btn => {
            btn.addEventListener('click', () => {
                const ip = btn.getAttribute('data-ip');
                unbanIp(ip);
            });
        });
    }

    function renderFilteredSecurityLogs() {
        if (!secLogsTableBody) return;
        secLogsTableBody.innerHTML = '';

        const query = (secLogsSearch ? secLogsSearch.value : '').toLowerCase().trim();
        const typeFilter = secFilterType ? secFilterType.value : 'all';

        let filtered = securityCachedLogs.filter(ev => {
            const matchQ = !query || 
                (ev.ip && ev.ip.toLowerCase().includes(query)) ||
                (ev.threat_type && ev.threat_type.toLowerCase().includes(query)) ||
                (ev.path && ev.path.toLowerCase().includes(query)) ||
                (ev.detail && ev.detail.toLowerCase().includes(query)) ||
                (ev.user_agent && ev.user_agent.toLowerCase().includes(query));

            if (!matchQ) return false;

            if (typeFilter === 'brute') return ev.threat_type.includes('تخمين') || ev.threat_type.includes('Login');
            if (typeFilter === 'scanner') return ev.threat_type.includes('Scanner') || ev.threat_type.includes('Fuzz') || ev.threat_type.includes('فحص');
            if (typeFilter === 'honeypot') return ev.threat_type.includes('Honeypot') || ev.threat_type.includes('فخ');
            if (typeFilter === 'manual') return ev.threat_type.includes('يدوي');

            return true;
        });

        if (filtered.length === 0) {
            secLogsTableBody.innerHTML = '<tr><td colspan="7" style="text-align: center; padding: 24px; color: var(--text-muted);">لا توجد أحداث مسجلة مطابقة للبحث</td></tr>';
            return;
        }

        filtered.forEach(ev => {
            const tr = document.createElement('tr');
            
            let threatBadgeColor = '#38bdf8';
            if (ev.severity === 'CRITICAL' || (ev.action && ev.action.includes('BANNED'))) threatBadgeColor = '#ef4444';
            else if (ev.severity === 'HIGH') threatBadgeColor = '#f59e0b';
            
            let actionBadge = `<span class="badge-proto" style="background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3);">${escapeHtml(ev.action)}</span>`;
            if (ev.action === 'AUTH_FAILED') {
                actionBadge = `<span class="badge-proto" style="background: rgba(245, 158, 11, 0.15); color: #fbbf24; border: 1px solid rgba(245, 158, 11, 0.3);">${escapeHtml(ev.action)}</span>`;
            } else if (ev.action === 'TRAPPED') {
                actionBadge = `<span class="badge-proto" style="background: rgba(168, 85, 247, 0.15); color: #c084fc; border: 1px solid rgba(168, 85, 247, 0.3);">🪤 مصيدة</span>`;
            }

            tr.innerHTML = `
                <td><span style="font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-muted);">${escapeHtml(ev.time_str)}</span></td>
                <td><strong style="color: var(--text-primary); font-family: 'JetBrains Mono', monospace; font-size: 12px;">${escapeHtml(ev.ip)}</strong></td>
                <td><span style="font-size: 12px; font-weight: 600; color: ${threatBadgeColor};">${escapeHtml(ev.threat_type)}</span></td>
                <td>
                    <div style="display: flex; flex-direction: column; gap: 2px;">
                        <strong style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: #e2e8f0;">${escapeHtml(ev.path || '/')}</strong>
                        <span style="font-size: 11px; color: var(--text-muted);">${escapeHtml(ev.detail || '')}</span>
                    </div>
                </td>
                <td><span style="font-size: 11px; color: var(--text-secondary); max-width: 170px; display: inline-block; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${escapeHtml(ev.user_agent)}">${escapeHtml(ev.user_agent || 'Unknown')}</span></td>
                <td style="text-align: center;">${actionBadge}</td>
                <td style="text-align: center;">
                    <button class="btn-srv stop btn-quick-ban-ip" data-ip="${escapeHtml(ev.ip)}" title="حظر هذا العنوان فوراً">🚫 حظر</button>
                </td>
            `;
            secLogsTableBody.appendChild(tr);
        });

        secLogsTableBody.querySelectorAll('.btn-quick-ban-ip').forEach(btn => {
            btn.addEventListener('click', () => {
                const ip = btn.getAttribute('data-ip');
                if (banIpInput) banIpInput.value = ip;
                if (banModal) banModal.classList.remove('hidden');
            });
        });
    }

    async function unbanIp(ip) {
        if (!(await window.customConfirm(`هل أنت متأكد من رغبتك في إلغاء وفك الحظر عن العنوان ${ip}؟`))) return;
        try {
            const res = await apiRequest('/api/security/unban', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip: ip })
            });
            showToast(res.message, 'success');
            loadSecurityData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    async function banIp(ip, reason, duration) {
        try {
            const res = await apiRequest('/api/security/ban', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ip: ip, reason: reason, duration_minutes: parseInt(duration, 10) })
            });
            showToast(res.message, 'success');
            if (banModal) banModal.classList.add('hidden');
            if (banIpForm) banIpForm.reset();
            loadSecurityData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    async function clearSecurityLogs() {
        if (!(await window.customConfirm('هل تريد تفريغ وحذف سجلات الأمان والهجمات بالكامل؟'))) return;
        try {
            const res = await apiRequest('/api/security/logs/clear', { method: 'POST' });
            showToast(res.message, 'success');
            loadSecurityData();
        } catch (err) {
            showToast(err.message, 'error');
        }
    }

    // Security Tab Events
    if (btnSecRefresh) btnSecRefresh.addEventListener('click', () => {
        loadSecurityData();
        showToast('تم تحديث بيانات الأمان وسجلات الهجمات', 'info');
    });

    if (btnSecClearLogs) btnSecClearLogs.addEventListener('click', clearSecurityLogs);

    if (btnSecBanManual) btnSecBanManual.addEventListener('click', () => {
        if (banIpInput) banIpInput.value = '';
        if (banModal) banModal.classList.remove('hidden');
    });

    if (btnCloseBanModal) btnCloseBanModal.addEventListener('click', () => {
        if (banModal) banModal.classList.add('hidden');
    });

    if (btnCancelBanModal) btnCancelBanModal.addEventListener('click', () => {
        if (banModal) banModal.classList.add('hidden');
    });

    if (banIpForm) {
        banIpForm.addEventListener('submit', (e) => {
            e.preventDefault();
            const ip = banIpInput.value.trim();
            const reason = banReasonInput.value.trim() || 'حظر يدوي بواسطة المسؤول';
            const duration = banDurationSelect.value;
            if (!ip) return;
            banIp(ip, reason, duration);
        });
    }

    if (secLogsSearch) secLogsSearch.addEventListener('input', renderFilteredSecurityLogs);
    if (secFilterType) secFilterType.addEventListener('change', renderFilteredSecurityLogs);

    // ==============================================================================
    // 🤖 1. BOTS & PYTHON APPS MANAGER LOGIC
    // ==============================================================================
    const botsCardsGrid = document.getElementById('bots-cards-grid');
    const botsTotalCount = document.getElementById('bots-total-count');
    const botsRunningCount = document.getElementById('bots-running-count');
    const botsRamCount = document.getElementById('bots-ram-count');
    const btnBotsRefresh = document.getElementById('btn-bots-refresh');
    const btnAddCustomBot = document.getElementById('btn-add-custom-bot');
    const botLogsModal = document.getElementById('bot-logs-modal');
    const botLogsTitle = document.getElementById('bot-logs-title');
    const botLogsSubtitle = document.getElementById('bot-logs-subtitle');
    const botLogsContent = document.getElementById('bot-logs-content');
    const btnCloseBotLogs = document.getElementById('btn-close-bot-logs');
    const btnDismissBotLogs = document.getElementById('btn-dismiss-bot-logs');
    const btnRefreshBotLogs = document.getElementById('btn-refresh-bot-logs');
    const addBotModal = document.getElementById('add-bot-modal');
    const btnCloseAddBot = document.getElementById('btn-close-add-bot');
    const btnCancelAddBot = document.getElementById('btn-cancel-add-bot');
    const addBotForm = document.getElementById('add-bot-form');

    let activeViewingBotId = null;

    async function loadBotsList() {
        if (!authToken) return;
        try {
            const res = await apiRequest('/api/bots/list');
            const bots = res.bots || [];
            
            let runningCount = 0;
            let totalRam = 0;
            bots.forEach(b => {
                if (b.is_running) {
                    runningCount++;
                    totalRam += (b.memory_mb || 0);
                }
            });

            if (botsTotalCount) botsTotalCount.textContent = bots.length;
            if (botsRunningCount) botsRunningCount.textContent = `${runningCount} شغال`;
            if (botsRamCount) botsRamCount.textContent = `${totalRam.toFixed(1)} MB`;

            renderBotsGrid(bots);
        } catch (e) {
            showToast('تعذر جلب قائمة البوتات: ' + e.message, 'error');
        }
    }

    function renderBotsGrid(bots) {
        if (!botsCardsGrid) return;
        botsCardsGrid.innerHTML = '';

        if (bots.length === 0) {
            botsCardsGrid.innerHTML = '<div style="grid-column: 1 / -1; text-align: center; padding: 40px; color: var(--text-muted);">لا توجد تطبيقات أو بوتات مسجلة حالياً</div>';
            return;
        }

        bots.forEach(bot => {
            const card = document.createElement('div');
            card.className = 'bot-card glass-card';
            
            const isWebhook = !!bot.webhook_url;
            const whActive = bot.webhook_active !== false;
            const statusClass = isWebhook ? (whActive ? 'status-running' : 'status-stopped') : (bot.is_running ? 'status-running' : 'status-stopped');
            const statusText = isWebhook ? (whActive ? '🌐 ويبهوك (متصل)' : '🌐 ويبهوك (مفصول)') : (bot.is_running ? '🟢 يعمل' : '🔴 متوقف');
            const statusColor = isWebhook ? (whActive ? '#a78bfa' : '#f87171') : (bot.is_running ? '#34d399' : '#f87171');

            card.innerHTML = `
                <div class="bot-card-top">
                    <div class="bot-info-wrap">
                        <div class="bot-avatar">${bot.type === 'php' ? '🐘' : '🐍'}</div>
                        <div class="bot-name-wrap">
                            <h4>${escapeHtml(bot.name)}</h4>
                            <span title="${escapeHtml(bot.script)}">${escapeHtml(bot.script.split('/').pop())}</span>
                        </div>
                    </div>
                    <span class="badge-status ${statusClass}" style="color: ${statusColor};">${statusText}</span>
                </div>

                <div class="bot-metrics-row">
                    <div class="bot-metric">
                        <span>المعالج (CPU)</span>
                        <strong>${isWebhook ? '—' : (bot.is_running ? bot.cpu_percent + '%' : '0%')}</strong>
                    </div>
                    <div class="bot-metric">
                        <span>الذاكرة (RAM)</span>
                        <strong>${isWebhook ? '—' : (bot.is_running ? bot.memory_mb + ' MB' : '0 MB')}</strong>
                    </div>
                    <div class="bot-metric">
                        <span>النظام/المدة</span>
                        <strong>${isWebhook ? 'Webhook' : (bot.is_running ? bot.uptime_str : '—')}</strong>
                    </div>
                </div>

                <div style="font-size: 11px; color: var(--text-muted); font-family: var(--font-code); overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                    PID: <strong style="color: #38bdf8;">${isWebhook ? 'N/A' : (bot.pid || '—')}</strong> &bull; المشغل: <span title="${escapeHtml(bot.venv)}">${escapeHtml(bot.venv.split('/').pop())}</span>
                </div>

                <div class="bot-actions-row">
                    ${isWebhook ?
                        (whActive ? 
                            `<button class="btn btn-sm btn-danger btn-bot-action" data-bot="${escapeHtml(bot.id)}" data-action="stop" style="flex: 2;">⏹️ فصل الويبهوك</button>` :
                            `<button class="btn btn-sm btn-primary btn-bot-action" data-bot="${escapeHtml(bot.id)}" data-action="start" style="flex: 2;">▶️ ربط الويبهوك</button>`) :
                        (bot.is_running ? 
                            `<button class="btn btn-sm btn-secondary btn-bot-action" data-bot="${escapeHtml(bot.id)}" data-action="restart" style="flex: 1;">🔄 إعادة تشغيل</button>
                             <button class="btn btn-sm btn-danger btn-bot-action" data-bot="${escapeHtml(bot.id)}" data-action="stop" style="flex: 1;">⏹️ إيقاف</button>` :
                            `<button class="btn btn-sm btn-primary btn-bot-action" data-bot="${escapeHtml(bot.id)}" data-action="start" style="flex: 2;">▶️ تشغيل البوت</button>`)
                    }
                    <button class="btn btn-sm btn-ghost btn-bot-logs" data-bot="${escapeHtml(bot.id)}" data-name="${escapeHtml(bot.name)}" data-script="${escapeHtml(bot.script)}" title="مشاهدة سجل الكونسول والأخطاء">📜 السجل</button>
                    <button class="btn btn-sm btn-danger btn-bot-action" data-bot="${escapeHtml(bot.id)}" data-action="delete" title="حذف البوت نهائياً" style="padding: 5px;">🗑️</button>
                </div>
            `;
            botsCardsGrid.appendChild(card);
        });

        botsCardsGrid.querySelectorAll('.btn-bot-action').forEach(btn => {
            btn.addEventListener('click', async () => {
                const botId = btn.getAttribute('data-bot');
                const action = btn.getAttribute('data-action');
                if (action === 'delete') {
                    if (!(await window.customConfirm('هل أنت متأكد أنك تريد إيقاف وحذف هذا البوت نهائياً؟'))) return;
                }
                btn.disabled = true;
                btn.innerHTML = '⏳';
                try {
                    const res = await apiRequest('/api/bots/action', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ bot_id: botId, action: action })
                    });
                    showToast(res.message, 'success');
                    await loadBotsList();
                } catch (e) {
                    showToast(e.message, 'error');
                    await loadBotsList();
                }
            });
        });

        botsCardsGrid.querySelectorAll('.btn-bot-logs').forEach(btn => {
            btn.addEventListener('click', () => {
                const botId = btn.getAttribute('data-bot');
                const botName = btn.getAttribute('data-name');
                const botScript = btn.getAttribute('data-script');
                openBotLogsModal(botId, botName, botScript);
            });
        });
    }

    async function openBotLogsModal(botId, botName, botScript) {
        activeViewingBotId = botId;
        currentLogBotName = botName;
        currentLogBotScript = botScript;
        if (botLogsTitle) botLogsTitle.textContent = `سجل مخرجات: ${botName}`;
        if (botLogsSubtitle) botLogsSubtitle.textContent = `المسار: ${botScript}`;
        if (botLogsContent) botLogsContent.textContent = 'جاري قراءة السجلات...';
        if (botLogsModal) botLogsModal.classList.remove('hidden');

        try {
            const res = await apiRequest(`/api/bots/logs?bot_id=${encodeURIComponent(botId)}&lines=120`);
            if (botLogsContent) {
                botLogsContent.textContent = res.logs || 'لا توجد أسطر في السجل بعد';
                botLogsContent.scrollTop = botLogsContent.scrollHeight;
            }
        } catch (e) {
            if (botLogsContent) botLogsContent.textContent = 'خطأ أثناء جلب السجلات: ' + e.message;
        }
    }

    if (btnRefreshBotLogs) {
        btnRefreshBotLogs.addEventListener('click', () => {
            if (activeViewingBotId) openBotLogsModal(activeViewingBotId, currentLogBotName, currentLogBotScript);
        });
    }
    if (btnCloseBotLogs) btnCloseBotLogs.addEventListener('click', () => botLogsModal.classList.add('hidden'));
    if (btnDismissBotLogs) btnDismissBotLogs.addEventListener('click', () => botLogsModal.classList.add('hidden'));
    if (btnBotsRefresh) btnBotsRefresh.addEventListener('click', () => {
        loadBotsList();
        showToast('تم تحديث حالة البوتات', 'info');
    });

    if (btnAddCustomBot) btnAddCustomBot.addEventListener('click', () => {
        if (addBotForm) addBotForm.reset();
        if (addBotModal) addBotModal.classList.remove('hidden');
    });
    if (btnCloseAddBot) btnCloseAddBot.addEventListener('click', () => addBotModal.classList.add('hidden'));
    if (btnCancelAddBot) btnCancelAddBot.addEventListener('click', () => addBotModal.classList.add('hidden'));

    if (addBotForm) {
        addBotForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const name = document.getElementById('new-bot-name').value.trim();
            const script = document.getElementById('new-bot-script').value.trim();
            const venv = document.getElementById('new-bot-venv').value.trim() || '/usr/bin/python3';
            const cwd = document.getElementById('new-bot-cwd').value.trim() || '';

            try {
                const res = await apiRequest('/api/bots/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ name, script, venv, cwd })
                });
                showToast(res.message, 'success');
                if (addBotModal) addBotModal.classList.add('hidden');
                loadBotsList();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    // ==============================================================================
    // 💾 2. BACKUP & RESTORE MANAGER LOGIC
    // ==============================================================================
    const backupsTableBody = document.getElementById('backups-table-body');
    const backupsCountStat = document.getElementById('backups-count-stat');
    const btnBackupsRefresh = document.getElementById('btn-backups-refresh');

    window.createPresetBackup = async function(preset) {
        if (!(await window.customConfirm(`هل تريد أخذ نسخة احتياطية فورية لـ (${preset}))؟`)) return;
        showToast('جاري إنشاء النسخة الاحتياطية وضغط الملفات...', 'info');
        try {
            const res = await apiRequest('/api/backups/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ preset })
            });
            showToast(res.message, 'success');
            loadBackups();
        } catch (e) {
            showToast(e.message, 'error');
        }
    };

    async function loadBackups() {
        if (!authToken) return;
        try {
            const res = await apiRequest('/api/backups/list');
            const backups = res.backups || [];
            if (backupsCountStat) backupsCountStat.textContent = `${backups.length} ملف نسخة`;
            renderBackupsTable(backups);
        } catch (e) {
            showToast('تعذر جلب النسخ الاحتياطية: ' + e.message, 'error');
        }
    }

    function renderBackupsTable(backups) {
        if (!backupsTableBody) return;
        backupsTableBody.innerHTML = '';

        if (backups.length === 0) {
            backupsTableBody.innerHTML = '<tr><td colspan="4" style="text-align: center; padding: 24px; color: var(--text-muted);">لا توجد نسخ احتياطية مسجلة بعد</td></tr>';
            return;
        }

        backups.forEach(b => {
            const tr = document.createElement('tr');
            const downloadUrl = `/api/backups/download?file=${encodeURIComponent(b.filepath)}&token=${authToken}`;
            tr.innerHTML = `
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span>📦</span>
                        <strong style="color: var(--text-primary); font-family: var(--font-code); font-size: 13px;">${escapeHtml(b.filename)}</strong>
                    </div>
                </td>
                <td><span class="badge-proto" style="background: rgba(56, 189, 248, 0.15); color: #38bdf8;">${escapeHtml(b.size_str)}</span></td>
                <td><span style="color: var(--text-muted); font-size: 12px; font-family: var(--font-code);">${escapeHtml(b.created_str)}</span></td>
                <td style="text-align: center;">
                    <a href="${downloadUrl}" class="btn-srv restart" style="text-decoration: none; display: inline-block; margin-left: 6px;" download>⬇️ تنزيل</a>
                    <button class="btn-srv stop btn-delete-backup" data-path="${escapeHtml(b.filepath)}">🗑️ حذف</button>
                </td>
            `;
            backupsTableBody.appendChild(tr);
        });

        backupsTableBody.querySelectorAll('.btn-delete-backup').forEach(btn => {
            btn.addEventListener('click', async () => {
                const filepath = btn.getAttribute('data-path');
                if (!(await window.customConfirm(`هل أنت متأكد من حذف النسخة الاحتياطية (${filepath.split('/')).pop()})؟`)) return;
                try {
                    const res = await apiRequest('/api/backups/delete', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ filepath })
                    });
                    showToast(res.message, 'success');
                    loadBackups();
                } catch (e) {
                    showToast(e.message, 'error');
                }
            });
        });
    }

    if (btnBackupsRefresh) btnBackupsRefresh.addEventListener('click', () => {
        loadBackups();
        showToast('تم تحديث قائمة النسخ الاحتياطية', 'info');
    });

    // Preset click listeners
    // Removed shop and yms
    const pDb = document.getElementById('preset-backup-db');
    if (pDb) pDb.addEventListener('click', () => window.createPresetBackup('databases'));
    const pPanel = document.getElementById('preset-backup-panel');
    if (pPanel) pPanel.addEventListener('click', () => window.createPresetBackup('server_panel'));

    // ==============================================================================
    // 🗄️ 3. SQLITE DATABASE STUDIO LOGIC
    // ==============================================================================
    const dbSelectDropdown = document.getElementById('db-select-dropdown');
    const btnDbRefresh = document.getElementById('btn-db-refresh');
    const dbTablesCount = document.getElementById('db-tables-count');
    const dbTablesList = document.getElementById('db-tables-list');
    const dbQueryInput = document.getElementById('db-query-input');
    const btnRunSql = document.getElementById('btn-run-sql');
    const dbQueryStat = document.getElementById('db-query-stat');
    const dbResultsHead = document.getElementById('db-results-head');
    const dbResultsBody = document.getElementById('db-results-body');

    async function loadDatabases() {
        if (!authToken || !dbSelectDropdown) return;
        try {
            const res = await apiRequest('/api/db/list');
            const dbs = res.databases || [];
            dbSelectDropdown.innerHTML = '';
            
            if (dbs.length === 0) {
                dbSelectDropdown.innerHTML = '<option value="">لا توجد قواعد بيانات SQLite في السيرفر</option>';
                return;
            }

            dbs.forEach(d => {
                const opt = document.createElement('option');
                opt.value = d.path;
                opt.textContent = `${d.name} (${d.size_str}) - ${d.path}`;
                dbSelectDropdown.appendChild(opt);
            });

            if (dbs.length > 0) {
                loadDbSchema(dbs[0].path);
            }
        } catch (e) {
            showToast('تعذر فحص قواعد البيانات: ' + e.message, 'error');
        }
    }

    async function loadDbSchema(dbPath) {
        if (!dbPath) return;
        try {
            const res = await apiRequest(`/api/db/schema?db_path=${encodeURIComponent(dbPath)}`);
            const tables = res.tables || [];
            const schema = res.schema || {};

            if (dbTablesCount) dbTablesCount.textContent = `${tables.length} جدول`;
            if (dbTablesList) {
                dbTablesList.innerHTML = '';
                if (tables.length === 0) {
                    dbTablesList.innerHTML = '<span style="color: var(--text-muted); font-size: 13px;">لا توجد جداول في هذه القاعدة</span>';
                } else {
                    tables.forEach(tbl => {
                        const count = schema[tbl] ? schema[tbl].total_rows : 0;
                        const btn = document.createElement('button');
                        btn.className = 'db-table-btn';
                        btn.innerHTML = `
                            <strong>📊 ${escapeHtml(tbl)}</strong>
                            <span class="badge-tag">${count} صف</span>
                        `;
                        btn.addEventListener('click', () => {
                            dbTablesList.querySelectorAll('.db-table-btn').forEach(b => b.classList.remove('active'));
                            btn.classList.add('active');
                            const sql = `SELECT * FROM "${tbl}" LIMIT 50;`;
                            if (dbQueryInput) dbQueryInput.value = sql;
                            runDbQuery(dbPath, sql);
                        });
                        dbTablesList.appendChild(btn);
                    });
                }
            }
        } catch (e) {
            showToast('تعذر قراءة هيكل القاعدة: ' + e.message, 'error');
        }
    }

    async function runDbQuery(dbPath, sql) {
        if (!dbPath || !sql) return;
        if (dbQueryStat) dbQueryStat.textContent = 'جاري التنفيذ...';
        try {
            const res = await apiRequest('/api/db/query', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ db_path: dbPath, query: sql, limit: 100 })
            });

            if (res.is_select) {
                if (dbQueryStat) dbQueryStat.textContent = `تم جلب ${res.count} صف في (${res.execution_ms} ms)`;
                renderDbResults(res.columns, res.rows);
            } else {
                if (dbQueryStat) dbQueryStat.textContent = `${res.message} في (${res.execution_ms} ms)`;
                if (dbResultsHead) dbResultsHead.innerHTML = '<tr><th>الحالة</th></tr>';
                if (dbResultsBody) dbResultsBody.innerHTML = `<tr><td style="color: #34d399; padding: 16px;">${escapeHtml(res.message)}</td></tr>`;
            }
        } catch (e) {
            if (dbQueryStat) dbQueryStat.textContent = 'خطأ في الاستعلام';
            if (dbResultsHead) dbResultsHead.innerHTML = '<tr><th>خطأ SQL</th></tr>';
            if (dbResultsBody) dbResultsBody.innerHTML = `<tr><td style="color: #f87171; padding: 16px;">${escapeHtml(e.message)}</td></tr>`;
        }
    }

    function renderDbResults(columns, rows) {
        if (!dbResultsHead || !dbResultsBody) return;
        dbResultsHead.innerHTML = '';
        dbResultsBody.innerHTML = '';

        if (!columns || columns.length === 0) {
            dbResultsHead.innerHTML = '<tr><th>النتيجة</th></tr>';
            dbResultsBody.innerHTML = '<tr><td style="text-align: center; padding: 18px; color: var(--text-muted);">الاستعلام لم يرجع أي حقول</td></tr>';
            return;
        }

        const trHead = document.createElement('tr');
        columns.forEach(col => {
            const th = document.createElement('th');
            th.textContent = col;
            trHead.appendChild(th);
        });
        dbResultsHead.appendChild(trHead);

        if (!rows || rows.length === 0) {
            const tr = document.createElement('tr');
            tr.innerHTML = `<td colspan="${columns.length}" style="text-align: center; padding: 20px; color: var(--text-muted);">الجدول فارغ (0 صفوف)</td>`;
            dbResultsBody.appendChild(tr);
            return;
        }

        rows.forEach(r => {
            const tr = document.createElement('tr');
            r.forEach(val => {
                const td = document.createElement('td');
                td.style.fontFamily = 'var(--font-code)';
                td.style.fontSize = '12px';
                td.textContent = val === null ? 'NULL' : String(val);
                if (val === null) td.style.color = 'var(--text-muted)';
                tr.appendChild(td);
            });
            dbResultsBody.appendChild(tr);
        });
    }

    if (dbSelectDropdown) {
        dbSelectDropdown.addEventListener('change', () => {
            loadDbSchema(dbSelectDropdown.value);
        });
    }
    if (btnDbRefresh) {
        btnDbRefresh.addEventListener('click', () => {
            loadDatabases();
            showToast('تم إعادة فحص قواعد البيانات', 'info');
        });
    }
    if (btnRunSql) {
        btnRunSql.addEventListener('click', () => {
            const dbPath = dbSelectDropdown ? dbSelectDropdown.value : '';
            const sql = dbQueryInput ? dbQueryInput.value.trim() : '';
            if (!dbPath) {
                showToast('يرجى اختيار قاعدة بيانات أولاً', 'warning');
                return;
            }
            if (!sql) {
                showToast('يرجى كتابة استعلام SQL', 'warning');
                return;
            }
            runDbQuery(dbPath, sql);
        });
    }

    // ==============================================================================
    // 📜 4. UNIFIED SYSTEM LOG VIEWER LOGIC
    // ==============================================================================
    const logSourceSelect = document.getElementById('log-source-select');
    const logFilterInput = document.getElementById('log-filter-input');
    const btnRefreshLog = document.getElementById('btn-refresh-log');
    const logViewerFileLabel = document.getElementById('log-viewer-file-label');
    const logLinesCount = document.getElementById('log-lines-count');
    const logContentDisplay = document.getElementById('log-content-display');

    async function loadLogView() {
        if (!authToken || !logSourceSelect || !logContentDisplay) return;
        const source = logSourceSelect.value;
        const filter = logFilterInput ? logFilterInput.value.trim() : '';

        if (logViewerFileLabel) logViewerFileLabel.textContent = `المصدر: ${source}`;
        logContentDisplay.textContent = 'جاري جلب السطور...';

        try {
            const res = await apiRequest(`/api/logs/view?source=${encodeURIComponent(source)}&lines=150&filter_query=${encodeURIComponent(filter)}`);
            const lines = res.lines || [];
            if (logLinesCount) logLinesCount.textContent = `${lines.length} سطر`;
            
            if (lines.length === 0) {
                logContentDisplay.textContent = 'لا توجد أسطر في ملف السجل الحالي مطابقة للبحث.';
            } else {
                logContentDisplay.textContent = lines.join('\n');
                logContentDisplay.scrollTop = logContentDisplay.scrollHeight;
            }
        } catch (e) {
            logContentDisplay.textContent = 'تعذر قراءة السجل: ' + e.message;
        }
    }

    if (logSourceSelect) logSourceSelect.addEventListener('change', loadLogView);
    if (btnRefreshLog) btnRefreshLog.addEventListener('click', () => {
        loadLogView();
        showToast('تم تحديث السجل', 'info');
    });
    if (logFilterInput) {
        let logFilterTimer = null;
        logFilterInput.addEventListener('input', () => {
            if (logFilterTimer) clearTimeout(logFilterTimer);
            logFilterTimer = setTimeout(loadLogView, 400);
        });
    }

    // ==============================================================================
    // 🔔 5. TELEGRAM SETTINGS & ALERTS LOGIC
    // ==============================================================================
    const tgSettingsForm = document.getElementById('telegram-settings-form');
    const tgBotTokenInput = document.getElementById('tg-bot-token');
    const tgChatIdInput = document.getElementById('tg-chat-id');
    const tgAlertsEnabled = document.getElementById('tg-alerts-enabled');
    const tgAlertAttack = document.getElementById('tg-alert-attack');
    const tgAlertBot = document.getElementById('tg-alert-bot');
    const btnTestTelegram = document.getElementById('btn-test-telegram');

    async function loadTelegramSettings() {
        if (!authToken || !tgBotTokenInput) return;
        try {
            const res = await apiRequest('/api/settings/telegram');
            if (res.has_token && tgBotTokenInput) tgBotTokenInput.placeholder = res.masked_token;
            if (tgChatIdInput) tgChatIdInput.value = res.chat_id || '';
            if (tgAlertsEnabled) tgAlertsEnabled.checked = !!res.alerts_enabled;
            if (tgAlertAttack) tgAlertAttack.checked = res.alert_on_attack !== false;
            if (tgAlertBot) tgAlertBot.checked = res.alert_on_bot_crash !== false;
        } catch (e) {
            // silent fail on load
        }
    }

    if (tgSettingsForm) {
        tgSettingsForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            const token = tgBotTokenInput ? tgBotTokenInput.value.trim() : '';
            const chatId = tgChatIdInput ? tgChatIdInput.value.trim() : '';
            const enabled = tgAlertsEnabled ? tgAlertsEnabled.checked : false;
            const alertAttack = tgAlertAttack ? tgAlertAttack.checked : true;
            const alertBot = tgAlertBot ? tgAlertBot.checked : true;

            try {
                const res = await apiRequest('/api/settings/telegram', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        bot_token: token,
                        chat_id: chatId,
                        alerts_enabled: enabled,
                        alert_on_attack: alertAttack,
                        alert_on_bot_crash: alertBot
                    })
                });
                showToast(res.message, 'success');
                loadTelegramSettings();
            } catch (err) {
                showToast(err.message, 'error');
            }
        });
    }

    if (btnTestTelegram) {
        btnTestTelegram.addEventListener('click', async () => {
            btnTestTelegram.disabled = true;
            btnTestTelegram.textContent = 'جاري الإرسال...';
            try {
                const res = await apiRequest('/api/settings/telegram/test', { method: 'POST' });
                showToast(res.message, 'success');
            } catch (e) {
                showToast(e.message, 'error');
            } finally {
                btnTestTelegram.disabled = false;
                btnTestTelegram.textContent = '⚡ تجربة إرسال تنبيه';
            }
        });
    }

    // Startup check
    checkAuth();
});



// --- MOBILE MENU TOGGLE ---
function initMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const appHeader = document.querySelector('.app-header');
    
    if (mobileMenuBtn && appHeader && !mobileMenuBtn.dataset.bound) {
        mobileMenuBtn.dataset.bound = true;
        mobileMenuBtn.addEventListener('click', () => {
            appHeader.classList.toggle('menu-open');
        });
        
        // Close menu when a tab is clicked
        const navTabs = document.querySelectorAll('.nav-tab');
        navTabs.forEach(tab => {
            tab.addEventListener('click', () => {
                appHeader.classList.remove('menu-open');
            });
        });
    }
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initMobileMenu);
} else {
    initMobileMenu();
}

// --- Native i18n Translation (Arabic / English) ---
document.addEventListener('DOMContentLoaded', () => {
    // Determine language from localStorage (default 'ar')
    let currentLang = localStorage.getItem('app_lang') || 'ar';
    
    const userActions = document.querySelector('.user-actions');
    if (userActions) {
        const langBtn = document.createElement('button');
        langBtn.id = 'lang-toggle-btn';
        langBtn.className = 'btn btn-icon';
        langBtn.title = 'English / عربي';
        langBtn.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>';
        
        langBtn.addEventListener('click', () => {
            const nextLang = currentLang === 'en' ? 'ar' : 'en';
            localStorage.setItem('app_lang', nextLang);
            // Clear any old google translate cookie to prevent conflicts
            document.cookie = `googtrans=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
            location.reload();
        });

        // Insert before the theme toggle
        userActions.insertBefore(langBtn, userActions.firstChild);
    }
    
    // Apply translations if English
    if (currentLang === 'en') {
        document.documentElement.dir = 'ltr';
        document.documentElement.lang = 'en';
        
        // Wait for window.ar_to_en to be available
        const applyTranslations = () => {
            if (!window.ar_to_en) return;
            
            // Sort keys by length descending to prevent partial match bugs (e.g. replacing short words inside longer ones)
            const sortedKeys = Object.keys(window.ar_to_en).sort((a, b) => b.length - a.length);

            // Fast text node replacer
            const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null, false);
            const nodes = [];
            let n;
            while (n = walker.nextNode()) nodes.push(n);
            
            for (let node of nodes) {
                if (node.nodeType === 3) {
                    let text = node.nodeValue.trim();
                    // Replace exact matches
                    if (text && window.ar_to_en[text] && window.ar_to_en[text] !== text) {
                        node.nodeValue = node.nodeValue.replace(text, window.ar_to_en[text]);
                    } else if (text) {
                        // Replace substrings (for dynamically inserted values like 0 سطر)
                        for (let ar of sortedKeys) {
                            if (ar.length > 2 && text.includes(ar) && window.ar_to_en[ar] !== ar) {
                                text = text.replace(ar, window.ar_to_en[ar]);
                                node.nodeValue = text;
                            }
                        }
                    }
                } else if (node.nodeType === 1) {
                    ['title', 'placeholder', 'value', 'data-act'].forEach(attr => {
                        let val = node.getAttribute(attr);
                        if (val && window.ar_to_en[val.trim()] && window.ar_to_en[val.trim()] !== val.trim()) {
                            node.setAttribute(attr, window.ar_to_en[val.trim()]);
                        }
                    });
                }
            }
            
            // Observe DOM changes (for dynamic toasts, logs, lists)
            const observer = new MutationObserver((mutations) => {
                mutations.forEach(m => {
                    m.addedNodes.forEach(node => {
                        if (node.nodeType === 1) {
                            const dynWalker = document.createTreeWalker(node, NodeFilter.SHOW_TEXT | NodeFilter.SHOW_ELEMENT, null, false);
                            let dynN;
                            while (dynN = dynWalker.nextNode()) {
                                if (dynN.nodeType === 3) {
                                    let text = dynN.nodeValue.trim();
                                    if (text && window.ar_to_en[text] && window.ar_to_en[text] !== text) {
                                        dynN.nodeValue = dynN.nodeValue.replace(text, window.ar_to_en[text]);
                                    } else if (text) {
                                        for (let ar of sortedKeys) {
                                            if (ar.length > 2 && text.includes(ar) && window.ar_to_en[ar] !== ar) {
                                                text = text.replace(ar, window.ar_to_en[ar]);
                                                dynN.nodeValue = text;
                                            }
                                        }
                                    }
                                }
                            }
                        } else if (node.nodeType === 3) {
                            let text = node.nodeValue.trim();
                            if (text && window.ar_to_en[text] && window.ar_to_en[text] !== text) {
                                node.nodeValue = node.nodeValue.replace(text, window.ar_to_en[text]);
                            } else if (text) {
                                for (let ar of sortedKeys) {
                                    if (ar.length > 2 && text.includes(ar) && window.ar_to_en[ar] !== ar) {
                                        text = text.replace(ar, window.ar_to_en[ar]);
                                        node.nodeValue = text;
                                    }
                                }
                            }
                        }
                    });
                });
            });
            observer.observe(document.body, { childList: true, subtree: true, characterData: true });
        };
        
        // Wait briefly for dictionary to load if it's placed after app.v2.js
        if (window.ar_to_en) {
            applyTranslations();
        } else {
            setTimeout(applyTranslations, 100);
        }
    } else {
        document.documentElement.dir = 'rtl';
        document.documentElement.lang = 'ar';
    }
});
