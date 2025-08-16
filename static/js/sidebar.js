// static/js/sidebar.js
document.addEventListener("DOMContentLoaded", function () {
  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebar-overlay");
  const toggleButton = document.getElementById("sidebar-toggle-button");

  // Pastikan semua elemen ada sebelum menambahkan event listener
  if (sidebar && sidebarOverlay && toggleButton) {
    // Fungsi untuk membuka sidebar
    const openSidebar = () => {
      sidebar.classList.remove("-translate-x-full");
      sidebarOverlay.classList.remove("hidden");
      document.body.style.overflow = "hidden"; // Mencegah scroll di background
    };

    // Fungsi untuk menutup sidebar
    const closeSidebar = () => {
      sidebar.classList.add("-translate-x-full");
      sidebarOverlay.classList.add("hidden");
      document.body.style.overflow = ""; // Mengembalikan scroll
    };

    // Event listener untuk tombol toggle
    toggleButton.addEventListener("click", (e) => {
      e.stopPropagation();
      if (sidebar.classList.contains("-translate-x-full")) {
        openSidebar();
      } else {
        closeSidebar();
      }
    });

    // Event listener untuk overlay (menutup sidebar saat diklik)
    sidebarOverlay.addEventListener("click", () => {
      closeSidebar();
    });

    // Menutup sidebar saat menekan tombol Escape
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !sidebar.classList.contains("-translate-x-full")) {
        closeSidebar();
      }
    });
  }
});
