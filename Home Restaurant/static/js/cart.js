window.onload = function() {
    fetchCartItems();
    getCustomerId();
};

function fetchCartItems() {
    const customerId = localStorage.getItem("customer_id");
    const url = `/get_cart_items?customer_id=${customerId}`;

    const loadingMessage = document.getElementById('loading-message');
    loadingMessage.style.display = 'block';

    fetch(url)
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to fetch cart items');
        }
        return response.json();
    })
    .then(data => {
        if (data.length === 0) {
            document.getElementById('empty-cart-message').style.display = 'block';
        } else {
            const productIds = data.map((item) => item.id);

            document.getElementById("product_ids").value = productIds.join(",");
            displayCartItems(data);
            updateCartInfo(data);
        }
        loadingMessage.style.display = 'none';
    })
    .catch(error => {
        console.error('Error fetching cart items:', error);
        loadingMessage.textContent = 'Ошибка при загрузке товаров';
    });
}

function displayCartItems(items) {
    const cartItemsDiv = document.querySelector('.product__container');
    cartItemsDiv.innerHTML = '';

    items.forEach(item => {
        const productCard = document.createElement('article');
        productCard.classList.add('product__card');

        const productImg = document.createElement('img');
        productImg.src = item.image;
        productImg.alt = item.name;
        productImg.classList.add('product__img');
        productImg.id = 'Image-card';
        productCard.appendChild(productImg);

        const productTitle = document.createElement('h3');
        productTitle.textContent = item.name;
        productTitle.classList.add('product__title');
        productCard.appendChild(productTitle);

        const productPrice = document.createElement('span');
        productPrice.textContent = `$${item.price}`;
        productPrice.classList.add('product__price');
        productCard.appendChild(productPrice);

        const productId = document.createElement('span');
        productId.textContent = `ID: ${item.id}`;
        productId.classList.add('product__price');
        productCard.appendChild(productId);

        const deleteButton = document.createElement('button');
        deleteButton.classList.add('button--flex', 'product__button');
        deleteButton.addEventListener('click', function() {
            deleteCartItem(item.id);
        });
        
        const addIcon = document.createElement('i');
        addIcon.classList.add('ri-delete-bin-line');
        deleteButton.appendChild(addIcon);

        productCard.appendChild(deleteButton);

        cartItemsDiv.appendChild(productCard);
    });
}

function deleteCartItem(productId) {
    const customerId = localStorage.getItem("customer_id");
    const url = `/delete_cart_item?customer_id=${customerId}&product_id=${productId}`;

    fetch(url, {
        method: 'DELETE'
    })
    .then(response => {
        if (!response.ok) {
            throw new Error('Failed to delete cart item');
        }
        return response.json();
    })
    .then(data => {
        fetchCartItems();
        showNotification('Товар успешно удален', 'success');
    })
    .catch(error => {
        console.error('Error deleting cart item:', error);
        showNotification('Ошибка при удалении товара', 'error');
    });
}

function updateCartInfo(items) {
    const totalItemsCount = items.length;
    const totalPrice = items.reduce((total, item) => total + parseFloat(item.price), 0);

    document.getElementById('total-items-count').textContent = totalItemsCount;
    document.getElementById('total-price-value').textContent = `$${totalPrice.toFixed(2)}`;
    document.getElementById('total_items').value = totalItemsCount;
    document.getElementById('total_price').value = `$${totalPrice.toFixed(2)}`;
}

function getCustomerId() {
    var customerID = localStorage.getItem("customer_id");
    document.getElementById("customerID").value = customerID;
}

function showNotification(message, type) {
    const notificationDiv = document.getElementById('notification');
    notificationDiv.textContent = message;
    notificationDiv.className = `notification ${type}`;
    notificationDiv.style.display = 'block';

    setTimeout(() => {
        notificationDiv.style.display = 'none';
    }, 3000);
}

function sendData() {
    const customerID = document.getElementById('customerID').value;
    const productIDs = document.getElementById('product_ids').value;
    const totalItems = document.getElementById('total_items').value;
    const totalPrice = document.getElementById('total_price').value;

    const data = {
        customerID: customerID,
        productIDs: productIDs,
        totalItems: totalItems,
        totalPrice: totalPrice
    };

    fetch('/submit_order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            showNotification(data.message, 'success');
            window.location.href = '/thank-you';
        } else {
            showNotification(data.message, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showNotification('Ошибка запроса', 'error');
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const button = document.getElementById('key-cart-button');
    button.addEventListener('click', () => {
        const keyInput = document.getElementById('key-cart');
        const key = keyInput.value;

        fetch('/check_key', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ key: key })
        })
        .then(response => response.json())
        .then(data => {
            button.textContent = data.message;
            if (data.status === 'success') {
                button.style.backgroundColor = 'green';
                sendData()
            } else {
                button.style.backgroundColor = 'red';
            }
        })
        .catch(error => {
            console.error('Error:', error);
            button.textContent = 'Ошибка запроса';
            button.style.backgroundColor = 'orange';
        });
    });
});

var modal = document.getElementById("modal-view-photo-card");
var modalImg = document.getElementById("modal-view-photo-card-img");
var captionText = document.getElementById("modal-view-photo-card-caption");

var images = document.querySelectorAll("img[id^='Image-card']");
images.forEach(function(img) {
    img.onclick = function() {
        modal.style.display = "block";
        modalImg.src = this.src;
        captionText.innerHTML = this.alt;
    }
});

var span = document.getElementsByClassName("modal-view-photo-card-close")[0];

span.onclick = function() { 
    modal.style.display = "none";
}

modal.onclick = function(event) {
    if (event.target === modal) {
        modal.style.display = "none";
    }
}