document.addEventListener("DOMContentLoaded", () => {
    // ... [existing UI tabs setup]
    const tabPy = document.getElementById("tab-bot-python");
    const tabPhp = document.getElementById("tab-bot-php");
    const formPy = document.getElementById("add-bot-form-python");
    const formPhp = document.getElementById("add-bot-form-php");

    if (tabPy && tabPhp) {
        tabPy.addEventListener("click", () => {
            tabPy.className = "btn btn-primary";
            tabPhp.className = "btn btn-ghost";
            formPy.style.display = "block";
            formPhp.style.display = "none";
        });
        tabPhp.addEventListener("click", () => {
            tabPhp.className = "btn btn-primary";
            tabPy.className = "btn btn-ghost";
            formPhp.style.display = "block";
            formPy.style.display = "none";
        });
    }

    // --- FILE PICKER LOGIC ---
    const modalFilePicker = document.getElementById("modal-file-picker");
    const btnCloseFilePicker = document.getElementById("btn-close-file-picker");
    const fpPathInput = document.getElementById("file-picker-path");
    const fpList = document.getElementById("file-picker-list");
    let currentPickerTarget = null; // input element to fill

    async function loadFiles(path) {
        fpList.innerHTML = '<div style="padding:15px; text-align:center;">جاري التحميل...</div>';
        fpPathInput.value = path;
        try {
            const req = await fetch(`/api/files/list?path=${encodeURIComponent(path)}`);
            const res = await req.json();
            
            let html = '';
            // Up dir button
            if (path !== '/') {
                const parentPath = path.substring(0, path.lastIndexOf('/')) || '/';
                html += `<div class="fp-item fp-dir" data-path="${parentPath}" style="padding:8px; cursor:pointer; border-bottom:1px solid var(--border-color); color: var(--text-primary); font-family: monospace;">
                    <span style="font-size: 16px;">📁</span> .. (رجوع)
                </div>`;
            }
            
            if (res.items && res.items.length > 0) {
                res.items.forEach(item => {
                    const icon = item.is_dir ? '📁' : '📄';
                    const color = item.is_dir ? 'var(--accent-warning)' : 'var(--text-primary)';
                    const cls = item.is_dir ? 'fp-dir' : 'fp-file';
                    html += `
                        <div class="fp-item ${cls}" data-path="${item.path}" style="padding:8px; cursor:pointer; border-bottom:1px solid var(--border-color); color:${color}; display:flex; gap:10px; align-items:center;">
                            <span style="font-size: 16px;">${icon}</span>
                            <span style="font-family: monospace; font-size: 13px;">${item.name}</span>
                        </div>
                    `;
                });
            } else {
                html += '<div style="padding:15px; text-align:center; color:#94a3b8;">المجلد فارغ</div>';
            }
            fpList.innerHTML = html;
            
            // Bind click events
            fpList.querySelectorAll('.fp-dir').forEach(el => {
                el.addEventListener('click', () => loadFiles(el.getAttribute('data-path')));
            });
            fpList.querySelectorAll('.fp-file').forEach(el => {
                el.addEventListener('click', () => {
                    if (currentPickerTarget) {
                        currentPickerTarget.value = el.getAttribute('data-path');
                        // Auto-fill CWD if it's the python form
                        if (currentPickerTarget.id === 'new-bot-script-py') {
                            const cwdInput = document.getElementById('new-bot-cwd-py');
                            if (cwdInput) cwdInput.value = path;
                        }
                    }
                    modalFilePicker.classList.add("hidden");
                });
            });
            
        } catch (e) {
            fpList.innerHTML = '<div style="padding:15px; text-align:center; color:#ef4444;">حدث خطأ أثناء تحميل الملفات</div>';
        }
    }

    window.openFilePicker = function(targetInputId) {
        currentPickerTarget = document.getElementById(targetInputId);
        modalFilePicker.classList.remove("hidden");
        // Start at root or target path's folder
        let startPath = "/root";
        if (currentPickerTarget && currentPickerTarget.value) {
            const parts = currentPickerTarget.value.split('/');
            parts.pop();
            if (parts.length > 0) startPath = parts.join('/') || '/';
        }
        loadFiles(startPath);
    }

    const btnBrowsePy = document.getElementById("btn-browse-py");
    const btnBrowsePhp = document.getElementById("btn-browse-php");
    if (btnBrowsePy) btnBrowsePy.addEventListener("click", () => openFilePicker("new-bot-script-py"));
    if (btnBrowsePhp) btnBrowsePhp.addEventListener("click", () => openFilePicker("new-bot-script-php"));
    
    const btnSelectCurrentDir = document.getElementById("btn-select-current-dir");
    if (btnSelectCurrentDir) {
        btnSelectCurrentDir.addEventListener("click", () => {
            if (currentPickerTarget) {
                currentPickerTarget.value = fpPathInput.value;
            }
            modalFilePicker.classList.add("hidden");
        });
    }

    if (btnCloseFilePicker) {
        btnCloseFilePicker.addEventListener("click", () => modalFilePicker.classList.add("hidden"));
    }

    // --- PHP ANALYSIS & FORM SUBMIT ---
    const btnAnalyze = document.getElementById("btn-analyze-php");
    const phpPath = document.getElementById("new-bot-script-php");
    const resBox = document.getElementById("php-analysis-result");
    const whFields = document.getElementById("php-webhook-fields");
    const modeSelectorBox = document.getElementById("php-mode-selector");
    const runModeDropdown = document.getElementById("php-run-mode");
    
    let detectedMode = "unknown";
    let finalSelectedMode = "unknown";

    if (runModeDropdown) {
        runModeDropdown.addEventListener("change", (e) => {
            finalSelectedMode = e.target.value;
            if (finalSelectedMode === "webhook") {
                whFields.style.display = "block";
            } else {
                whFields.style.display = "none";
            }
        });
    }

    if (btnAnalyze) {
        btnAnalyze.addEventListener("click", async () => {
            if (!phpPath.value.trim()) {
                window.showToast("الرجاء تحديد مسار الملف أولاً", "error");
                return;
            }
            btnAnalyze.textContent = "⏳...";
            try {
                const res = await window.apiRequest("/api/bots/analyze_php", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({file_path: phpPath.value.trim()})
                });
                if (res.status === "error") {
                    window.showToast(res.message, "error");
                    return;
                }
                detectedMode = res.mode;
                finalSelectedMode = detectedMode;
                
                // Pre-fill token if found
                const tokenInput = document.getElementById("php-bot-token");
                const urlInput = document.getElementById("php-bot-url");
                if (res.token && tokenInput) {
                    tokenInput.value = res.token;
                }
                
                // Pre-fill URL smartly
                if (urlInput) {
                    let filename = phpPath.value.split('/').pop();
                    urlInput.value = `https://${window.location.host}/${filename}`;
                }

                resBox.style.display = "block";
                modeSelectorBox.style.display = "none";
                
                if (detectedMode === "both") {
                    resBox.innerHTML = `تم الفحص: <strong>هذا الملف يدعم النظامين معاً (Webhook و Polling) 🌟</strong><br>اللوحة استخرجت التوكن والرابط تلقائياً، يرجى اختيار طريقة التشغيل:`;
                    modeSelectorBox.style.display = "block";
                    runModeDropdown.value = "webhook";
                    finalSelectedMode = "webhook";
                    whFields.style.display = "block";
                } else if (detectedMode === "webhook") {
                    resBox.innerHTML = `تم الفحص: <strong>النظام المكتشف Webhook 🌐</strong><br>اللوحة استخرجت التوكن والرابط تلقائياً.`;
                    whFields.style.display = "block";
                } else if (detectedMode === "polling") {
                    resBox.innerHTML = `تم الفحص: <strong>النظام المكتشف Polling 🔄</strong><br>سيتم تشغيله في الخلفية دون الحاجة لويبهوك.`;
                    whFields.style.display = "none";
                } else {
                    resBox.innerHTML = `لم يتم اكتشاف نظام واضح (ربما يكون سكربت عادي). سيتم تشغيله بنظام Polling افتراضياً.`;
                    whFields.style.display = "none";
                    finalSelectedMode = "polling";
                }
            } catch (e) {
                window.showToast("حدث خطأ أثناء الفحص", "error");
            } finally {
                btnAnalyze.textContent = "🔍 فحص الملف";
            }
        });
    }

    // Handle Python Submit
    if (formPy) {
        formPy.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                bot_id: "bot_" + Math.random().toString(36).substr(2, 6),
                name: document.getElementById("new-bot-name-py").value.trim(),
                script: document.getElementById("new-bot-script-py").value.trim(),
                venv: document.getElementById("new-bot-venv-py").value.trim(),
                cwd: document.getElementById("new-bot-cwd-py").value.trim(),
                log: "/root/" + document.getElementById("new-bot-name-py").value.trim().replace(/\s+/g, '_') + ".log",
                type: "python"
            };
            submitBot(payload);
        });
    }

    // Handle PHP Submit
    if (formPhp) {
        formPhp.addEventListener("submit", async (e) => {
            e.preventDefault();
            const payload = {
                bot_id: "bot_" + Math.random().toString(36).substr(2, 6),
                name: document.getElementById("new-bot-name-php").value.trim(),
                script: document.getElementById("new-bot-script-php").value.trim(),
                type: "php",
                webhook_url: finalSelectedMode === "webhook" ? (document.getElementById("php-bot-url") ? document.getElementById("php-bot-url").value.trim() : "") : "",
                bot_token: document.getElementById("php-bot-token") ? document.getElementById("php-bot-token").value.trim() : "",
                venv: document.getElementById("new-bot-venv-php") ? document.getElementById("new-bot-venv-php").value : "php",
                log: "/root/" + document.getElementById("new-bot-name-php").value.trim().replace(/\s+/g, '_') + ".log",
            };
            
            // If Webhook, we set it now
            
            // If Polling, delete Webhook first to prevent conflict!
            if (finalSelectedMode === "polling" && payload.bot_token) {
                try {
                    await window.apiRequest("/api/bots/webhook/delete", {
                        method: "POST",
                        headers: {"Content-Type": "application/json"},
                        body: JSON.stringify({token: payload.bot_token, url: ""})
                    });
                } catch(e) { console.error("Failed to delete webhook", e); }
            }

            // If Webhook, we set it now
            if (finalSelectedMode === "webhook") {

                if (!payload.bot_token || !payload.webhook_url) {
                    window.showToast("الرجاء إدخال التوكن والرابط!", "error");
                    return;
                }
                try {
                    const res = await window.apiRequest("/api/bots/webhook/set", {
                        method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({token: payload.bot_token, url: payload.webhook_url})
                    });
                    if (res.status === "error") {
                        window.showToast("خطأ من تليجرام: " + res.message, "error");
                        return;
                    }
                    window.showToast("تم ربط الويبهوك بنجاح!", "success");
                } catch(e) {
                    window.showToast("فشل الاتصال بتليجرام!", "error");
                    return;
                }
            }
            
            submitBot(payload);
        });
    }

    async function submitBot(payload) {
        try {
            const res = await window.apiRequest("/api/bots/register", {
                method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify(payload)
            });
            if (res.status === "success") {
                window.showToast("تم إضافة البوت بنجاح!", "success");
                document.getElementById("add-bot-modal").classList.add("hidden");
                
                // Triger refresh click on the main UI
                const btnBotsRefresh = document.getElementById('btn-bots-refresh');
                if (btnBotsRefresh) {
                    btnBotsRefresh.click();
                } else if (typeof window.loadBotsData === "function") {
                    window.loadBotsData();
                }
            }
        } catch(e) {
            window.showToast("خطأ أثناء الحفظ", "error");
        }
    }

    const btnAnalyzePy = document.getElementById("btn-analyze-py");
    const pyPath = document.getElementById("new-bot-script-py");
    const pyVenv = document.getElementById("new-bot-venv-py");

    if (btnAnalyzePy) {
        btnAnalyzePy.addEventListener("click", async () => {
            if (!pyPath.value.trim()) {
                window.showToast("الرجاء تحديد مسار الملف أولاً", "error");
                return;
            }
            btnAnalyzePy.textContent = "⏳...";
            try {
                const res = await window.apiRequest("/api/bots/analyze_python", {
                    method: "POST",
                    headers: {"Content-Type": "application/json"},
                    body: JSON.stringify({file_path: pyPath.value.trim()})
                });
                if (res.status === "error") {
                    window.showToast(res.message, "error");
                    return;
                }
                
                let msg = "تم فحص الملف!";
                if (res.venv) {
                    pyVenv.value = res.venv;
                    msg += " تم العثور على بيئة افتراضية (venv) مخصصة.";
                    window.showToast(msg, "success");
                } else {
                    pyVenv.value = "/usr/bin/python3";
                    if (res.has_requirements) {
                        if (await window.customConfirm("تم العثور على ملف requirements.txt ولكن لا توجد بيئة مخصصة (venv). هل ترغب في إنشاء بيئة افتراضية وتثبيت المكاتب تلقائياً الآن؟ (قد يستغرق ذلك دقيقة)")) {
                            btnAnalyzePy.textContent = "⏳ جاري التثبيت...";
                            try {
                                const setupRes = await window.apiRequest("/api/bots/setup_venv", {
                                    method: "POST",
                                    headers: {"Content-Type": "application/json"},
                                    body: JSON.stringify({script_path: pyPath.value.trim()})
                                });
                                if (setupRes.status === "success") {
                                    pyVenv.value = setupRes.venv_path;
                                    window.showToast("تم إنشاء البيئة الافتراضية وتثبيت المكاتب بنجاح!", "success");
                                } else {
                                    window.showToast(setupRes.message, "error");
                                }
                            } catch(e) {
                                window.showToast("فشل الاتصال أثناء إعداد البيئة", "error");
                            }
                        } else {
                            msg += " سيتم استخدام بايثون الأساسي.";
                            window.showToast(msg, "warning");
                        }
                    } else {
                        msg += " لم يتم العثور على venv، سيتم استخدام بايثون الأساسي.";
                        window.showToast(msg, "success");
                    }
                }
            } catch (e) {
                window.showToast("حدث خطأ أثناء الفحص", "error");
            } finally {
                btnAnalyzePy.textContent = "🔍 ذكاء";
            }
        });
    }


    if (pyPath) {
        pyPath.addEventListener("blur", () => {
            if (pyPath.value.trim() && btnAnalyzePy) {
                btnAnalyzePy.click();
            }
        });
    }


    if (phpPath) {
        phpPath.addEventListener("blur", () => {
            if (phpPath.value.trim() && btnAnalyze) {
                btnAnalyze.click();
            }
        });
    }
});
