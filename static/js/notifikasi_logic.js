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
    if (!menu) return; // Lewati jika menu tidak ada di halaman ini

    const chevron = chevronId ? document.getElementById(chevronId) : null;

    // Jika menu ada, tidak dikecualikan, dan sedang terbuka.
    if (menu.id !== excludeMenuId && !menu.classList.contains("hidden")) {
      menu.classList.add("hidden");
      menu.style.transform = "scale(0.95)";
      menu.style.opacity = "0";
      if (chevron) {
        chevron.classList.remove("rotate-180");
      }
    }
  });
}

/**
 * Mengatur fungsionalitas buka/tutup untuk sebuah dropdown.
 * @param {string} buttonId - ID dari elemen tombol.
 * @param {string} menuId - ID dari elemen menu dropdown.
 * @param {string|null} chevronId - (Opsional) ID dari ikon chevron untuk dirotasi.
 */
function setupDropdown(buttonId, menuId, chevronId = null) {
  const button = document.getElementById(buttonId);
  const menu = document.getElementById(menuId);
  if (!button || !menu) return; // Hentikan jika elemen tidak ditemukan

  const chevron = chevronId ? document.getElementById(chevronId) : null;

  button.addEventListener("click", (event) => {
    event.stopPropagation();
    const isHidden = menu.classList.toggle("hidden");

    if (!isHidden) {
      closeAllDropdowns(menuId);
    }

    if (chevron) {
      chevron.classList.toggle("rotate-180", !isHidden);
    }

    requestAnimationFrame(() => {
      menu.style.transform = isHidden ? "scale(0.95)" : "scale(1)";
      menu.style.opacity = isHidden ? "0" : "1";
    });
  });
}

// Event listener ini akan berjalan setelah DOM siap
document.addEventListener("DOMContentLoaded", () => {
  // Menambahkan event listener ke window untuk menutup dropdown saat mengklik di luar.
  window.addEventListener("click", (event) => {
    const isClickInsideDropdown = event.target.closest("#user-menu-button, #user-menu, #notification-button, #notification-dropdown");
    if (!isClickInsideDropdown) {
      closeAllDropdowns();
    }
  });
});
