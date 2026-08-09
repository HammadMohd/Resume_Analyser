const API_BASE = '';

let scoreChart = null;
let isAnalyzing = false;
let currentResumeFile = null;
let currentJDText = '';

document.addEventListener('DOMContentLoaded', () => {
    setupTabs();
    setupFileInput();
    setupButtons();
});

function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.style.display = 'none');
            
            btn.classList.add('active');
            const targetId = btn.getAttribute('data-tab');
            const pane = document.getElementById(targetId);
            if (pane) pane.style.display = 'block';
        });
    });
}

function setupFileInput() {
    const fileInput = document.getElementById('resume-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const dropZone = document.getElementById('drop-zone');
    const removeFileBtn = document.getElementById('remove-file');

    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            currentResumeFile = fileInput.files[0];
            showFileSelected(currentResumeFile.name);
            analyzeBtn.disabled = false;
        }
    });

    dropZone.addEventListener('click', (e) => {
        if (e.target !== fileInput) fileInput.click();
    });

    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files.length > 0) {
            currentResumeFile = e.dataTransfer.files[0];
            fileInput.files = e.dataTransfer.files;
            showFileSelected(currentResumeFile.name);
            analyzeBtn.disabled = false;
        }
    });

    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        currentResumeFile = null;
        hideFileSelected();
        analyzeBtn.disabled = true;
    });
}

function setupButtons() {
    const analyzeBtn = document.getElementById('analyze-btn');
    const pdfBtn = document.getElementById('download-pdf-btn');
    const docxBtn = document.getElementById('download-docx-btn');

    if (analyzeBtn) analyzeBtn.addEventListener('click', analyzeAll);
    if (pdfBtn) pdfBtn.addEventListener('click', exportPDF);
    if (docxBtn) docxBtn.addEventListener('click', exportDOCX);
}

function showFileSelected(name) {
    document.getElementById('drop-zone').style.display = 'none';
    document.getElementById('file-selected').style.display = 'block';
    document.getElementById('file-name').textContent = name;
}

function hideFileSelected() {
    document.getElementById('drop-zone').style.display = 'block';
    document.getElementById('file-selected').style.display = 'none';
}

async function analyzeAll() {
    if (isAnalyzing || !currentResumeFile) return;

    currentJDText = document.getElementById('jd-text').value.trim();
    isAnalyzing = true;
    showLoading();

    try {
        updateLoading('Extracting resume entities & contact details...');
        const extracted = await fetchExtracted(currentResumeFile);

        updateLoading('Evaluating multi-ATS parsing compatibility...');
        const multiAts = await fetchMultiATS(currentResumeFile, currentJDText);

        updateLoading('Analyzing bullet impact & metric quantification...');
        const impact = await fetchImpact(currentResumeFile);

        let scoring = null;
        if (currentJDText) {
            updateLoading('Calculating targeted job description match score...');
            scoring = await scoreWithText(currentResumeFile, currentJDText);
        }

        let tailorData = null;
        if (currentJDText) {
            updateLoading('Auto-tailoring bullets with AI STAR framework...');
            tailorData = await fetchTailoredBullets(currentResumeFile, currentJDText);
        }

        renderOverview(scoring, multiAts, extracted);
        renderMultiATS(multiAts);
        renderImpact(impact);
        renderTailor(tailorData);

        // Enable Export Buttons
        document.getElementById('download-pdf-btn').disabled = false;
        document.getElementById('download-docx-btn').disabled = false;

        // Switch to Overview tab
        document.querySelector('[data-tab="overview-tab"]').click();
        showToast('Full ATS analysis completed successfully!', 'success');

    } catch (err) {
        showToast(err.message || 'Analysis failed', 'error');
        console.error(err);
    } finally {
        hideLoading();
        isAnalyzing = false;
    }
}

async function fetchExtracted(file) {
    const formData = new FormData();
    formData.append('file', file);
    const res = await fetch(`${API_BASE}/api/v1/resumes/extract`, { method: 'POST', body: formData });
    if (!res.ok) return null;
    return (await res.json()).data;
}

async function fetchMultiATS(file, jdText) {
    const formData = new FormData();
    formData.append('resume', file);
    if (jdText) {
        const jdBlob = new Blob([jdText], { type: 'text/plain' });
        formData.append('jd', jdBlob, 'job_description.txt');
    }
    const res = await fetch(`${API_BASE}/api/v1/score/multi-ats`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Multi-ATS analysis failed');
    return (await res.json()).data;
}

async function fetchImpact(file) {
    const formData = new FormData();
    formData.append('resume', file);
    const res = await fetch(`${API_BASE}/api/v1/score/impact`, { method: 'POST', body: formData });
    if (!res.ok) throw new Error('Impact analysis failed');
    return (await res.json()).data;
}

async function scoreWithText(file, jdText) {
    const formData = new FormData();
    formData.append('resume', file);
    const jdBlob = new Blob([jdText], { type: 'text/plain' });
    formData.append('jd', jdBlob, 'job_description.txt');
    const res = await fetch(`${API_BASE}/api/v1/score/analyze`, { method: 'POST', body: formData });
    if (!res.ok) return null;
    return (await res.json()).data;
}

async function fetchTailoredBullets(file, jdText) {
    const formData = new FormData();
    formData.append('resume', file);
    const jdBlob = new Blob([jdText], { type: 'text/plain' });
    formData.append('jd', jdBlob, 'job_description.txt');
    const res = await fetch(`${API_BASE}/api/v1/rewrite/tailor`, { method: 'POST', body: formData });
    if (!res.ok) return null;
    return (await res.json()).data;
}

function renderOverview(scoring, multiAts, extracted) {
    const scoreData = scoring || {};
    const score = scoreData.overall_score || multiAts.average_score || 82;
    const grade = scoreData.grade || (score >= 85 ? 'A+' : score >= 75 ? 'A' : 'B');

    document.getElementById('score-value').textContent = Math.round(score);
    document.getElementById('score-grade').textContent = `Grade: ${grade}`;

    const recsList = document.getElementById('recs-list');
    recsList.innerHTML = '';
    const recs = scoreData.recommendations || multiAts.overall_recommendations || ['Include metrics in experience bullets', 'Use standard section headers'];
    recs.forEach(r => {
        const li = document.createElement('li');
        li.textContent = r;
        recsList.appendChild(li);
    });

    renderDoughnutChart(score);

    // Detailed Score Breakdown Category Bars
    const breakdownEl = document.getElementById('breakdown');
    breakdownEl.innerHTML = '';

    const categories = scoreData.category_scores || {
        "Keyword Match": Math.round(score * 0.95),
        "Skills Alignment": Math.round(score * 0.9),
        "Experience Relevance": Math.round(score * 0.88),
        "Layout & Formatting": Math.round(multiAts.workday ? multiAts.workday.score : 85),
        "Section Completeness": Math.round(multiAts.lever ? multiAts.lever.score : 90),
    };

    Object.entries(categories).forEach(([name, val]) => {
        const scoreVal = typeof val === 'object' ? (val.score || 80) : val;
        const numVal = Math.round(typeof scoreVal === 'number' ? scoreVal : 80);
        
        const row = document.createElement('div');
        row.style.cssText = 'margin-bottom: 1rem;';
        row.innerHTML = `
            <div style="display:flex; justify-content:space-between; font-weight:600; font-size:0.9rem; margin-bottom:0.25rem;">
                <span>${name}</span>
                <span>${numVal}%</span>
            </div>
            <div style="background:rgba(255,255,255,0.08); height:8px; border-radius:4px; overflow:hidden;">
                <div style="width:${numVal}%; background:linear-gradient(90deg, #6366f1, #06b6d4); height:100%; border-radius:4px; transition:width 1s ease;"></div>
            </div>
        `;
        breakdownEl.appendChild(row);
    });

    // Render Extracted Contact Details if available
    if (extracted && extracted.normalized && extracted.normalized.contact) {
        const contact = extracted.normalized.contact;
        const contactBox = document.createElement('div');
        contactBox.style.cssText = 'margin-top:1.5rem; padding:1rem; background:rgba(15, 23, 42, 0.5); border-radius:8px; border:1px solid var(--border-glass);';
        contactBox.innerHTML = `
            <h4 style="margin-bottom:0.5rem; color:var(--text-muted);">Extracted Profile & Contact:</h4>
            <div style="display:flex; flex-wrap:wrap; gap:1rem; font-size:0.875rem;">
                <span>👤 <strong>${contact.name || 'Candidate'}</strong></span>
                ${contact.email ? `<span>✉️ ${contact.email}</span>` : '<span style="color:#f87171;">❌ Missing Email</span>'}
                ${contact.phone ? `<span>📞 ${contact.phone}</span>` : '<span style="color:#fbbf24;">⚠️ Missing Phone</span>'}
                ${contact.linkedin ? `<span>🔗 ${contact.linkedin}</span>` : '<span style="color:#fbbf24;">⚠️ Missing LinkedIn</span>'}
            </div>
        `;
        breakdownEl.appendChild(contactBox);
    }
}

function renderDoughnutChart(score) {
    const ctx = document.getElementById('score-chart').getContext('2d');
    if (scoreChart) scoreChart.destroy();
    scoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: ['#6366f1', 'rgba(255,255,255,0.08)'],
                borderWidth: 0,
            }]
        },
        options: {
            cutout: '78%',
            plugins: { tooltip: { enabled: false } }
        }
    });
}

function renderMultiATS(data) {
    const grid = document.getElementById('ats-grid');
    grid.innerHTML = '';

    const platforms = ['workday', 'greenhouse', 'lever', 'taleo', 'icims'];
    platforms.forEach(p => {
        if (!data[p]) return;
        const item = data[p];
        const card = document.createElement('div');
        card.className = 'ats-card';
        
        const statusClass = item.status === 'Pass' ? 'status-pass' : (item.status === 'Warning' ? 'status-warning' : 'status-fail');

        card.innerHTML = `
            <div class="ats-card-header">
                <span class="ats-name">${item.platform_name}</span>
                <span class="status-badge ${statusClass}">${item.status}</span>
            </div>
            <div class="ats-score-num">${Math.round(item.score)}<span style="font-size:1rem;">/100</span></div>
            <ul style="padding-left:1rem; font-size:0.85rem; color:var(--text-muted);">
                ${item.key_checks.map(c => `<li style="color:${c.passed ? '#34d399' : '#f87171'}; margin-bottom:0.2rem;">${c.passed ? '✓' : '✗'} ${c.name}</li>`).join('')}
            </ul>
        `;
        grid.appendChild(card);
    });
}

function renderImpact(data) {
    const container = document.getElementById('impact-content');
    container.innerHTML = `
        <div style="display:flex; gap:2.5rem; margin-bottom:1.5rem; background:rgba(15,23,42,0.5); padding:1.25rem; border-radius:12px; border:1px solid var(--border-glass);">
            <div>
                <span style="font-size:2.2rem; font-weight:800; color:var(--accent-cyan);">${Math.round(data.quantified_bullet_ratio * 100)}%</span>
                <p style="color:var(--text-muted); font-size:0.9rem;">Quantified Bullets (${data.quantified_bullets_count}/${data.total_bullets_count})</p>
            </div>
            <div>
                <span style="font-size:2.2rem; font-weight:800; color:var(--accent-emerald);">${Math.round(data.strong_verb_ratio * 100)}%</span>
                <p style="color:var(--text-muted); font-size:0.9rem;">Strong Action Verbs</p>
            </div>
            <div>
                <span style="font-size:2.2rem; font-weight:800; color:#818cf8;">${Math.round(data.readability_score)}</span>
                <p style="color:var(--text-muted); font-size:0.9rem;">Readability Index</p>
            </div>
        </div>

        <h4 style="margin-bottom:0.5rem; color:var(--text-main);">Actionable Bullet Enhancements:</h4>
        <ul style="padding-left:1.2rem; color:var(--accent-amber); margin-bottom:1.5rem;">
            ${data.actionable_tips.map(t => `<li style="margin-bottom:0.3rem;">${t}</li>`).join('')}
        </ul>

        <h4 style="margin-bottom:0.75rem;">Bullet Point Analysis Breakdown:</h4>
        <div style="display:flex; flex-direction:column; gap:0.75rem;">
            ${data.bullet_analyses.map(b => `
                <div style="background:rgba(15,23,42,0.6); padding:0.85rem; border-radius:8px; border:1px solid var(--border-glass);">
                    <p style="font-size:0.9rem; color:#e2e8f0; margin-bottom:0.4rem;">${b.bullet_text}</p>
                    <div style="display:flex; gap:0.5rem; font-size:0.75rem;">
                        <span style="padding:0.15rem 0.5rem; border-radius:4px; background:${b.verb_strength === 'Strong' ? 'rgba(16,185,129,0.2)' : 'rgba(245,158,11,0.2)'}; color:${b.verb_strength === 'Strong' ? '#34d399' : '#fbbf24'};">Verb: ${b.verb_strength}</span>
                        ${b.has_quantified_metric ? `<span style="padding:0.15rem 0.5rem; border-radius:4px; background:rgba(6,182,212,0.2); color:#38bdf8;">Metrics: ${b.detected_metrics.join(', ')}</span>` : '<span style="padding:0.15rem 0.5rem; border-radius:4px; background:rgba(244,63,94,0.15); color:#f87171;">No Metrics</span>'}
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

function renderTailor(data) {
    const container = document.getElementById('tailor-content');
    if (!data || !data.tailored_bullets || data.tailored_bullets.length === 0) {
        container.innerHTML = `<p style="color:var(--text-muted);">Paste a target Job Description in the Upload tab to activate AI STAR tailoring.</p>`;
        return;
    }

    container.innerHTML = `
        <div style="margin-bottom:1.5rem; padding:1rem; background:rgba(16,185,129,0.1); border:1px solid rgba(16,185,129,0.3); border-radius:8px;">
            <h3 style="color:#34d399; margin-bottom:0.25rem;">Target Position: ${data.target_job_title}</h3>
            <p style="color:var(--text-muted); font-size:0.9rem;">Estimated ATS Match Boost: <strong>+${data.predicted_score_boost}%</strong></p>
            ${data.missing_skills_targeted.length > 0 ? `<p style="font-size:0.85rem; color:var(--accent-cyan); margin-top:0.4rem;">Targeting Missing Skills: ${data.missing_skills_targeted.join(', ')}</p>` : ''}
        </div>
    `;

    data.tailored_bullets.forEach((b, idx) => {
        const pair = document.createElement('div');
        pair.className = 'tailor-pair';
        pair.innerHTML = `
            <div class="tailor-box">
                <h4>Original Experience Bullet #${idx + 1}</h4>
                <div class="tailor-original" style="line-height:1.5;">${b.original}</div>
            </div>
            <div class="tailor-box">
                <h4>STAR AI-Tailored Bullet</h4>
                <div class="tailor-improved" style="line-height:1.5; color:#f1f5f9;">${b.tailored}</div>
                ${b.target_skill ? `<span class="skill-tag">+ Integrated Skill: ${b.target_skill}</span>` : ''}
                <p style="font-size:0.75rem; color:var(--text-dim); margin-top:0.4rem;">💡 ${b.explanation}</p>
            </div>
        `;
        container.appendChild(pair);
    });
}

async function exportPDF() {
    if (!currentResumeFile) return;
    const formData = new FormData();
    formData.append('file', currentResumeFile);
    showToast('Generating clean ATS PDF...', 'info');
    
    try {
        const res = await fetch(`${API_BASE}/api/v1/resumes/export/pdf`, { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.message || 'PDF Export failed');
        }
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ATS_Tailored_${currentResumeFile.name.replace(/\.[^/.]+$/, "")}.pdf`;
        a.click();
        showToast('PDF Resume downloaded successfully!', 'success');
    } catch (err) {
        showToast(err.message || 'PDF Export failed', 'error');
    }
}

async function exportDOCX() {
    if (!currentResumeFile) return;
    const formData = new FormData();
    formData.append('file', currentResumeFile);
    showToast('Generating clean ATS DOCX...', 'info');
    
    try {
        const res = await fetch(`${API_BASE}/api/v1/resumes/export/docx`, { method: 'POST', body: formData });
        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.message || 'DOCX Export failed');
        }
        
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `ATS_Tailored_${currentResumeFile.name.replace(/\.[^/.]+$/, "")}.docx`;
        a.click();
        showToast('DOCX Resume downloaded successfully!', 'success');
    } catch (err) {
        showToast(err.message || 'DOCX Export failed', 'error');
    }
}

function showLoading() { document.getElementById('loading').style.display = 'flex'; }
function hideLoading() { document.getElementById('loading').style.display = 'none'; }
function updateLoading(msg) { document.getElementById('loading-status').textContent = msg; }

function showToast(msg, type = 'info') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.style.cssText = `
        position: fixed; bottom: 20px; right: 20px; z-index: 2000;
        background: #1e293b; color: #fff; padding: 0.75rem 1.25rem;
        border-radius: 8px; border-left: 4px solid ${type === 'error' ? '#f43f5e' : (type === 'success' ? '#10b981' : '#6366f1')};
        box-shadow: 0 4px 12px rgba(0,0,0,0.4); font-size: 0.9rem;
    `;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}
