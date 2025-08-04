/**
 * Beralih antara mode lihat dan mode edit pada form informasi MWS.
 * @param {boolean} isEditing - True untuk mode edit, false untuk mode lihat.
 */
window.toggleEditMode = function (isEditing) {
  const viewElements = document.querySelectorAll(".mws-info-view");
  const editInputs = document.querySelectorAll(".mws-info-edit");
  const editButton = document.getElementById("edit-mws-btn");
  const duplicateButton = document.getElementById("duplicate-mws-btn");
  const finishButton = document.getElementById("finish-mws-btn");
  viewElements.forEach((el) => el.classList.toggle("hidden", isEditing));
  editInputs.forEach((el) => el.classList.toggle("hidden", !isEditing));
  if (editButton) editButton.classList.toggle("hidden", isEditing);
  if (duplicateButton) duplicateButton.classList.toggle("hidden", isEditing);
  if (finishButton) finishButton.classList.toggle("hidden", !isEditing);
};

/**
 * Menampilkan modal konfirmasi sebelum menyimpan perubahan.
 * @param {string} partId - ID dari part yang informasinya akan disimpan.
 */
window.saveMwsInfo = function (partId) {
  const modal = document.getElementById("confirmation-modal");
  const saveButton = document.getElementById("modal-btn-save");
  if (saveButton) saveButton.dataset.partId = partId;
  if (modal) modal.classList.remove("hidden");
};

/**
 * (BARU) Menampilkan modal konfirmasi sebelum menduplikasi MWS.
 * @param {string} partId - ID dari part yang akan diduplikasi.
 */
window.confirmDuplicateMws = function (partId) {
  const modal = document.getElementById("duplicate-confirmation-modal");
  const confirmButton = document.getElementById("modal-btn-confirm-duplicate");
  if (confirmButton) confirmButton.dataset.partId = partId;
  if (modal) modal.classList.remove("hidden");
};

// --- LOGIKA INTERNAL & EVENT LISTENERS ---
document.addEventListener("DOMContentLoaded", () => {
  let toastTimer;

  function showToast(message, type = "success") {
    const toast = document.getElementById("toast-notification");
    const toastContent = document.getElementById("toast-content");
    if (!toast || !toastContent) return;

    clearTimeout(toastTimer);
    const iconHtml =
      type === "success"
        ? `<div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-green-500 bg-green-100 rounded-lg"><i class="fas fa-check"></i></div>`
        : `<div class="inline-flex items-center justify-center flex-shrink-0 w-8 h-8 text-red-500 bg-red-100 rounded-lg"><i class="fas fa-exclamation-triangle"></i></div>`;
    toastContent.innerHTML = `${iconHtml}<div class="ml-3 text-sm font-normal">${message}</div>`;
    toast.classList.add("show");
    toastTimer = setTimeout(() => toast.classList.remove("show"), 3000);
  }

  /**
   * Mengeksekusi penyimpanan data informasi MWS.
   * @param {string} partId - ID dari part yang akan diupdate.
   */
  async function executeSave(partId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    const updatedData = { partId: partId };
    document.querySelectorAll(".mws-info-edit").forEach((input) => {
      updatedData[input.dataset.field] = input.value;
    });

    try {
      const response = await fetch("/update_mws_info", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify(updatedData),
      });
      const data = await response.json();
      if (data.success) {
        showToast("Informasi MWS berhasil diperbarui.", "success");
        document.querySelectorAll(".mws-info-edit").forEach((input) => {
          const viewEl = document.querySelector(`.mws-info-view[data-field="${input.dataset.field}"]`);
          if (viewEl) viewEl.textContent = input.value || "N/A";
        });
        window.toggleEditMode(false);
      } else {
        showToast("Error: " + data.error, "error");
      }
    } catch (error) {
      console.error("Error:", error);
      showToast("Terjadi kesalahan jaringan.", "error");
    }
  }

  /**
   * (BARU) Mengeksekusi duplikasi MWS.
   * @param {string} originalPartId - ID dari part yang akan diduplikasi.
   */
  async function executeDuplicate(originalPartId) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    try {
      const response = await fetch(`/duplicate_mws/${originalPartId}`, {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      });
      const data = await response.json();
      if (data.success) {
        showToast("MWS berhasil diduplikasi. Mengalihkan...", "success");
        setTimeout(() => (window.location.href = data.redirect_url), 1500);
      } else {
        showToast("Error: " + data.error, "error");
      }
    } catch (error) {
      console.error("Error:", error);
      showToast("Terjadi kesalahan jaringan saat duplikasi.", "error");
    }
  }

  // Event listener untuk modal konfirmasi SIMPAN
  const saveModal = document.getElementById("confirmation-modal");
  if (saveModal) {
    document.getElementById("modal-btn-cancel").addEventListener("click", () => saveModal.classList.add("hidden"));
    document.getElementById("modal-btn-save").addEventListener("click", (e) => {
      executeSave(e.target.dataset.partId);
      saveModal.classList.add("hidden");
    });
    saveModal.addEventListener("click", (e) => e.target === saveModal && saveModal.classList.add("hidden"));
  }

  // Event listener untuk modal konfirmasi DUPLIKASI
  const duplicateModal = document.getElementById("duplicate-confirmation-modal");
  if (duplicateModal) {
    document.getElementById("modal-btn-cancel-duplicate").addEventListener("click", () => duplicateModal.classList.add("hidden"));
    document.getElementById("modal-btn-confirm-duplicate").addEventListener("click", (e) => {
      executeDuplicate(e.target.dataset.partId);
      duplicateModal.classList.add("hidden");
    });
    duplicateModal.addEventListener("click", (e) => e.target === duplicateModal && duplicateModal.classList.add("hidden"));
  }
});
