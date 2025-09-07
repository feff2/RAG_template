/**
 * Профессиональный и безопасный рендерер Markdown для обработки ответов модели
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
            // КРИТИЧЕСКИ ВАЖНЫЙ порядок обработки:
            // 1. Сначала блочные элементы (код-блоки) - чтобы защитить их содержимое
            html = this.renderCodeBlocks(html);

            // 2. Инлайн код - защищаем от дальнейшей обработки
            html = this.renderCode(html);

            // 3. Источники [n] - до обработки ссылок, чтобы не конфликтовать
            html = this.renderSources(html);

            // 4. Обычные ссылки [text](url)
            html = this.renderLinks(html);

            // 5. Заголовки - ПЕРЕД форматированием текста
            html = this.renderHeaders(html);

            // 6. Горизонтальные линии
            html = this.renderHorizontalRules(html);

            // 7. Жирный и курсив текст
            html = this.renderBold(html);
            html = this.renderItalic(html);

            // 8. Списки
            html = this.renderLists(html);

            // 9. Переносы строк - в самом конце
            html = this.renderLineBreaks(html);

            return html;
        } catch (error) {
            console.warn('Ошибка при рендеринге Markdown:', error);
            // Возвращаем безопасный HTML в случае ошибки
            return this.safeEscape(text).replace(/\n/g, '<br>');
        }
    }

    /**
     * Безопасное экранирование HTML с сохранением переносов
     * @param {string} text - Исходный текст
     * @returns {string} Экранированный текст
     */
    safeEscape(text) {
        return text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    /**
     * Обрабатывает заголовки всех уровней с поддержкой вложенного форматирования
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderHeaders(text) {
        // Обрабатываем заголовки от больших к меньшим для корректности
        return text
            .replace(/^#### (.*$)/gm, '<h4>$1</h4>')
            .replace(/^### (.*$)/gm, '<h3>$1</h3>')
            .replace(/^## (.*$)/gm, '<h2>$1</h2>')
            .replace(/^# (.*$)/gm, '<h1>$1</h1>');
    }

    /**
     * Обрабатывает горизонтальные линии (---, ***, ___)
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderHorizontalRules(text) {
        return text
            .replace(/^---\s*$/gm, '<hr>')
            .replace(/^\*\*\*\s*$/gm, '<hr>')
            .replace(/^___\s*$/gm, '<hr>');
    }

    /**
     * Обрабатывает жирный текст с защитой от пересечений
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderBold(text) {
        // Используем non-greedy matching и защищаем от пересечений с кодом
        return text.replace(/\*\*(?!.*<code>)(.*?)(?<!<\/code>.*)\*\*/g, '<strong>$1</strong>');
    }

    /**
     * Обрабатывает курсив с защитой от конфликтов с жирным текстом
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderItalic(text) {
        // Избегаем конфликта с жирным текстом (**) и кодом
        return text.replace(/(?<!\*)\*(?!\*)([^*]+?)(?<!\*)\*(?!\*)/g, '<em>$1</em>');
    }

    /**
     * Обрабатывает инлайн код с защитой содержимого
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderCode(text) {
        return text.replace(/`([^`\n]+)`/g, (match, code) => {
            // Экранируем содержимое кода
            const escapedCode = this.safeEscape(code);
            return `<code>${escapedCode}</code>`;
        });
    }

    /**
     * Обрабатывает блоки кода с полной защитой содержимого
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderCodeBlocks(text) {
        return text.replace(/```([\s\S]*?)```/g, (match, code) => {
            // Экранируем и сохраняем форматирование
            const escapedCode = this.safeEscape(code.trim());
            return `<pre><code>${escapedCode}</code></pre>`;
        });
    }

    /**
     * Обрабатывает списки с поддержкой вложенности
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderLists(text) {
        // Обрабатываем многострочные списки
        let result = text;

        // Находим последовательности строк-списков
        result = result.replace(/(^- .+$\n?)+/gm, (match) => {
            const items = match.split('\n').filter(line => line.trim());
            const listItems = items.map(item => {
                const content = item.replace(/^- /, '');
                return `<li>${content}</li>`;
            }).join('');
            return `<ul>${listItems}</ul>`;
        });

        return result;
    }

    /**
     * Обрабатывает обычные ссылки [text](url) с валидацией
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderLinks(text) {
        return text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, (match, linkText, url) => {
            // Базовая валидация URL
            if (!url || url.length < 4) {
                return match;
            }

            const escapedText = this.safeEscape(linkText);
            const escapedUrl = this.safeEscape(url);
            return `<a href="${escapedUrl}" target="_blank" rel="noopener noreferrer">${escapedText}</a>`;
        });
    }

    /**
     * Обрабатывает источники в формате [n] с валидацией
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderSources(text) {
        if (!this.sourceLinks || this.sourceLinks.length === 0) {
            // Если нет источников, удаляем все [n] из текста
            return text.replace(/\[(\d+)\](?!\()/g, '');
        }

        // Заменяем [n] на интерактивные элементы, избегая конфликта с обычными ссылками
        return text.replace(/\[(\d+)\](?!\()/g, (match, num) => {
            // Проверяем, что num - валидное число
            const numInt = parseInt(num, 10);
            if (isNaN(numInt) || numInt <= 0) {
                // Удаляем некорректные номера
                return '';
            }

            const index = numInt - 1;

            // Проверяем, что индекс существует в массиве источников
            if (index >= 0 && index < this.sourceLinks.length && this.sourceLinks[index]) {
                const link = this.safeEscape(this.sourceLinks[index]);
                // Дополнительная проверка, что ссылка не пустая
                if (link && link.trim().length > 0) {
                    return `  <span class="source-ref" data-source-url="${link}" data-source-num="${num}">${num}</span>  `;
                }
            }

            // Если источник не найден или некорректный - удаляем из текста
            return '';
        });
    }

    /**
     * Обрабатывает переносы строк с правильной структурой параграфов
     * @param {string} text - Текст для обработки
     * @returns {string} Обработанный текст
     */
    renderLineBreaks(text) {
        // Разбиваем на параграфы по двойным переносам
        const paragraphs = text.split(/\n\s*\n/);

        const processedParagraphs = paragraphs.map(paragraph => {
            if (!paragraph.trim()) return '';

            // Проверяем, не является ли уже HTML-блоком
            if (paragraph.match(/^<(h[1-6]|ul|ol|pre|blockquote)/)) {
                return paragraph;
            }

            // Заменяем одинарные переносы на <br> внутри параграфа
            const withBreaks = paragraph.replace(/\n/g, '<br>');
            return `<p>${withBreaks}</p>`;
        });

        return processedParagraphs.filter(p => p).join('\n');
    }

    /**
     * Инициализирует обработчики событий для источников
     * @param {HTMLElement} container - Контейнер с обработанным HTML
     */
    initializeSourceHandlers(container) {
        const sourceRefs = container.querySelectorAll('.source-ref');

        sourceRefs.forEach(ref => {
            const url = ref.getAttribute('data-source-url');

            if (!url) return;

            // Создаем tooltip для ссылки
            const tooltip = this.createSourceTooltip(url);
            ref.appendChild(tooltip);

            // Обработчики событий с защитой от ошибок
            ref.addEventListener('mouseenter', () => {
                tooltip.classList.add('visible');
            });

            ref.addEventListener('mouseleave', () => {
                tooltip.classList.remove('visible');
            });

            ref.addEventListener('click', (e) => {
                e.preventDefault();
                try {
                    window.open(url, '_blank', 'noopener,noreferrer');
                } catch (error) {
                    console.warn('Не удалось открыть ссылку:', url, error);
                }
            });
        });
    }

    /**
     * Создает tooltip для источника с обрезкой длинных URL
     * @param {string} url - URL источника
     * @returns {HTMLElement} Элемент tooltip
     */
    createSourceTooltip(url) {
        const tooltip = document.createElement('div');
        tooltip.className = 'source-tooltip';

        // Обрезаем очень длинные URL для читаемости
        const displayUrl = url.length > 60 ? url.substring(0, 57) + '...' : url;
        tooltip.textContent = displayUrl;
        tooltip.title = url; // Полный URL в title

        return tooltip;
    }
}

// Экспортируем класс для использования в других файлах
window.MarkdownRenderer = MarkdownRenderer;
