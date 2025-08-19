/**
 * PUSTAKA LOGIKA NOTIFIKASI & DROPDOWN
 * File ini hanya berisi definisi fungsi (blueprint).
 * File ini tidak menjalankan kode apa pun sendirian.
 */

/**
 * Menutup semua dropdown yang terdaftar, kecuali yang dikecualikan.
 * @param {string|null} excludeMenuId - (Opsional) ID dari menu yang tidak akan ditutup.
 */
function closeAllDropdowns(excludeMenuId = null) {
  // Daftar semua dropdown yang bisa dikelola oleh fungsi ini.
  const allDropdowns = [
    { menuId: "user-menu" },
    { menuId: "notification-dropdown" },
    // Tambahkan dropdown lain di sini jika ada.
  ];

  allDropdowns.forEach(({ menuId }) => {
    const menu = document.getElementById(menuId);
    if (menu && menu.id !== excludeMenuId && !menu.classList.contains("hidden")) {
      menu.classList.add("hidden");
      menu.style.transform = "scale(0.95)";
      menu.style.opacity = "0";

      // Juga atur ulang chevron jika ada
      const button = document.querySelector(`[aria-controls="${menuId}"]`);
      if (button) {
        const chevron = button.querySelector(".fa-chevron-down");
        if (chevron) {
          chevron.classList.remove("rotate-180");
        }
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

  if (!button || !menu) {
    // Pesan ini akan muncul di console jika tombol atau menu tidak ditemukan
    console.warn(`Elemen tidak ditemukan untuk setupDropdown: buttonId=${buttonId}, menuId=${menuId}`);
    return;
  }

  // Menambahkan atribut untuk aksesibilitas dan relasi
  button.setAttribute("aria-haspopup", "true");
  button.setAttribute("aria-expanded", "false");
  button.setAttribute("aria-controls", menuId);

  const chevron = chevronId ? document.getElementById(chevronId) : null;

  button.addEventListener("click", (event) => {
    event.stopPropagation(); // Mencegah event 'click' window berjalan
    const isHidden = menu.classList.toggle("hidden");

    // Perbarui status aksesibilitas
    button.setAttribute("aria-expanded", !isHidden);

    // Jika dropdown dibuka, tutup semua dropdown lain
    if (!isHidden) {
      closeAllDropdowns(menuId);
    }

    if (chevron) {
      chevron.classList.toggle("rotate-180", !isHidden);
    }

    // Animasi
    requestAnimationFrame(() => {
      menu.style.transform = isHidden ? "scale(0.95)" : "scale(1)";
      menu.style.opacity = isHidden ? "0" : "1";
    });
  });
}

// PERHATIKAN: Blok "DOMContentLoaded" yang ada sebelumnya TELAH DIHAPUS TOTAL DARI FILE INI.
