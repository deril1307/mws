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
  const customerCheckboxContainer = document.getElementById("customer-checkbox-container");
  const assignedShopAreaInput = document.getElementById("assigned_shop_area");

  // Elemen-elemen modal untuk konfirmasi hapus
  const deleteModal = document.getElementById("delete-modal");
  const userToDeleteName = document.getElementById("user-to-delete-name");
  const confirmDeleteButton = document.getElementById("confirm-delete-button");
  const cancelDeleteButton = document.getElementById("cancel-delete-button");
  let nikToDelete = null;

  // Logika Pencarian Pengguna (sudah benar dari pembahasan sebelumnya)
  const searchInput = document.getElementById("search-input");
  const userTableBody = document.getElementById("user-table-body");
  const userRows = userTableBody.querySelectorAll("tr");

  searchInput.addEventListener("input", function () {
    const searchTerm = this.value.toLowerCase().trim();
    userRows.forEach((row) => {
      const nikCell = row.cells[2];
      const nameCell = row.cells[3];
      const assignmentCell = row.cells[5];

      if (nikCell && nameCell && assignmentCell) {
        const nikText = nikCell.textContent.toLowerCase();
        const nameText = nameCell.textContent.toLowerCase();
        const assignmentText = assignmentCell.textContent.toLowerCase();
        if (nikText.includes(searchTerm) || nameText.includes(searchTerm) || assignmentText.includes(searchTerm)) {
          row.style.display = "";
        } else {
          row.style.display = "none";
        }
      }
    });
  });

  // <<< PERUBAHAN DIMULAI DI SINI >>>

  /**
   * Fungsi untuk menampilkan/menyembunyikan field mekanik.
   * Dibuat menjadi async untuk bisa memanggil populateCustomerCheckboxes.
   */
  async function toggleMechanicFields() {
    if (roleSelect.value === "mechanic") {
      mechanicFields.classList.remove("hidden");
      // PANGGIL FUNGSI UNTUK MEMUAT CUSTOMER KETIKA ROLE MECHANIC DIPILIH
      // Kita panggil dengan array kosong karena kita tidak tahu customer mana yang terpilih
      // sampai data user diedit dimuat. `populateCustomerCheckboxes` akan menangani
      // checkbox yang sudah ada jika ada.
      await populateCustomerCheckboxes();
    } else {
      mechanicFields.classList.add("hidden");
      // Kosongkan container dan reset value jika role bukan mekanik
      customerCheckboxContainer.innerHTML = '<p class="text-gray-500 text-sm">Pilih role "Mechanic" untuk menampilkan.</p>';
      assignedShopAreaInput.value = "";
    }
  }

  // Panggil toggleMechanicFields saat role diubah.
  // Menggunakan fungsi async sebagai event listener.
  roleSelect.addEventListener("change", async () => {
    await toggleMechanicFields();
  });

  // <<< PERUBAHAN SELESAI DI SINI >>>

  // Fungsi untuk mengambil dan menampilkan customer
  // Parameter assignedCustomers dibuat optional, akan digunakan saat edit.
  async function populateCustomerCheckboxes(assignedCustomers = []) {
    // Jika ada form yang sedang ditampilkan, kita cek customer mana yang sudah terpilih
    const currentlyChecked = Array.from(customerCheckboxContainer.querySelectorAll('input[type="checkbox"]:checked')).map((cb) => cb.value);

    // Gabungkan customer yang sudah ada (dari edit) dan yang baru saja di-check
    const finalAssignedCustomers = [...new Set([...assignedCustomers, ...currentlyChecked])];

    customerCheckboxContainer.innerHTML = '<p class="text-gray-500 text-sm">Memuat daftar customer...</p>';

    try {
      const response = await fetch("/get_all_customers");
      if (!response.ok) throw new Error("Gagal mengambil daftar customer.");
      const data = await response.json();

      customerCheckboxContainer.innerHTML = ""; // Bersihkan container

      if (data.customers && data.customers.length > 0) {
        data.customers.forEach((customerName) => {
          const isChecked = finalAssignedCustomers.includes(customerName);
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
    customerCheckboxContainer.innerHTML = '<p class="text-gray-500 text-sm">Pilih role "Mechanic" untuk menampilkan.</p>';

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

        // Panggil toggleMechanicFields yang akan menangani pemanggilan populateCustomerCheckboxes
        await toggleMechanicFields();
        // Jika rolenya mechanic, panggil lagi populateCustomerCheckboxes dengan data yang benar
        if (data.role === "mechanic") {
          await populateCustomerCheckboxes(data.assigned_customers || []);
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
      // Untuk mode tambah, cukup panggil toggleMechanicFields. Jika role defaultnya mechanic,
      // ia akan memuat daftar customer.
      await toggleMechanicFields();
    }
    userModal.classList.remove("hidden");
  };

  // Sisa kode (closeUserModal, openDeleteModal, submit form, etc.) tidak perlu diubah.
  // ... (Sisa kode Anda dari sini ke bawah tetap sama)

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

  cancelDeleteButton.addEventListener("click", closeDeleteModal);

  userForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const isEditMode = nikOriginalInput.value !== "";
    if (!isEditMode && !passwordInput.value) {
      alert("Password wajib diisi untuk pengguna baru.");
      return;
    }

    const formData = new FormData(userForm);
    const data = Object.fromEntries(formData.entries());

    const selectedCustomers = Array.from(customerCheckboxContainer.querySelectorAll('input[name="assigned_customers"]:checked')).map((cb) => cb.value);
    data.assigned_customers = selectedCustomers;

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
        closeUserModal();
        location.reload();
      } else {
        alert("Error: " + (result.error || "Gagal menyimpan data. Silakan cek kembali input Anda."));
      }
    } catch (error) {
      alert("Terjadi kesalahan pada jaringan. Tidak dapat menghubungi server.");
      console.error("Submit error:", error);
    }
  });

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
