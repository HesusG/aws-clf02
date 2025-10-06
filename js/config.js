/**
 * Configuración del Examen AWS CLF-C02
 * Maneja la página de inicio y configuración del simulador
 */

// Cargar estadísticas de preguntas
async function loadQuestionStats() {
    try {
        const response = await fetch('data/questions.json');
        const data = await response.json();

        // Contar preguntas por dominio
        const domainCounts = {};
        data.questions.forEach(q => {
            domainCounts[q.domain] = (domainCounts[q.domain] || 0) + 1;
        });

        // Mostrar estadísticas
        displayStats(domainCounts, data.questions.length);

        return data;
    } catch (error) {
        console.error('Error cargando preguntas:', error);
        alert('Error al cargar las preguntas. Por favor, recarga la página.');
    }
}

// Mostrar estadísticas en la página
function displayStats(domainCounts, total) {
    const statsGrid = document.getElementById('statsGrid');
    if (!statsGrid) return;

    const domains = [
        { name: 'Domain 1: Cloud Concepts', color: '#FF9900' },
        { name: 'Domain 2: Security and Compliance', color: '#232F3E' },
        { name: 'Domain 3: Cloud Technology and Services', color: '#FF9900' },
        { name: 'Domain 4: Billing, Pricing, and Support', color: '#232F3E' }
    ];

    statsGrid.innerHTML = domains.map(domain => {
        const count = domainCounts[domain.name] || 0;
        const percentage = ((count / total) * 100).toFixed(1);

        return `
            <div class="stat-card">
                <div class="stat-header">
                    <div class="stat-badge" style="background-color: ${domain.color}"></div>
                    <div class="stat-name">${domain.name.split(': ')[1]}</div>
                </div>
                <div class="stat-number">${count}</div>
                <div class="stat-percentage">${percentage}% del total</div>
            </div>
        `;
    }).join('');
}

// Manejar el envío del formulario
document.getElementById('examConfigForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();

    // Obtener dominios seleccionados
    const selectedDomains = Array.from(document.querySelectorAll('input[name="domain"]:checked'))
        .map(input => input.value);

    if (selectedDomains.length === 0) {
        alert('Por favor, selecciona al menos un dominio.');
        return;
    }

    // Obtener configuración
    const config = {
        domains: selectedDomains,
        questionCount: document.getElementById('questionCount').value,
        timeLimit: parseInt(document.getElementById('timeLimit').value),
        examMode: document.getElementById('examMode').value,
        shuffleQuestions: document.getElementById('shuffleQuestions').checked
    };

    // Guardar configuración en localStorage
    localStorage.setItem('examConfig', JSON.stringify(config));

    // Redirigir al simulador
    window.location.href = 'simulator.html';
});

// Cargar estadísticas al cargar la página
document.addEventListener('DOMContentLoaded', () => {
    loadQuestionStats();
});
