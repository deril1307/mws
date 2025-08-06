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

  // --- BAGIAN BARU: Ambil elemen untuk field mekanik ---
  const roleSelect = document.getElementById("role");
  const mechanicFields = document.getElementById("mechanic-fields");
  const assignedCustomerInput = document.getElementById("assigned_customer");
  const assignedShopAreaInput = document.getElementById("assigned_shop_area");
  // --- AKHIR BAGIAN BARU ---

  // Elemen-elemen modal untuk konfirmasi hapus
  const deleteModal = document.getElementById("delete-modal");
  const userToDeleteName = document.getElementById("user-to-delete-name");
  const confirmDeleteButton = document.getElementById("confirm-delete-button");
  const cancelDeleteButton = document.getElementById("cancel-delete-button");
  let nikToDelete = null;

  // Logika Pencarian Pengguna (tidak berubah)
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

  // --- FUNGSI BARU: Untuk menampilkan/menyembunyikan field mekanik ---
  function toggleMechanicFields() {
    if (roleSelect.value === "mechanic") {
      mechanicFields.classList.remove("hidden");
    } else {
      mechanicFields.classList.add("hidden");
      // Kosongkan nilainya saat disembunyikan agar tidak terkirim data yang salah
      assignedCustomerInput.value = "";
      assignedShopAreaInput.value = "";
    }
  }
  // --- AKHIR FUNGSI BARU ---

  /**
   * Membuka modal untuk menambah atau mengedit pengguna.
   * @param {string|null} nik - NIK pengguna yang akan diedit. Jika null, mode tambah.
   */
  window.openUserModal = async (nik = null) => {
    userForm.reset();
    nikInput.classList.remove("bg-gray-100");
    nikInput.readOnly = false;

    // Pastikan field mekanik tersembunyi saat reset
    mechanicFields.classList.add("hidden");

    if (nik) {
      // Mode Edit
      modalTitle.textContent = "Edit Pengguna";
      nikInput.readOnly = true;
      nikInput.classList.add("bg-gray-100");
      nikOriginalInput.value = nik;
      passwordInput.placeholder = "Kosongkan jika tidak diubah";
      passwordHelp.textContent = "Kosongkan jika tidak ingin mengubah password.";
      passwordInput.required = false;

      try {
        const response = await fetch(`/users/${nik}`, {
          headers: { "X-CSRFToken": getCSRFToken() },
        });
        if (!response.ok) throw new Error("Gagal mendapatkan respons dari server.");
        const data = await response.json();

        if (data.error) {
          alert("Error: " + data.error);
          return;
        }

        nikInput.value = data.nik;
        document.getElementById("name").value = data.name;
        roleSelect.value = data.role; // Ganti 'role' menjadi 'roleSelect'

        // --- BAGIAN BARU: Isi data area jika user adalah mekanik ---
        if (data.role === "mechanic") {
          assignedCustomerInput.value = data.assigned_customer || "";
          assignedShopAreaInput.value = data.assigned_shop_area || "";
        }
        // --- AKHIR BAGIAN BARU ---
      } catch (error) {
        alert("Gagal mengambil data pengguna.");
        console.error("Fetch error:", error);
        return;
      }
    } else {
      // Mode Tambah
      modalTitle.textContent = "Tambah Pengguna Baru";
      nikOriginalInput.value = "";
      passwordInput.placeholder = "";
      passwordHelp.textContent = "Password wajib diisi untuk pengguna baru.";
      passwordInput.required = true;
    }

    // Panggil fungsi toggle SETELAH semua data diisi, untuk memastikan tampilan benar
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

  // --- EVENT LISTENER BARU: Panggil toggleMechanicFields saat role diubah ---
  roleSelect.addEventListener("change", toggleMechanicFields);
  // --- AKHIR EVENT LISTENER BARU ---

  // Event handler untuk submit form (tambah/edit) - TIDAK ADA PERUBAHAN DI SINI
  userForm.addEventListener("submit", async (e) => {
    e.preventDefault();

    const isEditMode = nikOriginalInput.value !== "";
    if (!isEditMode && !passwordInput.value) {
      alert("Password wajib diisi untuk pengguna baru.");
      return;
    }

    const formData = new FormData(userForm);
    const data = Object.fromEntries(formData.entries());

    if (isEditMode && data.password === "") {
      delete data.password;
    }

    // Jika rolenya bukan mekanik, hapus data area agar tidak terkirim
    if (data.role !== "mechanic") {
      delete data.assigned_customer;
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
      if (!response.ok) throw new Error("Server memberikan respons error.");
      const result = await response.json();

      if (result.success) {
        closeUserModal();
        location.reload();
      } else {
        alert("Error: " + (result.error || "Gagal menyimpan data."));
      }
    } catch (error) {
      alert("Terjadi kesalahan pada jaringan.");
      console.error("Submit error:", error);
    }
  });

  // Event handler untuk tombol konfirmasi hapus (tidak berubah)
  confirmDeleteButton.addEventListener("click", async () => {
    if (!nikToDelete) return;
    try {
      const response = await fetch(`/users/${nikToDelete}`, {
        method: "DELETE",
        headers: { "X-CSRFToken": getCSRFToken() },
      });
      if (!response.ok) throw new Error("Server memberikan respons error.");
      const result = await response.json();

      if (result.success) {
        closeDeleteModal();
        location.reload();
      } else {
        alert("Error: " + (result.error || "Gagal menghapus pengguna."));
      }
    } catch (error) {
      alert("Terjadi kesalahan pada jaringan.");
      console.error("Delete error:", error);
    }
  });
});
