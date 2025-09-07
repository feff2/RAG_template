/**
 * Простой и безопасный рендерер Markdown для обработки ответов модели
 * Обрабатывает основные элементы Markdown и источники в формате [n]
 */
class MarkdownRenderer {
    constructor() {
        this.sourceLinks = [];
    }

    /**
     * Основной метод для рендеринга Markdown текста
     * @param {string} text - Исходный текст в формате Markdown
     * @param {Array<string>} sources - Массив ссылок-источников
     * @returns {string} HTML строка
     */
    render(text, sources = []) {
        if (!text || typeof text !== 'string') {
            return '';
        }

        this.sourceLinks = sources;
        let html = text;

        try {
            // Безопасная обработка с проверками
            html = this.escapeHtml(html);
            html = this.renderHeaders(html);
            html = this.renderBold(html);
            html = this.renderItalic(html);
            html = this.renderCode(html);
            html = this.renderCodeBlocks(html);
            html = this.renderLists(html);
            html = this.renderLinks(html);
            html = this.renderSources(html);
            html = this.renderLineBreaks(html);

            return html;
        } catch (error) {
            console.warn('Ошибка при рендеринге Markdown:', error);
            // Возвращаем безопасный HTML в случае ошибки
            return this.escapeHtml(text).replace(/\n/g, '<br>');
        }
    }

    /**
     * Экранирует HTML символы для безопасности
     * @param {string} text - Исходный текст
     * @returns {string} Экранированный текст
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Обрабатывает заголовки (# ## ###)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderHeaders(text) {
        return text
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>');
    }

    /**
     * Обрабатывает жирный текст (**text**)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderBold(text) {
        return text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    }

    /**
     * Обрабатывает курсив (*text*)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderItalic(text) {
        return text.replace(/\*(.*?)\*/g, '<em>$1</em>');
    }

    /**
     * Обрабатывает инлайн код (`code`)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderCode(text) {
        return text.replace(/`([^`]+)`/g, '<code>$1</code>');
    }

    /**
     * Обрабатывает блоки кода (```code```)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderCodeBlocks(text) {
        return text.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    }

    /**
     * Обрабатывает списки (- item)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderLists(text) {
        // Простая обработка списков
        return text.replace(/^- (.*$)/gm, '<li>$1</li>')
                  .replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');
    }

    /**
     * Обрабатывает обычные ссылки [text](url)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderLinks(text) {
        return text.replace(/\[([^\]]+)\]\(([^)]+)\)/g,
            '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    }

    /**
     * Обрабатывает источники в формате [n]
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderSources(text) {
        if (!this.sourceLinks || this.sourceLinks.length === 0) {
            return text;
        }

        // Заменяем [n] на интерактивные элементы
        return text.replace(/\[(\d+)\]/g, (match, num) => {
            const index = parseInt(num) - 1; // Конвертируем в 0-based индекс

            if (index >= 0 && index < this.sourceLinks.length) {
                const link = this.sourceLinks[index];
                return `  <span class="source-ref" data-source-url="${link}" data-source-num="${num}">${num}</span>  `;
            }

            return match; // Возвращаем исходный текст, если индекс некорректный
        });
    }

    /**
     * Обрабатывает переносы строк
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderLineBreaks(text) {
        return text.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>');
    }

    /**
     * Инициализирует обработчики событий для источников
     * @param {HTMLElement} container - Контейнер с обработанным HTML
     */
    initializeSourceHandlers(container) {
        const sourceRefs = container.querySelectorAll('.source-ref');

        sourceRefs.forEach(ref => {
            const url = ref.getAttribute('data-source-url');
            const num = ref.getAttribute('data-source-num');

            // Создаем tooltip для ссылки
            const tooltip = this.createSourceTooltip(url);
            ref.appendChild(tooltip);

            // Обработчики событий
            ref.addEventListener('mouseenter', () => {
                tooltip.classList.add('visible');
            });

            ref.addEventListener('mouseleave', () => {
                tooltip.classList.remove('visible');
            });

            ref.addEventListener('click', (e) => {
                e.preventDefault();
                window.open(url, '_blank', 'noopener,noreferrer');
            });
        });
    }

    /**
     * Создает tooltip для источника
     * @param {string} url - URL источника
     * @returns {HTMLElement} Элемент tooltip
     */
    createSourceTooltip(url) {
        const tooltip = document.createElement('div');
        tooltip.className = 'source-tooltip';
        tooltip.textContent = url;
        return tooltip;
    }
}

// Экспортируем класс для использования в других файлах
window.MarkdownRenderer = MarkdownRenderer;
