document.getElementById('loginButton').addEventListener('click', () => {
    fetch('/get_hash')
        .then(response => response.json())
        .then(data => {
            const qrCode = document.getElementById('qrCode');
            qrCode.src = `https://api.qrserver.com/v1/create-qr-code/?data=${data.hash}&size=200x200`;
            document.getElementById('loginForm').style.display = 'block';
            checkAuthStatus(data.hash);
        });
});

function checkAuthStatus(hash) {
    const statusMessage = document.getElementById('statusMessage');
    const lastSixChars = hash.slice(-6);
    statusMessage.textContent = `Ожидание авторизации... Хеш: ${lastSixChars}`;

    const interval = setInterval(() => {
        fetch(`/check_auth_status?hash=${hash}`)
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    statusMessage.textContent = 'Успешная авторизация';
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 2000);
                    clearInterval(interval);
                } else if (data.status === 'error') {
                    if (data.regenerate) {
                        statusMessage.textContent = 'Время истекло. Генерация нового QR кода...';
                        fetch('/regenerate_hash', { method: 'POST' })
                            .then(response => response.json())
                            .then(data => {
                                const qrCode = document.getElementById('qrCode');
                                qrCode.src = `https://api.qrserver.com/v1/create-qr-code/?data=${data.hash}&size=200x200`;
                                statusMessage.textContent = `Новый QR код сгенерирован. Ожидание авторизации... Хеш: ${data.hash.slice(-6)}`;
                                checkAuthStatus(data.hash);
                            });
                    } else {
                        statusMessage.textContent = 'Ошибка: ' + data.message;
                        clearInterval(interval);
                    }
                }
            });
    }, 5000);
}