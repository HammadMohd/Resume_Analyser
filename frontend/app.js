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
        // Get extraction data
        const extracted = await extractFromResume(file);

        // Get validation data
        const validation = await validateFromResume(file);

        // Get scoring if JD provided
        let scoring = null;
        if (jdText) {
            scoring = await scoreWithText(file, jdText);
        }

        // Get bullet suggestions from first 5 skills
        let bullets = null;
        const skills = extracted.data?.extraction?.skills || [];
        if (skills.length > 0) {
            const bulletTexts = skills.slice(0, 5).map(s => `Experienced in ${s.name}`);
            bullets = await rewriteBullets(bulletTexts);
        }

        showResults(scoring, validation, extracted, bullets, jdText ? { text: jdText } : null);
    } catch (error) {
        alert('Error: ' + error.message);
        console.error(error);
    } finally {
        hideLoading();
    }
}

async function extractFromResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/v1/resumes/extract`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Extraction failed');
    }

    return response.json();
}

async function validateFromResume(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/api/v1/resumes/validate`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Validation failed');
    }

    return response.json();
}

async function scoreWithText(file, jdText) {
    const formData = new FormData();
    formData.append('resume', file);

    // Create a Blob for the JD text
    const jdBlob = new Blob([jdText], { type: 'text/plain' });
    formData.append('jd', jdBlob, 'job_description.txt');

    const response = await fetch(`${API_BASE}/api/v1/score/analyze`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.message || 'Scoring failed');
    }

    return response.json();
}

async function rewriteBullets(bullets) {
    const response = await fetch(`${API_BASE}/api/v1/rewrite/bullets`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ bullets })
    });

    if (!response.ok) {
        console.warn('Bullet rewriting not available');
        return null;
    }

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

    const extractionData = extracted?.data?.extraction || {};
    const validationData = validation?.data?.validation || {};
    const scoringData = scoring?.data || {};

    renderScoreChart(scoringData.ats_score || 0);
    renderBreakdown(scoringData.breakdown || {});
    renderSkills(extractionData, jdParsed);
    renderBullets(bullets);
    renderValidation(validationData);
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

    for (const [key, catLabel] of Object.entries(categories)) {
        if (breakdown[key] !== undefined) {
            const item = document.createElement('div');
            item.className = 'item';
            item.innerHTML = `
                <span class="label">${catLabel}</span>
                <span class="value">${breakdown[key].toFixed(0)}%</span>
            `;
            container.appendChild(item);
        }
    }
}

function renderSkills(extractionData, jdParsed) {
    const skillsCard = document.getElementById('skills-card');
    const matchDiv = document.getElementById('skills-match');
    const missingDiv = document.getElementById('missing-skills');

    if (!jdParsed || !jdParsed.text) {
        skillsCard.style.display = 'none';
        return;
    }

    const resumeSkills = (extractionData.skills || []).map(s =>
        (typeof s === 'string' ? s : s.name || '').toLowerCase()
    );

    // Simple keyword extraction from JD text
    const jdText = jdParsed.text.toLowerCase();
    const commonSkills = [
        'python', 'javascript', 'typescript', 'java', 'c++', 'sql', 'aws', 'docker',
        'kubernetes', 'react', 'node', 'api', 'rest', 'graphql', 'git', 'linux',
        'machine learning', 'data', 'analytics', 'agile', 'scrum'
    ];

    const jdSkills = commonSkills.filter(skill => jdText.includes(skill));

    if (jdSkills.length === 0) {
        skillsCard.style.display = 'none';
        return;
    }

    skillsCard.style.display = 'block';
    matchDiv.innerHTML = '<h4>Matched Skills</h4>';
    missingDiv.innerHTML = '<h4>Missing Skills</h4>';

    jdSkills.forEach(skill => {
        const isMatched = resumeSkills.some(rs => rs.includes(skill));

        const tag = document.createElement('span');
        tag.className = `tag ${isMatched ? 'matched' : 'missing'}`;
        tag.textContent = skill;

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

    if (!bullets || !bullets.data || !bullets.data.rewrites || bullets.data.rewrites.length === 0) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '';

    bullets.data.rewrites.forEach(item => {
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

function renderValidation(validationData) {
    const card = document.getElementById('validation-card');
    const container = document.getElementById('validation');

    if (!validationData) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '';

    // Show overall score
    const scoreDiv = document.createElement('div');
    scoreDiv.className = 'item';
    scoreDiv.innerHTML = `
        <span class="label">Overall Score</span>
        <span class="value">${validationData.overall_score || 0}% (${validationData.overall_grade || 'N/A'})</span>
    `;
    container.appendChild(scoreDiv);

    // Show issues
    const issues = validationData.all_issues || [];
    issues.slice(0, 10).forEach(issue => {
        const item = document.createElement('div');
        item.className = 'item';
        const passed = issue.severity !== 'error';
        item.innerHTML = `
            <span class="icon ${passed ? 'pass' : 'fail'}">${passed ? '✓' : '✗'}</span>
            <span>${issue.message}</span>
        `;
        container.appendChild(item);
    });
}
