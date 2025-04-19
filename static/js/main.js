// Constants
const API_URL = 'https://resume-insights.onrender.com';

// DOM Elements
const resumeForm = document.getElementById('resume-form');
const uploadSection = document.getElementById('upload-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const backButton = document.getElementById('back-button');

// Event Listeners
resumeForm.addEventListener('submit', handleFormSubmit);
backButton.addEventListener('submit', resetForm);

// Handle form submission
async function handleFormSubmit(event) {
    event.preventDefault();
    
    // Show loading screen
    uploadSection.classList.add('d-none');
    loadingSection.classList.remove('d-none');
    
    // Get form data
    const formData = new FormData(resumeForm);
    
    try {
        // Send data to API
        const response = await fetch(`${API_URL}/analyze`, {
            method: 'POST',
            body: formData,
        });
        
        if (!response.ok) {
            throw new Error('Failed to analyze resume');
        }
        
        const data = await response.json();
        
        // Display results
        displayResults(data);
        
        // Hide loading, show results
        loadingSection.classList.add('d-none');
        resultsSection.classList.remove('d-none');
        
    } catch (error) {
        console.error('Error:', error);
        alert('There was an error analyzing your resume. Please try again.');
        
        // Return to upload screen
        loadingSection.classList.add('d-none');
        uploadSection.classList.remove('d-none');
    }
}

// Display analysis results
function displayResults(data) {
    // Update ATS score
    document.getElementById('ats-score').textContent = `${data.ats_score}%`;
    
    // Update metrics
    document.getElementById('word-count').textContent = data.word_count;
    document.getElementById('action-verb-count').textContent = data.action_verb_count;
    document.getElementById('weak-phrase-count').textContent = data.weak_phrase_count;
    
    // Update sections found
    const sectionsFoundEl = document.getElementById('sections-found');
    sectionsFoundEl.innerHTML = '';
    
    data.sections_found.forEach(section => {
        const badge = document.createElement('span');
        badge.className = 'badge bg-success me-1 mb-1';
        badge.textContent = section;
        sectionsFoundEl.appendChild(badge);
    });
    
    // Update formatting issues
    const formattingIssuesEl = document.getElementById('formatting-issues');
    formattingIssuesEl.innerHTML = '';
    
    if (data.formatting_issues.length === 0) {
        const noIssues = document.createElement('p');
        noIssues.className = 'text-success mb-0';
        noIssues.textContent = 'No formatting issues detected';
        formattingIssuesEl.appendChild(noIssues);
    } else {
        data.formatting_issues.forEach(issue => {
            const issueItem = document.createElement('div');
            issueItem.className = 'alert alert-warning py-1 px-2 mb-1';
            issueItem.textContent = issue;
            formattingIssuesEl.appendChild(issueItem);
        });
    }
    
    // Update recommendations
    const recommendationsEl = document.getElementById('recommendations');
    recommendationsEl.innerHTML = '';
    
    data.recommendations.forEach(rec => {
        const recItem = document.createElement('div');
        recItem.className = 'alert alert-warning mb-2';
        recItem.textContent = rec;
        recommendationsEl.appendChild(recItem);
    });
    
    // Update keyword analysis
    const keywordAnalysisEl = document.getElementById('keyword-analysis');
    keywordAnalysisEl.innerHTML = '';
    
    if (data.job_description_match) {
        // Create matched keywords section
        const matchedKeywords = document.createElement('div');
        matchedKeywords.className = 'mb-3';
        
        const matchedTitle = document.createElement('h5');
        matchedTitle.textContent = 'Matched Keywords';
        matchedKeywords.appendChild(matchedTitle);
        
        const matchedContainer = document.createElement('div');
        matchedContainer.className = 'd-flex flex-wrap';
        
        data.job_description_match.matched_keywords.forEach(keyword => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-success me-1 mb-1';
            badge.textContent = keyword;
            matchedContainer.appendChild(badge);
        });
        
        matchedKeywords.appendChild(matchedContainer);
        keywordAnalysisEl.appendChild(matchedKeywords);
        
        // Create missing keywords section
        const missingKeywords = document.createElement('div');
        missingKeywords.className = 'mb-3';
        
        const missingTitle = document.createElement('h5');
        missingTitle.textContent = 'Missing Keywords';
        missingKeywords.appendChild(missingTitle);
        
        const missingContainer = document.createElement('div');
        missingContainer.className = 'd-flex flex-wrap';
        
        data.job_description_match.missing_keywords.forEach(keyword => {
            const badge = document.createElement('span');
            badge.className = 'badge bg-danger me-1 mb-1';
            badge.textContent = keyword;
            missingContainer.appendChild(badge);
        });
        
        missingKeywords.appendChild(missingContainer);
        keywordAnalysisEl.appendChild(missingKeywords);
        
        // Add match percentage
        const matchPercentage = document.createElement('p');
        matchPercentage.className = 'mt-2';
        matchPercentage.innerHTML = `<strong>Match Rate:</strong> ${data.job_description_match.match_percentage}%`;
        keywordAnalysisEl.appendChild(matchPercentage);
    } else {
        const noJobDesc = document.createElement('p');
        noJobDesc.textContent = 'No job description provided for keyword matching.';
        keywordAnalysisEl.appendChild(noJobDesc);
    }
    
    // Create factor scores chart
    createFactorScoresChart(data.factor_scores);
}

// Create radar chart for factor scores
function createFactorScoresChart(factorScores) {
    const ctx = document.getElementById('factorScoresChart').getContext('2d');
    
    // Format data for chart
    const labels = Object.keys(factorScores);
    const scores = Object.values(factorScores);
    
    // Destroy existing chart if it exists
    if (window.factorChart) {
        window.factorChart.destroy();
    }
    
    // Create new chart
    window.factorChart = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: labels,
            datasets: [{
                label: 'Factor Scores',
                data: scores,
                fill: true,
                backgroundColor: 'rgba(54, 162, 235, 0.2)',
                borderColor: 'rgb(54, 162, 235)',
                pointBackgroundColor: 'rgb(54, 162, 235)',
                pointBorderColor: '#fff',
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: 'rgb(54, 162, 235)'
            }]
        },
        options: {
            elements: {
                line: {
                    borderWidth: 3
                }
            },
            scales: {
                r: {
                    angleLines: {
                        display: true
                    },
                    suggestedMin: 0,
                    suggestedMax: 100
                }
            }
        }
    });
}

// Reset the form to analyze another resume
function resetForm() {
    // Hide results, show upload form
    resultsSection.classList.add('d-none');
    uploadSection.classList.remove('d-none');
    
    // Reset form fields
    resumeForm.reset();
}