document.addEventListener("DOMContentLoaded", function () {
  // Fungsi untuk mendapatkan CSRF token dari meta tag
  function getCSRFToken() {
    const token = document.querySelector('meta[name="csrf-token"]');
    return token ? token.getAttribute("content") : "";
  }

  // Elemen-elemen modal untuk tambah/edit pengguna
  const userModal = document.getElementById("user-modal");
  const userForm = document.getElementById("user-form");
  const modalTitle = document.getElementById("modal-title");
  const nikInput = document.getElementById("nik");
  const nikOriginalInput = document.getElementById("nik_original");
  const passwordInput = document.getElementById("password");
  const passwordHelp = document.getElementById("password-help");

  // Ambil elemen untuk field mekanik
  const roleSelect = document.getElementById("role");
  const mechanicFields = document.getElementById("mechanic-fields");
  // <<< PERUBAHAN DIMULAI >>>
  const customerCheckboxContainer = document.getElementById("customer-checkbox-container");
  // <<< PERUBAHAN SELESAI >>>
  const assignedShopAreaInput = document.getElementById("assigned_shop_area");

  // Elemen-elemen modal untuk konfirmasi hapus
  const deleteModal = document.getElementById("delete-modal");
  const userToDeleteName = document.getElementById("user-to-delete-name");
  const confirmDeleteButton = document.getElementById("confirm-delete-button");
  const cancelDeleteButton = document.getElementById("cancel-delete-button");
  let nikToDelete = null;

  // Logika Pencarian Pengguna
  const searchInput = document.getElementById("search-input");
  const userTableBody = document.getElementById("user-table-body");
  const userRows = userTableBody.querySelectorAll("tr");

  searchInput.addEventListener("input", function () {
    const searchTerm = this.value.toLowerCase().trim();
    userRows.forEach((row) => {
      const nikCell = row.cells[1];
      const nameCell = row.cells[2];
      if (nikCell && nameCell) {
        const nikText = nikCell.textContent.toLowerCase();
        const nameText = nameCell.textContent.toLowerCase();
        if (nikText.includes(searchTerm) || nameText.includes(searchTerm)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      }
    });
  });

  // Fungsi untuk menampilkan/menyembunyikan field mekanik
  function toggleMechanicFields() {
    if (roleSelect.value === "mechanic") {
      mechanicFields.classList.remove("hidden");
    } else {
      mechanicFields.classList.add("hidden");
      // <<< PERUBAHAN DIMULAI >>>
      // Kosongkan container checkbox
      customerCheckboxContainer.innerHTML = '<p class="text-gray-500 text-sm">Memuat daftar customer...</p>';
      // <<< PERUBAHAN SELESAI >>>
      assignedShopAreaInput.value = "";
    }
  }

  // <<< FUNGSI BARU UNTUK MENGAMBIL DAN MENAMPILKAN CUSTOMER >>>
  async function populateCustomerCheckboxes(assignedCustomers = []) {
    try {
      const response = await fetch("/get_all_customers");
      if (!response.ok) throw new Error("Gagal mengambil daftar customer.");
      const data = await response.json();

      customerCheckboxContainer.innerHTML = ""; // Bersihkan container

      if (data.customers && data.customers.length > 0) {
        data.customers.forEach((customerName) => {
          const isChecked = assignedCustomers.includes(customerName);
          const checkboxWrapper = document.createElement("div");
          checkboxWrapper.className = "flex items-center";

          const checkbox = document.createElement("input");
          checkbox.type = "checkbox";
          checkbox.id = `customer-${customerName.replace(/\s+/g, "-")}`;
          checkbox.name = "assigned_customers";
          checkbox.value = customerName;
          checkbox.checked = isChecked;
          checkbox.className = "h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded";

          const label = document.createElement("label");
          label.htmlFor = checkbox.id;
          label.textContent = customerName;
          label.className = "ml-3 block text-sm font-medium text-gray-700";

          checkboxWrapper.appendChild(checkbox);
          checkboxWrapper.appendChild(label);
          customerCheckboxContainer.appendChild(checkboxWrapper);
        });
      } else {
        customerCheckboxContainer.innerHTML = '<p class="text-gray-500 text-sm">Tidak ada data customer ditemukan.</p>';
      }
    } catch (error) {
      console.error("Error populating customers:", error);
      customerCheckboxContainer.innerHTML = `<p class="text-red-500 text-sm">Error: ${error.message}</p>`;
    }
  }

  /**
   * Membuka modal untuk menambah atau mengedit pengguna.
   * @param {string|null} nik - NIK pengguna yang akan diedit. Jika null, mode tambah.
   */
  window.openUserModal = async (nik = null) => {
    userForm.reset();
    nikInput.readOnly = false;
    nikInput.classList.remove("bg-gray-100");
    mechanicFields.classList.add("hidden");
    // Kosongkan container saat modal dibuka
    customerCheckboxContainer.innerHTML = '<p class="text-gray-500 text-sm">Memuat daftar customer...</p>';

    if (nik) {
      modalTitle.textContent = "Edit Pengguna";
      nikOriginalInput.value = nik;
      passwordInput.placeholder = "Kosongkan jika tidak diubah";
      passwordHelp.textContent = "Kosongkan jika tidak ingin mengubah password.";
      passwordInput.required = false;

      try {
        const response = await fetch(`/users/${nik}`, {
          headers: { "X-CSRFToken": getCSRFToken() },
        });
        if (!response.ok) throw new Error("Gagal mendapatkan data pengguna dari server.");
        const data = await response.json();

        if (data.error) {
          alert("Error: " + data.error);
          return;
        }

        nikInput.value = data.nik;
        document.getElementById("name").value = data.name;
        roleSelect.value = data.role;

        // Panggil fungsi untuk mengisi checkbox dengan data customer yang sudah ditugaskan
        await populateCustomerCheckboxes(data.assigned_customers || []);

        if (data.role === "mechanic") {
          assignedShopAreaInput.value = data.assigned_shop_area || "";
        }
      } catch (error) {
        alert("Gagal mengambil data pengguna. " + error.message);
        console.error("Fetch error:", error);
        return;
      }
    } else {
      // Mode Tambah
      modalTitle.textContent = "Tambah Pengguna Baru";
      nikOriginalInput.value = "";
      passwordInput.placeholder = "Password wajib diisi";
      passwordHelp.textContent = "Password wajib diisi untuk pengguna baru.";
      passwordInput.required = true;
      // Panggil fungsi untuk mengisi checkbox tanpa ada yang tercentang
      await populateCustomerCheckboxes([]);
    }

    toggleMechanicFields();
    userModal.classList.remove("hidden");
  };

  /**
   * Menutup modal tambah/edit pengguna.
   */
  window.closeUserModal = () => {
    userModal.classList.add("hidden");
  };

  /**
   * Membuka modal konfirmasi penghapusan.
   */
  window.openDeleteModal = (nik, name) => {
    nikToDelete = nik;
    userToDeleteName.textContent = name;
    deleteModal.classList.remove("hidden");
  };

  /**
   * Menutup modal konfirmasi penghapusan.
   */
  window.closeDeleteModal = () => {
    deleteModal.classList.add("hidden");
  };

  // Event listener untuk tombol batal di modal hapus
  cancelDeleteButton.addEventListener("click", closeDeleteModal);

  // Panggil toggleMechanicFields saat role diubah
  roleSelect.addEventListener("change", toggleMechanicFields);

  // Event handler untuk submit form (tambah/edit)
  userForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const isEditMode = nikOriginalInput.value !== "";
    if (!isEditMode && !passwordInput.value) {
      alert("Password wajib diisi untuk pengguna baru.");
      return;
    }

    const formData = new FormData(userForm);
    const data = Object.fromEntries(formData.entries());

    // <<< PERUBAHAN PENGUMPULAN DATA CHECKBOX >>>
    // FormData.entries() tidak bisa handle multiple checkbox dengan nama sama,
    // jadi kita ambil manual.
    const selectedCustomers = Array.from(customerCheckboxContainer.querySelectorAll('input[name="assigned_customers"]:checked')).map((cb) => cb.value);
    data.assigned_customers = selectedCustomers;
    // <<< AKHIR PERUBAHAN >>>

    if (isEditMode && data.password === "") {
      delete data.password;
    }

    if (data.role !== "mechanic") {
      delete data.assigned_customers;
      delete data.assigned_shop_area;
    }

    try {
      const response = await fetch("/users", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": getCSRFToken(),
        },
        body: JSON.stringify(data),
      });
      const result = await response.json();

      if (response.ok && result.success) {
        // Jika sukses
        closeUserModal();
        location.reload();
      } else {
        alert("Error: " + (result.error || "Gagal menyimpan data. Silakan cek kembali input Anda."));
      }
    } catch (error) {
      // Ini untuk error jaringan sejati (misal: server mati, tidak ada koneksi)
      alert("Terjadi kesalahan pada jaringan. Tidak dapat menghubungi server.");
      console.error("Submit error:", error);
    }
  });

  // Event handler untuk tombol konfirmasi hapus
  confirmDeleteButton.addEventListener("click", async () => {
    if (!nikToDelete) return;
    try {
      const response = await fetch(`/users/${nikToDelete}`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCSRFToken() },
      });
      const result = await response.json();

      if (response.ok && result.success) {
        closeDeleteModal();
        location.reload();
      } else {
        alert("Error: " + (result.error || "Gagal menghapus pengguna."));
      }
    } catch (error) {
      alert("Terjadi kesalahan pada jaringan saat menghapus.");
      console.error("Delete error:", error);
    }
  });
});
