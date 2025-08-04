// --- FUNGSI GLOBAL ---
// Fungsi-fungsi ini tidak perlu diubah karena bersifat sinkron (mengatur tampilan UI).

/**
 * Beralih antara mode lihat dan mode edit pada form informasi MWS.
 * @param {boolean} isEditing - True untuk mode edit, false untuk mode lihat.
 */
window.toggleEditMode = function (isEditing) {
  const viewElements = document.querySelectorAll(".mws-info-view");
  const editInputs = document.querySelectorAll(".mws-info-edit");
  const editButton = document.getElementById("edit-mws-btn");
  const finishButton = document.getElementById("finish-mws-btn");

  viewElements.forEach((el) => el.classList.toggle("hidden", isEditing));
  editInputs.forEach((el) => el.classList.toggle("hidden", !isEditing));

  if (editButton) editButton.classList.toggle("hidden", isEditing);
  if (finishButton) finishButton.classList.toggle("hidden", !isEditing);
};

/**
 * Menampilkan modal konfirmasi sebelum menyimpan perubahan.
 * @param {string} partId - ID dari part yang informasinya akan disimpan.
 */
window.saveMwsInfo = function (partId) {
  const modal = document.getElementById("confirmation-modal");
  const saveButton = document.getElementById("modal-btn-save");

  // Menyimpan partId ke tombol "Simpan" agar bisa diambil nanti saat event click
  if (saveButton) {
    saveButton.dataset.partId = partId;
  }
  if (modal) {
    modal.classList.remove("hidden");
  }
};

// --- LOGIKA INTERNAL & EVENT LISTENERS ---
// Kode di bawah ini akan berjalan setelah seluruh halaman siap.

document.addEventListener("DOMContentLoaded", () => {
  let toastTimer;

  /**
   * Menampilkan notifikasi toast di pojok layar.
   * @param {string} message - Pesan yang akan ditampilkan.
   * @param {'success'|'error'} type - Tipe notifikasi.
   */
  function showToast(message, type = "success") {
    const toast = document.getElementById("toast-notification");
    const toastContent = document.getElementById("toast-content");
    if (!toast || !toastContent) return;

    clearTimeout(toastTimer);

    let iconHtml =
      type === "success"
        ? `<div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-green-500 bg-green-100 rounded-lg"><i class="fas fa-check"></i></div>`
        : `<div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-red-500 bg-red-100 rounded-lg"><i class="fas fa-exclamation-triangle"></i></div>`;

    toastContent.innerHTML = `${iconHtml}<div class="ml-3 text-sm font-normal">${message}</div>`;
    toast.classList.add("show");

    toastTimer = setTimeout(() => {
      toast.classList.remove("show");
    }, 3000);
  }

  /**
   * (REFACTORED) Fungsi untuk mengeksekusi penyimpanan data menggunakan async/await.
   * @param {string} partId - ID dari part yang akan diupdate.
   */
  async function executeSave(partId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    const editInputs = document.querySelectorAll(".mws-info-edit");
    const updatedData = { partId: partId };

    editInputs.forEach((input) => {
      updatedData[input.dataset.field] = input.value;
    });

    try {
      // Menunggu (await) response dari server
      const response = await fetch("/update_mws_info", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
        body: JSON.stringify(updatedData),
      });

      // Menunggu (await) data JSON selesai di-parsing
      const data = await response.json();

      if (data.success) {
        showToast("Informasi MWS berhasil diperbarui.", "success");

        // Memperbarui tampilan UI dengan data baru
        const viewElements = document.querySelectorAll(".mws-info-view");
        editInputs.forEach((input) => {
          const fieldName = input.dataset.field;
          const viewEl = Array.from(viewElements).find((p) => p.nextElementSibling?.dataset.field === fieldName);
          if (viewEl) {
            viewEl.textContent = input.value || "N/A";
          }
        });

        const headerPartNumber = document.getElementById("header-part-number");
        if (headerPartNumber && updatedData.partNumber) {
          headerPartNumber.textContent = updatedData.partNumber;
        }

        window.toggleEditMode(false);
      } else {
        showToast("Error: " + data.error, "error");
      }
    } catch (error) {
      console.error("Error:", error);
      showToast("Terjadi kesalahan jaringan.", "error");
    }
  }

  // --- Menambahkan event listener untuk modal konfirmasi ---
  const modal = document.getElementById("confirmation-modal");
  const cancelButton = document.getElementById("modal-btn-cancel");
  const saveButton = document.getElementById("modal-btn-save");

  if (modal && cancelButton && saveButton) {
    // Sembunyikan modal jika tombol "Batal" diklik
    cancelButton.addEventListener("click", () => {
      modal.classList.add("hidden");
    });

    // Jalankan penyimpanan jika tombol "Yakin, Simpan" diklik
    saveButton.addEventListener("click", () => {
      const partId = saveButton.dataset.partId;
      if (partId) {
        executeSave(partId);
      }
      modal.classList.add("hidden");
    });

    // Sembunyikan modal jika klik di luar area konten modal
    modal.addEventListener("click", (event) => {
      if (event.target === modal) {
        modal.classList.add("hidden");
      }
    });
  }
});
