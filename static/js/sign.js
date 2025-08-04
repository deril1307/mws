/**
 * (REFACTORED) Mengirim data penandatanganan dokumen ke server.
 * @param {string} partId - ID dari MWS.
 * @param {string} type - Tipe tanda tangan (misal: 'preparedBy').
 */
async function signDocument(partId, type) {
  if (!confirm("Apakah Anda yakin ingin menandatangani dokumen ini?")) return;

  try {
    const response = await fetch("/sign_document", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId: partId, type: type }),
    });

    const data = await response.json();

    if (data.success) {
      showNotification("Dokumen berhasil di Approved.", "success");
      location.reload();
    } else {
      showNotification("Error: " + data.error, "error");
    }
  } catch (error) {
    console.error("Sign Document Error:", error);
    showNotification("Terjadi kesalahan jaringan.", "error");
  }
}

/**
 * (REFACTORED) Memperbarui tanggal (seperti start date) pada MWS.
 * @param {string} partId - ID dari MWS.
 * @param {string} field - Nama field tanggal yang akan diupdate.
 * @param {string} value - Nilai tanggal yang baru.
 */
async function updateDates(partId, field, value) {
  try {
    const response = await fetch("/update_dates", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, field, value }),
    });

    const data = await response.json();

    if (data.success) {
      showNotification("Date updated", "success");
      if (field === "startDate" && typeof checkStrippingStatus === "function") {
        // Panggil checkStrippingStatus jika ada setelah update berhasil
        setTimeout(checkStrippingStatus, 1000);
      }
    } else {
      showNotification("Error: " + data.error, "error");
    }
  } catch (error) {
    console.error("Update Dates Error:", error);
    showNotification("Terjadi kesalahan jaringan.", "error");
  }
}

/**
 * (REFACTORED) Mengirim permintaan untuk membatalkan tanda tangan.
 * @param {string} partId - ID dari MWS.
 * @param {string} signType - Tipe tanda tangan yang akan dibatalkan.
 * @param {string} confirmMessage - Pesan konfirmasi yang akan ditampilkan.
 */
async function cancelSignature(partId, signType, confirmMessage) {
  if (!confirm(confirmMessage)) return;

  try {
    const response = await fetch("/cancel_signature", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId: partId, type: signType }),
    });

    const data = await response.json();

    if (data.success) {
      showNotification(data.message, "success");
      location.reload();
    } else {
      showNotification("Error: " + data.error, "error");
    }
  } catch (error) {
    console.error("Cancel Signature Error:", error);
    showNotification("Terjadi kesalahan jaringan.", "error");
  }
}
