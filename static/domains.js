function toggleDomainTypeFields() {
    const type = document.getElementById('domain-type').value;
    if (type === 'static') {
        document.getElementById('domain-static-fields').style.display = 'block';
        document.getElementById('domain-proxy-fields').style.display = 'none';
    } else {
        document.getElementById('domain-static-fields').style.display = 'none';
        document.getElementById('domain-proxy-fields').style.display = 'block';
    }
}

function showDomainModal(isEdit = false, domainName = '', domainType = 'static', domainRoot = '', domainProxy = '', forceHttps = false) {
    document.getElementById('modal-domain').classList.remove('hidden');
    
    document.getElementById('domain-name').value = domainName;
    document.getElementById('domain-type').value = domainType;
    document.getElementById('domain-root').value = domainRoot;
    document.getElementById('domain-proxy').value = domainProxy;
    document.getElementById('domain-force-https').checked = forceHttps;
    
    document.getElementById('modal-domain').dataset.editMode = isEdit ? 'true' : 'false';
    document.getElementById('modal-domain').dataset.oldDomain = domainName;
    
    document.querySelector('#modal-domain .modal-header h3').innerText = isEdit ? 'تعديل إعدادات النطاق' : 'إضافة نطاق جديد';
    document.getElementById('domain-name').disabled = isEdit;
    
    toggleDomainTypeFields();
}

function closeDomainModal() {
    document.getElementById('modal-domain').classList.add('hidden');
}

function calcDaysLeft(expiryStr) {
    if(!expiryStr) return null;
    const expDate = new Date(expiryStr);
    const diff = expDate.getTime() - new Date().getTime();
    return Math.ceil(diff / (1000 * 3600 * 24));
}

async function loadDomains() {
    const tbody = document.getElementById('domains-table-body');
    if (!tbody) return;
    
    try {
        const res = await window.apiRequest('/api/domains/list');
        if (res.success) {
            tbody.innerHTML = '';
            
            let total = 0;
            let secured = 0;
            let expiring = 0;

            if (res.domains.length === 0) {
                tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #64748b; padding: 20px; font-size:16px;">لم يتم إضافة أي نطاقات بعد. انقر على "إضافة نطاق جديد" للبدء.</td></tr>';
            } else {
                res.domains.forEach(d => {
                    total++;
                    if(d.ssl) secured++;
                    
                    const rootVal = escapeHtml(d.root || '');
                    const proxyVal = escapeHtml(d.proxy_url || '');
                    
                    let sslHtml = '';
                    if (d.ssl) {
                        const daysLeft = calcDaysLeft(d.ssl_expiry);
                        if(daysLeft !== null && daysLeft < 30) expiring++;
                        
                        const expiryColor = (daysLeft !== null && daysLeft < 15) ? '#ef4444' : (daysLeft !== null && daysLeft < 30) ? '#facc15' : '#4ade80';
                        const expiryText = daysLeft !== null ? (daysLeft < 0 ? 'منتهية' : `باقي ${daysLeft} يوم`) : (d.ssl_expiry || 'مفعل');
                        const issuerText = d.ssl_issuer || 'شهادة صالحة';

                        sslHtml = `
                            <div style="display:flex; flex-direction:column; gap:2px;">
                                <span class="badge" style="background: rgba(34, 197, 94, 0.1); border: 1px solid rgba(34,197,94,0.3); color: #4ade80; align-self: flex-start; padding: 2px 8px;">
                                    <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px; vertical-align:middle;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
                                    محمي (SSL)
                                </span>
                                <span style="font-size: 11px; color: #94a3b8; margin-top:4px;">المصدر: ${escapeHtml(issuerText)}</span>
                                <span style="font-size: 11px; color: ${expiryColor};">تاريخ الانتهاء: ${escapeHtml(d.ssl_expiry || 'غير معروف')} (${expiryText})</span>
                            </div>
                        `;
                    } else {
                        sslHtml = `
                            <span class="badge" style="background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.3); color: #f87171; padding: 2px 8px;">
                                <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px; vertical-align:middle;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 9.9-1"></path></svg> غير محمي
                            </span>
                        `;
                    }
                    
                    let httpsHtml = d.force_https ? '<span style="font-size:10px; padding:2px 6px; background: rgba(56,189,248,0.1); color: #38bdf8; border-radius:4px; margin-right:5px; border:1px solid rgba(56,189,248,0.3);">Force HTTPS</span>' : '';
                    let urlLink = d.force_https || d.ssl ? `https://${d.domain}` : `http://${d.domain}`;

                    const tr = document.createElement('tr');
                    tr.style.transition = 'all 0.2s';
                    tr.onmouseenter = () => tr.style.backgroundColor = 'rgba(255,255,255,0.02)';
                    tr.onmouseleave = () => tr.style.backgroundColor = 'transparent';
                    
                    tr.innerHTML = `
                        <td>
                            <div style="display:flex; flex-direction:column; gap:4px;">
                                <a href="${urlLink}" target="_blank" style="font-weight: bold; color: #60a5fa; text-decoration: none; display: flex; align-items: center; gap: 5px;">
                                    ${escapeHtml(d.domain)}
                                    <svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>
                                </a>
                                <div>${httpsHtml}</div>
                            </div>
                        </td>
                        <td>
                            <span class="badge ${d.type === 'proxy' ? 'badge-warning' : 'badge-primary'}" style="opacity: 0.9;">
                                ${d.type === 'proxy' ? '<svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px;vertical-align:middle;"><polyline points="8 17 12 21 16 17"></polyline><line x1="12" y1="12" x2="12" y2="21"></line><path d="M20.88 18.09A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.29"></path></svg> بروكسي' : '<svg viewBox="0 0 24 24" width="12" height="12" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px;vertical-align:middle;"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"></path><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"></path></svg> ثابت (Static)'}
                            </span>
                        </td>
                        <td style="color: #cbd5e1; font-family: monospace; font-size: 13px; background: rgba(0,0,0,0.15); border-radius: 6px; padding: 6px 10px; max-width: 200px; overflow-x: auto;">
                            ${d.type === 'proxy' ? proxyVal : rootVal}
                        </td>
                        <td>
                            ${sslHtml}
                        </td>
                        <td>
                            <div class="action-btns" style="display: flex; gap: 8px; flex-wrap: wrap;">
                                <button class="btn btn-sm" style="background: rgba(56, 189, 248, 0.1); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.3); padding: 6px 12px;" onclick="showDomainModal(true, '${escapeHtml(d.domain)}', '${d.type}', '${rootVal}', '${proxyVal}', ${d.force_https})"><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px;"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg> الإعدادات</button>
                                ${!d.ssl ? 
                                    `<button class="btn btn-sm" style="background: rgba(74, 222, 128, 0.1); color: #4ade80; border: 1px solid rgba(74, 222, 128, 0.3); padding: 6px 12px;" onclick="installSSL('${escapeHtml(d.domain)}')"><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px;"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg> تفعيل SSL</button>` : 
                                    `<button class="btn btn-sm" style="background: rgba(148, 163, 184, 0.1); color: #94a3b8; border: 1px solid rgba(148, 163, 184, 0.3); padding: 6px 12px;" onclick="installSSL('${escapeHtml(d.domain)}')"><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px;"><path d="M21.5 2v6h-6M2.5 22v-6h6M21.34 15.57a10 10 0 1 1-.57-8.38l5.67-5.67M2.66 8.43a10 10 0 1 1 .57 8.38l-5.67 5.67"></path></svg> تجديد SSL</button>`
                                }
                                <button class="btn btn-sm" style="background: rgba(239, 68, 68, 0.1); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); padding: 6px 12px;" onclick="deleteDomain('${escapeHtml(d.domain)}')"><svg viewBox="0 0 24 24" width="14" height="14" stroke="currentColor" stroke-width="2" fill="none" style="margin-left:4px;"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg> مسح</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            // Update Stats Widgets
            document.getElementById('stat-total-domains').innerText = total;
            document.getElementById('stat-secured-domains').innerText = secured;
            document.getElementById('stat-expiring-domains').innerText = expiring;
            
        } else {
            tbody.innerHTML = `<tr><td colspan="5" style="text-align: center; color: #ef4444; padding: 20px;">خطأ: ${res.error}</td></tr>`;
        }
    } catch (e) {
        console.error(e);
        tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #ef4444; padding: 20px;">خطأ في الاتصال بالسيرفر</td></tr>';
    }
}

async function submitDomain() {
    const domain = document.getElementById('domain-name').value.trim();
    const type = document.getElementById('domain-type').value;
    const root = document.getElementById('domain-root').value.trim();
    const proxy = document.getElementById('domain-proxy').value.trim();
    const forceHttps = document.getElementById('domain-force-https').checked;
    
    const isEdit = document.getElementById('modal-domain').dataset.editMode === 'true';
    const endpoint = isEdit ? '/api/domains/edit' : '/api/domains/create';
    
    if (!domain) {
        showToast('الرجاء إدخال اسم النطاق', 'error');
        return;
    }
    
    const payload = {
        domain: domain,
        type: type,
        force_https: forceHttps
    };
    
    if (type === 'static' && root) payload.document_root = root;
    if (type === 'proxy' && proxy) payload.proxy_url = proxy;
    
    const btn = document.querySelector('#modal-domain .btn-primary');
    const oldText = btn.innerHTML;
    btn.innerHTML = '<span class="loader-spinner" style="width:16px;height:16px;display:inline-block;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 1s linear infinite; vertical-align: middle;"></span> جاري الحفظ...';
    btn.disabled = true;
    
    try {
        const res = await window.apiRequest(endpoint, { method: 'POST', body: JSON.stringify(payload) });
        if (res.success) {
            showToast(res.message, 'success');
            closeDomainModal();
            loadDomains();
        } else {
            showToast(res.error || 'فشل في الحفظ', 'error');
        }
    } catch (e) {
        showToast('حدث خطأ في الاتصال', 'error');
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function deleteDomain(domain) {
    if (!confirm(`تحذير خطير: هل أنت متأكد من حذف النطاق ${domain}؟ سيتم مسح الإعدادات والشهادات المرتبطة به نهائياً.`)) return;
    
    try {
        const res = await window.apiRequest('/api/domains/delete', { method: 'POST', body: JSON.stringify({ domain }) });
        if (res.success) {
            showToast(res.message, 'success');
            loadDomains();
        } else {
            showToast(res.error || 'فشل الحذف', 'error');
        }
    } catch (e) {
        showToast('حدث خطأ', 'error');
    }
}

async function installSSL(domain) {
    if (!confirm(`سيتم الآن طلب وتثبيت / تجديد شهادة SSL للنطاق ${domain}.\n\nالرجاء التأكد أن النطاق (DNS) موجه بالفعل إلى الـ IP الخاص بهذا السيرفر، وإلا ستفشل العملية.\n\nهل تريد الاستمرار؟`)) return;
    
    showToast(`جاري الاتصال بـ Let's Encrypt لاستخراج شهادة النطاق ${domain}... الرجاء الانتظار`, 'info');
    
    try {
        const res = await window.apiRequest('/api/domains/ssl', { method: 'POST', body: JSON.stringify({ domain }) });
        if (res.success) {
            showToast(res.message, 'success');
            loadDomains();
        } else {
            showToast(res.error || 'فشل التثبيت', 'error');
        }
    } catch (e) {
        showToast('حدث خطأ أثناء الاتصال', 'error');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const domainTabBtn = document.querySelector('.nav-tab[data-tab="tab-domains"]');
    if (domainTabBtn) {
        domainTabBtn.addEventListener('click', () => {
            loadDomains();
        });
    }
});
