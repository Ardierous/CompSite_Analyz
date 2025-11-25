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

let currentTaskId = null;
let statusCheckInterval = null;

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const url = urlInput.value.trim();
    if (!url) return;
    
    // Скрываем предыдущие результаты
    resultContainer.style.display = 'none';
    errorContainer.style.display = 'none';
    
    // Блокируем форму
    submitBtn.disabled = true;
    submitBtn.querySelector('.btn-text').style.display = 'none';
    submitBtn.querySelector('.btn-loader').style.display = 'block';
    urlInput.disabled = true;
    
    // Показываем статус
    statusContainer.style.display = 'block';
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
            const data = await response.json();
            
            if (data.status === 'completed') {
                clearInterval(statusCheckInterval);
                showResult(data.result);
                resetForm();
            } else if (data.status === 'error') {
                clearInterval(statusCheckInterval);
                showError(data.message);
                resetForm();
            } else if (data.status === 'processing') {
                updateProgress(data.progress, data.message);
            }
        } catch (error) {
            clearInterval(statusCheckInterval);
            showError('Ошибка при проверке статуса');
            resetForm();
        }
    }, 2000); // Проверяем каждые 2 секунды
}

function updateProgress(progress, message) {
    progressFill.style.width = `${progress}%`;
    progressText.textContent = `${progress}%`;
    statusMessage.textContent = message;
}

function showResult(result) {
    statusContainer.style.display = 'none';
    resultContainer.style.display = 'block';
    
    // Форматируем результат
    const formattedResult = formatResult(result.result);
    resultContent.textContent = formattedResult;
    
    // Прокручиваем к результату
    resultContainer.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
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

// Закрытие результатов и ошибок
document.getElementById('closeResult').addEventListener('click', () => {
    resultContainer.style.display = 'none';
});

document.getElementById('closeError').addEventListener('click', () => {
    errorContainer.style.display = 'none';
});

