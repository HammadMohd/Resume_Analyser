const API_BASE = '';

let scoreChart = null;
let isAnalyzing = false;

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('resume-file');
    const analyzeBtn = document.getElementById('analyze-btn');
    const dropZone = document.getElementById('drop-zone');
    const removeFileBtn = document.getElementById('remove-file');

    // File input change
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            showFileSelected(fileInput.files[0].name);
            analyzeBtn.disabled = false;
        }
    });

    // Drag and drop
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });

    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            fileInput.files = files;
            showFileSelected(files[0].name);
            analyzeBtn.disabled = false;
        }
    });

    // Remove file
    removeFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        fileInput.value = '';
        hideFileSelected();
        analyzeBtn.disabled = true;
        hideResults();
    });

    // Analyze
    analyzeBtn.addEventListener('click', analyze);
});

function showFileSelected(name) {
    document.getElementById('drop-zone').style.display = 'none';
    document.getElementById('file-selected').style.display = 'block';
    document.getElementById('file-name').textContent = name;
}

function hideFileSelected() {
    document.getElementById('drop-zone').style.display = '';
    document.getElementById('file-selected').style.display = 'none';
}

async function analyze() {
    if (isAnalyzing) return;

    const fileInput = document.getElementById('resume-file');
    const jdText = document.getElementById('jd-text').value.trim();
    const file = fileInput.files[0];

    if (!file) return;

    isAnalyzing = true;
    showLoading();
    hideResults();

    const loadingStatus = document.getElementById('loading-status');

    try {
        loadingStatus.textContent = 'Extracting content...';
        const extracted = await extractFromResume(file);

        loadingStatus.textContent = 'Validating structure...';
        const validation = await validateFromResume(file);

        let scoring = null;
        if (jdText) {
            loadingStatus.textContent = 'Scoring against job description...';
            scoring = await scoreWithText(file, jdText);
        }

        let bullets = null;
        const skills = extracted.data?.extraction?.skills || [];
        if (skills.length > 0) {
            loadingStatus.textContent = 'Generating suggestions...';
            const bulletTexts = skills.slice(0, 3).map(s => `Experienced in ${s.name}`);
            bullets = await rewriteBullets(bulletTexts);
        }

        showResults(scoring, validation, extracted, bullets, jdText);
    } catch (error) {
        showToast(error.message || 'Analysis failed. Please try again.', 'error');
        console.error(error);
    } finally {
        hideLoading();
        isAnalyzing = false;
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
        throw new Error(error.detail || error.message || 'Extraction failed');
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
        throw new Error(error.detail || error.message || 'Validation failed');
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
        throw new Error(error.detail || error.message || 'Scoring failed');
    }

    return response.json();
}

async function rewriteBullets(bullets) {
    try {
        const response = await fetch(`${API_BASE}/api/v1/rewrite/bullets`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ bullets })
        });

        if (!response.ok) return null;
        return response.json();
    } catch {
        return null;
    }
}

// ===== UI Helpers =====

function showLoading() {
    document.getElementById('loading').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading').style.display = 'none';
}

function hideResults() {
    document.getElementById('results').style.display = 'none';
}

function showToast(message, type = 'error') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(20px)';
        toast.style.transition = '300ms ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ===== Rendering =====

function showResults(scoring, validation, extracted, bullets, jdText) {
    const results = document.getElementById('results');
    results.style.display = 'block';

    const extractionData = extracted?.data?.extraction || {};
    const validationData = validation?.data?.validation || {};
    const consolidatedIssues = validation?.data?.consolidated_issues || [];
    const bulletExamples = validation?.data?.bullet_examples || [];
    const scoringData = scoring?.data || {};

    // When no JD provided, show validation score in the graph so both
    // the chart and Resume Validation section display the same number.
    const graphScore = jdText ? scoringData.overall_score : validationData.overall_score;
    const graphGrade = jdText ? scoringData.overall_grade : validationData.overall_grade;

    renderScoreChart(graphScore, graphGrade);
    renderRecommendations(scoringData.recommendations, scoringData.missing_skills);
    renderBreakdown(scoringData.breakdown, jdText);
    renderExtractedSkills(extractionData, scoringData);
    renderContactInfo(extractionData);
    renderValidation(validationData, consolidatedIssues, bulletExamples);
    renderBullets(bullets);
}

function renderScoreChart(score, grade) {
    const ctx = document.getElementById('score-chart').getContext('2d');
    const valueEl = document.getElementById('score-value');
    const gradeEl = document.getElementById('score-grade');
    const subtitleEl = document.getElementById('score-subtitle');

    const s = score || 0;
    valueEl.textContent = s.toFixed(0) + '%';

    // Grade and color
    let gradeText = grade || '';
    let color = '#94a3b8';
    let label = 'Add a job description for scoring';

    if (s >= 80) {
        color = '#22c55e';
        label = 'Excellent - Your resume is well-optimized';
        if (!gradeText) gradeText = 'A';
    } else if (s >= 60) {
        color = '#6366f1';
        label = 'Good - Minor improvements possible';
        if (!gradeText) gradeText = 'B';
    } else if (s >= 40) {
        color = '#f59e0b';
        label = 'Fair - Several areas need improvement';
        if (!gradeText) gradeText = 'C';
    } else if (s > 0) {
        color = '#ef4444';
        label = 'Needs work - Significant improvements needed';
        if (!gradeText) gradeText = 'D';
    }

    gradeEl.textContent = gradeText ? `Grade ${gradeText}` : '';
    valueEl.style.color = color;
    subtitleEl.textContent = label;

    if (scoreChart) {
        scoreChart.destroy();
    }

    scoreChart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [s || 0.5, 100 - (s || 0.5)],
                backgroundColor: [s > 0 ? color : '#e2e8f0', '#f1f5f9'],
                borderWidth: 0,
                borderRadius: s > 0 ? 6 : 0,
            }]
        },
        options: {
            cutout: '75%',
            responsive: false,
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            },
            animation: {
                animateRotate: true,
                duration: 800,
            }
        }
    });
}

function renderRecommendations(recs, missingSkills) {
    const card = document.getElementById('recs-card');
    const list = document.getElementById('recs-list');

    const allRecs = [...(recs || [])];
    if (missingSkills && missingSkills.length > 0) {
        allRecs.push(`Add these skills from the job description: ${missingSkills.join(', ')}`);
    }

    if (allRecs.length === 0) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    list.innerHTML = '';

    allRecs.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        list.appendChild(li);
    });
}

function renderBreakdown(breakdown, jdText) {
    const card = document.getElementById('breakdown-card');
    const container = document.getElementById('breakdown');

    if (!jdText || !breakdown) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '';

    const categories = {
        skills: 'Skills Match',
        experience: 'Experience',
        projects: 'Projects',
        education: 'Education',
        formatting: 'Formatting',
        structure: 'Structure'
    };

    for (const [key, catLabel] of Object.entries(categories)) {
        if (breakdown[key] !== undefined) {
            const detail = breakdown[key];
            const val = typeof detail === 'object' && detail !== null
                ? (detail.score || 0)
                : (typeof detail === 'number' ? detail : 0);
            const color = val >= 70 ? '#22c55e' : val >= 40 ? '#f59e0b' : '#ef4444';

            const item = document.createElement('div');
            item.className = 'breakdown-item';
            item.innerHTML = `
                <div class="breakdown-header">
                    <span class="breakdown-label">${catLabel}</span>
                    <span class="breakdown-score" style="color:${color}">${val.toFixed(0)}%</span>
                </div>
                <div class="breakdown-bar">
                    <div class="breakdown-bar-fill" style="width:${val}%;background:${color}"></div>
                </div>
            `;
            container.appendChild(item);
        }
    }
}

function renderExtractedSkills(extractionData, scoringData) {
    const card = document.getElementById('skills-card');
    const extractedSection = document.getElementById('extracted-skills-section');
    const matchedSection = document.getElementById('matched-skills-section');
    const missingSection = document.getElementById('missing-skills-section');

    const skills = extractionData.skills || [];
    const missingSkills = scoringData?.missing_skills || [];

    if (skills.length === 0) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';

    // Extracted skills
    extractedSection.innerHTML = '<h4>Extracted Skills</h4><div class="skills-tags"></div>';
    const tagsContainer = extractedSection.querySelector('.skills-tags');
    skills.forEach(skill => {
        const tag = document.createElement('span');
        tag.className = 'skill-tag extracted';
        tag.textContent = skill.name || skill;
        tagsContainer.appendChild(tag);
    });

    // Matched skills (skills in both resume and JD)
    if (scoringData && missingSkills.length >= 0) {
        const resumeSkillNames = skills.map(s => (s.name || s).toLowerCase());
        const allJdSkills = scoringData.breakdown?.skills?.reasoning || [];

        // Find matched: resume skills that appear in JD
        const matched = [];
        const resumeSet = new Set(resumeSkillNames);
        // Use the scoring data to infer matched skills
        // If a skill is not in missing_skills, it's matched
        // But we need the full JD skill list. We can infer from breakdown reasoning.
        // Simpler: just show missing skills from scoring
    }

    // Missing skills (required by JD but not in resume)
    if (missingSkills.length > 0) {
        missingSection.style.display = 'block';
        missingSection.innerHTML = '<h4>Missing Skills (Required by JD)</h4><div class="skills-tags"></div>';
        const missingTags = missingSection.querySelector('.skills-tags');
        missingSkills.forEach(skill => {
            const tag = document.createElement('span');
            tag.className = 'skill-tag missing';
            tag.textContent = skill;
            missingTags.appendChild(tag);
        });
    } else {
        missingSection.style.display = 'none';
    }
}

function renderContactInfo(extractionData) {
    const card = document.getElementById('contact-card');
    const container = document.getElementById('contact-info');

    const emails = extractionData.emails || [];
    const phones = extractionData.phones || [];
    const linkedin = extractionData.linkedin || [];
    const github = extractionData.github || [];
    const urls = extractionData.urls || [];

    const hasAny = emails.length || phones.length || linkedin.length || github.length || urls.length;

    if (!hasAny) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '<div class="contact-grid"></div>';
    const grid = container.querySelector('.contact-grid');

    const addContact = (label, values) => {
        values.forEach(val => {
            const item = document.createElement('div');
            item.className = 'contact-item';
            item.innerHTML = `<span class="contact-label">${label}</span><span>${escapeHtml(val)}</span>`;
            grid.appendChild(item);
        });
    };

    if (emails.length) addContact('Email', emails);
    if (phones.length) addContact('Phone', phones);
    if (linkedin.length) addContact('LinkedIn', linkedin);
    if (github.length) addContact('GitHub', github);
    if (urls.length) addContact('URL', urls);
}

function renderValidation(validationData, consolidatedIssues, bulletExamples) {
    const card = document.getElementById('validation-card');
    const container = document.getElementById('validation');
    const countBadge = document.getElementById('issue-count');

    if (!validationData) {
        card.style.display = 'none';
        return;
    }

    card.style.display = 'block';
    container.innerHTML = '';

    // Score summary
    const scoreDiv = document.createElement('div');
    const score = validationData.overall_score || 0;
    const grade = validationData.overall_grade || 'N/A';
    const scoreColor = score >= 70 ? '#22c55e' : score >= 40 ? '#f59e0b' : '#ef4444';

    scoreDiv.className = 'issue-item pass';
    scoreDiv.innerHTML = `
        <span class="issue-icon" style="background:${scoreColor}">${getGradeIcon(grade)}</span>
        <span class="issue-message"><strong>Score: ${score.toFixed(0)}%</strong> &mdash; Grade ${grade}</span>
    `;
    container.appendChild(scoreDiv);

    // Use consolidated issues if available, fallback to raw issues
    const issues = consolidatedIssues.length > 0
        ? consolidatedIssues
        : (validationData.all_issues || []);

    const errorCount = issues.filter(i => i.severity === 'error').length;
    const warnCount = issues.filter(i => i.severity === 'warning').length;

    if (errorCount || warnCount) {
        countBadge.style.display = 'inline-flex';
        countBadge.textContent = `${errorCount + warnCount} issue${errorCount + warnCount !== 1 ? 's' : ''}`;
    } else {
        countBadge.style.display = 'none';
    }

    issues.forEach(issue => {
        const item = document.createElement('div');
        const sev = issue.severity || 'info';
        item.className = `issue-item ${sev}`;

        const icon = getIssueIcon(sev);
        const section = issue.section ? `<span style="opacity:0.7;font-size:0.75rem;">[${escapeHtml(issue.section)}]</span> ` : '';

        item.innerHTML = `
            <span class="issue-icon">${icon}</span>
            <span class="issue-message">
                ${section}${escapeHtml(issue.message)}
                ${issue.suggestion ? `<span class="issue-suggestion">${escapeHtml(issue.suggestion)}</span>` : ''}
            </span>
        `;
        container.appendChild(item);
    });

    // Show bullet examples if available
    if (bulletExamples && bulletExamples.length > 0) {
        const examplesDiv = document.createElement('div');
        examplesDiv.className = 'bullet-examples';
        examplesDiv.innerHTML = `
            <h4 style="margin:16px 0 8px;color:#6366f1;font-size:0.9rem;">Improved Bullet Examples</h4>
        `;

        bulletExamples.forEach(ex => {
            const exDiv = document.createElement('div');
            exDiv.className = 'example-item';
            exDiv.innerHTML = `
                <div class="example-original"><strong>Before:</strong> ${escapeHtml(ex.original)}</div>
                <div class="example-improved"><strong>After:</strong> ${escapeHtml(ex.improved)}</div>
            `;
            examplesDiv.appendChild(exDiv);
        });

        container.appendChild(examplesDiv);
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
        div.className = 'bullet-item';
        div.innerHTML = `
            <div class="bullet-original">Original: ${escapeHtml(item.original)}</div>
            <div class="bullet-improved">Improved: ${escapeHtml(item.improved)}</div>
            ${item.changes ? `<div class="bullet-changes">${escapeHtml(item.changes)}</div>` : ''}
        `;
        container.appendChild(div);
    });
}

// ===== Helpers =====

function getGradeIcon(grade) {
    const icons = { A: '&#10003;', B: '&#10003;', C: '!', D: '!', F: '&#10007;' };
    return icons[grade] || '?';
}

function getIssueIcon(severity) {
    switch (severity) {
        case 'error': return '&#10007;';
        case 'warning': return '!';
        case 'pass': return '&#10003;';
        default: return 'i';
    }
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
