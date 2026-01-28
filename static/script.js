const form = document.getElementById('analysisForm');
const urlInput = document.getElementById('urlInput');
const submitBtn = document.getElementById('submitBtn');
const statusContainer = document.getElementById('statusContainer');
const resultContainer = document.getElementById('resultContainer');
const errorContainer = document.getElementById('errorContainer');
const progressFill = document.getElementById('progressFill');
const progressText = document.getElementById('progressText');
const statusMessage = document.getElementById('statusMessage');
const resultContent = document.getElementById('resultContent');
const errorText = document.getElementById('errorText');
const resultInfo = document.getElementById('resultInfo');
const costInfo = document.getElementById('costInfo');
const costValue = document.getElementById('costValue');
const resultActions = document.getElementById('resultActions');
const exportDocxBtn = document.getElementById('exportDocxBtn');
const newAnalysisBtn = document.getElementById('newAnalysisBtn');
const instrumentsBlock = document.getElementById('instrumentsBlock');
const analysisSection = document.getElementById('analysisSection');
const btnMdToDocx = document.getElementById('btnMdToDocx');
const btnAnalysis = document.getElementById('btnAnalysis');
const backToInstrumentsBtn = document.getElementById('backToInstrumentsBtn');
const toolModalOverlay = document.getElementById('toolModalOverlay');
const toolModalCloseBtn = document.getElementById('toolModalCloseBtn');
const toolModalMdToDocxBtn = document.getElementById('toolModalMdToDocxBtn');
const mdFileInput = document.getElementById('mdFileInput');

let currentTaskId = null;
let currentResult = null;
let statusCheckInterval = null;
let currentProgress = 0; // Текущее значение прогресса (только увеличивается)

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = urlInput.value.trim();
    if (!url) return;
    
    // Скрываем предыдущие результаты и ошибки
    resultContainer.style.display = 'none';
    resultInfo.style.display = 'none';
    errorContainer.style.display = 'none';
    costInfo.style.display = 'none';
    resultActions.style.display = 'none';
    
    // Блокируем форму
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loader').style.display = 'block';
    urlInput.disabled = true;
    
    // Показываем статус
    statusContainer.style.display = 'block';
    currentProgress = 0; // Сбрасываем прогресс при новом анализе
    progressFill.style.width = '0%';
    progressText.textContent = '0%';
    statusMessage.textContent = 'Запуск анализа...';
    
    try {
        const response = await fetch('/api/analyze', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url: url })
        });
        
        // Проверяем Content-Type перед парсингом JSON
        const contentType = response.headers.get('content-type');
        if (!contentType || !contentType.includes('application/json')) {
            throw new Error('Сервер вернул не JSON ответ');
        }
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'Ошибка при запуске анализа');
        }
        
        currentTaskId = data.task_id;
        startStatusPolling();
        
    } catch (error) {
        showError(error.message);
        resetForm();
    }
});

function startStatusPolling() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        if (!currentTaskId) return;
        
        try {
            const response = await fetch(`/api/status/${currentTaskId}`);
            
            // Проверяем, что ответ успешный и это JSON
            if (!response.ok) {
                // Если ответ не OK, пытаемся получить JSON ошибки
                let errorData;
                try {
                    errorData = await response.json();
                } catch (e) {
                    // Если не JSON, значит это HTML страница ошибки
                    throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
                }
                throw new Error(errorData.error || `Ошибка ${response.status}`);
            }
            
            // Проверяем Content-Type
            const contentType = response.headers.get('content-type');
            if (!contentType || !contentType.includes('application/json')) {
                throw new Error('Сервер вернул не JSON ответ');
            }
            
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(statusCheckInterval);
                
                // Убеждаемся, что результат есть
                if (!data.result) {
                    showError('Результат анализа не найден');
                    resetForm();
                    return;
                }
                
                // Приоритетно используем стоимость из статуса, затем из результата
                let finalCost = null;
                if (data.cost !== null && data.cost !== undefined) {
                    finalCost = data.cost;
                } else if (data.result.cost !== null && data.result.cost !== undefined) {
                    finalCost = data.result.cost;
                }
                
                // Устанавливаем стоимость в результат
                data.result.cost = finalCost;
                
                // Добавляем task_id в результат для экспорта
                data.result.task_id = currentTaskId;
                
                console.log('Отображение результата:', {
                    cost: finalCost,
                    hasResult: !!data.result,
                    taskId: currentTaskId
                });
                
                showResult(data.result);
                resetForm();
                // НЕ очищаем поле ввода - пользователь может использовать кнопку "Анализ другого сайта"
            } else if (data.status === 'error') {
                clearInterval(statusCheckInterval);
                showError(data.message);
                resetForm();
            } else if (data.status === 'processing') {
                updateProgress(data.progress, data.message);
            }
        } catch (error) {
            clearInterval(statusCheckInterval);
            const errorMessage = error.message || 'Ошибка при проверке статуса';
            console.error('Ошибка при проверке статуса:', error);
            showError(errorMessage);
            resetForm();
        }
    }, 2000); // Проверяем каждые 2 секунды
}

function updateProgress(progress, message) {
    // Прогресс может только увеличиваться, никогда не уменьшаться
    // Используем Math.max, чтобы гарантировать, что прогресс не откатывается назад
    const newProgress = Math.max(currentProgress, Math.min(progress, 100));
    
    // Обновляем только если прогресс действительно увеличился
    if (newProgress > currentProgress) {
        currentProgress = newProgress;
        progressFill.style.width = `${currentProgress}%`;
        progressText.textContent = `${currentProgress}%`;
    }
    
    // Сообщение обновляем всегда (может меняться независимо от прогресса)
    if (message) {
        statusMessage.textContent = message;
    }
}

function showResult(result) {
    statusContainer.style.display = 'none';
    resultContainer.style.display = 'block';
    resultInfo.style.display = 'flex';
    
    // Сохраняем результат и task_id для экспорта
    currentResult = result;
    // currentTaskId уже должен быть установлен, но убеждаемся
    if (!currentTaskId && result.task_id) {
        currentTaskId = result.task_id;
    }
    
    // Форматируем результат
    const formattedResult = formatResult(result.result);
    resultContent.textContent = formattedResult;
    
    // Отображаем стоимость анализа
    console.log('Попытка отобразить стоимость:', result.cost, typeof result.cost);
    
    const costValueNum = result.cost !== null && result.cost !== undefined && 
                        result.cost !== 'None' && result.cost !== '' && 
                        !isNaN(parseFloat(result.cost)) ? parseFloat(result.cost) : null;
    
    if (costValueNum !== null) {
        costValue.textContent = `${costValueNum.toFixed(2)} руб.`;
        costInfo.style.display = 'inline-flex';
        console.log('Стоимость отображена:', costValueNum);
    } else {
        costValue.textContent = 'Недоступно';
        costInfo.style.display = 'inline-flex';
        console.log('Стоимость недоступна');
    }
    
    // Показываем кнопки действий
    resultActions.style.display = 'flex';
    
    // Прокручиваем к результатам
    resultInfo.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function formatResult(text) {
    // Простое форматирование текста
    return text;
}

function showError(message) {
    statusContainer.style.display = 'none';
    errorContainer.style.display = 'block';
    errorText.textContent = message;
    
    // Прокручиваем к ошибке
    errorContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

function resetForm() {
    submitBtn.disabled = false;
    submitBtn.querySelector('.btn-text').style.display = 'block';
    submitBtn.querySelector('.btn-loader').style.display = 'none';
    urlInput.disabled = false;
    currentTaskId = null;
}

// Обработчик экспорта в DOCX
exportDocxBtn.addEventListener('click', async () => {
    // Используем task_id из результата или сохраненный currentTaskId
    const taskIdForExport = currentResult?.task_id || currentTaskId;
    
    if (!taskIdForExport || !currentResult) {
        showError('Нет данных для экспорта');
        return;
    }
    
    try {
        exportDocxBtn.disabled = true;
        exportDocxBtn.querySelector('span').textContent = '⏳ Экспорт...';
        
        const response = await fetch(`/api/export/${taskIdForExport}`, {
            method: 'GET',
        });
        
        if (!response.ok) {
            // Пытаемся получить JSON ошибки
            let errorData;
            try {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    errorData = await response.json();
                } else {
                    throw new Error(`Ошибка ${response.status}: ${response.statusText}`);
                }
            } catch (e) {
                throw new Error(`Ошибка при экспорте: ${response.status} ${response.statusText}`);
            }
            throw new Error(errorData.error || 'Ошибка при экспорте');
        }
        
        // Получаем файл
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `analysis_${currentResult.company_name || 'report'}_${new Date().toISOString().split('T')[0]}.docx`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
        
        exportDocxBtn.querySelector('span').textContent = '✅ Экспортировано';
        setTimeout(() => {
            exportDocxBtn.querySelector('span').textContent = '📄 Экспорт в DOCX';
            exportDocxBtn.disabled = false;
        }, 2000);
        
    } catch (error) {
        showError(`Ошибка экспорта: ${error.message}`);
        exportDocxBtn.querySelector('span').textContent = '📄 Экспорт в DOCX';
        exportDocxBtn.disabled = false;
    }
});

// Обработчик нового анализа
newAnalysisBtn.addEventListener('click', () => {
    // Скрываем результаты и ошибки
    resultContainer.style.display = 'none';
    resultInfo.style.display = 'none';
    errorContainer.style.display = 'none';
    
    // Очищаем данные
    currentTaskId = null;
    currentResult = null;
    resultContent.textContent = '';
    
    // Очищаем поле ввода и фокусируемся
    urlInput.value = '';
    urlInput.focus();
    
    // Прокручиваем к форме
    form.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
});

// Закрытие результатов и ошибок (если есть кнопка закрытия)
const closeResultBtn = document.getElementById('closeResult');
if (closeResultBtn) {
    closeResultBtn.addEventListener('click', () => {
        resultContainer.style.display = 'none';
        resultInfo.style.display = 'none';
        // Очищаем поле ввода для новой итерации
        urlInput.value = '';
        urlInput.focus();
    });
}

document.getElementById('closeError').addEventListener('click', () => {
    errorContainer.style.display = 'none';
});

// Главный экран: кнопка «MD → DOCX» открывает модалку конвертера
if (btnMdToDocx && toolModalOverlay) {
    btnMdToDocx.addEventListener('click', () => {
        toolModalOverlay.style.display = 'flex';
        toolModalOverlay.setAttribute('aria-hidden', 'false');
    });
}

// Кнопка «Анализ корпоративного сайта» — показываем секцию анализа
if (btnAnalysis && instrumentsBlock && analysisSection) {
    btnAnalysis.addEventListener('click', () => {
        instrumentsBlock.style.display = 'none';
        analysisSection.style.display = 'block';
    });
}

// «К инструментам» — возврат на главный экран с двумя кнопками
if (backToInstrumentsBtn && instrumentsBlock && analysisSection) {
    backToInstrumentsBtn.addEventListener('click', () => {
        instrumentsBlock.style.display = 'block';
        analysisSection.style.display = 'none';
        errorContainer.style.display = 'none';
    });
}
if (toolModalCloseBtn && toolModalOverlay) {
    toolModalCloseBtn.addEventListener('click', () => {
        toolModalOverlay.style.display = 'none';
        toolModalOverlay.setAttribute('aria-hidden', 'true');
    });
}
if (toolModalOverlay) {
    toolModalOverlay.addEventListener('click', (e) => {
        if (e.target === toolModalOverlay) {
            toolModalOverlay.style.display = 'none';
            toolModalOverlay.setAttribute('aria-hidden', 'true');
        }
    });
}

// MD → DOCX: по клику на кнопку в модалке — выбор файла
if (toolModalMdToDocxBtn && mdFileInput) {
    toolModalMdToDocxBtn.addEventListener('click', () => {
        mdFileInput.value = '';
        mdFileInput.click();
    });
}
// После выбора .md — отправка на сервер и скачивание DOCX
if (mdFileInput) {
    mdFileInput.addEventListener('change', async () => {
        const file = mdFileInput.files[0];
        if (!file) return;
        const btn = toolModalMdToDocxBtn;
        if (btn) btn.disabled = true;
        try {
            const formData = new FormData();
            formData.append('file', file);
            const response = await fetch('/api/convert/md-to-docx', {
                method: 'POST',
                body: formData,
            });
            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (toolModalOverlay) {
                    toolModalOverlay.style.display = 'none';
                    toolModalOverlay.setAttribute('aria-hidden', 'true');
                }
                if (contentType && contentType.includes('application/json')) {
                    const err = await response.json();
                    showError(err.error || 'Ошибка конвертации');
                } else {
                    showError(`Ошибка ${response.status}: ${response.statusText}`);
                }
                return;
            }
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            const name = response.headers.get('content-disposition');
            let filename = (file.name || 'document').replace(/\.md$/i, '') + '_converted.docx';
            if (name && name.includes('filename=')) {
                const m = name.match(/filename\*?=['"]?(?:UTF-8'')?([^'";\n]+)/i) || name.match(/filename=['"]?([^'";\n]+)/);
                if (m) filename = m[1].trim();
            }
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
            if (toolModalOverlay) {
                toolModalOverlay.style.display = 'none';
                toolModalOverlay.setAttribute('aria-hidden', 'true');
            }
        } catch (e) {
            if (toolModalOverlay) {
                toolModalOverlay.style.display = 'none';
                toolModalOverlay.setAttribute('aria-hidden', 'true');
            }
            showError('Ошибка при конвертации: ' + (e.message || String(e)));
        } finally {
            mdFileInput.value = '';
            if (btn) btn.disabled = false;
        }
    });
}
