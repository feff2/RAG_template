/**
 * Основная логика фронтенда Q&A системы
 * Обеспечивает взаимодействие с пользователем и API backend'а
 */

class ChatApp {
    /**
     * Инициализация приложения чата
     */
    constructor() {
        // API конфигурация
        this.apiBaseUrl = 'http://localhost:8080';
        this.apiEndpoint = '/api/v1/query';
        this.feedbackEndpoint = '/api/v1/feedback';

        // UUID пользователя (генерируется при загрузке)
        this.userUuid = this.generateUUID();

        // DOM элементы
        this.messageInput = document.getElementById('messageInput');
        this.sendButton = document.getElementById('sendButton');
        this.resetButton = document.getElementById('resetButton');
        this.messagesContainer = document.getElementById('messages');
        this.chatContainer = document.getElementById('chatContainer');
        this.container = document.querySelector('.container');

        // Состояние приложения
        this.isLoading = false;
        this.messageHistory = [];
        this.currentPopup = null;
        this.currentRating = 0;

        // Инициализируем Markdown рендерер
        this.markdownRenderer = new MarkdownRenderer();

        this.initializeEventListeners();
        this.showWelcomeMessage();
        this.createRatingPopup();
    }

    /**
     * Генерирует UUID для пользователя
     * @returns {string} UUID пользователя
     */
    generateUUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
            const r = Math.random() * 16 | 0;
            const v = c === 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }

    /**
     * Инициализация обработчиков событий
     */
    initializeEventListeners() {
        // Обработка отправки сообщения
        this.sendButton.addEventListener('click', () => this.sendMessage());

        // Обработка нажатия Enter в поле ввода
        this.messageInput.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' && !event.shiftKey) {
                event.preventDefault();
                this.sendMessage();
            }
        });

        // Обработка изменения текста в поле ввода
        this.messageInput.addEventListener('input', () => {
            this.updateSendButtonState();
            this.autoResizeTextarea();
        });

        // Обработка сброса чата
        this.resetButton.addEventListener('click', () => this.resetChat());
    }

    /**
     * Показывает приветственное сообщение
     */
    showWelcomeMessage() {
        const welcomeMessage = 'Добро пожаловать, я ваш интеллектуальный помощник в сфере закупок, задавайте вопросы, а я на них отвечу .';
        this.addMessage(welcomeMessage, 'assistant');
    }

    /**
     * Автоматическое изменение размера текстового поля
     */
    autoResizeTextarea() {
        this.messageInput.style.height = 'auto';
        this.messageInput.style.height = Math.min(this.messageInput.scrollHeight, 120) + 'px';
    }

    /**
     * Обновляет состояние кнопки отправки
     */
    updateSendButtonState() {
        const hasText = this.messageInput.value.trim().length > 0;
        this.sendButton.disabled = !hasText || this.isLoading;
    }

    /**
     * Добавляет сообщение в чат
     * @param {string} text - Текст сообщения
     * @param {string} sender - Отправитель ('user' или 'assistant')
     * @param {boolean} isLoading - Индикатор загрузки
     * @param {string} requestId - ID запроса для связи с рейтингом
     */
    addMessage(text, sender, isLoading = false, requestId = null) {
        const messageDiv = document.createElement('div');
        messageDiv.classList.add('message', sender);

        if (isLoading) {
            messageDiv.classList.add('loading');
            messageDiv.innerHTML = `
                Генерирую ответ...
                <div class="loading-dots">
                    <span></span>
                    <span></span>
                    <span></span>
                </div>
            `;
        } else {
            // Обрабатываем контент в зависимости от отправителя
            if (sender === 'assistant') {
                // Для ассистента обрабатываем как Markdown с источниками
                let sources = [];
                let responseText = text;

                // Если это ответ от API с источниками
                if (typeof text === 'string' && this.lastResponseSources) {
                    sources = this.lastResponseSources;
                    responseText = text;
                }

                const processedHtml = this.markdownRenderer.render(responseText, sources);
                messageDiv.innerHTML = processedHtml;

                // Инициализируем обработчики для источников
                this.markdownRenderer.initializeSourceHandlers(messageDiv);
            } else {
                // Для пользователя просто отображаем текст
                messageDiv.textContent = text;
            }
        }

        this.messagesContainer.appendChild(messageDiv);

        // Добавляем кнопку оценки для ответов ассистента
        if (sender === 'assistant' && !isLoading && requestId) {
            const feedbackButton = this.createFeedbackButton(requestId);
            this.messagesContainer.appendChild(feedbackButton);
        }

        this.scrollToBottom();

        return messageDiv;
    }

    /**
     * Создает кнопку для оставления оценки
     * @param {string} requestId - ID запроса для отправки рейтинга
     * @returns {HTMLElement} DOM элемент кнопки оценки
     */
    createFeedbackButton(requestId) {
        const buttonDiv = document.createElement('div');
        buttonDiv.classList.add('feedback-button');
        buttonDiv.setAttribute('data-request-id', requestId);
        buttonDiv.textContent = 'Оставить оценку ✍️';

        buttonDiv.addEventListener('click', () => this.openRatingPopup(requestId, buttonDiv));

        return buttonDiv;
    }

    /**
     * Создает popup окно для рейтинга
     */
    createRatingPopup() {
        const popup = document.createElement('div');
        popup.classList.add('rating-popup');
        popup.innerHTML = `
            <div class="rating-popup-content">
                <div class="rating-popup-title">Поставьте оценку</div>
                <div class="rating-stars-popup">
                    <span class="rating-star-popup" data-rating="1">🔘</span>
                    <span class="rating-star-popup" data-rating="2">🔘</span>
                    <span class="rating-star-popup" data-rating="3">🔘</span>
                    <span class="rating-star-popup" data-rating="4">🔘</span>
                    <span class="rating-star-popup" data-rating="5">🔘</span>
                </div>
                <textarea class="feedback-textarea" placeholder="Оставьте дополнительный комментарий (необязательно)"></textarea>
                <div class="feedback-actions">
                    <button class="feedback-cancel">Отмена</button>
                    <button class="feedback-submit">Отправить</button>
                </div>
            </div>
        `;

        document.body.appendChild(popup);
        this.currentPopup = popup;

        // Обработчики событий для popup
        this.setupPopupEventListeners(popup);
    }

    /**
     * Настраивает обработчики событий для popup окна
     * @param {HTMLElement} popup - Popup элемент
     */
    setupPopupEventListeners(popup) {
        const stars = popup.querySelectorAll('.rating-star-popup');
        const cancelBtn = popup.querySelector('.feedback-cancel');
        const submitBtn = popup.querySelector('.feedback-submit');

        // Обработчики для звезд
        stars.forEach(star => {
            const rating = parseInt(star.getAttribute('data-rating'));

            star.addEventListener('mouseenter', () => this.highlightPopupStars(stars, rating));
            star.addEventListener('mouseleave', () => this.resetPopupStars(stars));
            star.addEventListener('click', () => this.selectRating(popup, rating));
        });

        // Закрытие по клику на фон
        popup.addEventListener('click', (e) => {
            if (e.target === popup) {
                this.closeRatingPopup();
            }
        });

        // Кнопка отмены
        cancelBtn.addEventListener('click', () => this.closeRatingPopup());

        // Кнопка отправки
        submitBtn.addEventListener('click', () => this.submitPopupRating());
    }

    /**
     * Получает смайлики для рейтинга
     * @param {number} rating - Рейтинг от 1 до 5
     * @returns {Array} Массив смайликов
     */
    getRatingEmojis(rating) {
        const emojis = {
            1: ['🔴', '🔘', '🔘', '🔘', '🔘'],
            2: ['🟠', '🟠', '🔘', '🔘', '🔘'],
            3: ['🟡', '🟡', '🟡', '🔘', '🔘'],
            4: ['🔵', '🔵', '🔵', '🔵', '🔘'],
            5: ['🟢', '🟢', '🟢', '🟢', '🟢']
        };
        return emojis[rating] || ['🔘', '🔘', '🔘', '🔘', '🔘'];
    }

    /**
     * Подсвечивает звезды в popup при наведении
     * @param {NodeList} stars - Звезды в popup
     * @param {number} rating - Рейтинг для подсветки
     */
    highlightPopupStars(stars, rating) {
        const emojis = this.getRatingEmojis(rating);
        stars.forEach((star, index) => {
            star.textContent = emojis[index];
        });
    }

    /**
     * Сбрасывает подсветку звезд в popup
     * @param {NodeList} stars - Звезды в popup
     */
    resetPopupStars(stars) {
        if (this.currentRating === 0) {
            stars.forEach(star => {
                star.textContent = '🔘';
            });
        } else {
            this.highlightPopupStars(stars, this.currentRating);
        }
    }

    /**
     * Обрабатывает ссылки в тексте, делая их кликабельными
     * @param {string} text - Исходный текст
     * @returns {string} Обработанный текст с HTML ссылками
     */
    processLinks(text) {
        // Регулярное выражение для поиска markdown-ссылок [text](url)
        const markdownLinkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;

        // Замена markdown-ссылок на HTML ссылки
        let processedText = text.replace(markdownLinkRegex, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');

        // Регулярное выражение для поиска обычных URL
        const urlRegex = /(https?:\/\/[^\s]+)/g;

        // Замена обычных URL на кликабельные ссылки (если они не уже в HTML тегах)
        processedText = processedText.replace(urlRegex, (match) => {
            // Проверяем, не находится ли URL уже внутри HTML тега
            if (processedText.indexOf(`href="${match}"`) !== -1) {
                return match;
            }
            return `<a href="${match}" target="_blank" rel="noopener noreferrer">${match}</a>`;
        });

        // Обработка переносов строк
        processedText = processedText.replace(/\n/g, '<br>');

        return processedText;
    }

    /**
     * Прокрутка чата к последнему сообщению
     */
    scrollToBottom() {
        this.messagesContainer.scrollTop = this.messagesContainer.scrollHeight;
    }

    /**
     * Открывает popup окно для рейтинга
     * @param {string} requestId - ID запроса
     * @param {HTMLElement} buttonElement - Кнопка, которая открыла popup
     */
    openRatingPopup(requestId, buttonElement) {
        this.currentRequestId = requestId;
        this.currentButtonElement = buttonElement;
        this.currentRating = 0;

        // Сбрасываем форму
        const textarea = this.currentPopup.querySelector('.feedback-textarea');
        textarea.value = '';

        // Сбрасываем цветовые классы
        this.currentPopup.className = 'rating-popup';

        // Сбрасываем звезды к начальному состоянию
        const stars = this.currentPopup.querySelectorAll('.rating-star-popup');
        stars.forEach(star => {
            star.textContent = '🔘';
        });

        // Показываем popup
        this.currentPopup.classList.add('visible');
    }

    /**
     * Закрывает popup окно
     */
    closeRatingPopup() {
        if (this.currentPopup) {
            this.currentPopup.classList.remove('visible');
            this.currentRating = 0;
            this.currentRequestId = null;
            this.currentButtonElement = null;
        }
    }

    /**
     * Выбирает рейтинг в popup
     * @param {HTMLElement} popup - Popup элемент
     * @param {number} rating - Выбранный рейтинг
     */
    selectRating(popup, rating) {
        this.currentRating = rating;

        // Обновляем цветовую схему popup
        popup.className = `rating-popup visible rating-${rating}`;

        // Фиксируем звезды
        const stars = popup.querySelectorAll('.rating-star-popup');
        this.highlightPopupStars(stars, rating);
    }

    /**
     * Отправляет рейтинг из popup
     */
    async submitPopupRating() {
        if (this.currentRating === 0) {
            alert('Пожалуйста, выберите оценку');
            return;
        }

        try {
            const textarea = this.currentPopup.querySelector('.feedback-textarea');
            const feedbackText = textarea.value.trim() || null;

            // Получаем последние сообщения пользователя и модели
            const userMessage = this.getLastUserMessage();
            const modelResponse = this.getLastModelResponse();

            const feedbackData = {
                user_id: this.userUuid,
                user_message: userMessage,
                model_response: modelResponse,
                rating: this.currentRating,
                feedback: feedbackText
            };

            console.log('Отправляем feedback:', feedbackData);

            const response = await fetch(`${this.apiBaseUrl}${this.feedbackEndpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(feedbackData)
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            // Заменяем кнопку на индикатор отправленной оценки
            this.showSubmittedRating(this.currentButtonElement, this.currentRating);

            // Закрываем popup
            this.closeRatingPopup();

        } catch (error) {
            console.error('Ошибка при отправке feedback:', error);
            alert('Ошибка при отправке оценки. Попробуйте еще раз.');
        }
    }

    /**
     * Показывает отправленную оценку вместо кнопки
     * @param {HTMLElement} buttonElement - Кнопка для замены
     * @param {number} rating - Отправленный рейтинг
     */
    showSubmittedRating(buttonElement, rating) {
        const submittedDiv = document.createElement('div');
        submittedDiv.classList.add('submitted-rating', `rating-${rating}`);
        submittedDiv.textContent = `Ваша оценка: ${rating}/5`;

        buttonElement.parentNode.replaceChild(submittedDiv, buttonElement);
    }

    /**
     * Отправка сообщения пользователя
     */
    async sendMessage() {
        const messageText = this.messageInput.value.trim();

        if (!messageText || this.isLoading) {
            return;
        }

        // Добавляем сообщение пользователя
        this.addMessage(messageText, 'user');
        this.messageHistory.push({ sender: 'user', text: messageText });

        // Очищаем поле ввода
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButtonState();

        // Показываем индикатор загрузки
        this.setLoadingState(true);
        const loadingMessage = this.addMessage('', 'assistant', true);

        try {
            // Отправляем запрос к API
            const response = await this.callAPI(messageText);

            // Убираем индикатор загрузки
            loadingMessage.remove();

            // Добавляем ответ от системы с requestId для рейтинга
            this.addMessage(response.response, 'assistant', false, response.requestId);
            this.messageHistory.push({ sender: 'assistant', text: response.response });

        } catch (error) {
            console.error('Ошибка при отправке запроса:', error);

            // Убираем индикатор загрузки
            loadingMessage.remove();

            // Показываем сообщение об ошибке
            const errorMessage = 'Извините, произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте еще раз.';
            this.addMessage(errorMessage, 'assistant');

        } finally {
            this.setLoadingState(false);
        }
    }


    /**
     * Вызов API для получения ответа на запрос
     * @param {string} query - Запрос пользователя
     * @returns {Promise<Object>} Ответ от API
     */
    async callAPI(query) {
        const requestBody = {
            user_id: this.userUuid,
            query: query
        };

        const response = await fetch(`${this.apiBaseUrl}${this.apiEndpoint}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestBody)
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const result = await response.json();
        // Добавляем user_id к результату для связи с рейтингом
        result.userId = result.user_id;
        result.requestId = this.generateUUID(); // Генерируем ID для рейтинга

        // Обрабатываем response как tuple[str, list[str]]
        if (Array.isArray(result.response) && result.response.length >= 2) {
            this.lastResponseSources = result.response[1]; // Источники
            result.response = result.response[0]; // Текст ответа
        } else if (Array.isArray(result.response) && result.response.length >= 1) {
            this.lastResponseSources = [];
            result.response = result.response[0]; // Берем первый элемент - основной ответ
        } else {
            this.lastResponseSources = [];
        }

        return result;
    }

    /**
     * Устанавливает состояние загрузки
     * @param {boolean} loading - Состояние загрузки
     */
    setLoadingState(loading) {
        this.isLoading = loading;
        this.updateSendButtonState();

        if (loading) {
            this.container.classList.add('loading');
        } else {
            this.container.classList.remove('loading');
        }
    }

    /**
     * Получает последнее сообщение пользователя
     * @returns {string} Последнее сообщение пользователя
     */
    getLastUserMessage() {
        const userMessages = this.messageHistory.filter(msg => msg.sender === 'user');
        return userMessages.length > 0 ? userMessages[userMessages.length - 1].text : '';
    }

    /**
     * Получает последний ответ модели
     * @returns {string} Последний ответ модели
     */
    getLastModelResponse() {
        const assistantMessages = this.messageHistory.filter(msg => msg.sender === 'assistant');
        return assistantMessages.length > 0 ? assistantMessages[assistantMessages.length - 1].text : '';
    }

    /**
     * Сброс чата к начальному состоянию
     */
    resetChat() {
        // Очищаем историю сообщений
        this.messageHistory = [];

        // Очищаем контейнер сообщений
        this.messagesContainer.innerHTML = '';

        // Очищаем поле ввода
        this.messageInput.value = '';
        this.autoResizeTextarea();
        this.updateSendButtonState();

        // Генерируем новый UUID пользователя
        this.userUuid = this.generateUUID();

        // Показываем приветственное сообщение
        this.showWelcomeMessage();

        // Убираем состояние загрузки, если оно было активно
        this.setLoadingState(false);
    }
}

// Инициализация приложения после загрузки DOM
document.addEventListener('DOMContentLoaded', () => {
    new ChatApp();
});
