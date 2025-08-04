/**
 * Fungsi fetch generik untuk mengirim data ke server menggunakan metode POST.
 * Fungsi ini tidak diubah karena perannya adalah sebagai 'promise producer'
 * yang akan digunakan oleh fungsi async/await lainnya.
 * @param {string} endpoint - Alamat URL tujuan di server.
 * @param {object} data - Objek JavaScript yang akan dikirim sebagai JSON.
 * @returns {Promise<Response>} - Mengembalikan promise dari proses fetch.
 */
function updateField(endpoint, data) {
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
  return fetch(endpoint, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-CSRFToken": csrfToken,
    },
    body: JSON.stringify(data),
  });
}

/**
 * Menampilkan notifikasi sementara di pojok kanan atas layar.
 * @param {string} message - Pesan yang akan ditampilkan.
 * @param {'success'|'error'} type - Tipe notifikasi.
 */
function showNotification(message, type) {
  const notification = document.createElement("div");
  const bgColor = type === "success" ? "bg-green-500" : "bg-red-500";
  notification.className = `fixed top-4 right-4 px-4 py-2 rounded-lg text-white z-50 shadow-lg animate-pulse ${bgColor}`;
  notification.textContent = message;
  document.body.appendChild(notification);

  setTimeout(() => {
    notification.remove();
  }, 3000);
}

/**
 * (REFACTORED) Fungsi untuk memproses penandatanganan dokumen menggunakan async/await.
 * Kode ini lebih mudah dibaca dan error handling-nya lebih terstruktur.
 * @param {string} type - Tipe tanda tangan ('prepared', 'approved', 'verified').
 * @param {string} partId - ID dari MWS yang akan ditandatangani.
 */
async function signDocument(type, partId) {
  if (!confirm(`Apakah Anda yakin ingin menandatangani sebagai "${type}"?`)) {
    return;
  }
  try {
    const response = await updateField("/sign_document", { type, partId });
    const data = await response.json();
    if (data.success) {
      showNotification("Maintenance Work Sheet berhasil di Approved.", "success");
      setTimeout(() => location.reload(), 500);
    } else {
      showNotification("Gagal: " + (data.error || "Aksi tidak diizinkan."), "error");
    }
  } catch (error) {
    console.error("Error:", error);
    showNotification("Terjadi kesalahan pada jaringan.", "error");
  }
}

/**
 * Mengubah visibilitas menu mobile (hamburger menu).
 */
function toggleMobileMenu() {
  const menu = document.getElementById("mobile-menu");
  if (menu) {
    menu.classList.toggle("hidden");
  }
}

/**
 * Memastikan semua tabel dengan kelas .worksheet-table bisa di-scroll secara horizontal
 * pada layar kecil dengan membungkusnya dalam sebuah div.
 */
function initResponsiveTables() {
  const tables = document.querySelectorAll(".worksheet-table");
  tables.forEach((table) => {
    if (table.parentElement.classList.contains("overflow-x-auto")) return;
    const wrapper = document.createElement("div");
    wrapper.className = "overflow-x-auto";
    table.parentNode.insertBefore(wrapper, table);
    wrapper.appendChild(table);
  });
}
document.addEventListener("DOMContentLoaded", function () {
  initResponsiveTables();
});
