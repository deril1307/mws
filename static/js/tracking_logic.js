// Script JavaScript untuk filter dan aksi pada halaman tracking.
document.addEventListener("DOMContentLoaded", function () {
  // --- BAGIAN FILTER (DENGAN FILTER STATUS) ---
  const searchInput = document.getElementById("mws-search-input");
  // ## PERUBAHAN ##: Variabel untuk step dropdown dihilangkan
  // const stepDropdown = document.getElementById("step-filter-dropdown");
  const customerDropdown = document.getElementById("customer-filter-dropdown");
  const statusDropdown = document.getElementById("status-filter-dropdown");
  const clearFiltersBtn = document.getElementById("clear-filters-btn");
  const partsContainer = document.getElementById("parts-container");
  const noResultsMessage = document.getElementById("no-results-message");
  const filterSummary = document.getElementById("filter-summary");
  const activeFiltersSpan = document.getElementById("active-filters");
  const filteredCountSpan = document.getElementById("filtered-count");

  // ## PERUBAHAN ##: Pengecekan stepDropdown dihapus dari kondisi if
  if (searchInput && partsContainer && noResultsMessage && statusDropdown) {
    const partCards = Array.from(partsContainer.getElementsByClassName("part-card"));

    function applyFilters() {
      const searchTerm = searchInput.value
        .toLowerCase()
        .trim()
        .replace(/[^a-zA-Z0-9]/g, "");
      // ## PERUBAHAN ##: Variabel untuk step terpilih dihilangkan
      // const selectedStep = stepDropdown.value.toLowerCase();
      const selectedCustomer = customerDropdown ? customerDropdown.value : "";
      const selectedStatus = statusDropdown.value;
      let visibleCounter = 0;
      let activeFilters = [];

      if (searchInput.value.trim()) activeFilters.push(`Pencarian: "${searchInput.value}"`);
      if (selectedCustomer) activeFilters.push(`Customer: "${selectedCustomer}"`);
      if (selectedStatus) {
        const statusText = statusDropdown.options[statusDropdown.selectedIndex].text;
        activeFilters.push(`Status: "${statusText}"`);
      }
      // ## PERUBAHAN ##: Logika untuk menampilkan filter step aktif dihilangkan
      // if (selectedStep) activeFilters.push(`Step: "${selectedStep}"`);

      for (const card of partCards) {
        const titleText = (card.dataset.title || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
        const customerName = (card.dataset.customer || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
        const partNumber = (card.dataset.partNumber || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
        const iwoNo = (card.dataset.iwoNo || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
        const wbsNo = (card.dataset.wbsNo || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
        const serialNumber = (card.dataset.serialNumber || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");

        // ## PERUBAHAN ##: Logika untuk mencocokkan step dihilangkan
        // const stepText = (card.querySelector(".step-info")?.textContent || "").toLowerCase();

        const searchMatch =
          searchTerm === "" || titleText.includes(searchTerm) || customerName.includes(searchTerm) || partNumber.includes(searchTerm) || iwoNo.includes(searchTerm) || wbsNo.includes(searchTerm) || serialNumber.includes(searchTerm);

        // ## PERUBAHAN ##: Variabel stepMatch dihilangkan
        // const stepMatch = selectedStep === "" || stepText.includes(selectedStep);
        const customerMatch = selectedCustomer === "" || card.dataset.customer === selectedCustomer;
        const statusMatch = selectedStatus === "" || card.dataset.status === selectedStatus;

        // ## PERUBAHAN ##: Pengecekan stepMatch dihapus dari kondisi if
        if (searchMatch && customerMatch && statusMatch) {
          card.style.display = "flex";
          visibleCounter++;
          const numberSpan = card.querySelector(".number-display");
          if (numberSpan) numberSpan.textContent = visibleCounter;
        } else {
          card.style.display = "none";
        }
      }

      if (activeFilters.length > 0) {
        filterSummary.classList.remove("hidden");
        activeFiltersSpan.textContent = activeFilters.join(", ");
        filteredCountSpan.textContent = `${visibleCounter} item ditemukan`;
      } else {
        filterSummary.classList.add("hidden");
      }
      noResultsMessage.style.display = visibleCounter === 0 ? "block" : "none";
      if (typeof window.filterChartsByCustomer === "function") {
        window.filterChartsByCustomer(selectedCustomer);
      }
    }

    searchInput.addEventListener("input", applyFilters);
    // ## PERUBAHAN ##: Event listener untuk step dropdown dihilangkan
    // stepDropdown.addEventListener("change", applyFilters);
    statusDropdown.addEventListener("change", applyFilters);
    if (customerDropdown) customerDropdown.addEventListener("change", applyFilters);
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener("click", () => {
        searchInput.value = "";
        // ## PERUBAHAN ##: Reset untuk step dropdown dihilangkan
        // stepDropdown.value = "";
        statusDropdown.value = "";
        if (customerDropdown) customerDropdown.value = "";
        applyFilters();
      });
    }
    document.addEventListener("click", (e) => {
      if (e.target.classList.contains("customer-name")) {
        const customerName = e.target.dataset.customer;
        if (customerDropdown) {
          customerDropdown.value = customerName;
          applyFilters();
          window.scrollTo({ top: 0, behavior: "smooth" });
        }
      }
    });
  }

  // --- BAGIAN MODAL KONFIRMASI (TIDAK ADA PERUBAHAN) ---
  const modal = document.getElementById("confirmation-modal");
  const modalContent = document.getElementById("modal-content");
  const modalTitle = document.getElementById("modal-title");
  const modalMessage = document.getElementById("modal-message");
  const confirmBtn = document.getElementById("modal-confirm-btn");
  const cancelBtn = document.getElementById("modal-cancel-btn");
  let onConfirmCallback = null;

  function showConfirmationModal(title, message, onConfirm) {
    modalTitle.textContent = title;
    modalMessage.textContent = message;
    onConfirmCallback = onConfirm;
    modal.classList.remove("hidden");
    setTimeout(() => modalContent.classList.remove("scale-95", "opacity-0"), 10);
  }

  function hideConfirmationModal() {
    modalContent.classList.add("scale-95", "opacity-0");
    setTimeout(() => {
      modal.classList.add("hidden");
      onConfirmCallback = null;
    }, 300);
  }

  confirmBtn.addEventListener("click", () => {
    if (onConfirmCallback) onConfirmCallback();
    hideConfirmationModal();
  });
  cancelBtn.addEventListener("click", hideConfirmationModal);
  modal.addEventListener("click", (e) => {
    if (e.target === modal) hideConfirmationModal();
  });

  // --- BAGIAN AKSI URGENT ---
  document.body.addEventListener("click", function (event) {
    const button = event.target.closest(".urgent-action-btn");
    if (button) {
      const partId = button.dataset.partId;
      const action = button.dataset.action;
      let confirmationTitle = "Konfirmasi Aksi";
      let confirmationMessage = "Apakah Anda yakin ingin melanjutkan aksi ini?";
      const buttonText = button.textContent.trim();

      if (action === "request") {
        confirmationTitle = "Minta Urgensi";
        confirmationMessage = "Anda akan meminta status urgensi untuk MWS ini. Lanjutkan?";
      } else if (action === "approve") {
        confirmationTitle = "Setujui Permintaan";
        confirmationMessage = "Anda akan menyetujui permintaan dan menjadikan MWS ini urgen. Lanjutkan?";
      } else if (action === "toggle") {
        confirmationTitle = buttonText.includes("Cancel Urgent") ? "Hapus Status Urgent" : "Jadikan Urgent";
        confirmationMessage = `Anda akan ${buttonText.includes("Cancel Urgent") ? "menghapus status urgensi dari" : "menjadikan"} MWS ini urgen. Lanjutkan?`;
      } else if (action === "cancel_request") {
        confirmationTitle = "Batalkan Permintaan Urgensi";
        confirmationMessage = "Anda yakin ingin membatalkan permintaan urgensi untuk MWS ini?";
        // ## PERUBAHAN ##: Logika konfirmasi untuk aksi baru "reject_request"
      } else if (action === "reject_request") {
        confirmationTitle = "Tolak Permintaan Urgensi";
        confirmationMessage = "Anda yakin ingin menolak permintaan urgensi untuk MWS ini? Status akan kembali normal.";
      }

      showConfirmationModal(confirmationTitle, confirmationMessage, async () => {
        button.disabled = true;
        button.innerHTML += ' <i class="fas fa-spinner fa-spin"></i>';
        const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");

        try {
          const response = await fetch(`/set_urgent_status/${partId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({ action: action }),
          });
          const data = await response.json();
          if (data.success) {
            window.location.reload();
          } else {
            alert("Error: " + (data.error || "Terjadi kesalahan."));
            button.disabled = false;
            button.querySelector(".fa-spinner")?.remove();
          }
        } catch (error) {
          console.error("Fetch error:", error);
          alert("Terjadi kesalahan jaringan.");
          button.disabled = false;
          button.querySelector(".fa-spinner")?.remove();
        }
      });
    }
  });
});

// --- BAGIAN MODAL HAPUS (TIDAK ADA PERUBAHAN) ---
const deleteModal = document.getElementById("delete-modal");
const confirmDeleteButton = document.getElementById("confirm-delete-button");
const cancelDeleteButton = document.getElementById("cancel-delete-button");
const partToDeleteName = document.getElementById("part-to-delete-name");
let partIdToDelete = null;

window.showDeleteModal = function (partId, partName) {
  partIdToDelete = partId;
  partToDeleteName.textContent = partName;
  if (deleteModal) {
    deleteModal.classList.remove("hidden");
    requestAnimationFrame(() => deleteModal.classList.remove("opacity-0"));
  }
};

const hideDeleteModal = () => {
  if (deleteModal) {
    deleteModal.classList.add("opacity-0");
    setTimeout(() => deleteModal.classList.add("hidden"), 300);
  }
};

cancelDeleteButton?.addEventListener("click", hideDeleteModal);

confirmDeleteButton?.addEventListener("click", async () => {
  if (partIdToDelete) {
    const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute("content");
    try {
      const response = await fetch(`/delete_mws/${partIdToDelete}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": csrfToken,
        },
      });
      const data = await response.json();
      if (data.success) {
        location.reload();
      } else {
        alert("Gagal menghapus: " + data.error);
      }
    } catch (err) {
      console.error("Error saat menghapus MWS:", err);
      alert("Terjadi kesalahan jaringan saat mencoba menghapus.");
    }
  }
  hideDeleteModal();
});
