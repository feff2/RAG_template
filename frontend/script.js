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

        this.initializeEventListeners();
        this.showWelcomeMessage();
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
        const welcomeMessage = 'Добро пожаловать, задайте любой вопрос по закупкам 223 ФЗ и я постараюсь помочь вам найти ответ.';
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
     */
    addMessage(text, sender, isLoading = false) {
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
            // Обработка ссылок в тексте
            const processedText = this.processLinks(text);
            messageDiv.innerHTML = processedText;
        }

        this.messagesContainer.appendChild(messageDiv);
        this.scrollToBottom();

        return messageDiv;
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

            // Добавляем ответ от системы
            this.addMessage(response.response, 'assistant');
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
        const requestId = this.generateUUID();

        const requestBody = {
            request_id: requestId,
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

        return await response.json();
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
