// Global variables for timers and notifications
let strippingNotificationTimer;
let strippingStatus = null;
window.activeTimers = {};

/**
 * Displays a feature-rich, temporary notification on the screen.
 * @param {string} message The message to display.
 * @param {('success'|'error')} type The type of notification.
 */
function showNotification(message, type) {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;

  const iconClass = type === "success" ? "fa-check-circle" : "fa-times-circle";
  const title = type === "success" ? "Success" : "Error";

  notification.innerHTML = `
    <div class="flex items-start space-x-3">
        <div class="flex-shrink-0 text-xl pt-1">
            <i class="fas ${iconClass}"></i>
        </div>
        <div class="flex-1">
            <p class="font-bold">${title}</p>
            <p class="text-sm">${message}</p>
        </div>
        <div class="flex-shrink-0">
            <button class="notification-close-btn">
                <i class="fas fa-times"></i>
            </button>
        </div>
    </div>
  `;

  document.body.appendChild(notification);

  const timer = setTimeout(() => {
    notification.remove();
  }, 5000);

  notification.querySelector(".notification-close-btn").addEventListener("click", () => {
    clearTimeout(timer);
    notification.remove();
  });
}

/**
 * @param {string} message The message to show.
 * @param {('success'|'error')} type The notification type.
 * @param {number} delay The delay in ms before reloading.
 */
function showNotificationAndReload(message, type, delay = 1500) {
  showNotification(message, type);
  setTimeout(() => location.reload(), delay);
}

// --- Stripping Notification Functions ---

function checkStrippingStatus() {
  fetch(`/get_stripping_status/${partId}`)
    .then((r) => r.json())
    .then((data) => {
      if (data.success) {
        strippingStatus = data.status;
        updateStrippingNotification();
        highlightCheckStep();
      }
    })
    .catch((e) => console.error("Error checking stripping status:", e));
}

function updateStrippingNotification() {
  if (!strippingStatus || strippingStatus.status === "no_start_date") {
    hideStrippingNotification();
    return;
  }

  const notification = document.getElementById("stripping-notification");
  const icon = document.getElementById("stripping-icon");
  const message = document.getElementById("stripping-message");
  const progressFill = document.getElementById("stripping-progress-fill");
  const percentage = document.getElementById("stripping-percentage");
  const deadline = document.getElementById("stripping-deadline");

  notification.className = "stripping-notification";

  let notificationClass, iconClass, messageText;

  switch (strippingStatus.status) {
    case "safe":
      notificationClass = "safe";
      iconClass = "fas fa-check-circle";
      messageText = `Masih tersisa ${strippingStatus.working_days_remaining} hari kerja untuk stripping step.`;
      break;
    case "warning":
      notificationClass = "warning";
      iconClass = "fas fa-exclamation-triangle";
      messageText = `Peringatan! Tersisa ${strippingStatus.working_days_remaining} hari kerja untuk stripping step Check.`;
      break;
    case "critical":
      notificationClass = "critical";
      iconClass = "fas fa-exclamation-circle";
      if (strippingStatus.working_days_remaining <= 0) {
        const overdue = Math.abs(strippingStatus.working_days_remaining);
        messageText = `KRITIS! Batas waktu stripping telah terlewat ${overdue} hari kerja.`;
      } else {
        messageText = `KRITIS! Hanya tersisa ${strippingStatus.working_days_remaining} hari kerja untuk stripping step Check.`;
      }
      break;
  }

  notification.classList.add(notificationClass);
  icon.className = iconClass + " text-xl";
  message.textContent = messageText;
  progressFill.style.width = `${strippingStatus.percentage}%`;
  percentage.textContent = `${strippingStatus.percentage}%`;

  if (strippingStatus.deadline_date) {
    const deadlineDate = new Date(strippingStatus.deadline_date);
    deadline.textContent = `Deadline: ${deadlineDate.toLocaleDateString("id-ID")}`;
  }

  notification.style.display = "block";

  if (strippingStatus.status === "safe") {
    clearTimeout(strippingNotificationTimer);
    strippingNotificationTimer = setTimeout(() => {
      hideStrippingNotification();
    }, 10000);
  }
}

function highlightCheckStep() {
  document.querySelectorAll(".check-step-row").forEach((row) => {
    row.classList.remove("stripping-warning", "stripping-critical");
  });

  if (!strippingStatus || strippingStatus.status === "no_start_date" || strippingStatus.status === "safe") {
    return;
  }

  document.querySelectorAll(".check-step-row").forEach((row) => {
    if (strippingStatus.status === "warning") {
      row.classList.add("stripping-warning");
    } else if (strippingStatus.status === "critical") {
      row.classList.add("stripping-critical");
    }
  });
}

function hideStrippingNotification() {
  const notification = document.getElementById("stripping-notification");
  if (notification) notification.style.display = "none";
  clearTimeout(strippingNotificationTimer);
}

function dismissStrippingNotification() {
  hideStrippingNotification();
  if (strippingStatus && strippingStatus.status === "critical") {
    setTimeout(checkStrippingStatus, 5 * 60 * 1000);
  }
}

// --- Timer and General Functions ---

function parseHHMMToMinutes(timeStr) {
  if (!timeStr || typeof timeStr !== "string" || !timeStr.includes(":")) {
    return 0;
  }
  try {
    const parts = timeStr.split(":").map(Number);
    if (isNaN(parts[0]) || isNaN(parts[1])) return 0;
    return parts[0] * 60 + parts[1];
  } catch (e) {
    console.error("Gagal parse waktu:", timeStr, e);
    return 0;
  }
}

function initializeLiveTimers() {
  document.querySelectorAll("[data-start-time]").forEach((displayElement) => {
    const stepNo = displayElement.id.split("-").pop();
    const startTimeISO = displayElement.dataset.startTime;
    const initialMinutesValue = displayElement.dataset.initialHours || "00:00";
    const initialMinutes = parseHHMMToMinutes(initialMinutesValue);

    if (window.activeTimers[stepNo]) {
      clearInterval(window.activeTimers[stepNo]);
    }

    const startTime = new Date(startTimeISO);
    window.activeTimers[stepNo] = setInterval(() => {
      const totalMinutes = initialMinutes + (new Date() - startTime) / 60000;
      const hours = Math.floor(totalMinutes / 60);
      const minutes = Math.floor(totalMinutes % 60);
      displayElement.textContent = `${hours.toString().padStart(2, "0")}:${minutes.toString().padStart(2, "0")}`;
    }, 1000);
  });
}

// --- NEW FUNCTIONS for Plan Edit/Save ---

function togglePlanEdit(stepNo, field, isEditing) {
  const viewMode = document.getElementById(`plan-${field}-view-${stepNo}`);
  const editMode = document.getElementById(`plan-${field}-edit-${stepNo}`);

  if (!viewMode || !editMode) {
    console.error(`Elements for plan ${field} at step ${stepNo} not found.`);
    return;
  }

  if (isEditing) {
    viewMode.classList.add("hidden");
    editMode.classList.remove("hidden");
    document.getElementById(`plan-${field}-input-${stepNo}`).focus();
  } else {
    viewMode.classList.remove("hidden");
    editMode.classList.add("hidden");
  }
}

async function savePlan(partId, stepNo, field) {
  const input = document.getElementById(`plan-${field}-input-${stepNo}`);
  const value = input.value;
  const button = event.currentTarget;
  const originalHtml = button.innerHTML;

  button.disabled = true;
  button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

  const backendField = `plan${field.charAt(0).toUpperCase() + field.slice(1)}`;

  try {
    const response = await fetch("/update_step_field", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo, field: backendField, value: value }),
    });

    const data = await response.json();

    if (data.success) {
      showNotification(`Plan ${field} berhasil disimpan.`, "success");
      document.getElementById(`plan-${field}-text-${stepNo}`).textContent = value || "N/A";
      togglePlanEdit(stepNo, field, false);
    } else {
      showNotification(`Gagal menyimpan Plan ${field}: ` + data.error, "error");
    }
  } catch (error) {
    console.error(`Network error saving plan ${field}:`, error);
    showNotification("Terjadi kesalahan jaringan saat menyimpan.", "error");
  } finally {
    button.disabled = false;
    button.innerHTML = originalHtml;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  initializeLiveTimers();
  checkStrippingStatus();
  setInterval(checkStrippingStatus, 5 * 60 * 1000);
});

// --- Role-Specific Functions ---

if (currentUserRole !== "customer") {
  function startTimer(partId, stepNo) {
    const startBtn = event.currentTarget;
    startBtn.disabled = true;
    startBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    fetch("/start_timer", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          showNotificationAndReload("Timer berhasil dimulai.", "success");
        } else {
          showNotification("Error: " + d.error, "error");
          startBtn.disabled = false;
          startBtn.textContent = "Start";
        }
      })
      .catch((e) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
        startBtn.disabled = false;
        startBtn.textContent = "Start";
      });
  }

  function stopTimer(partId, stepNo) {
    const stopBtn = event.currentTarget;
    stopBtn.disabled = true;
    stopBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    if (window.activeTimers[stepNo]) {
      clearInterval(window.activeTimers[stepNo]);
    }

    fetch("/stop_timer", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          showNotificationAndReload(`Timer dihentikan. Total waktu: ${d.hours}`, "success");
        } else {
          showNotification("Error: " + d.error, "error");
          stopBtn.disabled = false;
          stopBtn.textContent = "Stop";
        }
      })
      .catch((e) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
        stopBtn.disabled = false;
        stopBtn.textContent = "Stop";
      });
  }

  function updateStepField(partId, stepNo, field, value) {
    fetch("/update_step_field", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo, field, value }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (!d.success) {
          showNotification("Error: " + d.error, "error");
          location.reload();
        }
      })
      .catch((e) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
        location.reload();
      });
  }

  function cancelApproval(partId, stepNo) {
    if (confirm("Apakah Anda yakin ingin membatalkan approval mekanik untuk langkah ini?\n\nLangkah kerja akan kembali ke status 'pending' dan mekanik dapat mengisi ulang MAN, HOURS, dan melakukan approval kembali.")) {
      fetch("/update_step_field", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
        body: JSON.stringify({ partId: partId, stepNo: stepNo, field: "tech", value: "" }),
      })
        .then((r) => r.json())
        .then((d) => {
          if (d.success) {
            updateStepStatus(partId, stepNo, "pending", "Approval berhasil dibatalkan.");
          } else {
            showNotification("Gagal membatalkan approval: " + d.error, "error");
          }
        })
        .catch((e) => showNotification("Terjadi kesalahan jaringan.", "error"));
    }
  }

  function finishStep(partId, stepNo) {
    if (!confirm("Apakah Anda yakin ingin menyelesaikan langkah kerja ini?")) return;
    updateStepStatus(partId, stepNo, "completed", "Langkah kerja berhasil diselesaikan.");
  }

  function cancelFinishStep(partId, stepNo) {
    if (confirm("Apakah Anda yakin ingin membatalkan penyelesaian langkah kerja ini?\n\nKonsekuensi: Langkah kerja akan kembali ke status in_progress, kata 'Approved' akan dihapus dari database, dan dapat diinspeksi ulang.")) {
      updateStepStatus(partId, stepNo, "in_progress", "Penyelesaian langkah kerja dibatalkan.");
    }
  }

  function updateStepStatus(partId, stepNo, status, successMessage = "Status berhasil diperbarui.") {
    fetch("/update_step_status", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo, status }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          showNotificationAndReload(successMessage, "success");
        } else {
          showNotificationAndReload("Error: " + d.error, "error");
        }
      })
      .catch((e) => {
        showNotificationAndReload("Terjadi kesalahan jaringan.", "error");
      });
  }

  function addDetail(partId, stepNo) {
    const input = document.getElementById(`new-detail-input-${stepNo}`);
    const newDetailText = input.value.trim();
    if (!newDetailText) return;
    const detailsList = document.querySelector(`#details-list-${stepNo} ul`);
    const existingDetails = Array.from(detailsList.querySelectorAll("li > span")).map((span) => span.textContent);
    const updatedDetails = [...existingDetails, newDetailText];
    updateStepDetails(partId, stepNo, updatedDetails, "Catatan berhasil ditambahkan.");
  }

  function editDetail(partId, stepNo, detailIndex) {
    const span = document.getElementById(`detail-text-${stepNo}-${detailIndex}`);
    const currentText = span.textContent;
    const newText = prompt("Edit catatan:", currentText);
    if (newText !== null && newText !== currentText) {
      const detailsList = document.querySelector(`#details-list-${stepNo} ul`);
      const existingDetails = Array.from(detailsList.querySelectorAll("li > span")).map((span) => span.textContent);
      const updatedDetails = [...existingDetails];
      updatedDetails[detailIndex] = newText.trim();
      updateStepDetails(partId, stepNo, updatedDetails, "Catatan berhasil diubah.");
    }
  }

  function deleteDetail(partId, stepNo, detailIndex) {
    if (!confirm("Apakah Anda yakin ingin menghapus catatan ini?")) return;
    const detailsList = document.querySelector(`#details-list-${stepNo} ul`);
    const existingDetails = Array.from(detailsList.querySelectorAll("li > span")).map((span) => span.textContent);
    const updatedDetails = existingDetails.filter((_, index) => index !== detailIndex);
    updateStepDetails(partId, stepNo, updatedDetails, "Catatan berhasil dihapus.");
  }

  function updateStepDetails(partId, stepNo, detailsArray, successMessage) {
    fetch("/update_step_details", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId: partId, stepNo: stepNo, details: detailsArray }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(successMessage, "success");
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }

  function insertStepAfter(partId, afterStepNo) {
    const description = prompt("Masukkan deskripsi untuk langkah kerja baru:");
    if (!description || description.trim() === "") return;
    fetch(`/insert_step/${partId}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ description: description.trim(), after_step_no: afterStepNo }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload("Langkah kerja baru berhasil disisipkan.", "success");
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }

  function editStepDescription(partId, stepNo) {
    const currentDescriptionEl = document.getElementById(`step-desc-${stepNo}`);
    const currentDescription = currentDescriptionEl.textContent;
    const newDescription = prompt("Edit deskripsi langkah kerja:", currentDescription);

    if (!newDescription || newDescription.trim() === "" || newDescription === currentDescription) return;

    fetch(`/update_step_description/${partId}/${stepNo}`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ description: newDescription.trim() }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotification("Deskripsi berhasil diubah.", "success");
          currentDescriptionEl.textContent = newDescription.trim();
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }

  function deleteStep(partId, stepNo) {
    if (!confirm(`Apakah Anda yakin ingin menghapus Langkah #${stepNo}?`)) return;
    fetch(`/delete_step/${partId}/${stepNo}`, {
      method: "DELETE",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(`Langkah #${stepNo} berhasil dihapus.`, "success");
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }

  function cancelSignature(partId, signType, confirmMessage) {
    if (!confirm(confirmMessage)) return;
    fetch("/cancel_signature", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId: partId, type: signType }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(data.message, "success");
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }
}

// --- Admin/Superadmin Functions ---
if (currentUserRole === "admin" || currentUserRole === "superadmin") {
  function removeMechanicFromStep(partId, stepNo, nikToRemove) {
    if (!confirm(`Apakah Anda yakin ingin menghapus mekanik dengan NIK ${nikToRemove} dari langkah ini?`)) return;
    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    fetch("/step/remove_mechanic", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo, nik: nikToRemove }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(data.message || "Mekanik berhasil dihapus.", "success");
        } else {
          showNotification("Error: " + data.error, "error");
          button.disabled = false;
          button.innerHTML = "&times;";
        }
      })
      .catch((err) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
        button.disabled = false;
        button.innerHTML = "&times;";
      });
  }
}

// --- Mechanic Functions ---
if (currentUserRole === "mechanic") {
  function addMeToStep(partId, stepNo) {
    if (!confirm("Apakah Anda yakin ingin Sign On ke langkah kerja ini?")) return;

    const button = event.currentTarget;
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';

    fetch("/step/add_mechanic", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(data.message, "success");
        } else {
          showNotification("Error: " + data.error, "error");
          button.disabled = false;
          button.innerHTML = '<i class="fas fa-sign-in-alt mr-1"></i> Sign On';
        }
      })
      .catch((err) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-sign-in-alt mr-1"></i> Sign On';
      });
  }

  function approveStep(partId, stepNo) {
    const manCountElement = document.querySelector(`#step-row-${stepNo} .font-semibold span.text-blue-600`);
    const manCount = manCountElement ? parseInt(manCountElement.textContent, 10) : 0;
    if (manCount === 0) {
      showNotification("MAN belum terisi. Anda harus 'Sign On' ke langkah ini terlebih dahulu.", "error");
      return;
    }

    const hoursValue = document.getElementById(`hours-${stepNo}`).value;
    if (!hoursValue || hoursValue === "00:00" || hoursValue.trim() === "") {
      showNotification("HOURS belum terisi. Silakan gunakan timer Start/Stop untuk mencatat waktu kerja.", "error");
      return;
    }

    if (!confirm("Apakah Anda yakin ingin menyetujui (Approve) langkah kerja ini?\n\nTindakan ini akan mengunci MAN dan HOURS, lalu meneruskan pekerjaan ke Quality.\nAnda tidak dapat mengubahnya lagi.")) {
      return;
    }

    fetch("/update_step_field", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId: partId, stepNo: stepNo, field: "tech", value: "Approved" }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          updateStepStatus(partId, stepNo, "in_progress", "Langkah kerja berhasil di-approve.");
        } else {
          showNotification("Gagal menyimpan approval: " + data.error, "error");
        }
      })
      .catch((error) => {
        showNotification("Terjadi kesalahan jaringan saat menyimpan approval.", "error");
      });
  }

  // --- FUNGSI BARU UNTUK LAMPIRAN ---
  function uploadStepAttachment(partId, stepNo) {
    const input = document.getElementById(`step-attachment-input-${stepNo}`);
    const files = input.files;
    const button = event.currentTarget;

    if (files.length === 0) {
      showNotification("Silakan pilih file untuk diunggah.", "error");
      return;
    }

    const formData = new FormData();
    for (let i = 0; i < files.length; i++) {
      formData.append("attachments", files[i]);
    }

    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';

    fetch(`/upload_step_attachment/${partId}/${stepNo}`, {
      method: "POST",
      headers: { "X-CSRFToken": csrfToken }, // FormData sets Content-Type automatically
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(data.message, "success");
        } else {
          showNotification(data.error || "Gagal mengunggah file.", "error");
          button.disabled = false;
          button.innerHTML = '<i class="fas fa-upload mr-1"></i> Unggah';
        }
      })
      .catch((error) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-upload mr-1"></i> Unggah';
      });
  }

  function deleteStepAttachment(partId, stepNo, storedFilename) {
    if (!confirm("Apakah Anda yakin ingin menghapus lampiran ini?")) {
      return;
    }

    fetch(`/delete_step_attachment/${partId}/${stepNo}/${storedFilename}`, {
      method: "DELETE",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": csrfToken,
      },
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          showNotificationAndReload(data.message, "success");
        } else {
          showNotification(data.error || "Gagal menghapus lampiran.", "error");
        }
      })
      .catch((error) => {
        showNotification("Terjadi kesalahan jaringan.", "error");
      });
  }
}
