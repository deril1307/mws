document.addEventListener("DOMContentLoaded", function () {
  setupDropdown("notification-button", "notification-dropdown");
  // --- Elemen-elemen DOM ---
  const searchInput = document.getElementById("mws-search-input");
  const statusDropdown = document.getElementById("status-filter-dropdown");
  const clearFiltersBtn = document.getElementById("clear-filters-btn");
  const partsContainer = document.getElementById("parts-container");
  const noResultsMessage = document.getElementById("no-results-message");
  const filterSummary = document.getElementById("filter-summary");
  const activeFiltersSpan = document.getElementById("active-filters");
  const filteredCountSpan = document.getElementById("filtered-count");
  const paginationContainer = document.getElementById("pagination-container");
  const loadingIndicator = document.getElementById("loading-indicator");

  // --- State Aplikasi ---
  let currentPage = 1;
  let selectedCustomers = [];
  let selectedShopAreas = [];
  let searchTimeout;

  // --- Fungsi Utama untuk Mengambil dan Merender Data ---
  async function fetchAndRenderMws(page = 1) {
    currentPage = page;
    loadingIndicator.style.display = "block";
    noResultsMessage.style.display = "none";
    partsContainer.innerHTML = ""; // Kosongkan container sebelum memuat

    // 1. Bangun URL dengan parameter query
    const searchTerm = searchInput.value.trim();
    const selectedStatus = statusDropdown.value;
    const params = new URLSearchParams({
      page: currentPage,
      q: searchTerm,
      status: selectedStatus,
      customers: selectedCustomers.join(","),
      shop_areas: selectedShopAreas.join(","),
    });

    try {
      // 2. Lakukan request ke API
      const response = await fetch(`/api/mws-paginated?${params.toString()}`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const result = await response.json();

      // 3. Proses respons
      loadingIndicator.style.display = "none";
      if (result.success && result.parts.length > 0) {
        renderPartCards(result.parts);
        renderPagination(result.meta);
      } else {
        partsContainer.innerHTML = ""; // Pastikan kosong
        paginationContainer.innerHTML = ""; // Kosongkan paginasi jika tidak ada hasil
        noResultsMessage.style.display = "block";
      }
      updateFilterSummary(result.meta);
    } catch (error) {
      console.error("Fetch error:", error);
      loadingIndicator.style.display = "none";
      partsContainer.innerHTML = `<div class="text-center py-12 text-red-500">Gagal memuat data. Silakan coba lagi.</div>`;
    }
  }

  // --- Fungsi untuk Mengambil Data Filter Dinamis (Peningkatan) ---
  async function populateFilterDropdowns() {
    // Fungsi ini akan menggantikan data filter statis dengan data dari API
    try {
      const [customerRes, shopAreaRes] = await Promise.all([fetch("/get_all_customers"), fetch("/get_all_shop_areas")]);

      if (customerRes.ok) {
        const customerData = await customerRes.json();
        const customerListDiv = document.getElementById("customer-filter-list");
        if (customerListDiv && customerData.success) {
          customerListDiv.innerHTML = customerData.customers
            .map(
              (customer) => `
            <label class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">
              <input type="checkbox" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" value="${customer}" data-filter-type="customer" />
              <span class="ml-3">${customer}</span>
            </label>`
            )
            .join("");
        }
      }

      if (shopAreaRes.ok) {
        const shopAreaData = await shopAreaRes.json();
        const shopAreaListDiv = document.getElementById("shop-area-filter-list");
        if (shopAreaListDiv && shopAreaData.success) {
          shopAreaListDiv.innerHTML = shopAreaData.shop_areas
            .map(
              (area) => `
             <label class="flex items-center px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 cursor-pointer">
              <input type="checkbox" class="h-4 w-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500" value="${area}" data-filter-type="shop-area" />
              <span class="ml-3">${area}</span>
            </label>`
            )
            .join("");
        }
      }
    } catch (error) {
      console.error("Gagal memuat data filter:", error);
    }
  }

  // --- Sisa Fungsi Render (tidak berubah) ---
  function renderPartCards(parts) {
    let cardHtml = "";
    parts.forEach((part, index) => {
      const displayIndex = (currentPage - 1) * 50 + index + 1;
      cardHtml += createPartCardHtml(part, displayIndex);
    });
    partsContainer.innerHTML = cardHtml;
  }

  function renderPagination(meta) {
    if (!meta || meta.total_pages <= 1) {
      paginationContainer.innerHTML = "";
      return;
    }

    let paginationHtml = `
      <div class="text-sm text-gray-700">
        Menampilkan <span class="font-medium">${(meta.page - 1) * meta.per_page + 1}</span>
        sampai <span class="font-medium">${Math.min(meta.page * meta.per_page, meta.total_items)}</span>
        dari <span class="font-medium">${meta.total_items}</span> hasil
      </div>
      <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px" aria-label="Pagination">
    `;

    // Tombol Previous
    paginationHtml += `<a href="#" data-page="${meta.page - 1}" class="pagination-btn ${!meta.has_prev ? "disabled" : ""}"><i class="fas fa-chevron-left"></i></a>`;

    // Logika untuk menampilkan nomor halaman
    const pagesToShow = getPaginationPages(meta.page, meta.total_pages);
    pagesToShow.forEach((p) => {
      if (p === "...") {
        paginationHtml += `<span class="pagination-ellipsis">...</span>`;
      } else {
        paginationHtml += `<a href="#" data-page="${p}" class="pagination-btn ${p === meta.page ? "active" : ""}">${p}</a>`;
      }
    });

    // Tombol Next
    paginationHtml += `<a href="#" data-page="${meta.page + 1}" class="pagination-btn ${!meta.has_next ? "disabled" : ""}"><i class="fas fa-chevron-right"></i></a>`;

    paginationHtml += `</nav>`;
    paginationContainer.innerHTML = paginationHtml;
  }

  function getPaginationPages(currentPage, totalPages, width = 2) {
    if (totalPages <= width * 2 + 3) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }
    let pages = [1];
    if (currentPage - width > 2) pages.push("...");
    for (let i = Math.max(2, currentPage - width); i <= Math.min(totalPages - 1, currentPage + width); i++) {
      pages.push(i);
    }
    if (currentPage + width < totalPages - 1) pages.push("...");
    pages.push(totalPages);
    return pages;
  }

  function updateFilterSummary(meta) {
    if (!meta) {
      filterSummary.classList.add("hidden");
      return;
    }
    const searchTerm = searchInput.value.trim();
    const statusText = statusDropdown.options[statusDropdown.selectedIndex].text;

    let activeFilters = [];
    if (searchTerm) activeFilters.push(`Pencarian: "${searchTerm}"`);
    if (selectedCustomers.length > 0) activeFilters.push(`Customer: "${selectedCustomers.join(", ")}"`);
    if (selectedShopAreas.length > 0) activeFilters.push(`Shop Area: "${selectedShopAreas.join(", ")}"`);
    if (statusDropdown.value) activeFilters.push(`Status: "${statusText}"`);

    if (activeFilters.length > 0) {
      filterSummary.classList.remove("hidden");
      activeFiltersSpan.textContent = activeFilters.join(" | ");
      filteredCountSpan.textContent = `${meta.total_items} item ditemukan`;
    } else {
      filterSummary.classList.add("hidden");
    }
  }

  // --- Setup Event Listeners ---

  searchInput.addEventListener("input", () => {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(() => {
      fetchAndRenderMws(1);
    }, 500);
  });

  statusDropdown.addEventListener("change", () => fetchAndRenderMws(1));
  clearFiltersBtn.addEventListener("click", () => {
    searchInput.value = "";
    statusDropdown.value = "";
    selectedCustomers = [];
    selectedShopAreas = [];

    document.querySelectorAll('[id$="-filter-panel"]').forEach((panel) => {
      panel.querySelector('input[type="text"]').value = "";
      panel.querySelectorAll("label").forEach((label) => label.classList.remove("hidden"));
      panel.querySelectorAll('input[type="checkbox"]').forEach((cb) => (cb.checked = false));
    });

    updateButtonText(document.getElementById("customer-filter-text"), "customer");
    updateButtonText(document.getElementById("shop-area-filter-text"), "shop-area");

    fetchAndRenderMws(1);
  });

  paginationContainer.addEventListener("click", (e) => {
    e.preventDefault();
    const target = e.target.closest(".pagination-btn");
    if (target && !target.classList.contains("disabled") && !target.classList.contains("active")) {
      const page = parseInt(target.dataset.page, 10);
      fetchAndRenderMws(page);
    }
  });

  // --- Logika Dropdown Multi-Pilih ---
  function setupCustomDropdown(btnId, panelId, textId, type) {
    const btn = document.getElementById(btnId);
    const panel = document.getElementById(panelId);
    const textSpan = document.getElementById(textId);
    const listContainer = document.getElementById(`${type}-filter-list`); // Ambil kontainer list dinamis

    if (!btn || !panel || !listContainer) return;

    const searchInput = panel.querySelector('input[type="text"]');

    btn.addEventListener("click", (event) => {
      event.stopPropagation();
      closeAllDropdowns(panelId);
      panel.classList.toggle("hidden");
      if (!panel.classList.contains("hidden")) searchInput.focus();
    });

    searchInput.addEventListener("input", () => {
      const searchTerm = searchInput.value.toLowerCase().trim();
      const labels = listContainer.querySelectorAll("label"); // Cari label di dalam kontainer yang dinamis
      labels.forEach((label) => {
        const labelText = label.textContent.toLowerCase().trim();
        label.classList.toggle("hidden", !labelText.includes(searchTerm));
      });
    });

    // Gunakan event delegation karena checkbox dibuat secara dinamis
    listContainer.addEventListener("change", (event) => {
      if (event.target.type === "checkbox") {
        updateSelections(listContainer, type);
        updateButtonText(textSpan, type);
        fetchAndRenderMws(1);
      }
    });
  }

  function closeAllDropdowns(excludePanelId = null) {
    document.querySelectorAll('[id$="-filter-panel"]').forEach((p) => {
      if (p.id !== excludePanelId) p.classList.add("hidden");
    });
  }

  window.addEventListener("click", () => closeAllDropdowns());

  function updateSelections(listContainer, type) {
    const selected = Array.from(listContainer.querySelectorAll('input[type="checkbox"]:checked')).map((cb) => cb.value);
    if (type === "customer") selectedCustomers = selected;
    else if (type === "shop-area") selectedShopAreas = selected;
  }

  function updateButtonText(textSpan, type) {
    const placeholder = type === "customer" ? "Pilih Customer" : "Pilih Shop Area";
    const selections = type === "customer" ? selectedCustomers : selectedShopAreas;
    if (selections.length === 0) textSpan.textContent = placeholder;
    else if (selections.length <= 2) textSpan.textContent = selections.join(", ");
    else textSpan.textContent = `${selections.length} item terpilih`;
  }

  setupCustomDropdown("customer-filter-btn", "customer-filter-panel", "customer-filter-text", "customer");
  setupCustomDropdown("shop-area-filter-btn", "shop-area-filter-panel", "shop-area-filter-text", "shop-area");

  // --- Sisa kode untuk Modal dan Aksi lainnya (tidak berubah) ---
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
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute("content"); // Tambah safety check

        try {
          const response = await fetch(`/set_urgent_status/${partId}`, {
            method: "POST",
            headers: { "Content-Type": "application/json", "X-CSRFToken": csrfToken },
            body: JSON.stringify({ action: action }),
          });
          const data = await response.json();
          if (data.success) {
            // Panggil lagi fetchAndRenderMws daripada reload halaman penuh
            fetchAndRenderMws(currentPage);
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

  // --- Inisialisasi ---
  // Hapus pemanggilan populateFilterDropdowns jika Anda lebih suka data awal dari Jinja
  // populateFilterDropdowns(); // Opsional: Uncomment jika ingin filter selalu dinamis
  fetchAndRenderMws();
});

// --- Sisa fungsi createPartCardHtml dan logika modal hapus tidak berubah ---
// ... (salin sisa kode dari file tracking_logic.js asli Anda di sini) ...
function createPartCardHtml(part, index) {
  // Fungsi ini membuat string HTML untuk satu kartu MWS.
  // Logika dari template Jinja2 dipindahkan ke sini.
  const part_id = part.part_id;

  // Border
  let borderColorClass = "border-gray-200";
  if (part.is_urgent) borderColorClass = "border-red-500 border-2";
  else if (part.urgent_request) borderColorClass = "border-yellow-400 border-2";
  else if (part.shopArea === "FO") borderColorClass = "border-l-8 border-l-gray-800 border-gray-200";
  else if (part.status === "completed") borderColorClass = "border-l-8 border-l-blue-500 border-gray-200";
  else if (part.status === "in_progress") borderColorClass = "border-l-8 border-l-green-500 border-gray-200";
  else if (part.status === "pending") borderColorClass = "border-l-8 border-l-red-400 border-gray-200";

  // Status Badge
  let statusBadgeHtml = `<span class="px-3 py-1 rounded-full text-xs font-bold flex items-center bg-gray-100 text-gray-800 border border-gray-300"><i class="mr-2"></i> Pending</span>`;
  if (part.is_urgent) {
    statusBadgeHtml = `<span class="px-3 py-1 rounded-full text-xs font-bold flex items-center bg-red-100 text-red-800 border border-red-300"><i class="fas fa-fire-alt mr-2"></i> URGENT !!</span>`;
  } else if (part.shopArea === "FO") {
    statusBadgeHtml = `<span class="px-3 py-1 rounded-full text-xs font-bold flex items-center bg-gray-600 text-white border border-gray-600"><i class="fas fa-tools mr-2" style="display: none"></i> FO</span>`;
  } else if (part.status === "completed") {
    statusBadgeHtml = `<span class="px-3 py-1 rounded-full text-xs font-bold flex items-center bg-blue-100 text-blue-800 border border-blue-300"><i class="mr-2"></i> Completed</span>`;
  } else if (part.status === "in_progress") {
    statusBadgeHtml = `<span class="px-3 py-1 rounded-full text-xs font-bold flex items-center bg-green-100 text-green-800 border border-green-300"><i class="mr-2"></i> In Progress</span>`;
  } else if (part.status === "pending") {
    statusBadgeHtml = `<span class="px-3 py-1 rounded-full text-xs font-bold flex items-center bg-red-100 text-red-800 border border-red-300"><i class="mr-2"></i> Pending</span>`;
  }

  // Urgent Request Badge (jika ada)
  let urgentRequestBadge = "";
  if (part.urgent_request && !part.is_urgent && ["admin", "superadmin"].includes(currentUserRole)) {
    urgentRequestBadge = `<span class="ml-2 px-3 py-1 rounded-full text-xs font-medium bg-yellow-400 text-yellow-900 animate-pulse"> <i class="fas fa-bell mr-1"></i> Permintaan Urgensi </span>`;
  }

  // Tombol Aksi
  let actionButtonsHtml = "";
  const mwsDetailUrl = `/mws/${part_id}`; // Bangun URL secara manual
  if (currentUserRole === "customer") {
    actionButtonsHtml = `<a href="${mwsDetailUrl}" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"> <i class="fas fa-eye mr-2"></i>Lihat MWS </a>`;
  } else {
    // Logika untuk tombol urgensi
    if (["admin", "superadmin"].includes(currentUserRole)) {
      if (part.urgent_request && !part.is_urgent) {
        actionButtonsHtml += `<button class="urgent-action-btn px-3 py-2 bg-blue-500 hover:bg-blue-600 text-white text-xs font-bold rounded-lg" data-part-id="${part_id}" data-action="approve"><i class="fas fa-check-circle mr-1"></i> Setujui</button>
                                     <button class="urgent-action-btn px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-lg" data-part-id="${part_id}" data-action="reject_request"><i class="fas fa-times-circle mr-1"></i> Tolak</button>`;
      } else if (part.is_urgent) {
        actionButtonsHtml += `<button class="urgent-action-btn px-3 py-2 bg-gray-500 hover:bg-gray-600 text-white text-xs font-bold rounded-lg" data-part-id="${part_id}" data-action="toggle"><i class="fas fa-times-circle mr-1"></i> Cancel Urgent</button>`;
      } else if (part.status !== "completed") {
        actionButtonsHtml += `<button class="urgent-action-btn px-3 py-2 bg-yellow-400 hover:bg-yellow-500 text-yellow-800 text-xs font-bold rounded-lg" data-part-id="${part_id}" data-action="toggle"><i class="fas fa-exclamation-triangle mr-1"></i> Jadikan Urgent</button>`;
      }
    } else if (currentUserRole === "mechanic") {
      if (part.is_urgent) {
        actionButtonsHtml += `<span class="px-3 py-2 text-red-600 text-sm font-bold"> <i class="fas fa-fire mr-1"></i>URGENT</span>`;
      } else if (part.urgent_request) {
        actionButtonsHtml += `<button class="px-3 py-2 bg-gray-300 text-gray-500 text-xs font-bold rounded-lg cursor-not-allowed" disabled><i class="fas fa-clock mr-1"></i> Menunggu Persetujuan</button>
                                      <button class="urgent-action-btn px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-xs font-bold rounded-lg" data-part-id="${part_id}" data-action="cancel_request"><i class="fas fa-ban mr-1"></i> Batal Urgensi</button>`;
      } else if (part.status !== "completed") {
        actionButtonsHtml += `<button class="urgent-action-btn px-3 py-2 bg-red-500 hover:bg-orange-600 text-white text-xs font-bold rounded-lg" data-part-id="${part_id}" data-action="request"><i class="fas fa-bell mr-1"></i> Minta Urgensi</button>`;
      }
    }

    // Tombol Kelola/Lihat MWS
    if (currentUserRole === "admin") {
      actionButtonsHtml += `<a href="${mwsDetailUrl}" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"> <i class="fas fa-eye mr-2"></i>Kelola MWS </a>
                                <button onclick="showDeleteModal('${part_id}', '${part.tittle}')" class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm"><i class="fas fa-trash-alt"></i></button>`;
    } else if (currentUserRole === "superadmin") {
      actionButtonsHtml += `<a href="${mwsDetailUrl}" class="bg-blue-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg text-sm font-medium"> <i class="fas fa-user-shield mr-2"></i>Kelola MWS </a>
                                <button onclick="showDeleteModal('${part_id}', '${part.tittle}')" class="bg-red-600 hover:bg-red-700 text-white px-3 py-2 rounded-lg text-sm"><i class="fas fa-trash-alt"></i></button>`;
    } else if (currentUserRole === "mechanic") {
      actionButtonsHtml += `<a href="${mwsDetailUrl}" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"> <i class="fas fa-eye mr-2"></i>Kerjakan MWS</a>`;
    } else if (["quality1", "quality2"].includes(currentUserRole)) {
      actionButtonsHtml += `<a href="${mwsDetailUrl}" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium"> <i class="fas fa-eye mr-2"></i>Lihat MWS</a>`;
    }
  }

  // Progress Bar / Footer
  const progress_percentage = part.progress_percentage || 0;
  let footerHtml = "";
  let footerBgClass = "bg-gray-50";
  if (part.shopArea === "FO") {
    footerBgClass = "bg-gray-100";
    footerHtml = `<div class="flex items-center"><div class="flex-shrink-0"><i class="fas fa-tools text-gray-600 text-2xl"></i></div><div class="ml-4 flex-grow"><div class="text-md font-bold text-gray-600">Form Out</div><div class="text-sm text-gray-600">Pekerjaan di area FO.</div></div></div>`;
  } else if (part.status === "completed") {
    footerBgClass = "bg-blue-50";
    footerHtml = `<div class="flex items-center"><div class="flex-shrink-0"><i class="fas fa-check-circle text-blue-500 text-2xl"></i></div><div class="ml-4 flex-grow"><div class="text-md font-bold text-blue-800">Pekerjaan Selesai</div><div class="text-sm text-gray-600">Semua langkah telah selesai diverifikasi.</div></div></div>`;
  } else if (part.status === "in_progress") {
    footerBgClass = "bg-green-50";
    const currentStepDescription = part.steps.find((s) => s.no == part.currentStep)?.description || "";
    footerHtml = `<div><div class="flex justify-between items-center mb-1"><span class="step-info text-sm font-bold text-green-800 truncate"><i class="fas fa-clock mr-2"></i>Step ${part.currentStep}: <span class="font-medium">${currentStepDescription}</span><span class="font-bold text-green-800 ml-2">${progress_percentage}%</span></span></div><div class="w-full bg-gray-200 rounded-full h-3"><div class="bg-green-500 h-3 rounded-full" style="width: ${progress_percentage}%"></div></div></div>`;
  } else if (part.status === "pending") {
    footerBgClass = "bg-red-50";
    footerHtml = `<div class="flex items-center"><div class="flex-shrink-0"><i class="fas fa-pause-circle text-red-500 text-2xl"></i></div><div class="ml-4 flex-grow"><div class="step-info text-md font-bold text-red-800">Menunggu Dimulai</div></div></div>`;
  } else {
    footerHtml = `<div class="flex items-center"><div class="flex-shrink-0"><i class="fas fa-info-circle text-gray-500 text-2xl"></i></div><div class="ml-4 flex-grow"><div class="step-info text-md font-bold text-gray-800">Pending</div><div class="text-sm text-gray-600">Status tidak diketahui.</div></div></div>`;
  }

  return `
    <div class="part-card flex border rounded-lg card-hover overflow-hidden shadow-sm transition-all duration-300 ${borderColorClass}">
        <div class="flex-shrink-0 w-16 flex items-center justify-center bg-gray-50 border-r border-gray-200">
            <span class="number-display text-2xl font-bold text-gray-400">${index}</span>
        </div>
        <div class="flex-grow">
            <div class="p-4 bg-white">
                <div class="flex flex-col md:flex-row md:justify-between md:items-start">
                    <div class="flex-1 mb-4 md:mb-0">
                        <div class="flex items-center mb-2 flex-wrap gap-2">
                            <h3 class="mws-title text-lg font-semibold text-gray-800 mr-3">${part.customer} - ${part.tittle}</h3>
                            ${statusBadgeHtml}
                            ${urgentRequestBadge}
                        </div>
                        <div class="grid grid-cols-1 lg:grid-cols-2 gap-x-6 gap-y-2 text-sm text-gray-600">
                            <div class="flex flex-col space-y-1">
                                <div><span class="font-medium text-black">Part Number:</span> <span class="searchable-part-number text-black">${part.partNumber}</span></div>
                                <div><span class="font-medium text-black">IWO No:</span> <span class="searchable-iwo-no text-black">${part.iwoNo}</span></div>
                            </div>
                            <div class="flex flex-col space-y-1">
                                ${part.wbsNo ? `<div><span class="font-medium text-black">WBS No:</span> <span class="searchable-wbs-no text-black">${part.wbsNo}</span></div>` : ""}
                                ${part.serialNumber ? `<div><span class="font-medium text-black">Serial Number:</span> <span class="searchable-serial-number text-black">${part.serialNumber}</span></div>` : ""}
                                <div><span class="font-medium text-black">Component Order:</span> <span class="text-black">${part.jobType}</span></div>
                                ${part.shopArea ? `<div><span class="font-medium text-black">Shop Area:</span> <span class="text-black">${part.shopArea}</span></div>` : ""}
                            </div>
                        </div>
                    </div>
                    <div class="flex items-center space-x-2 flex-shrink-0">
                        ${actionButtonsHtml}
                    </div>
                </div>
            </div>
            <div class="p-3 border-t ${footerBgClass}">
                ${footerHtml}
            </div>
        </div>
    </div>
    `;
}

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
      const response = await fetch(`/delete-mws/${partIdToDelete}`, {
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
