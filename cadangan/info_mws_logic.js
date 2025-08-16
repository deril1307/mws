let toastTimer;

/**
 * Menampilkan notifikasi toast.
 * @param {string} message - Pesan yang akan ditampilkan.
 * @param {string} type - Tipe notifikasi ('success' atau 'error').
 */
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

// --- FUNGSI UNTUK MWS INFO ---
window.toggleEditMode = function (isEditing) {
  document.querySelectorAll(".mws-info-view").forEach((el) => el.classList.toggle("hidden", isEditing));
  document.querySelectorAll(".mws-info-edit").forEach((el) => el.classList.toggle("hidden", !isEditing));
  document.getElementById("edit-mws-btn")?.classList.toggle("hidden", isEditing);
  document.getElementById("duplicate-mws-btn")?.classList.toggle("hidden", isEditing);
  document.getElementById("finish-mws-btn")?.classList.toggle("hidden", !isEditing);
};

window.saveMwsInfo = function (partId) {
  const modal = document.getElementById("confirmation-modal");
  const saveButton = document.getElementById("modal-btn-save");
  if (saveButton) saveButton.dataset.partId = partId;
  if (modal) modal.classList.remove("hidden");
};

window.confirmDuplicateMws = function (partId) {
  const modal = document.getElementById("duplicate-confirmation-modal");
  const confirmButton = document.getElementById("modal-btn-confirm-duplicate");
  if (confirmButton) confirmButton.dataset.partId = partId;
  if (modal) modal.classList.remove("hidden");
};

// =====================================================================
// LOGIKA UNTUK LAMPIRAN
// =====================================================================

/**
 * Menampilkan atau menyembunyikan bagian lampiran.
 */
window.toggleAttachmentSection = function () {
  const section = document.getElementById("attachment-section");
  const button = document.getElementById("toggle-attachment-btn");
  if (!section || !button) return;

  const isVisible = !section.classList.contains("hidden");
  if (isVisible) {
    section.classList.add("hidden");
    button.innerHTML = `<i class="fas fa-paperclip mr-2"></i> Lampiran`;
  } else {
    section.classList.remove("hidden");
    button.innerHTML = `<i class="fas fa-chevron-up mr-2"></i> Tutup Lampiran`;
    section.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
};

/**
 * Merender daftar lampiran ke dalam DOM.
 */
function renderAttachmentList(partId, attachments, userIsAdmin) {
  const listContainer = document.getElementById("attachment-list");
  if (!listContainer) return;

  listContainer.innerHTML = "";

  if (attachments && attachments.length > 0) {
    document.getElementById("no-attachment-text")?.remove();
    attachments.forEach((att) => {
      const deleteButtonHtml = userIsAdmin
        ? `<button onclick="deleteAttachment('${partId}', '${att.public_id}')" class="text-red-500 hover:text-red-700 text-xs font-semibold" title="Hapus Lampiran">
             <i class="fas fa-trash"></i>
           </button>`
        : "";

      const elementId = `attachment-item-${att.public_id.replace(/[\/.]/g, "-")}`;

      const listItem = `
        <li id="${elementId}" class="flex items-center justify-between bg-gray-50 p-2 rounded-md hover:bg-gray-100">
            <a href="${att.file_url}" target="_blank" class="text-blue-600 hover:underline truncate pr-4" title="${att.original_filename}">
                <i class="fas fa-file-alt mr-2 text-gray-500"></i>
                ${att.original_filename}
            </a>
            ${deleteButtonHtml}
        </li>
      `;
      listContainer.insertAdjacentHTML("beforeend", listItem);
    });
  } else {
    listContainer.innerHTML = '<p id="no-attachment-text" class="text-gray-500">Belum ada lampiran.</p>';
  }
}

/**
 * Mengunggah satu atau lebih file lampiran yang dipilih.
 */
window.uploadAttachment = async function (partId) {
  const fileInput = document.getElementById("attachment-file-input");
  const uploadBtn = document.getElementById("upload-attachment-btn");
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

  if (!fileInput.files.length) {
    showToast("Silakan pilih satu atau lebih file terlebih dahulu.", "error");
    return;
  }

  const formData = new FormData();
  for (const file of fileInput.files) {
    formData.append("attachment", file);
  }

  uploadBtn.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> Mengunggah...`;
  uploadBtn.disabled = true;

  try {
    const response = await fetch(`/upload_attachment/${partId}`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken },
      body: formData,
    });
    const result = await response.json();
    if (result.success) {
      showToast(result.message, "success");
      const userIsAdmin = !!document.querySelector("button[onclick^='deleteAttachment']");
      renderAttachmentList(partId, result.attachments, userIsAdmin);
      fileInput.value = "";
    } else {
      showToast(`Error: ${result.error}`, "error");
    }
  } catch (error) {
    showToast("Terjadi kesalahan jaringan saat mengunggah file.", "error");
  } finally {
    uploadBtn.innerHTML = `<i class="fas fa-upload mr-2"></i> Unggah`;
    uploadBtn.disabled = fileInput.files.length === 0;
  }
};

/**
 * Menghapus file lampiran.
 */
window.deleteAttachment = async function (partId, publicId) {
  if (!confirm("Apakah Anda yakin ingin menghapus lampiran ini secara permanen?")) {
    return;
  }

  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

  try {
    const response = await fetch(`/delete_attachment/${partId}/${publicId}`, {
      method: "DELETE",
      headers: { "X-CSRFToken": csrfToken },
    });

    const result = await response.json();
    if (result.success) {
      showToast(result.message, "success");
      const elementId = `attachment-item-${publicId.replace(/[\/.]/g, "-")}`;
      document.getElementById(elementId)?.remove();

      const listContainer = document.getElementById("attachment-list");
      if (listContainer && listContainer.children.length === 0) {
        listContainer.innerHTML = '<p id="no-attachment-text" class="text-gray-500">Belum ada lampiran.</p>';
      }
    } else {
      showToast(`Error: ${result.error}`, "error");
    }
  } catch (error) {
    console.error("Delete error:", error);
    showToast("Terjadi kesalahan jaringan saat menghapus lampiran.", "error");
  }
};

// =====================================================================
// LOGIKA UNTUK STRIPPING REPORT (per part_id)
// =====================================================================

window.getStrippingReportData = async function (partId, forceRefresh = false) {
  const button = document.getElementById("get-stripping-report-btn");
  const dropdown = document.getElementById("stripping-report-dropdown");
  if (!button || !dropdown) return;

  const isDropdownVisible = !dropdown.classList.contains("hidden");

  if (isDropdownVisible && !forceRefresh) {
    dropdown.classList.add("hidden");
    button.innerHTML = `<i class="fas fa-cogs mr-2"></i> Informasi Stripping`;
    return;
  }

  button.innerHTML = `<i class="fas fa-spinner fa-spin mr-2"></i> Mengambil...`;
  button.disabled = true;

  try {
    const response = await fetch(`/get_stripping/${partId}`);
    const result = await response.json();

    if (result.success) {
      displayStrippingReportInTable(result.data);
      dropdown.classList.remove("hidden");
      if (!forceRefresh) {
        dropdown.scrollIntoView({ behavior: "smooth", block: "nearest" });
      }
      button.innerHTML = `<i class="fas fa-chevron-up mr-2"></i> Tutup Stripping`;
    } else {
      showToast(`Error: ${result.error}`, "error");
      button.innerHTML = `<i class="fas fa-cogs mr-2"></i> Informasi Stripping`;
    }
  } catch (error) {
    console.error("Terjadi kesalahan jaringan:", error);
    showToast("Terjadi kesalahan jaringan saat mengambil data Stripping Report.", "error");
    button.innerHTML = `<i class="fas fa-cogs mr-2"></i> Informasi Stripping`;
  } finally {
    button.disabled = false;
  }
};

function displayStrippingReportInTable(data) {
  const tableBody = document.getElementById("stripping-report-table-body");
  if (!tableBody) return;

  const userIsAdmin = !!document.getElementById("add-stripping-btn");
  tableBody.innerHTML = "";

  if (data.length === 0) {
    const colspan = userIsAdmin ? 12 : 11;
    tableBody.innerHTML = `<tr><td colspan="${colspan}" class="text-center py-4 text-gray-500 border border-gray-300">Data tidak ditemukan</td></tr>`;
  } else {
    data.forEach((item) => {
      const itemData = JSON.stringify(item).replace(/'/g, "&apos;").replace(/"/g, "&quot;");
      let actionButtons = "";
      if (userIsAdmin) {
        actionButtons = `
          <td class="px-4 py-3 whitespace-nowrap text-sm text-center border border-gray-300">
            <button onclick='toggleStrippingEditMode(this, ${itemData})' class="text-blue-600 hover:text-blue-800 mr-3" title="Edit"><i class="fas fa-edit"></i></button>
            <button onclick='deleteStripping(${item.id})' class="text-red-600 hover:text-red-800" title="Hapus"><i class="fas fa-trash"></i></button>
          </td>
        `;
      }
      const row = `
        <tr id="strep-row-${item.id}" class="hover:bg-gray-50">
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.bdp_name || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.bdp_number || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.bdp_number_eqv || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.qty || "0"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.unit || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.op_number || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.op_date || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.defect || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.mt_number || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.mt_qty || "-"}</td>
          <td class="px-4 py-3 whitespace-nowrap text-sm text-gray-500 border border-gray-300">${item.mt_date || "-"}</td>
          ${actionButtons}
        </tr>
      `;
      tableBody.innerHTML += row;
    });
  }
}

window.deleteStripping = async function (strepId) {
  if (!confirm("Apakah Anda yakin ingin menghapus data stripping ini?")) return;
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
  const partId = document
    .getElementById("get-stripping-report-btn")
    .onclick.toString()
    .match(/'([^']+)'/)[1];
  try {
    const response = await fetch(`/delete_stripping/${strepId}`, { method: "DELETE", headers: { "X-CSRFToken": csrfToken } });
    const result = await response.json();
    if (result.success) {
      showToast(result.message, "success");
      getStrippingReportData(partId, true);
    } else {
      showToast(`Error: ${result.error}`, "error");
    }
  } catch (error) {
    showToast("Terjadi kesalahan jaringan.", "error");
  }
};

const inputClass = "w-full bg-gray-50 border border-gray-300 rounded-md shadow-sm focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm p-1";

window.toggleStrippingEditMode = function (button, itemData) {
  const row = button.closest("tr");
  row.dataset.originalHtml = row.innerHTML;
  row.innerHTML = `
    <td class="p-1"><input type="text" value="${itemData.bdp_name || ""}" class="${inputClass}" data-field="bdp_name"></td>
    <td class="p-1"><input type="text" value="${itemData.bdp_number || ""}" class="${inputClass}" data-field="bdp_number"></td>
    <td class="p-1"><input type="text" value="${itemData.bdp_number_eqv || ""}" class="${inputClass}" data-field="bdp_number_eqv"></td>
    <td class="p-1"><input type="number" value="${itemData.qty || ""}" class="${inputClass}" data-field="qty"></td>
    <td class="p-1"><input type="text" value="${itemData.unit || ""}" class="${inputClass}" data-field="unit"></td>
    <td class="p-1"><input type="text" value="${itemData.op_number || ""}" class="${inputClass}" data-field="op_number"></td>
    <td class="p-1"><input type="date" value="${itemData.op_date || ""}" class="${inputClass}" data-field="op_date"></td>
    <td class="p-1"><input type="text" value="${itemData.defect || ""}" class="${inputClass}" data-field="defect"></td>
    <td class="p-1"><input type="text" value="${itemData.mt_number || ""}" class="${inputClass}" data-field="mt_number"></td>
    <td class="p-1"><input type="text" value="${itemData.mt_qty || ""}" class="${inputClass}" data-field="mt_qty"></td>
    <td class="p-1"><input type="date" value="${itemData.mt_date || ""}" class="${inputClass}" data-field="mt_date"></td>
    <td class="px-4 py-3 whitespace-nowrap text-sm text-center border border-gray-300">
        <button onclick="saveStrippingEdit(${itemData.id}, this)" class="text-green-600 hover:text-green-800 mr-3" title="Simpan"><i class="fas fa-check"></i></button>
        <button onclick="cancelStrippingEdit(this)" class="text-gray-600 hover:text-gray-800" title="Batal"><i class="fas fa-times"></i></button>
    </td>
  `;
};

window.saveStrippingEdit = async function (strepId, button) {
  const row = button.closest("tr");
  const inputs = row.querySelectorAll("input");
  const formData = {};

  // ***FIXED LOGIC***
  // Always send the field to the backend, even if its value is empty.
  // This allows the backend to know it should clear the field.
  inputs.forEach((input) => {
    formData[input.dataset.field] = input.value;
  });

  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
  const partId = document
    .getElementById("get-stripping-report-btn")
    .onclick.toString()
    .match(/'([^']+)'/)[1];
  try {
    const response = await fetch(`/edit_stripping/${strepId}`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken }, body: JSON.stringify(formData) });
    const result = await response.json();
    if (result.success) {
      showToast(result.message, "success");
      getStrippingReportData(partId, true);
    } else {
      showToast(`Error: ${result.error}`, "error");
    }
  } catch (error) {
    showToast("Terjadi kesalahan jaringan.", "error");
  }
};

window.cancelStrippingEdit = function (button) {
  const row = button.closest("tr");
  row.innerHTML = row.dataset.originalHtml;
};

window.addStrippingRow = function () {
  const tableBody = document.getElementById("stripping-report-table-body");
  if (document.getElementById("new-stripping-row")) return;
  const newRowHtml = `
    <tr id="new-stripping-row" class="bg-yellow-50">
        <td class="p-1"><input type="text" placeholder="Nama BDP..." class="${inputClass}" data-field="bdp_name"></td>
        <td class="p-1"><input type="text" placeholder="Nomor BDP..." class="${inputClass}" data-field="bdp_number"></td>
        <td class="p-1"><input type="text" placeholder="Eqv..." class="${inputClass}" data-field="bdp_number_eqv"></td>
        <td class="p-1"><input type="number" placeholder="0" class="${inputClass}" data-field="qty"></td>
        <td class="p-1"><input type="text" placeholder="Unit..." class="${inputClass}" data-field="unit"></td>
        <td class="p-1"><input type="text" placeholder="Nomor OP..." class="${inputClass}" data-field="op_number"></td>
        <td class="p-1"><input type="date" class="${inputClass}" data-field="op_date"></td>
        <td class="p-1"><input type="text" placeholder="Defect..." class="${inputClass}" data-field="defect"></td>
        <td class="p-1"><input type="text" placeholder="Nomor MT..." class="${inputClass}" data-field="mt_number"></td>
        <td class="p-1"><input type="text" placeholder="Qty MT..." class="${inputClass}" data-field="mt_qty"></td>
        <td class="p-1"><input type="date" placeholder="Qty Date..." class="${inputClass}" data-field="mt_date"></td>
        <td class="px-4 py-3 whitespace-nowrap text-sm text-center border border-gray-300">
            <button onclick="saveNewStripping(this)" class="text-green-600 hover:text-green-800 mr-3" title="Simpan"><i class="fas fa-check"></i></button>
            <button onclick="this.closest('tr').remove()" class="text-gray-600 hover:text-gray-800" title="Batal"><i class="fas fa-times"></i></button>
        </td>
    </tr>
  `;
  tableBody.insertAdjacentHTML("beforeend", newRowHtml);
  const newRow = tableBody.querySelector("#new-stripping-row");
  newRow.scrollIntoView({ behavior: "smooth", block: "center" });
  newRow.querySelector("input").focus();
};

window.saveNewStripping = async function (button) {
  const row = button.closest("tr");
  const inputs = row.querySelectorAll("input");
  const formData = {};
  let hasValue = false;
  inputs.forEach((input) => {
    if (input.value) {
      formData[input.dataset.field] = input.value;
      hasValue = true;
    }
  });
  if (!hasValue) {
    showToast("Harap isi setidaknya satu kolom.", "error");
    return;
  }
  const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
  const partId = document
    .getElementById("get-stripping-report-btn")
    .onclick.toString()
    .match(/'([^']+)'/)[1];
  try {
    const response = await fetch(`/add_stripping/${partId}`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken }, body: JSON.stringify(formData) });
    const result = await response.json();
    if (result.success) {
      showToast(result.message, "success");
      getStrippingReportData(partId, true);
    } else {
      showToast(`Error: ${result.error}`, "error");
    }
  } catch (error) {
    showToast("Terjadi kesalahan jaringan.", "error");
  }
};

document.addEventListener("DOMContentLoaded", () => {
  const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content");
  const userRole = document.querySelector('meta[name="user-role"]')?.getAttribute("content");
  if (userRole) {
    document.body.dataset.userRole = userRole;
  }

  const attachmentInput = document.getElementById("attachment-file-input");
  const uploadButton = document.getElementById("upload-attachment-btn");

  if (attachmentInput && uploadButton) {
    attachmentInput.addEventListener("change", () => {
      uploadButton.disabled = attachmentInput.files.length === 0;
    });
  }

  async function executeSaveMws(partIdToSave) {
    const updatedData = { partId: partIdToSave };
    document.querySelectorAll(".mws-info-edit").forEach((input) => {
      updatedData[input.dataset.field] = input.value;
    });
    try {
      const response = await fetch("/update_mws_info", { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken }, body: JSON.stringify(updatedData) });
      const data = await response.json();
      if (data.success) {
        showToast("Informasi MWS berhasil diperbarui.", "success");
        document.querySelectorAll(".mws-info-edit").forEach((input) => {
          input.previousElementSibling.textContent = input.value || "N/A";
        });
        toggleEditMode(false);
      } else {
        showToast("Error: " + data.error, "error");
      }
    } catch (error) {
      showToast("Terjadi kesalahan jaringan.", "error");
    }
  }

  async function executeDuplicate(originalPartId) {
    try {
      const response = await fetch(`/duplicate_mws/${originalPartId}`, { method: "POST", headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken } });
      const data = await response.json();
      if (data.success) {
        showToast("MWS berhasil diduplikasi. Mengalihkan...", "success");
        setTimeout(() => (window.location.href = data.redirect_url), 1500);
      } else {
        showToast("Error: " + data.error, "error");
      }
    } catch (error) {
      showToast("Terjadi kesalahan jaringan saat duplikasi.", "error");
    }
  }

  const saveModal = document.getElementById("confirmation-modal");
  if (saveModal) {
    document.getElementById("modal-btn-cancel").addEventListener("click", () => saveModal.classList.add("hidden"));
    document.getElementById("modal-btn-save").addEventListener("click", (e) => {
      executeSaveMws(e.target.dataset.partId);
      saveModal.classList.add("hidden");
    });
  }

  const duplicateModal = document.getElementById("duplicate-confirmation-modal");
  if (duplicateModal) {
    document.getElementById("modal-btn-cancel-duplicate").addEventListener("click", () => duplicateModal.classList.add("hidden"));
    document.getElementById("modal-btn-confirm-duplicate").addEventListener("click", (e) => {
      executeDuplicate(e.target.dataset.partId);
      duplicateModal.classList.add("hidden");
    });
  }

  const addStrippingButton = document.getElementById("add-stripping-btn");
  if (addStrippingButton) {
    addStrippingButton.addEventListener("click", () => addStrippingRow());
  }
});
