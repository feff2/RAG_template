/**
 * Класс для управления страницей популярных вопросов
 */
class CommonQuestionsApp {
    /**
     * Инициализация приложения
     */
    constructor() {
        // API конфигурация
        this.apiBaseUrl = '';
        this.apiEndpoint = '/api/v1/common_questions';

        // DOM элементы
        this.questionsDropdown = document.getElementById('questionsLimit');
        this.questionsContainer = document.getElementById('questionsContainer');
        this.loadingContainer = document.getElementById('loadingContainer');

        // Состояние
        this.currentLimit = 10;
        this.questions = [];

        this.initializeEventListeners();
        this.loadQuestions();
    }

    /**
     * Инициализация обработчиков событий
     */
    initializeEventListeners() {
        // Обработчик изменения количества вопросов
        this.questionsDropdown.addEventListener('change', (e) => {
            const value = e.target.value;
            this.currentLimit = value === 'all' ? 'all' : parseInt(value, 10);
            this.loadQuestions();
        });

        // Обработчик клавиатуры для доступности
        this.questionsDropdown.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                this.questionsDropdown.click();
            }
        });
    }

    /**
     * Загрузка вопросов с сервера
     */
    async loadQuestions() {
        try {
            this.showLoading();

            // Формируем URL с параметрами
            const limitParam = this.currentLimit === 'all' ? '200' : this.currentLimit;
            const response = await fetch(
                `${this.apiBaseUrl}${this.apiEndpoint}?limit=${limitParam}`,
                {
                    method: 'GET',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                }
            );

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.questions = data.results || [];

            this.renderQuestions();

        } catch (error) {
            console.error('Ошибка загрузки вопросов:', error);
            this.showError('Не удалось загрузить популярные вопросы. Попробуйте обновить страницу.');
        }
    }

    /**
     * Отображение индикатора загрузки
     */
    showLoading() {
        this.questionsContainer.innerHTML = `
            <div class="loading-container">
                <div class="loading-message">
                    Загружаю популярные вопросы...
                    <div class="loading-dots">
                        <span></span>
                        <span></span>
                        <span></span>
                    </div>
                </div>
            </div>
        `;
    }

    /**
     * Отображение сообщения об ошибке
     * @param {string} message - Текст ошибки
     */
    showError(message) {
        this.questionsContainer.innerHTML = `
            <div class="error-container">
                <div class="error-message">
                    <div class="error-title">Ошибка загрузки</div>
                    <p class="error-text">${message}</p>
                </div>
            </div>
        `;
    }

    /**
     * Отображение списка вопросов
     */
    renderQuestions() {
        if (!this.questions || this.questions.length === 0) {
            this.questionsContainer.innerHTML = `
                <div class="error-container">
                    <div class="error-message">
                        <div class="error-title">Нет данных</div>
                        <p class="error-text">Популярные вопросы пока не найдены.</p>
                    </div>
                </div>
            `;
            return;
        }

        const questionsHtml = this.questions.map((question, index) => {
            const normalizedText = this.escapeHtml(question.normalized || 'Вопрос без текста');
            const count = question.count || 0;
            const examples = question.examples || [];

            // Подготовка примеров и кнопки раскрытия
            let examplesHtml = '';
            let expandButtonHtml = '';

            if (count > 1 && examples.length > 0) {
                // Создаем уникальный ID для каждого вопроса
                const questionId = `question-${index}`;

                // Кнопка раскрытия
                expandButtonHtml = `
                    <button class="expand-button"
                            onclick="event.stopPropagation(); window.commonQuestionsApp.toggleExamples('${questionId}')"
                            title="Показать примеры вопросов"
                            aria-label="Показать примеры">
                        <span class="expand-icon">▶</span>
                    </button>
                `;

                // Примеры (изначально скрыты)
                const randomExamples = this.getRandomExamples(examples, 5);
                const exampleItems = randomExamples.map(example =>
                    `<div class="example-item">${this.escapeHtml(example)}</div>`
                ).join('');

                examplesHtml = `
                    <div class="question-examples" id="${questionId}-examples" style="display: none;">
                        <div class="examples-title">Примеры из этой группы:</div>
                        ${exampleItems}
                    </div>
                `;
            }

            return `
                <div class="question-item" id="${count > 1 && examples.length > 0 ? `question-${index}` : ''}"
                     role="button"
                     tabindex="0"
                     aria-label="Вопрос ${index + 1}: ${normalizedText}"
                     data-question="${this.escapeHtml(normalizedText)}"
                     onclick="this.handleQuestionClick('${this.escapeHtml(normalizedText)}')"
                     onkeydown="this.handleQuestionKeydown(event, '${this.escapeHtml(normalizedText)}')">
                    <div class="question-content">
                        <p class="question-text">${normalizedText}</p>
                        ${examplesHtml}
                    </div>
                    <div class="question-meta">
                        ${expandButtonHtml}
                        <div class="question-count" title="Количество раз, когда задавался этот вопрос">
                            ${count.toLocaleString('ru-RU')}
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        this.questionsContainer.innerHTML = questionsHtml;

        // Добавляем обработчики событий после рендеринга
        this.attachQuestionHandlers();
    }

    /**
     * Добавление обработчиков событий к вопросам
     */
    attachQuestionHandlers() {
        const questionItems = this.questionsContainer.querySelectorAll('.question-item');

        questionItems.forEach(item => {
            const questionText = item.getAttribute('data-question');

            // Клик по вопросу (но не по кнопке раскрытия)
            item.addEventListener('click', (e) => {
                // Проверяем, что клик не по кнопке раскрытия или её дочерним элементам
                if (!e.target.closest('.expand-button')) {
                    this.handleQuestionClick(questionText);
                }
            });

            // Обработка клавиатуры для доступности
            item.addEventListener('keydown', (e) => {
                // Проверяем, что фокус не на кнопке раскрытия
                if (!e.target.closest('.expand-button')) {
                    this.handleQuestionKeydown(e, questionText);
                }
            });
        });
    }

    /**
     * Обработка клика по вопросу
     * @param {string} questionText - Текст вопроса
     */
    handleQuestionClick(questionText) {
        // Переходим на главную страницу с вопросом
        const encodedQuestion = encodeURIComponent(questionText);
        window.location.href = `/?question=${encodedQuestion}`;
    }

    /**
     * Обработка нажатий клавиш для доступности
     * @param {KeyboardEvent} e - Событие клавиатуры
     * @param {string} questionText - Текст вопроса
     */
    handleQuestionKeydown(e, questionText) {
        if (e.key === 'Enter' || e.key === ' ') {
            e.preventDefault();
            this.handleQuestionClick(questionText);
        }
    }

    /**
     * Экранирование HTML для безопасности
     * @param {string} text - Исходный текст
     * @returns {string} Экранированный текст
     */
    /**
     * Получение случайных примеров из массива
     * @param {Array} examples - Массив примеров
     * @param {number} count - Количество примеров для выбора
     * @returns {Array} Массив случайных примеров
     */
    getRandomExamples(examples, count) {
        if (examples.length <= count) {
            return examples;
        }

        const shuffled = examples.sort(() => 0.5 - Math.random());
        return shuffled.slice(0, count);
    }

    /**
     * Переключение видимости примеров
     * @param {string} questionId - ID вопроса
     */
    toggleExamples(questionId) {
        const examplesElement = document.getElementById(`${questionId}-examples`);
        const expandButton = document.querySelector(`#${questionId} .expand-button`);
        const expandIcon = expandButton?.querySelector('.expand-icon');

        if (examplesElement && expandIcon) {
            const isVisible = examplesElement.style.display !== 'none';

            if (isVisible) {
                examplesElement.style.display = 'none';
                expandIcon.textContent = '▶';
                expandButton.title = 'Показать примеры вопросов';
            } else {
                examplesElement.style.display = 'block';
                expandIcon.textContent = '▼';
                expandButton.title = 'Скрыть примеры вопросов';
            }
        }
    }

    escapeHtml(text) {
        if (typeof text !== 'string') {
            return '';
        }

        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }
}

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    window.commonQuestionsApp = new CommonQuestionsApp();
});
