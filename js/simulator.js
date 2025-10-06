/**
 * Simulador de Examen AWS CLF-C02
 * Gestiona la lógica del examen, temporizador, navegación y respuestas
 */

// Estado del examen
let examState = {
    config: null,
    questions: [],
    currentIndex: 0,
    answers: {},
    markedQuestions: new Set(),
    startTime: null,
    timeRemaining: 0,
    timerInterval: null,
    examMode: 'simulation'
};

// Inicializar examen
async function initExam() {
    try {
        // Cargar configuración
        const configStr = localStorage.getItem('examConfig');
        if (!configStr) {
            alert('No hay configuración de examen. Redirigiendo...');
            window.location.href = 'index.html';
            return;
        }

        examState.config = JSON.parse(configStr);
        examState.examMode = examState.config.examMode;

        // Cargar preguntas
        const response = await fetch('data/questions.json');
        const data = await response.json();

        // Filtrar preguntas por dominios seleccionados
        let filteredQuestions = data.questions.filter(q =>
            examState.config.domains.includes(q.domain)
        );

        // Aleatorizar si está configurado
        if (examState.config.shuffleQuestions) {
            filteredQuestions = shuffleArray(filteredQuestions);
        }

        // Limitar cantidad de preguntas
        const questionCount = examState.config.questionCount === 'all'
            ? filteredQuestions.length
            : parseInt(examState.config.questionCount);

        examState.questions = filteredQuestions.slice(0, questionCount);

        // Inicializar temporizador
        if (examState.config.timeLimit > 0) {
            examState.timeRemaining = examState.config.timeLimit * 60; // convertir a segundos
            startTimer();
        } else {
            document.getElementById('timer').textContent = 'Sin límite';
        }

        // Actualizar UI
        document.getElementById('totalQuestions').textContent = examState.questions.length;

        // Mostrar primera pregunta
        displayQuestion(0);

        // Guardar estado inicial
        saveExamState();

    } catch (error) {
        console.error('Error inicializando examen:', error);
        alert('Error al cargar el examen. Por favor, intenta nuevamente.');
        window.location.href = 'index.html';
    }
}

// Mezclar array (algoritmo Fisher-Yates)
function shuffleArray(array) {
    const shuffled = [...array];
    for (let i = shuffled.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
    }
    return shuffled;
}

// Mostrar pregunta
function displayQuestion(index) {
    if (index < 0 || index >= examState.questions.length) return;

    examState.currentIndex = index;
    const question = examState.questions[index];

    // Actualizar número de pregunta
    document.getElementById('currentQuestion').textContent = index + 1;

    // Mostrar dominio
    document.getElementById('questionDomain').textContent = question.domain;

    // Mostrar texto de pregunta
    document.getElementById('questionText').textContent = question.question;

    // Generar opciones
    const optionsList = document.getElementById('optionsList');
    const userAnswer = examState.answers[question.id];

    optionsList.innerHTML = Object.entries(question.options).map(([letter, text]) => {
        const isChecked = userAnswer === letter ? 'checked' : '';
        const isCorrect = letter === question.correctAnswer;
        const isUserAnswer = userAnswer === letter;

        // En modo estudio, mostrar respuestas correctas/incorrectas
        let optionClass = '';
        if (examState.examMode === 'study' && userAnswer) {
            if (isCorrect) {
                optionClass = 'correct';
            } else if (isUserAnswer && !isCorrect) {
                optionClass = 'incorrect';
            }
        }

        return `
            <li class="option-item">
                <label class="option-label ${optionClass}">
                    <input type="radio"
                           name="answer"
                           value="${letter}"
                           ${isChecked}
                           onchange="saveAnswer('${question.id}', '${letter}')">
                    <span class="option-letter">${letter})</span>
                    <span class="option-text">${text}</span>
                </label>
            </li>
        `;
    }).join('');

    // Mostrar explicación en modo estudio si ya respondió
    const explanationBox = document.getElementById('explanationBox');
    const explanationText = document.getElementById('explanationText');

    if (examState.examMode === 'study' && userAnswer) {
        explanationBox.style.display = 'block';
        explanationText.textContent = question.explanation || 'No hay explicación disponible.';
    } else {
        explanationBox.style.display = 'none';
    }

    // Actualizar estado de botón "Marcar"
    updateMarkButton();

    // Actualizar botones de navegación
    updateNavigationButtons();
}

// Guardar respuesta
function saveAnswer(questionId, answer) {
    examState.answers[questionId] = answer;
    saveExamState();

    // En modo estudio, mostrar explicación inmediatamente
    if (examState.examMode === 'study') {
        displayQuestion(examState.currentIndex);
    }
}

// Navegar a pregunta anterior
function previousQuestion() {
    if (examState.currentIndex > 0) {
        displayQuestion(examState.currentIndex - 1);
    }
}

// Navegar a pregunta siguiente
function nextQuestion() {
    if (examState.currentIndex < examState.questions.length - 1) {
        displayQuestion(examState.currentIndex + 1);
    } else {
        // Última pregunta - preguntar si quiere finalizar
        if (confirm('Has llegado al final del examen. ¿Deseas finalizarlo y ver los resultados?')) {
            finishExam();
        }
    }
}

// Marcar/desmarcar pregunta para revisión
function toggleMark() {
    const questionId = examState.questions[examState.currentIndex].id;

    if (examState.markedQuestions.has(questionId)) {
        examState.markedQuestions.delete(questionId);
    } else {
        examState.markedQuestions.add(questionId);
    }

    updateMarkButton();
    saveExamState();
}

// Actualizar botón de marcar
function updateMarkButton() {
    const btn = document.getElementById('btnMark');
    const questionId = examState.questions[examState.currentIndex].id;
    const isMarked = examState.markedQuestions.has(questionId);

    btn.classList.toggle('marked', isMarked);
    btn.textContent = isMarked ? '✓ Marcada' : '🔖 Marcar para Revisión';
}

// Actualizar botones de navegación
function updateNavigationButtons() {
    const btnPrevious = document.getElementById('btnPrevious');
    const btnNext = document.getElementById('btnNext');

    btnPrevious.disabled = examState.currentIndex === 0;

    // Cambiar texto del botón "Siguiente" en la última pregunta
    if (examState.currentIndex === examState.questions.length - 1) {
        btnNext.textContent = 'Finalizar Examen';
        btnNext.classList.add('btn-primary');
    } else {
        btnNext.textContent = 'Siguiente →';
    }
}

// Temporizador
function startTimer() {
    examState.timerInterval = setInterval(() => {
        examState.timeRemaining--;

        // Actualizar display
        const minutes = Math.floor(examState.timeRemaining / 60);
        const seconds = examState.timeRemaining % 60;
        const timerElement = document.getElementById('timer');

        timerElement.textContent = `${minutes}:${seconds.toString().padStart(2, '0')}`;

        // Advertencia cuando quedan 5 minutos
        if (examState.timeRemaining <= 300) {
            timerElement.classList.add('warning');
        }

        // Tiempo agotado
        if (examState.timeRemaining <= 0) {
            clearInterval(examState.timerInterval);
            alert('El tiempo ha finalizado. El examen se enviará automáticamente.');
            finishExam();
        }

        saveExamState();
    }, 1000);
}

// Guardar estado del examen en localStorage
function saveExamState() {
    localStorage.setItem('examState', JSON.stringify({
        ...examState,
        timerInterval: null // No guardar el interval
    }));
}

// Finalizar examen
function finishExam() {
    // Detener temporizador
    if (examState.timerInterval) {
        clearInterval(examState.timerInterval);
    }

    // Calcular resultados
    const results = calculateResults();

    // Guardar resultados
    localStorage.setItem('examResults', JSON.stringify(results));

    // Limpiar estado del examen
    localStorage.removeItem('examState');

    // Redirigir a página de resultados
    window.location.href = 'review.html';
}

// Calcular resultados
function calculateResults() {
    let correctCount = 0;
    let incorrectCount = 0;
    let unansweredCount = 0;
    const domainScores = {};
    const detailedAnswers = [];

    examState.questions.forEach(question => {
        const userAnswer = examState.answers[question.id];
        const isCorrect = userAnswer === question.correctAnswer;

        // Contadores generales
        if (!userAnswer) {
            unansweredCount++;
        } else if (isCorrect) {
            correctCount++;
        } else {
            incorrectCount++;
        }

        // Puntaje por dominio
        if (!domainScores[question.domain]) {
            domainScores[question.domain] = { correct: 0, total: 0 };
        }
        domainScores[question.domain].total++;
        if (isCorrect) {
            domainScores[question.domain].correct++;
        }

        // Detalle de respuestas
        detailedAnswers.push({
            question: question.question,
            domain: question.domain,
            userAnswer: userAnswer || 'Sin responder',
            correctAnswer: question.correctAnswer,
            isCorrect: isCorrect,
            options: question.options,
            explanation: question.explanation,
            wasMarked: examState.markedQuestions.has(question.id)
        });
    });

    // Calcular puntaje escalado (100-1000, mínimo 700 para aprobar)
    const percentageCorrect = correctCount / examState.questions.length;
    const scaledScore = Math.round(100 + (percentageCorrect * 900));

    return {
        totalQuestions: examState.questions.length,
        correctCount,
        incorrectCount,
        unansweredCount,
        percentageCorrect: Math.round(percentageCorrect * 100),
        scaledScore,
        passed: scaledScore >= 700,
        domainScores,
        detailedAnswers,
        config: examState.config,
        timeUsed: examState.config.timeLimit > 0
            ? (examState.config.timeLimit * 60 - examState.timeRemaining)
            : null
    };
}

// Manejar cierre de ventana (advertir sobre pérdida de progreso)
window.addEventListener('beforeunload', (e) => {
    if (examState.questions.length > 0) {
        e.preventDefault();
        e.returnValue = '¿Estás seguro de que quieres salir? Perderás tu progreso.';
    }
});

// Inicializar al cargar la página
document.addEventListener('DOMContentLoaded', initExam);
