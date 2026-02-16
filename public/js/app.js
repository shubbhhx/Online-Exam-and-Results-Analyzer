(function () {
  const loader = document.getElementById("pageLoader");
  const toastContainer = document.getElementById("toastContainer");

  function showLoader() {
    if (!loader) return;
    loader.classList.add("is-visible");
  }

  function hideLoader() {
    if (!loader) return;
    loader.classList.remove("is-visible");
  }

  function showToast(type, message) {
    if (!toastContainer || !message) return;
    const toastEl = document.createElement("div");
    toastEl.className = "toast align-items-center text-bg-" + (type || "primary");
    toastEl.setAttribute("role", "alert");
    toastEl.setAttribute("aria-live", "assertive");
    toastEl.setAttribute("aria-atomic", "true");
    toastEl.innerHTML =
      '<div class="d-flex">' +
      '<div class="toast-body">' +
      message +
      "</div>" +
      '<button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>' +
      "</div>";
    toastContainer.appendChild(toastEl);
    const toast = new bootstrap.Toast(toastEl, { delay: 4000 });
    toast.show();
  }

  document.addEventListener("submit", (event) => {
    const form = event.target;
    if (form && form.dataset && form.dataset.showLoader === "true") {
      showLoader();
    }
  });

  function startLiveDateTime() {
    const target = document.getElementById("liveDateTime");
    if (!target) return;

    function updateClock() {
      const now = new Date();
      const dateText = now.toLocaleDateString("en-GB", {
        day: "2-digit",
        month: "short",
        year: "numeric"
      });
      const timeText = now.toLocaleTimeString("en-US", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: true
      });
      target.textContent = `${dateText} | ${timeText}`;
    }

    updateClock();
    setInterval(updateClock, 1000);
  }

  window.addEventListener("load", () => {
    const shouldShowPageLoader =
      document.body.getAttribute("data-page-loading") === "true";
    if (shouldShowPageLoader) {
      showLoader();
      setTimeout(hideLoader, 400);
    } else {
      hideLoader();
    }

    const toastMessage = document.body.getAttribute("data-toast-message") || "";
    const toastType = document.body.getAttribute("data-toast-type") || "";
    if (toastMessage) {
      showToast(toastType, toastMessage);
    }

    startLiveDateTime();
  });
})();
