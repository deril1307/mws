/*
File: static/js/notifikasi/notifikasi_logic.js
Deskripsi: Berisi logika JavaScript untuk menangani semua komponen dropdown di aplikasi,
           termasuk menu user dan notifikasi.
*/

document.addEventListener("DOMContentLoaded", () => {
  /**
   * Mengatur fungsionalitas buka/tutup untuk sebuah dropdown.
   * @param {string} buttonId - ID dari elemen tombol.
   * @param {string} menuId - ID dari elemen menu dropdown.
   * @param {string|null} chevronId - (Opsional) ID dari ikon chevron untuk dirotasi.
   */
  function setupDropdown(buttonId, menuId, chevronId = null) {
    const button = document.getElementById(buttonId);
    const menu = document.getElementById(menuId);
    const chevron = chevronId ? document.getElementById(chevronId) : null;

    if (!button || !menu) {
      // Jika salah satu elemen tidak ditemukan, hentikan eksekusi untuk dropdown ini.
      // console.warn(`Dropdown elements not found: buttonId=${buttonId}, menuId=${menuId}`);
      return;
    }

    button.addEventListener("click", (event) => {
      event.stopPropagation(); // Mencegah event 'click' di window langsung menutup menu.

      const isHidden = menu.classList.toggle("hidden");

      // Tutup semua dropdown lain jika dropdown ini dibuka.
      if (!isHidden) {
        closeAllDropdowns(menuId);
      }

      // Atur rotasi chevron jika ada.
      if (chevron) {
        chevron.classList.toggle("rotate-180", !isHidden);
      }

      // Atur animasi transisi.
      requestAnimationFrame(() => {
        menu.style.transform = isHidden ? "scale(0.95)" : "scale(1)";
        menu.style.opacity = isHidden ? "0" : "1";
      });
    });
  }

  /**
   * Menutup semua dropdown yang terbuka, kecuali yang dikecualikan.
   * @param {string|null} excludeMenuId - (Opsional) ID dari menu yang tidak akan ditutup.
   */
  function closeAllDropdowns(excludeMenuId = null) {
    // Daftar semua dropdown yang ada di aplikasi.
    const allDropdowns = [
      { menuId: "user-menu", chevronId: "user-menu-chevron" },
      { menuId: "notification-dropdown", chevronId: null },
      // Tambahkan dropdown lain di sini jika ada di masa depan.
    ];

    allDropdowns.forEach(({ menuId, chevronId }) => {
      const menu = document.getElementById(menuId);
      const chevron = chevronId ? document.getElementById(chevronId) : null;

      // Jika menu ada, tidak dikecualikan, dan sedang terbuka.
      if (menu && menu.id !== excludeMenuId && !menu.classList.contains("hidden")) {
        menu.classList.add("hidden");
        menu.style.transform = "scale(0.95)";
        menu.style.opacity = "0";
        if (chevron) {
          chevron.classList.remove("rotate-180");
        }
      }
    });
  }

  // --- Inisialisasi Semua Dropdown ---
  setupDropdown("user-menu-button", "user-menu", "user-menu-chevron");
  setupDropdown("notification-button", "notification-dropdown");

  // Menambahkan event listener ke window untuk menutup dropdown saat mengklik di luar.
  window.addEventListener("click", (event) => {
    // Cek apakah target klik bukan bagian dari tombol atau menu dropdown manapun.
    const isClickInsideDropdown = event.target.closest("#user-menu-button, #user-menu, #notification-button, #notification-dropdown");

    if (!isClickInsideDropdown) {
      closeAllDropdowns();
    }
  });
});
