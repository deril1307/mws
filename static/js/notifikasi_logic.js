/*
File: static/js/notifikasi/notifikasi_logic.js
Deskripsi: Berisi logika JavaScript untuk menangani semua komponen dropdown di aplikasi.
*/

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

  if (!button || !menu) return;

  button.addEventListener("click", (event) => {
    event.stopPropagation();
    const isHidden = menu.classList.toggle("hidden");

    if (!isHidden) {
      // Jika dropdown ini dibuka, tutup semua dropdown lain
      closeAllDropdowns(menuId);
    }

    if (chevron) {
      chevron.classList.toggle("rotate-180", !isHidden);
    }

    // Animasi
    menu.style.transform = isHidden ? "scale(0.95)" : "scale(1)";
    menu.style.opacity = isHidden ? "0" : "1";
  });
}

/**
 * Menutup semua dropdown yang terbuka, kecuali yang dikecualikan.
 * @param {string|null} excludeMenuId - (Opsional) ID dari menu yang tidak akan ditutup.
 */
function closeAllDropdowns(excludeMenuId = null) {
  const allDropdowns = [
    { menu: document.getElementById("user-menu"), chevron: document.getElementById("user-menu-chevron") },
    { menu: document.getElementById("notification-dropdown"), chevron: null },
  ];

  allDropdowns.forEach((item) => {
    if (item.menu && item.menu.id !== excludeMenuId && !item.menu.classList.contains("hidden")) {
      item.menu.classList.add("hidden");
      item.menu.style.transform = "scale(0.95)";
      item.menu.style.opacity = "0";
      if (item.chevron) {
        item.chevron.classList.remove("rotate-180");
      }
    }
  });
}
