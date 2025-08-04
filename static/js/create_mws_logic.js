document.addEventListener("DOMContentLoaded", function () {
  // --- FUNGSI NOTIFIKASI (TIDAK ADA PERUBAHAN) ---
  function showNotification(message, type = "success") {
    const existingNotification = document.getElementById("toast-notification");
    if (existingNotification) {
      existingNotification.remove();
    }
    const icons = {
      success: `<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
      error: `<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
    };
    const styles = {
      success: { bg: "bg-green-500", title: "Berhasil!" },
      error: { bg: "bg-red-600", title: "Terjadi Kesalahan!" },
    };

    const notification = document.createElement("div");
    notification.id = "toast-notification";
    notification.className = `fixed top-5 right-5 flex items-center w-full max-w-xs p-4 space-x-4 text-white ${styles[type].bg} rounded-xl shadow-2xl z-50 transition-all duration-300 ease-in-out transform translate-x-full opacity-0`;
    notification.innerHTML = `
      <div class="flex-shrink-0">${icons[type]}</div>
      <div class="pl-2">
        <div class="text-sm font-bold">${styles[type].title}</div>
        <div class="text-sm font-normal">${message}</div>
      </div>
    `;
    document.body.appendChild(notification);
    requestAnimationFrame(() => {
      notification.classList.remove("translate-x-full", "opacity-0");
      notification.classList.add("translate-x-0", "opacity-100");
    });
    setTimeout(() => {
      notification.classList.remove("translate-x-0", "opacity-100");
      notification.classList.add("translate-x-full", "opacity-0");
      setTimeout(() => notification.remove(), 300);
    }, 4000);
  }

  // SCRIPT SUBMIT FORM (REFACTORED DENGAN ASYNC/AWAIT)
  const createMwsForm = document.getElementById("createMwsForm");
  if (createMwsForm) {
    // Jadikan fungsi callback dari event listener ini sebagai 'async'
    createMwsForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const data = {};
      for (let [key, value] of formData.entries()) {
        if (key !== "csrf_token") {
          data[key] = value;
        }
      }
      const csrfToken = document.querySelector('input[name="csrf_token"]').value;

      // Gunakan try...catch untuk menangani semua kemungkinan error
      try {
        const response = await fetch("/create_mws", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.success) {
          showNotification("MWS berhasil dibuat!", "success");
          setTimeout(() => {
            window.location.href = "/mws/" + result.partId;
          }, 500);
        } else {
          showNotification(result.error || "Gagal menyimpan data.", "error");
        }
      } catch (error) {
        console.error("Error:", error);
        showNotification("Tidak dapat terhubung ke server.", "error");
      }
    });
  }
});
