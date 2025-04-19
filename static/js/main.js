// static/js/main.js
document.addEventListener('DOMContentLoaded', function() {
    const resumeForm = document.getElementById('resume-form');
    const uploadSection = document.getElementById('upload-section');
    const loadingSection = document.getElementById('loading-section');
    const resultsSection = document.getElementById('results-section');
    const backButton = document.getElementById('back-button');
    
    let factorScoresChart = null;

    // Form submission handler
    resumeForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Show loading
        uploadSection.classList.add('d-none');
        loadingSection.classList.remove('d-none');
        
        // Get form data
        const formData = new FormData(resumeForm);
        
        // Send request to backend
        fetch('/analyze', {
            method: 'POST',
            body: formData
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Server responded with an error');
            }
            return response.json();
        })
        .then(data => {
            if (data.error) {
                throw new Error(data.error);
            }
            displayResults(data);
        })
        .catch(error => {
            alert('Error: ' + error.message);
            // Show upload section again
            loadingSection.classList.add('d-none');
            uploadSection.classList.remove('d-none');
        });
    });
    
    // Back button handler
    backButton.addEventListener('click', function() {
        resultsSection.classList.add('d-none');
        uploadSection.classList.remove('d-none');
        resumeForm.reset();
        
        // Destroy chart to prevent memory leaks
        if (factorScoresChart) {
            factorScoresChart.destroy();
            factorScoresChart = null;
        }
    });
    
    // Function to display results
    function displayResults(data) {
        // Hide loading
        loadingSection.classList.add('d-none');
        resultsSection.classList.remove('d-none');
        
        // Update ATS score
        const atsScore = document.getElementById('ats-score');
        atsScore.textContent = data.ats_score + '%';
        
        // Set score circle color based on score
        const scoreCircle = document.querySelector('.score-circle');
        let scoreColor;
        
        if (data.ats_score >= 80) {
            scoreColor = '#28a745'; // Green for high score
        } else if (data.ats_score >= 60) {
            scoreColor = '#ffc107'; // Yellow for medium score
        } else {
            scoreColor = '#dc3545'; // Red for low score
        }
        
        scoreCircle.style.setProperty('--score-color', scoreColor);
        scoreCircle.style.setProperty('--score-percent', data.ats_score + '%');
        
        // Update metrics
        document.getElementById('word-count').textContent = data.metrics.wordCount;
        document.getElementById('action-verb-count').textContent = data.metrics.actionVerbCount;
        document.getElementById('weak-phrase-count').textContent = data.metrics.weakPhraseCount;
        
        // Update sections found
        const sectionsFound = document.getElementById('sections-found');
        sectionsFound.innerHTML = '';
        if (data.metrics.sectionsFound && data.metrics.sectionsFound.length > 0) {
            data.metrics.sectionsFound.forEach(section => {
                const badge = document.createElement('span');
                badge.className = 'section-badge';
                badge.textContent = section.charAt(0).toUpperCase() + section.slice(1);
                sectionsFound.appendChild(badge);
            });
        } else {
            sectionsFound.textContent = 'No standard sections detected';
        }
        
        // Update formatting issues
        const formattingIssues = document.getElementById('formatting-issues');
        formattingIssues.innerHTML = '';
        if (data.metrics.formattingIssues && data.metrics.formattingIssues.length > 0) {
            const issuesList = document.createElement('div');
            issuesList.className = 'text-danger';
            data.metrics.formattingIssues.forEach(issue => {
                const issueItem = document.createElement('div');
                issueItem.innerHTML = `<i class="bi bi-exclamation-triangle-fill"></i> ${issue}`;
                issuesList.appendChild(issueItem);
            });
            formattingIssues.appendChild(issuesList);
        } else {
            formattingIssues.innerHTML = '<span class="text-success">No formatting issues detected</span>';
        }
        
        // Update recommendations
        const recommendationsDiv = document.getElementById('recommendations');
        recommendationsDiv.innerHTML = '';
        
        if (data.recommendations && data.recommendations.length > 0) {
            data.recommendations.forEach(rec => {
                const recItem = document.createElement('div');
                recItem.className = `recommendation-item ${rec.priority}`;
                
                recItem.innerHTML = `
                    <div class="d-flex justify-content-between align-items-center">
                        <strong>${rec.category}</strong>
                        <span class="priority-tag priority-${rec.priority}">${rec.priority}</span>
                    </div>
                    <p class="mb-0 mt-1">${rec.recommendation}</p>
                `;
                
                recommendationsDiv.appendChild(recItem);
            });
        } else {
            recommendationsDiv.textContent = 'No recommendations';
        }
        
        // Update keyword analysis
        const keywordAnalysis = document.getElementById('keyword-analysis');
        keywordAnalysis.innerHTML = '';
        
        if (data.keywordAnalysis && data.keywordAnalysis.industryKeywords) {
            const industriesDiv = document.createElement('div');
            
            Object.entries(data.keywordAnalysis.industryKeywords).forEach(([industry, keywords]) => {
                const industryDiv = document.createElement('div');
                industryDiv.className = 'mb-3';
                
                const industryTitle = document.createElement('h5');
                industryTitle.textContent = industry.replace('_', ' ').charAt(0).toUpperCase() + industry.replace('_', ' ').slice(1);
                industryDiv.appendChild(industryTitle);
                
                const keywordsDiv = document.createElement('div');
                keywordsDiv.className = 'mt-2';
                
                keywords.forEach(keyword => {
                    const keywordPill = document.createElement('span');
                    keywordPill.className = 'keyword-pill';
                    keywordPill.textContent = keyword;
                    keywordsDiv.appendChild(keywordPill);
                });
                
                industryDiv.appendChild(keywordsDiv);
                industriesDiv.appendChild(industryDiv);
            });
            
            keywordAnalysis.appendChild(industriesDiv);
        } else {
            keywordAnalysis.textContent = 'No industry keywords detected';
        }
        
        // Create factor scores chart
        if (data.factorScores) {
            const ctx = document.getElementById('factorScoresChart').getContext('2d');
            
            // Format factor names for display
            const labels = Object.keys(data.factorScores).map(factor => 
                factor.split('_').map(word => word.charAt(0).toUpperCase() + word.slice(1)).join(' ')
            );
            
            // Convert scores to percentages
            const scores = Object.values(data.factorScores).map(score => Math.round(score * 100));
            
            // Destroy existing chart if it exists
            if (factorScoresChart) {
                factorScoresChart.destroy();
            }
            
            // Create new chart
            factorScoresChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Factor Score (%)',
                        data: scores,
                        backgroundColor: [
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                            'rgba(255, 159, 64, 0.7)',
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(199, 199, 199, 0.7)'
                        ],
                        borderColor: [
                            'rgba(54, 162, 235, 1)',
                            'rgba(75, 192, 192, 1)',
                            'rgba(255, 206, 86, 1)',
                            'rgba(153, 102, 255, 1)',
                            'rgba(255, 159, 64, 1)',
                            'rgba(255, 99, 132, 1)',
                            'rgba(199, 199, 199, 1)'
                        ],
                        borderWidth: 1
                    }]
                },
                options: {
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100
                        }
                    },
                    plugins: {
                        legend: {
                            display: false
                        }
                    }
                }
            });
        }
    }
});