window.onload = function () {
  const customerId = getCustomerId();
};

function getCustomerId() {
  let customerId = localStorage.getItem("customer_id");
  if (!customerId) {
    customerId = uuidv4();
    localStorage.setItem("customer_id", customerId);
  }
  return customerId;
}

function uuidv4() {
    return "10000000-1000-4000-8000-100000000000".replace(/[018]/g, (c) =>
      (
        c ^
        (crypto.getRandomValues(new Uint8Array(1))[0] & (15 >> (c / 4)))
      ).toString(16)
    );
}

function addToCart(productId) {
  const customerId = getCustomerId();
  const url = "/add_to_cart";

  const data = JSON.stringify({
    product_id: productId,
    customer_id: customerId,
    });

  fetch(url, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: data,
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Failed to add to cart");
      }
      return response.json();
    })
    .then((data) => {
      showNotification("Товар успешно добавлен в корзину", "success");
    })
    .catch((error) => {
      console.error("Error adding to cart:", error);
      showNotification("Произошла ошибка при добавлении товара", "error");
    });
}

function showNotification(message, type) {
  const notification = document.getElementById("notification");
  notification.textContent = message;
  notification.classList.add(type);
  notification.style.display = "block";

  setTimeout(function () {
    notification.style.display = "none";
    notification.classList.remove(type);
  }, 2000); // Скрыть уведомление через 2 секунды
}

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