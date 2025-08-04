document.addEventListener("DOMContentLoaded", function () {
  const loginForm = document.getElementById("login-form");
  const flashContainer = document.getElementById("flash-container");
  const submitButton = document.getElementById("submit-button");
  const submitButtonText = document.getElementById("submit-button-text");
  const successOverlay = document.getElementById("success-overlay");
  const successIcon = document.getElementById("success-icon");
  const successText = document.getElementById("success-text");
  const nikInput = document.getElementById("nik");
  const passwordInput = document.getElementById("password");

  // (REFACTORED) Event listener untuk submit form dengan async/await
  loginForm.addEventListener("submit", async function (e) {
    e.preventDefault();

    // Disable button dan tampilkan status loading
    submitButton.disabled = true;
    submitButtonText.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i>Memproses...';
    flashContainer.innerHTML = "";

    const formData = new FormData(loginForm);
    const csrfToken = document.querySelector('input[name="csrf_token"]').value;
    const loginUrl = loginForm.dataset.loginUrl; // Ambil URL dari atribut data-*

    try {
      const response = await fetch(loginUrl, {
        method: "POST",
        headers: { "X-CSRFToken": csrfToken },
        body: formData,
      });

      const data = await response.json();
      const isSuccess = response.ok;

      if (isSuccess && data.redirect_url) {
        // Tampilkan animasi sukses
        successOverlay.style.opacity = "1";
        successOverlay.style.visibility = "visible";
        setTimeout(() => (successIcon.style.transform = "scale(1)"), 50);
        setTimeout(() => {
          successText.style.transform = "translateY(0)";
          successText.style.opacity = "1";
        }, 150);
        // Arahkan ke halaman dashboard setelah animasi
        setTimeout(() => (window.location.href = data.redirect_url), 100);
      } else {
        // Tampilkan pesan error
        const errorMessage = `
          <div class="mb-4 p-4 rounded-lg text-sm bg-red-50 border border-red-200 text-red-700 flex items-center">
            <i class="fas fa-exclamation-triangle mr-2"></i>
            ${data.message}
          </div>
        `;
        flashContainer.innerHTML = errorMessage;
        // Aktifkan kembali tombol submit
        submitButton.disabled = false;
        submitButtonText.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Masuk';
      }
    } catch (error) {
      // Tangani error jaringan atau error lainnya
      console.error("Error:", error);
      const errorMessage = `
        <div class="mb-4 p-4 rounded-lg text-sm bg-red-50 border border-red-200 text-red-700 flex items-center">
          <i class="fas fa-wifi mr-2"></i>
          Terjadi kesalahan jaringan. Silakan coba lagi.
        </div>
      `;
      flashContainer.innerHTML = errorMessage;
      // Aktifkan kembali tombol submit
      submitButton.disabled = false;
      submitButtonText.innerHTML = '<i class="fas fa-sign-in-alt mr-2"></i>Masuk';
    }
  });

  // (TIDAK ADA PERUBAHAN) Logika untuk toggle password
  const togglePassword = document.getElementById("togglePassword");
  if (togglePassword) {
    togglePassword.addEventListener("click", function () {
      const type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
      passwordInput.setAttribute("type", type);
      const icon = this.querySelector("i");
      icon.classList.toggle("fa-eye");
      icon.classList.toggle("fa-eye-slash");
    });
  }

  // (TIDAK ADA PERUBAHAN) Logika untuk tombol akun demo
  const demoButtons = document.querySelectorAll(".demo-account-btn");
  demoButtons.forEach((button) => {
    button.addEventListener("click", function () {
      nikInput.value = this.dataset.nik;
      passwordInput.value = this.dataset.password;
      setTimeout(() => submitButton.focus(), 100);
    });
  });

  nikInput.focus();
});
