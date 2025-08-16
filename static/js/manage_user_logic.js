document.addEventListener("DOMContentLoaded", function () {
  // --- Fungsi Global ---
  function getCSRFToken() {
    return document.querySelector('meta[name="csrf-token"]')?.getAttribute("content") || "";
  }

  // --- Elemen Modal Pengguna ---
  const userModal = document.getElementById("user-modal");
  const userForm = document.getElementById("user-form");
  const modalTitle = document.getElementById("modal-title");
  const nikInput = document.getElementById("nik");
  const nikOriginalInput = document.getElementById("nik_original");
  const passwordInput = document.getElementById("password");
  const passwordHelp = document.getElementById("password-help");
  const roleSelect = document.getElementById("role");
  const mechanicFields = document.getElementById("mechanic-fields");

  // --- Elemen untuk visibilitas password ---
  const togglePasswordVisibilityButton = document.getElementById("toggle-password-visibility");
  const passwordToggleIcon = togglePasswordVisibilityButton.querySelector("i");

  // --- Elemen untuk Customer ---
  const customerCheckboxContainer = document.getElementById("customer-checkbox-container");
  const customerSearchInput = document.getElementById("customer-search-input");
  const selectAllCustomersCheckbox = document.getElementById("select-all-customers");

  // --- Elemen untuk Shop Area ---
  const shopAreaCheckboxContainer = document.getElementById("shop-area-checkbox-container");
  const shopAreaSearchInput = document.getElementById("shop-area-search-input");
  const selectAllShopAreasCheckbox = document.getElementById("select-all-shop-areas");

  // --- Elemen Modal Hapus ---
  const deleteModal = document.getElementById("delete-modal");
  const userToDeleteName = document.getElementById("user-to-delete-name");
  const confirmDeleteButton = document.getElementById("confirm-delete-button");
  const cancelDeleteButton = document.getElementById("cancel-delete-button");
  let nikToDelete = null;

  // --- Pencarian di Tabel Utama ---
  document.getElementById("search-input").addEventListener("input", function () {
    const searchTerm = this.value.toLowerCase().trim();
    document
      .getElementById("user-table-body")
      .querySelectorAll("tr")
      .forEach((row) => {
        const rowText = row.textContent.toLowerCase();
        row.style.display = rowText.includes(searchTerm) ? "" : "none";
      });
  });

  // --- Event listener untuk tombol lihat/sembunyikan password ---
  togglePasswordVisibilityButton.addEventListener("click", () => {
    const isPassword = passwordInput.type === "password";
    passwordInput.type = isPassword ? "text" : "password";
    passwordToggleIcon.classList.toggle("fa-eye");
    passwordToggleIcon.classList.toggle("fa-eye-slash");
  });

  /**
   * Fungsi generik untuk mengelola logika checkbox (pencarian, pilih semua).
   * @param {object} config - Konfigurasi elemen.
   */
  function manageCheckboxLogic(config) {
    function updateSelectAllState() {
      const allCheckboxes = Array.from(config.container.querySelectorAll(`.${config.wrapperClass} input[type='checkbox']`));
      if (!allCheckboxes.length) {
        config.selectAllCheckbox.checked = false;
        config.selectAllCheckbox.indeterminate = false;
        return;
      }
      const totalChecked = allCheckboxes.filter((cb) => cb.checked).length;
      if (totalChecked === allCheckboxes.length) {
        config.selectAllCheckbox.checked = true;
        config.selectAllCheckbox.indeterminate = false;
      } else if (totalChecked > 0) {
        config.selectAllCheckbox.checked = false;
        config.selectAllCheckbox.indeterminate = true;
      } else {
        config.selectAllCheckbox.checked = false;
        config.selectAllCheckbox.indeterminate = false;
      }
    }

    config.searchInput.addEventListener("input", () => {
      const searchTerm = config.searchInput.value.toLowerCase().trim();
      config.container.querySelectorAll(`.${config.wrapperClass}`).forEach((wrapper) => {
        const labelText = wrapper.querySelector("label")?.textContent.toLowerCase() || "";
        wrapper.style.display = labelText.includes(searchTerm) ? "flex" : "none";
      });
      // Do not update select all state on search to avoid confusion
    });

    config.selectAllCheckbox.addEventListener("change", () => {
      const isChecked = config.selectAllCheckbox.checked;
      // When "Select All" is toggled, it affects ALL checkboxes, not just visible ones.
      config.container.querySelectorAll(`.${config.wrapperClass} input[type='checkbox']`).forEach((checkbox) => {
        checkbox.checked = isChecked;
      });
      updateSelectAllState();
    });

    config.container.addEventListener("change", (event) => {
      if (event.target.type === "checkbox") {
        updateSelectAllState();
      }
    });

    return { updateSelectAllState };
  }

  // Inisialisasi logika untuk Customer dan Shop Area
  const customerLogic = manageCheckboxLogic({
    searchInput: customerSearchInput,
    selectAllCheckbox: selectAllCustomersCheckbox,
    container: customerCheckboxContainer,
    wrapperClass: "customer-checkbox-wrapper",
  });
  const shopAreaLogic = manageCheckboxLogic({
    searchInput: shopAreaSearchInput,
    selectAllCheckbox: selectAllShopAreasCheckbox,
    container: shopAreaCheckboxContainer,
    wrapperClass: "shop-area-checkbox-wrapper",
  });

  /**
   * Fungsi generik untuk mengambil data dan mengisi container checkbox.
   * @param {object} config
   */
  async function populateCheckboxes(config) {
    config.container.innerHTML = `<p class="text-gray-500 text-sm">Memuat data...</p>`;
    try {
      const response = await fetch(config.endpoint);
      if (!response.ok) throw new Error("Gagal mengambil data dari server.");
      const result = await response.json();
      config.container.innerHTML = ""; // Bersihkan container

      const items = result[config.itemKey] || [];
      const isAssignedAll = config.assignedItems.includes("*");

      if (items.length > 0) {
        items.forEach((item) => {
          const isChecked = isAssignedAll || config.assignedItems.includes(item);
          const wrapper = document.createElement("div");
          wrapper.className = `flex items-center ${config.wrapperClass}`;

          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.id = `${config.name}-${item.replace(/[\s/]+/g, "-")}`;
          checkbox.name = config.name;
          checkbox.value = item;
          checkbox.checked = isChecked;
          checkbox.className = "h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded";

          const label = document.createElement("label");
          label.htmlFor = checkbox.id;
          label.textContent = item;
          label.className = "ml-3 block text-sm font-medium text-gray-700";

          wrapper.appendChild(checkbox);
          wrapper.appendChild(label);
          config.container.appendChild(wrapper);
        });
      } else {
        config.container.innerHTML = `<p class="text-gray-500 text-sm">Tidak ada data ditemukan.</p>`;
      }
    } catch (error) {
      console.error(`Error populating ${config.name}:`, error);
      config.container.innerHTML = `<p class="text-red-500 text-sm">Error: ${error.message}</p>`;
    } finally {
      config.updateSelectAll();
    }
  }

  /**
   * [FIXED] Shows or hides mechanic-specific fields and populates them with data if needed.
   * This function is now the single source of truth for managing these fields.
   * @param {object} userData - Optional user data for pre-populating fields in edit mode.
   */
  async function toggleMechanicFields(userData = {}) {
    const assignedCustomers = userData.assigned_customers || [];
    const assignedShopArea = userData.assigned_shop_area || [];

    if (roleSelect.value === "mechanic") {
      mechanicFields.classList.remove("hidden");

      // Only populate if the container is empty, or if we are in edit mode (userData is provided).
      const needsPopulation = customerCheckboxContainer.innerHTML.trim() === "" || Object.keys(userData).length > 0;

      if (needsPopulation) {
        await Promise.all([
          populateCheckboxes({
            endpoint: "/get_all_customers",
            container: customerCheckboxContainer,
            name: "assigned_customers",
            itemKey: "customers",
            wrapperClass: "customer-checkbox-wrapper",
            assignedItems: assignedCustomers,
            updateSelectAll: customerLogic.updateSelectAllState,
          }),
          populateCheckboxes({
            endpoint: "/get_all_shop_areas",
            container: shopAreaCheckboxContainer,
            name: "assigned_shop_area",
            itemKey: "shop_areas",
            wrapperClass: "shop-area-checkbox-wrapper",
            assignedItems: assignedShopArea,
            updateSelectAll: shopAreaLogic.updateSelectAllState,
          }),
        ]);
      }
    } else {
      mechanicFields.classList.add("hidden");
    }
  }

  // This event listener now correctly populates the fields when the role is changed to 'mechanic'.
  roleSelect.addEventListener("change", toggleMechanicFields);

  window.openUserModal = async (nik = null) => {
    userForm.reset();
    mechanicFields.classList.add("hidden");
    customerSearchInput.value = "";
    shopAreaSearchInput.value = "";
    selectAllCustomersCheckbox.checked = false;
    selectAllShopAreasCheckbox.checked = false;
    // Clear the containers to ensure they are repopulated correctly on each modal open.
    customerCheckboxContainer.innerHTML = "";
    shopAreaCheckboxContainer.innerHTML = "";

    passwordInput.type = "password";
    passwordToggleIcon.classList.remove("fa-eye-slash");
    passwordToggleIcon.classList.add("fa-eye");

    if (nik) {
      // --- Mode Edit (FIXED) ---
      // The logic is now cleaner and more reliable.
      modalTitle.textContent = "Edit Pengguna";
      nikOriginalInput.value = nik;
      passwordInput.required = false;
      passwordHelp.textContent = "Kosongkan jika tidak ingin mengubah password.";

      try {
        const response = await fetch(`/users/${nik}`);
        if (!response.ok) throw new Error("Gagal mendapatkan data pengguna.");
        const data = await response.json();

        nikInput.value = data.nik;
        document.getElementById("name").value = data.name;
        roleSelect.value = data.role;
        passwordInput.value = ""; // Never pre-fill password for security

        // Single call to the refactored function handles both visibility and population.
        await toggleMechanicFields(data);
      } catch (error) {
        alert("Gagal memuat data pengguna: " + error.message);
        return;
      }
    } else {
      // --- Mode Tambah (FIXED) ---
      // This is also simplified.
      modalTitle.textContent = "Tambah Pengguna Baru";
      nikOriginalInput.value = "";
      passwordInput.required = true;
      passwordHelp.textContent = "Password wajib diisi untuk pengguna baru.";

      // Call the function to set the initial state.
      // If the default role is 'mechanic' (for admin), fields will show and populate.
      // If the user (superadmin) changes the role to 'mechanic', the event listener will handle it.
      await toggleMechanicFields();
    }
    userModal.classList.remove("hidden");
  };

  window.closeUserModal = () => userModal.classList.add("hidden");

  window.openDeleteModal = (nik, name) => {
    nikToDelete = nik;
    userToDeleteName.textContent = name;
    deleteModal.classList.remove("hidden");
  };

  window.closeDeleteModal = () => deleteModal.classList.add("hidden");

  cancelDeleteButton.addEventListener("click", closeDeleteModal);

  userForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const formData = new FormData(userForm);
    const data = Object.fromEntries(formData.entries());

    if (data.role === "mechanic") {
      if (selectAllCustomersCheckbox.checked) {
        data.assigned_customers = ["*"];
      } else {
        data.assigned_customers = Array.from(customerCheckboxContainer.querySelectorAll('input[name="assigned_customers"]:checked')).map((cb) => cb.value);
      }

      if (selectAllShopAreasCheckbox.checked) {
        data.assigned_shop_area = ["*"];
      } else {
        data.assigned_shop_area = Array.from(shopAreaCheckboxContainer.querySelectorAll('input[name="assigned_shop_area"]:checked')).map((cb) => cb.value);
      }
    } else {
      delete data.assigned_customers;
      delete data.assigned_shop_area;
    }

    if (data.nik_original && data.password === "") {
      delete data.password;
    }

    try {
      const response = await fetch("/users", {
        method: "POST",
        headers: { "Content-Type": "application/json", "X-CSRFToken": getCSRFToken() },
        body: JSON.stringify(data),
      });
      const result = await response.json();
      if (response.ok && result.success) {
        location.reload();
      } else {
        alert("Error: " + (result.error || "Gagal menyimpan data."));
      }
    } catch (error) {
      alert("Tidak dapat terhubung ke server.");
    }
  });

  confirmDeleteButton.addEventListener("click", async () => {
    if (!nikToDelete) return;
    try {
      const response = await fetch(`/users/${nikToDelete}`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCSRFToken() },
      });
      if (response.ok) {
        location.reload();
      } else {
        const result = await response.json();
        alert("Error: " + (result.error || "Gagal menghapus pengguna."));
      }
    } catch (error) {
      alert("Tidak dapat terhubung ke server.");
    }
  });
});
