const API_BASE = '';

let scoreChart = null;

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('resume-file');
    const analyzeBtn = document.getElementById('analyze-btn');

    fileInput.addEventListener('change', () => {
        analyzeBtn.disabled = !fileInput.files.length;
    });

    analyzeBtn.addEventListener('click', analyze);
});

async function analyze() {
    const fileInput = document.getElementById('resume-file');
    const jdText = document.getElementById('jd-text').value.trim();
    const file = fileInput.files[0];

    if (!file) return;

    showLoading();
    hideResults();

    try {
        const uploadResult = await uploadResume(file);
        const uploadId = uploadResult.upload_id;

        const parsed = await parseResume(uploadId);
        const normalized = await normalizeResume(uploadId);
        const extracted = await extractData(uploadId);

        let jdParsed = null;
        if (jdText) {
            jdParsed = await parseJDText(jdText);
        }

        const scoring = await scoreResume(uploadId, jdParsed);
        const validation = await validateResume(uploadId);

        let bullets = null;
        if (scoring.breakdown) {
            bullets = await rewriteBullets(extracted);
        }

        showResults(scoring, validation, extracted, bullets, jdParsed);
    } catch (error) {
        alert('Error: ' + error.message);
    } finally {
        hideLoading();
    }
}

async function uploadResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/resume/upload`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }

    return response.json();
}

async function parseResume(uploadId) {
    const response = await fetch(`${API_BASE}/api/resume/${uploadId}/parse`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Parse failed');
    return response.json();
}

async function normalizeResume(uploadId) {
    const response = await fetch(`${API_BASE}/api/resume/${uploadId}/normalize`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Normalize failed');
    return response.json();
}

async function extractData(uploadId) {
    const response = await fetch(`${API_BASE}/api/resume/${uploadId}/extract`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Extract failed');
    return response.json();
}

async function parseJDText(text) {
    const response = await fetch(`${API_BASE}/api/jd/parse-text`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text })
    });
    if (!response.ok) throw new Error('JD parse failed');
    return response.json();
}

async function scoreResume(uploadId, jdParsed) {
    const response = await fetch(`${API_BASE}/api/score/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            resume_id: uploadId,
            jd: jdParsed
        })
    });
    if (!response.ok) throw new Error('Scoring failed');
    return response.json();
}

async function validateResume(uploadId) {
    const response = await fetch(`${API_BASE}/api/resume/${uploadId}/validate`, {
        method: 'POST'
    });
    if (!response.ok) throw new Error('Validation failed');
    return response.json();
}

async function rewriteBullets(extracted) {
    const bullets = extracted.bullets || [];
    if (bullets.length === 0) return null;

    const response = await fetch(`${API_BASE}/api/rewrite/bullets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bullets: bullets.slice(0, 5) })
    });
    if (!response.ok) throw new Error('Rewrite failed');
    return response.json();
}

function showLoading() {
    document.getElementById('loading').style.display = 'block';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function hideResults() {
    document.getElementById('results').style.display = 'none';
}

function showResults(scoring, validation, extracted, bullets, jdParsed) {
    const results = document.getElementById('results');
    results.style.display = 'block';

    renderScoreChart(scoring.ats_score || 0);
    renderBreakdown(scoring.breakdown || {});
    renderSkills(extracted, jdParsed);
    renderBullets(bullets);
    renderValidation(validation);
}

function renderScoreChart(score) {
    const ctx = document.getElementById('score-chart').getContext('2d');
    const label = document.getElementById('score-label');
    label.textContent = score.toFixed(0) + '%';

    if (scoreChart) {
        scoreChart.destroy();
    }

    scoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 100 - score],
                backgroundColor: ['#2563eb', '#e5e7eb'],
                borderWidth: 0
            }]
        },
        options: {
            cutout: '70%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

function renderBreakdown(breakdown) {
    const container = document.getElementById('breakdown');
    container.innerHTML = '';

    const categories = {
        skills: 'Skills',
        experience: 'Experience',
        projects: 'Projects',
        education: 'Education',
        formatting: 'Formatting',
        structure: 'Structure'
    };

    for (const [key, label] of Object.entries(categories)) {
        if (breakdown[key] !== undefined) {
            const item = document.createElement('div');
            item.className = 'item';
            item.innerHTML = `
                <span class="label">${label}</span>
                <span class="value">${breakdown[key].toFixed(0)}%</span>
            `;
            container.appendChild(item);
        }
    }
}

function renderSkills(extracted, jdParsed) {
    const skillsCard = document.getElementById('skills-card');
    const matchDiv = document.getElementById('skills-match');
    const missingDiv = document.getElementById('missing-skills');

    if (!jdParsed || !jdParsed.skills || jdParsed.skills.length === 0) {
        skillsCard.style.display = 'none';
        return;
    }

    skillsCard.style.display = 'block';
    matchDiv.innerHTML = '<h4>Matched Skills</h4>';
    missingDiv.innerHTML = '<h4>Missing Skills</h4>';

    const resumeSkills = (extracted.skills || []).map(s =>
        (typeof s === 'string' ? s : s.name || '').toLowerCase()
    );

    const jdSkills = jdParsed.skills || [];

    jdSkills.forEach(skill => {
        const name = skill.name || skill;
        const isMatched = resumeSkills.includes(name.toLowerCase());

        const tag = document.createElement('span');
        tag.className = `tag ${isMatched ? 'matched' : 'missing'}`;
        tag.textContent = name;

        if (isMatched) {
            matchDiv.appendChild(tag);
        } else {
            missingDiv.appendChild(tag);
        }
    });
}

function renderBullets(bullets) {
    const card = document.getElementById('bullets-card');
    const container = document.getElementById('bullets');

    if (!bullets || !bullets.rewrites || bullets.rewrites.length === 0) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '';

    bullets.rewrites.forEach(item => {
        const div = document.createElement('div');
        div.className = 'item';
        div.innerHTML = `
            <div class="original">Original: ${item.original}</div>
            <div class="improved">Improved: ${item.improved}</div>
            <div class="changes">Changes: ${(item.changes_made || []).join(', ')}</div>
        `;
        container.appendChild(div);
    });
}

function renderValidation(validation) {
    const card = document.getElementById('validation-card');
    const container = document.getElementById('validation');

    if (!validation || !validation.results) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '';

    validation.results.forEach(rule => {
        const item = document.createElement('div');
        item.className = 'item';
        const passed = rule.severity !== 'error';
        item.innerHTML = `
            <span class="icon ${passed ? 'pass' : 'fail'}">${passed ? '✓' : '✗'}</span>
            <span>${rule.message}</span>
        `;
        container.appendChild(item);
    });
}
