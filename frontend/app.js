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
        // Get extraction data (works without JD)
        const extracted = await extractFromResume(file);

        // Get validation data (works without JD)
        const validation = await validateFromResume(file);

        // Get scoring only if JD provided
        let scoring = null;
        if (jdText) {
            scoring = await scoreWithText(file, jdText);
        }

        // Get bullet suggestions from skills
        let bullets = null;
        const skills = extracted.data?.extraction?.skills || [];
        if (skills.length > 0) {
            const bulletTexts = skills.slice(0, 3).map(s => `Experienced in ${s.name}`);
            bullets = await rewriteBullets(bulletTexts);
        }

        showResults(scoring, validation, extracted, bullets, jdText);
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

function showResults(scoring, validation, extracted, bullets, jdText) {
    const results = document.getElementById('results');
    results.style.display = 'block';

    const extractionData = extracted?.data?.extraction || {};
    const validationData = validation?.data?.validation || {};
    const scoringData = scoring?.data || {};

    // Show score (0 if no JD)
    renderScoreChart(scoringData.ats_score || 0);

    // Show breakdown (empty if no JD)
    renderBreakdown(scoringData.breakdown || {}, jdText);

    // Show extracted skills
    renderExtractedSkills(extractionData);

    // Show validation results
    renderValidation(validationData);

    // Show bullet suggestions
    renderBullets(bullets);
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
                data: [score || 1, 100 - (score || 1)],
                backgroundColor: [score > 0 ? '#2563eb' : '#9ca3af', '#e5e7eb'],
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

function renderBreakdown(breakdown, jdText) {
    const container = document.getElementById('breakdown');
    container.innerHTML = '';

    if (!jdText) {
        container.innerHTML = '<p style="color: #6b7280; font-style: italic;">Add a job description to see ATS scoring</p>';
        return;
    }

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

function renderExtractedSkills(extractionData) {
    const container = document.getElementById('skills-match');
    const missingContainer = document.getElementById('missing-skills');
    const skillsCard = document.getElementById('skills-card');

    const skills = extractionData.skills || [];
    const emails = extractionData.emails || [];
    const phones = extractionData.phones || [];
    const linkedin = extractionData.linkedin || [];
    const github = extractionData.github || [];

    if (skills.length === 0 && emails.length === 0) {
        skillsCard.style.display = 'none';
        return;
    }

    skillsCard.style.display = 'block';
    container.innerHTML = '<h4>Extracted Skills</h4>';
    missingContainer.innerHTML = '<h4>Contact Info</h4>';

    // Show skills
    skills.forEach(skill => {
        const tag = document.createElement('span');
        tag.className = 'tag matched';
        tag.textContent = skill.name || skill;
        container.appendChild(tag);
    });

    // Show contact info
    if (emails.length > 0) {
        const p = document.createElement('p');
        p.textContent = 'Email: ' + emails.join(', ');
        missingContainer.appendChild(p);
    }
    if (phones.length > 0) {
        const p = document.createElement('p');
        p.textContent = 'Phone: ' + phones.join(', ');
        missingContainer.appendChild(p);
    }
    if (linkedin.length > 0) {
        const p = document.createElement('p');
        p.textContent = 'LinkedIn: ' + linkedin.join(', ');
        missingContainer.appendChild(p);
    }
    if (github.length > 0) {
        const p = document.createElement('p');
        p.textContent = 'GitHub: ' + github.join(', ');
        missingContainer.appendChild(p);
    }
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
        <span class="label">Resume Score</span>
        <span class="value">${validationData.overall_score || 0}% (${validationData.overall_grade || 'N/A'})</span>
    `;
    container.appendChild(scoreDiv);

    // Show issues
    const issues = validationData.all_issues || [];
    if (issues.length > 0) {
        const header = document.createElement('h4');
        header.textContent = 'Issues Found';
        header.style.marginTop = '1rem';
        container.appendChild(header);
    }

    issues.slice(0, 10).forEach(issue => {
        const item = document.createElement('div');
        item.className = 'item';
        const isError = issue.severity === 'error';
        item.innerHTML = `
            <span class="icon ${isError ? 'fail' : 'pass'}">${isError ? '✗' : '✓'}</span>
            <span>${issue.message}</span>
        `;
        container.appendChild(item);
    });
}
