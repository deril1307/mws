document.addEventListener("DOMContentLoaded", function () {
  // --- FUNGSI NOTIFIKASI ---
  function showNotification(message, type = "success") {
    const existingNotification = document.getElementById("toast-notification");
    if (existingNotification) {
      existingNotification.remove();
    }
    const icons = {
      success: `<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
      error: `<svg class="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z"></path></svg>`,
    };
    const styles = {
      success: { bg: "bg-green-500", title: "Berhasil!" },
      error: { bg: "bg-red-600", title: "Terjadi Kesalahan!" },
    };

    const notification = document.createElement("div");
    notification.id = "toast-notification";
    notification.className = `fixed top-5 right-5 flex items-center w-full max-w-xs p-4 space-x-4 text-white ${styles[type].bg} rounded-xl shadow-2xl z-50 transition-all duration-300 ease-in-out transform translate-x-full opacity-0`;
    notification.innerHTML = `
      <div class="flex-shrink-0">${icons[type]}</div>
      <div class="pl-2">
        <div class="text-sm font-bold">${styles[type].title}</div>
        <div class="text-sm font-normal">${message}</div>
      </div>
    `;
    document.body.appendChild(notification);
    requestAnimationFrame(() => {
      notification.classList.remove("translate-x-full", "opacity-0");
      notification.classList.add("translate-x-0", "opacity-100");
    });
    setTimeout(() => {
      notification.classList.remove("translate-x-0", "opacity-100");
      notification.classList.add("translate-x-full", "opacity-0");
      setTimeout(() => notification.remove(), 300);
    }, 4000);
  }

  // ========== LOGIKA UNTUK DROPDOWN & INPUT MANUAL JENIS PEKERJAAN ==========
  const jobTypeContainer = document.getElementById("jobTypeContainer");
  if (jobTypeContainer) {
    const searchInput = document.getElementById("jobTypeSearch");
    const hiddenInput = document.getElementById("jobTypeInput");
    const dropdown = document.getElementById("jobTypeDropdown");
    const list = document.getElementById("jobTypeList");
    const addBtn = document.getElementById("addJobTypeBtn");

    let isManualMode = false; // State untuk melacak mode input

    function populateJobTypes() {
      if (typeof JOB_TYPES_FROM_SERVER !== "undefined" && Array.isArray(JOB_TYPES_FROM_SERVER)) {
        // const defaultOptions = ["F.Test", "Repair", "Overhaul", "IRAN", "Recharging"];
        // // ...
        // HANYA MENGGUNAKAN DATA DATABASE)
        const allOptions = [...new Set(JOB_TYPES_FROM_SERVER)].sort();
        // ...

        list.innerHTML = "";
        allOptions.forEach((job) => {
          const li = document.createElement("li");
          li.textContent = job;
          li.className = "px-4 py-2 hover:bg-blue-50 cursor-pointer";
          li.addEventListener("click", () => {
            searchInput.value = job;
            hiddenInput.value = job;
            dropdown.classList.add("hidden");
          });
          list.appendChild(li);
        });
      } else {
        console.error("Variabel JOB_TYPES_FROM_SERVER tidak ditemukan atau bukan array.");
        list.innerHTML = `<li class="px-4 py-2 text-gray-500">Gagal memuat data.</li>`;
      }
    }

    function switchToManualMode() {
      isManualMode = true;
      dropdown.classList.add("hidden");
      searchInput.placeholder = "Ketik Jenis Pekerjaan Baru...";
      searchInput.value = "";
      hiddenInput.value = "";
      addBtn.innerHTML = `<i class="fas fa-list"></i>`;
      addBtn.title = "Pilih dari daftar";
    }

    function switchToSelectMode() {
      isManualMode = false;
      searchInput.placeholder = "Cari atau pilih dari daftar...";
      searchInput.value = "";
      hiddenInput.value = "";
      addBtn.innerHTML = `<i class="fas fa-plus"></i>`;
      addBtn.title = "Tambah baru";
    }

    addBtn.addEventListener("click", () => {
      if (isManualMode) {
        switchToSelectMode();
      } else {
        switchToManualMode();
      }
    });

    searchInput.addEventListener("input", () => {
      if (isManualMode) {
        hiddenInput.value = searchInput.value.trim();
        return;
      }

      hiddenInput.value = "";
      const filter = searchInput.value.toLowerCase();
      const items = list.getElementsByTagName("li");
      let hasVisibleItems = false;
      for (let i = 0; i < items.length; i++) {
        const txtValue = items[i].textContent || items[i].innerText;
        if (txtValue.toLowerCase().indexOf(filter) > -1) {
          items[i].style.display = "";
          hasVisibleItems = true;
        } else {
          items[i].style.display = "none";
        }
      }
      if (hasVisibleItems && filter.length > 0) {
        dropdown.classList.remove("hidden");
      } else {
        dropdown.classList.add("hidden");
      }
    });

    searchInput.addEventListener("focus", () => {
      if (!isManualMode) {
        // Hanya tampilkan jika ada isi atau jika user klik
        if (list.getElementsByTagName("li").length > 0) {
          dropdown.classList.remove("hidden");
        }
      }
    });

    window.addEventListener("click", (e) => {
      if (!jobTypeContainer.contains(e.target)) {
        dropdown.classList.add("hidden");
      }
    });

    populateJobTypes();
  }
  // ========== AKHIR LOGIKA DROPDOWN ==========

  // SCRIPT SUBMIT FORM
  const createMwsForm = document.getElementById("createMwsForm");
  if (createMwsForm) {
    createMwsForm.addEventListener("submit", async function (e) {
      e.preventDefault();

      const formData = new FormData(this);
      const data = {};
      for (let [key, value] of formData.entries()) {
        if (key !== "csrf_token") {
          data[key] = value;
        }
      }

      if (!data.jobType || data.jobType.trim() === "") {
        showNotification("Jenis Pekerjaan wajib diisi atau dipilih.", "error");
        return;
      }

      const csrfToken = document.querySelector('input[name="csrf_token"]').value;

      try {
        const response = await fetch("/create_mws", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-CSRFToken": csrfToken,
          },
          body: JSON.stringify(data),
        });

        const result = await response.json();

        if (result.success) {
          showNotification("MWS berhasil dibuat!", "success");
          setTimeout(() => {
            window.location.href = "/mws/" + result.partId;
          }, 500);
        } else {
          showNotification(result.error || "Gagal menyimpan data.", "error");
        }
      } catch (error) {
        console.error("Error:", error);
        showNotification("Tidak dapat terhubung ke server.", "error");
      }
    });
  }
});
