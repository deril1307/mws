document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("mws-search-input");
  const statusDropdown = document.getElementById("status-filter-dropdown");
  const clearFiltersBtn = document.getElementById("clear-filters-btn");
  const partsContainer = document.getElementById("parts-container");
  const noResultsMessage = document.getElementById("no-results-message");
  const filterSummary = document.getElementById("filter-summary");
  const activeFiltersSpan = document.getElementById("active-filters");
  const filteredCountSpan = document.getElementById("filtered-count");
  const partCards = Array.from(partsContainer.getElementsByClassName("part-card"));

  // Variabel untuk menyimpan state filter multi-pilih
  let selectedCustomers = [];
  let selectedShopAreas = [];
  function setupCustomDropdown(btnId, panelId, textId, type) {
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    const textSpan = document.getElementById(textId);

    if (!btn || !panel) return;

    //  Dapatkan elemen search input dan semua label di dalam panel
    const searchInput = panel.querySelector('input[type="text"]');
    const labels = panel.querySelectorAll("label");

    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      closeAllDropdowns(panelId);
      panel.classList.toggle("hidden");
      // Fokus ke search bar saat dropdown dibuka
      if (!panel.classList.contains("hidden")) {
        searchInput.focus();
      }
    });

    // MODIFIKASI: Tambahkan event listener untuk search bar
    searchInput.addEventListener("input", () => {
      const searchTerm = searchInput.value.toLowerCase().trim();
      labels.forEach((label) => {
        const labelText = label.textContent.toLowerCase().trim();
        // Tampilkan atau sembunyikan label berdasarkan kecocokan
        label.classList.toggle("hidden", !labelText.includes(searchTerm));
      });
    });

    const checkboxes = panel.querySelectorAll('input[type="checkbox"]');
    checkboxes.forEach((checkbox) => {
      checkbox.addEventListener("change", () => {
        updateSelections(checkboxes, type);
        updateButtonText(textSpan, type);
        applyFilters();
      });
    });
  }

  function closeAllDropdowns(excludePanelId = null) {
    const allPanels = document.querySelectorAll('[id$="-filter-panel"]');
    allPanels.forEach((p) => {
      if (p.id !== excludePanelId) {
        p.classList.add("hidden");
      }
    });
  }

  window.addEventListener("click", () => {
    closeAllDropdowns();
  });

  function updateSelections(checkboxes, type) {
    const selected = Array.from(checkboxes)
      .filter((cb) => cb.checked)
      .map((cb) => cb.value);

    if (type === "customer") {
      selectedCustomers = selected;
    } else if (type === "shop-area") {
      selectedShopAreas = selected;
    }
  }

  function updateButtonText(textSpan, type) {
    const placeholder = type === "customer" ? "Pilih Customer" : "Pilih Shop Area";
    const selections = type === "customer" ? selectedCustomers : selectedShopAreas;

    if (selections.length === 0) {
      textSpan.textContent = placeholder;
    } else if (selections.length <= 2) {
      textSpan.textContent = selections.join(", ");
    } else {
      textSpan.textContent = `${selections.length} item terpilih`;
    }
  }

  setupCustomDropdown("customer-filter-btn", "customer-filter-panel", "customer-filter-text", "customer");
  setupCustomDropdown("shop-area-filter-btn", "shop-area-filter-panel", "shop-area-filter-text", "shop-area");
  function applyFilters() {
    const searchTerm = searchInput.value
      .toLowerCase()
      .trim()
      .replace(/[^a-zA-Z0-9]/g, "");
    const selectedStatus = statusDropdown.value;

    let visibleCounter = 0;
    let activeFilters = [];

    if (searchInput.value.trim()) activeFilters.push(`Pencarian: "${searchInput.value}"`);
    if (selectedCustomers.length > 0) activeFilters.push(`Customer: "${selectedCustomers.join(", ")}"`);
    if (selectedShopAreas.length > 0) activeFilters.push(`Shop Area: "${selectedShopAreas.join(", ")}"`);

    if (selectedStatus) {
      const statusText = statusDropdown.options[statusDropdown.selectedIndex].text;
      activeFilters.push(`Status: "${statusText}"`);
    }

    for (const card of partCards) {
      const titleText = (card.dataset.title || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
      const customerName = (card.dataset.customer || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
      const partNumber = (card.dataset.partNumber || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
      const iwoNo = (card.dataset.iwoNo || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
      const wbsNo = (card.dataset.wbsNo || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");
      const serialNumber = (card.dataset.serialNumber || "").toLowerCase().replace(/[^a-zA-Z0-9]/g, "");

      const searchMatch =
        searchTerm === "" || titleText.includes(searchTerm) || customerName.includes(searchTerm) || partNumber.includes(searchTerm) || iwoNo.includes(searchTerm) || wbsNo.includes(searchTerm) || serialNumber.includes(searchTerm);

      const customerMatch = selectedCustomers.length === 0 || selectedCustomers.includes(card.dataset.customer);
      const shopAreaMatch = selectedShopAreas.length === 0 || selectedShopAreas.includes(card.dataset.shopArea);
      const statusMatch = selectedStatus === "" || card.dataset.status === selectedStatus;

      if (searchMatch && customerMatch && statusMatch && shopAreaMatch) {
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
      activeFiltersSpan.textContent = activeFilters.join(" | ");
      filteredCountSpan.textContent = `${visibleCounter} item ditemukan`;
    } else {
      filterSummary.classList.add("hidden");
    }
    noResultsMessage.style.display = visibleCounter === 0 ? "block" : "none";
  }

  searchInput.addEventListener("input", applyFilters);
  statusDropdown.addEventListener("change", applyFilters);

  clearFiltersBtn.addEventListener("click", () => {
    searchInput.value = "";
    statusDropdown.value = "";

    selectedCustomers = [];
    selectedShopAreas = [];

    // Kosongkan juga search bar di dalam dropdown dan tampilkan semua item
    document.querySelectorAll('[id$="-filter-panel"]').forEach((panel) => {
      const searchInput = panel.querySelector('input[type="text"]');
      if (searchInput) searchInput.value = "";
      panel.querySelectorAll("label").forEach((label) => label.classList.remove("hidden"));
      panel.querySelectorAll('input[type="checkbox"]').forEach((cb) => (cb.checked = false));
    });

    updateButtonText(document.getElementById("customer-filter-text"), "customer");
    updateButtonText(document.getElementById("shop-area-filter-text"), "shop-area");

    applyFilters();
  });

  // --- BAGIAN MODAL KONFIRMASI DAN AKSI ---
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
