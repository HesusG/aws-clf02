/**
 * Sistema de Revisión y Resultados AWS CLF-C02
 * Muestra resultados del examen, desglose por dominio y revisión detallada
 */

let examResults = null;

// Inicializar página de resultados
function initResults() {
    // Cargar resultados del localStorage
    const resultsStr = localStorage.getItem('examResults');

    if (!resultsStr) {
        alert('No hay resultados disponibles. Redirigiendo al inicio...');
        window.location.href = 'index.html';
        return;
    }

    examResults = JSON.parse(resultsStr);

    // Mostrar resultados
    displayResults();
}

// Mostrar resultados
function displayResults() {
    // Header con puntaje
    const header = document.getElementById('resultsHeader');
    const passStatus = document.getElementById('passStatus');
    const scoreDisplay = document.getElementById('scoreDisplay');

    scoreDisplay.textContent = examResults.scaledScore;

    if (examResults.passed) {
        header.classList.add('passed');
        passStatus.innerHTML = '🎉 ¡APROBADO!';
    } else {
        header.classList.add('failed');
        passStatus.innerHTML = '❌ No Aprobado';
    }

    // Summary cards
    displaySummary();

    // Domain breakdown
    displayDomainBreakdown();

    // Detailed review
    displayDetailedReview();
}

// Mostrar resumen
function displaySummary() {
    const summaryGrid = document.getElementById('summaryGrid');

    summaryGrid.innerHTML = `
        <div class="summary-card">
            <div class="summary-number correct">${examResults.correctCount}</div>
            <div class="summary-label">Correctas</div>
        </div>
        <div class="summary-card">
            <div class="summary-number incorrect">${examResults.incorrectCount}</div>
            <div class="summary-label">Incorrectas</div>
        </div>
        <div class="summary-card">
            <div class="summary-number unanswered">${examResults.unansweredCount}</div>
            <div class="summary-label">Sin Responder</div>
        </div>
        <div class="summary-card">
            <div class="summary-number" style="color: var(--aws-orange);">${examResults.percentageCorrect}%</div>
            <div class="summary-label">Porcentaje</div>
        </div>
    `;

    // Agregar tiempo si estaba configurado
    if (examResults.timeUsed !== null) {
        const minutes = Math.floor(examResults.timeUsed / 60);
        const seconds = examResults.timeUsed % 60;

        summaryGrid.innerHTML += `
            <div class="summary-card">
                <div class="summary-number" style="color: var(--aws-dark);">${minutes}:${seconds.toString().padStart(2, '0')}</div>
                <div class="summary-label">Tiempo Usado</div>
            </div>
        `;
    }
}

// Mostrar desglose por dominio
function displayDomainBreakdown() {
    const domainBreakdown = document.getElementById('domainBreakdown');

    const domainsHTML = Object.entries(examResults.domainScores).map(([domain, scores]) => {
        const percentage = Math.round((scores.correct / scores.total) * 100);

        return `
            <div class="domain-item">
                <div class="domain-name">
                    <span>${domain.split(': ')[1]}</span>
                    <span>${scores.correct}/${scores.total} (${percentage}%)</span>
                </div>
                <div class="domain-bar">
                    <div class="domain-fill" style="width: ${percentage}%">
                        ${percentage}%
                    </div>
                </div>
            </div>
        `;
    }).join('');

    domainBreakdown.innerHTML = domainsHTML;
}

// Mostrar revisión detallada
function displayDetailedReview() {
    const detailedReview = document.getElementById('detailedReview');

    const reviewHTML = examResults.detailedAnswers.map((answer, index) => {
        let statusClass = 'unanswered';
        let statusText = 'Sin Responder';
        let statusIcon = '⊘';

        if (answer.userAnswer !== 'Sin responder') {
            if (answer.isCorrect) {
                statusClass = 'correct';
                statusText = 'Correcta';
                statusIcon = '✓';
            } else {
                statusClass = 'incorrect';
                statusText = 'Incorrecta';
                statusIcon = '✗';
            }
        }

        const markedBadge = answer.wasMarked ? '<span style="color: var(--aws-orange);">🔖 Marcada</span>' : '';

        return `
            <div class="review-question">
                <div class="review-question-header">
                    <span style="font-weight: 700; color: var(--aws-gray);">Pregunta ${index + 1}</span>
                    <span class="review-status ${statusClass}">${statusIcon} ${statusText}</span>
                    ${markedBadge}
                    <span style="margin-left: auto; color: var(--aws-gray); font-size: 0.9rem;">${answer.domain.split(': ')[1]}</span>
                </div>

                <div class="review-question-text">${answer.question}</div>

                ${answer.userAnswer !== 'Sin responder' ? `
                    <div class="review-answer user">
                        <strong>Tu respuesta:</strong> ${answer.userAnswer}) ${answer.options[answer.userAnswer]}
                    </div>
                ` : '<div class="review-answer unanswered"><strong>No respondiste esta pregunta</strong></div>'}

                ${!answer.isCorrect ? `
                    <div class="review-answer correct-answer">
                        <strong>✓ Respuesta correcta:</strong> ${answer.correctAnswer}) ${answer.options[answer.correctAnswer]}
                    </div>
                ` : ''}

                ${answer.explanation ? `
                    <div class="explanation-box" style="margin-top: 1rem;">
                        <div class="explanation-title">Explicación</div>
                        <div class="explanation-text">${answer.explanation}</div>
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');

    detailedReview.innerHTML = reviewHTML;
}

// Exportar resultados
function exportResults() {
    const exportData = {
        date: new Date().toISOString(),
        exam: 'AWS Certified Cloud Practitioner CLF-C02',
        results: examResults
    };

    const dataStr = JSON.stringify(exportData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `aws-clf-c02-results-${new Date().toISOString().split('T')[0]}.json`;
    link.click();

    URL.revokeObjectURL(url);
}

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', initResults);
