// Global variables for timers and notifications
let strippingNotificationTimer;
let strippingStatus = null;
window.activeTimers = {};

/**
 * Displays a temporary notification message on the screen.
 * @param {string} message The message to display.
 * @param {('success'|'error')} type The type of notification.
 */
function showNotification(message, type) {
  const notification = document.createElement("div");
  notification.className = `notification ${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);
  setTimeout(() => {
    notification.remove();
  }, 3000);
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

document.addEventListener("DOMContentLoaded", function () {
  initializeLiveTimers();
  checkStrippingStatus();
  setInterval(checkStrippingStatus, 5 * 60 * 1000); // Check every 5 minutes
});

// --- Role-Specific Functions ---

if (currentUserRole !== "customer") {
  function startTimer(partId, stepNo) {
    const startBtn = event.currentTarget; // FIX: Changed from event.target
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
          showNotification("Timer dimulai.", "success");
          location.reload();
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
    const stopBtn = event.currentTarget; // FIX: Changed from event.target
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
          showNotification(`Timer dihentikan. Total waktu: ${d.hours}`, "success");
          location.reload();
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
      .catch((e) => showNotification("Terjadi kesalahan jaringan.", "error"));
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
            updateStepStatus(partId, stepNo, "pending");
          } else {
            showNotification("Gagal membatalkan approval: " + d.error, "error");
          }
        })
        .catch((e) => showNotification("Terjadi kesalahan jaringan.", "error"));
    }
  }

  function finishStep(partId, stepNo) {
    if (!confirm("Apakah Anda yakin ingin menyelesaikan langkah kerja ini?")) return;
    updateStepField(partId, stepNo, "insp", "Approved");
    updateStepStatus(partId, stepNo, "completed");
  }

  function cancelFinishStep(partId, stepNo) {
    if (confirm("Apakah Anda yakin ingin membatalkan penyelesaian langkah kerja ini?\n\nKonsekuensi: Langkah kerja akan kembali ke status in_progress, kata 'Approved' akan dihapus dari database, dan dapat diinspeksi ulang.")) {
      updateStepStatus(partId, stepNo, "in_progress");
    }
  }

  function updateStepStatus(partId, stepNo, status) {
    fetch("/update_step_status", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo, status }),
    })
      .then((r) => r.json())
      .then((d) => {
        if (d.success) {
          location.reload();
        } else {
          alert("Error: " + d.error);
          location.reload();
        }
      })
      .catch((e) => {
        alert("Terjadi kesalahan jaringan.");
        location.reload();
      });
  }

  function addDetail(partId, stepNo) {
    const input = document.getElementById(`new-detail-input-${stepNo}`);
    const newDetailText = input.value.trim();
    if (!newDetailText) return;
    const detailsList = document.querySelector(`#details-list-${stepNo} ul`);
    const existingDetails = Array.from(detailsList.querySelectorAll("li > span")).map((span) => span.textContent);
    const updatedDetails = [...existingDetails, newDetailText];
    updateStepDetails(partId, stepNo, updatedDetails);
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
      updateStepDetails(partId, stepNo, updatedDetails);
    }
  }

  function deleteDetail(partId, stepNo, detailIndex) {
    if (!confirm("Apakah Anda yakin ingin menghapus catatan ini?")) return;
    const detailsList = document.querySelector(`#details-list-${stepNo} ul`);
    const existingDetails = Array.from(detailsList.querySelectorAll("li > span")).map((span) => span.textContent);
    const updatedDetails = existingDetails.filter((_, index) => index !== detailIndex);
    updateStepDetails(partId, stepNo, updatedDetails);
  }

  function updateStepDetails(partId, stepNo, detailsArray) {
    fetch("/update_step_details", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId: partId, stepNo: stepNo, details: detailsArray }),
    })
      .then((response) => response.json())
      .then((data) => {
        if (data.success) {
          location.reload();
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan.", "error"));
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
      .then((data) => (data.success ? location.reload() : showNotification("Error: " + data.error, "error")))
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }

  function editStepDescription(partId, stepNo) {
    const currentDescription = document.getElementById(`step-desc-${stepNo}`).textContent;
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
          document.getElementById(`step-desc-${stepNo}`).textContent = newDescription.trim();
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
      .then((data) => (data.success ? location.reload() : showNotification("Error: " + data.error, "error")))
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
          showNotification(data.message, "success");
          location.reload();
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((error) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }
}

// --- Admin/Superadmin Functions ---
if (currentUserRole === "admin" || currentUserRole === "superadmin") {
  function openAssignModal() {
    const allCheckboxes = document.querySelectorAll('input[name="mechanic_checkbox"]');
    allCheckboxes.forEach((checkbox) => {
      checkbox.checked = assignedMechanics.includes(checkbox.value);
    });
    const modal = document.getElementById("assign-mechanic-modal");
    modal.classList.remove("hidden");
    modal.classList.add("flex");
  }

  function closeAssignModal() {
    const modal = document.getElementById("assign-mechanic-modal");
    modal.classList.add("hidden");
    modal.classList.remove("flex");
  }

  function saveMechanicAssignments() {
    const checkedBoxes = document.querySelectorAll('input[name="mechanic_checkbox"]:checked');
    const selectedNiks = Array.from(checkedBoxes).map((checkbox) => checkbox.value);
    const selectedNames = Array.from(checkedBoxes).map((checkbox) => {
      return document.querySelector(`label[for="${checkbox.id}"]`).textContent.trim();
    });

    let confirmationMessage = selectedNames.length > 0 ? "Anda akan menugaskan mekanik berikut ke MWS ini:\n\n- " + selectedNames.join("\n- ") : "Anda akan MENGHAPUS SEMUA mekanik yang ditugaskan dari MWS ini.";

    confirmationMessage += "\n\nApakah Anda yakin ingin melanjutkan?";

    if (!confirm(confirmationMessage)) return;

    fetch(`/mws/${partId}/assign_mechanics`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ mechanic_niks: selectedNiks }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showNotification(data.message, "success");
          location.reload();
        } else {
          showNotification("Error: " + data.error, "error");
        }
      })
      .catch((err) => showNotification("Terjadi kesalahan jaringan.", "error"));
  }

  function removeMechanicFromStep(partId, stepNo, nikToRemove) {
    if (!confirm(`Apakah Anda yakin ingin menghapus mekanik dengan NIK ${nikToRemove} dari langkah ini?`)) return;
    const button = event.currentTarget; // FIX: Changed from event.target
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
          showNotification(data.message || "Mekanik berhasil dihapus.", "success");
          location.reload();
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

    const button = event.currentTarget; // FIX: Changed from event.target
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Memproses...';

    // --- PENJELASAN LOGIKA BACKEND ---
    // Request ini akan dikirim ke server untuk validasi final.
    // Ada dua kemungkinan logika validasi di server (file app.py), tergantung mana yang aktif:
    //
    // 1. KONDISI BERDASARKAN APPROVAL 'TECH' (Default):
    //    Server akan menolak request ini jika Anda (mekanik) terdeteksi masih "Sign On"
    //    di step lain (di MWS mana pun) yang status TECH-nya belum "Approved".
    //    Anda harus menyelesaikan pekerjaan Anda di step tersebut dan klik "Approve"
    //    sebelum bisa "Sign On" ke step yang baru.
    //
    // 2. KONDISI BERDASARKAN APPROVAL 'INSP':
    //    Jika diaktifkan, server akan menolak request ini jika Anda masih "Sign On"
    //    di step lain yang statusnya belum "completed" (belum di-approve oleh Quality Inspector).
    //
    // Jika validasi gagal, server akan mengirim pesan error yang akan ditampilkan di notifikasi.
    // ------------------------------------

    fetch("/step/add_mechanic", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
      body: JSON.stringify({ partId, stepNo }),
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.success) {
          showNotification(data.message, "success");
          location.reload();
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
      alert("MAN belum terisi. Anda harus 'Sign On' ke langkah ini terlebih dahulu.");
      return;
    }

    const hoursValue = document.getElementById(`hours-${stepNo}`).value;
    if (!hoursValue || hoursValue === "00:00" || hoursValue.trim() === "") {
      alert("HOURS belum terisi. Silakan gunakan timer Start/Stop untuk mencatat waktu kerja.");
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
          updateStepStatus(partId, stepNo, "in_progress");
        } else {
          showNotification("Gagal menyimpan approval: " + data.error, "error");
        }
      })
      .catch((error) => {
        showNotification("Terjadi kesalahan jaringan saat menyimpan approval.", "error");
      });
  }
}
