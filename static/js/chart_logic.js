// Pembungkus document.addEventListener("DOMContentLoaded", ...) telah dihapus.
// Kode ini sekarang akan langsung berjalan saat file dimuat.

if (typeof originalData === "undefined") {
  console.error("Error: Data untuk chart (originalData) tidak ditemukan. Pastikan variabel ini didefinisikan sebelum script ini dijalankan.");
} else if (typeof Chart === "undefined") {
  console.error("Error: Library Chart.js tidak ditemukan. Pastikan sudah dimuat.");
} else {
  if (typeof ChartDataLabels !== "undefined") {
    Chart.register(ChartDataLabels);
  }
  let mwsStatusChart, mwsStatusBarChart, mwsUrgencyChart, mwsTimelineChart, mwsShopAreaChart;
  const HIGH_CONTRAST_PALETTE = [
    // 7 Warna Dasar Mejikuhibiniu
    "#FF0000", // Merah
    "#FFA500", // Jingga
    "#FFFF00", // Kuning
    "#008000", // Hijau
    "#0000FF", // Biru
    "#4B0082", // Nila (Indigo)
    "#800080", // Ungu (Purple)
    "#f032e6", // Magenta
    "#42d4f4", // Sian (Cyan)
    "#bfef45", // Hijau Limau
    "#E6194B", // Merah Terang (dari palet lama)
    "#3cb44b", // Hijau Terang (dari palet lama)
    "#9A6324", // Cokelat
    "#800000", // Merah Marun
    "#000075", // Biru Navy
    "#fabed4", // Merah Muda Pastel
    "#469990", // Hijau Teal
    "#a9a9a9", // Abu-abu
  ];
  function generateColor(name) {
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
      hash = name.charCodeAt(i) + ((hash << 5) - hash);
      hash = hash & hash;
    }
    const index = Math.abs(hash) % HIGH_CONTRAST_PALETTE.length;
    return HIGH_CONTRAST_PALETTE[index];
  }

  const statusConfig = {
    labels: ["Menunggu", "Dikerjakan", "Selesai"],
    colors: ["#FFC107", "#1E88E5", "#43A047"],
  };
  const urgencyConfig = {
    labels: ["Urgent", "Reguler"],
    colors: ["#D32F2F", "#546E7A"],
  };

  // Elemen Filter
  const yearFilter = document.getElementById("chart-year-filter");
  const filterTriggerBtn = document.getElementById("chart-customer-filter-btn");
  const filterPanel = document.getElementById("customer-filter-panel");
  const customerButtons = document.querySelectorAll(".customer-select-btn");
  const applyBtn = document.getElementById("chart-filter-apply-btn");
  const resetBtn = document.getElementById("chart-filter-reset-btn");

  const shopAreaFilterTriggerBtn = document.getElementById("chart-shop-area-filter-btn");
  const shopAreaFilterPanel = document.getElementById("shop-area-filter-panel");
  const shopAreaButtons = document.querySelectorAll(".shop-area-select-btn");
  const shopAreaApplyBtn = document.getElementById("chart-filter-apply-btn-shop-area");
  const shopAreaResetBtn = document.getElementById("chart-filter-reset-btn-shop-area");

  // Event Listener untuk Filter
  if (filterTriggerBtn && filterPanel) {
    filterTriggerBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      filterPanel.classList.toggle("hidden");
    });
    document.addEventListener("click", (event) => {
      if (!filterPanel.contains(event.target) && !filterTriggerBtn.contains(event.target)) {
        filterPanel.classList.add("hidden");
      }
    });
    customerButtons.forEach((button) => {
      button.addEventListener("click", () => {
        button.classList.toggle("bg-blue-600");
        button.classList.toggle("text-white");
        button.classList.toggle("border-blue-600");
      });
    });
    applyBtn.addEventListener("click", () => {
      const selectedCustomers = Array.from(customerButtons)
        .filter((btn) => btn.classList.contains("bg-blue-600"))
        .map((btn) => btn.dataset.customer);
      const selectedShopAreas = Array.from(shopAreaButtons)
        .filter((btn) => btn.classList.contains("bg-blue-600"))
        .map((btn) => btn.dataset.shopArea);
      const selectedYear = yearFilter.value;
      updateFilteredData(selectedCustomers, selectedShopAreas, selectedYear);
      filterPanel.classList.add("hidden");
    });
    resetBtn.addEventListener("click", () => {
      customerButtons.forEach((button) => {
        button.classList.remove("bg-blue-600", "text-white", "border-blue-600");
      });
      const selectedShopAreas = Array.from(shopAreaButtons)
        .filter((btn) => btn.classList.contains("bg-blue-600"))
        .map((btn) => btn.dataset.shopArea);
      updateFilteredData([], selectedShopAreas, yearFilter.value);
    });
  }

  if (shopAreaFilterTriggerBtn && shopAreaFilterPanel) {
    shopAreaFilterTriggerBtn.addEventListener("click", (event) => {
      event.stopPropagation();
      shopAreaFilterPanel.classList.toggle("hidden");
    });
    document.addEventListener("click", (event) => {
      if (!shopAreaFilterPanel.contains(event.target) && !shopAreaFilterTriggerBtn.contains(event.target)) {
        shopAreaFilterPanel.classList.add("hidden");
      }
    });
    shopAreaButtons.forEach((button) => {
      button.addEventListener("click", () => {
        button.classList.toggle("bg-blue-600");
        button.classList.toggle("text-white");
        button.classList.toggle("border-blue-600");
      });
    });
    shopAreaApplyBtn.addEventListener("click", () => {
      const selectedCustomers = Array.from(customerButtons)
        .filter((btn) => btn.classList.contains("bg-blue-600"))
        .map((btn) => btn.dataset.customer);
      const selectedShopAreas = Array.from(shopAreaButtons)
        .filter((btn) => btn.classList.contains("bg-blue-600"))
        .map((btn) => btn.dataset.shopArea);
      updateFilteredData(selectedCustomers, selectedShopAreas, yearFilter.value);
      shopAreaFilterPanel.classList.add("hidden");
    });
    shopAreaResetBtn.addEventListener("click", () => {
      shopAreaButtons.forEach((button) => {
        button.classList.remove("bg-blue-600", "text-white", "border-blue-600");
      });
      const selectedCustomers = Array.from(customerButtons)
        .filter((btn) => btn.classList.contains("bg-blue-600"))
        .map((btn) => btn.dataset.customer);
      updateFilteredData(selectedCustomers, [], yearFilter.value);
    });
  }

  yearFilter.addEventListener("change", () => {
    const selectedCustomers = Array.from(customerButtons)
      .filter((btn) => btn.classList.contains("bg-blue-600"))
      .map((btn) => btn.dataset.customer);
    const selectedShopAreas = Array.from(shopAreaButtons)
      .filter((btn) => btn.classList.contains("bg-blue-600"))
      .map((btn) => btn.dataset.shopArea);
    updateFilteredData(selectedCustomers, selectedShopAreas, yearFilter.value);
  });

  // Kalkulasi Data
  function calculateTimelineStats(filteredData) {
    const yearlyCounts = {};
    const customerYearlyCounts = {};
    filteredData.forEach((part) => {
      if (part.iwoNo) {
        const match = part.iwoNo.match(/^(\d{2})/);
        if (match) {
          const year = `20${match[1]}`;
          const customer = part.customer;
          if (!yearlyCounts[year]) yearlyCounts[year] = 0;
          if (!customerYearlyCounts[customer]) customerYearlyCounts[customer] = {};
          if (!customerYearlyCounts[customer][year]) customerYearlyCounts[customer][year] = 0;
          yearlyCounts[year]++;
          customerYearlyCounts[customer][year]++;
        }
      }
    });
    const sortedYears = Object.keys(yearlyCounts).sort();
    const customerNames = Object.keys(customerYearlyCounts).sort();
    const customerDatasets = customerNames.map((customer) => ({
      type: "bar",
      label: `MWS ${customer}`,
      data: sortedYears.map((year) => customerYearlyCounts[customer][year] || 0),
      backgroundColor: generateColor(customer),
      barPercentage: 0.5,
    }));
    const totalDataset = {
      type: "line",
      label: "Total MWS per Tahun",
      data: sortedYears.map((year) => yearlyCounts[year]),
      borderColor: "#000000",
      backgroundColor: "rgba(0, 0, 0, 0.5)",
      tension: 0.1,
      fill: false,
    };
    return {
      labels: sortedYears,
      datasets: [...customerDatasets, totalDataset],
    };
  }

  function calculateAllStats(filteredData) {
    const stats = {
      status: { total: 0, pending: 0, inProgress: 0, completed: 0 },
      urgency: { urgent: 0, regular: 0 },
      customerProgress: {},
      shopAreaDistribution: {}, // <-- Data untuk chart baru
    };

    filteredData.forEach((part) => {
      stats.status.total++;
      if (part.status === "pending") stats.status.pending++;
      else if (part.status === "in_progress") stats.status.inProgress++;
      else if (part.status === "completed") stats.status.completed++;

      if (part.is_urgent) stats.urgency.urgent++;
      else stats.urgency.regular++;

      const customer = part.customer;
      const completed_steps = part.steps ? part.steps.filter((s) => s.status === "completed").length : 0;
      const total_steps = part.steps ? part.steps.length : 1;
      const progress = total_steps > 0 ? (completed_steps / total_steps) * 100 : 0;

      if (!stats.customerProgress[customer]) {
        stats.customerProgress[customer] = { progresses: [], count: 0 };
      }
      stats.customerProgress[customer].progresses.push(progress);
      stats.customerProgress[customer].count++;

      // Menghitung distribusi shop area
      const shopArea = part.shopArea || "Tidak Diketahui";
      if (!stats.shopAreaDistribution[shopArea]) {
        stats.shopAreaDistribution[shopArea] = 0;
      }
      stats.shopAreaDistribution[shopArea]++;
    });

    const finalCustomerProgress = {};
    for (const customer in stats.customerProgress) {
      const totalProgress = stats.customerProgress[customer].progresses.reduce((sum, p) => sum + p, 0);
      const count = stats.customerProgress[customer].count;
      finalCustomerProgress[customer] = count > 0 ? totalProgress / count : 0;
    }

    stats.customerProgress = finalCustomerProgress;
    return stats;
  }

  // Update Tampilan
  function updateFilteredData(customerNames = [], shopAreaNames = [], selectedYear = "") {
    const filteredData = Object.values(originalData).filter((part) => {
      const customerMatch = customerNames.length === 0 || customerNames.includes(part.customer);
      const shopAreaMatch = shopAreaNames.length === 0 || shopAreaNames.includes(part.shopArea);
      let yearMatch = true;
      if (selectedYear) {
        yearMatch = part.iwoNo && part.iwoNo.startsWith(selectedYear.substring(2));
      }
      return customerMatch && shopAreaMatch && yearMatch;
    });

    const newStats = calculateAllStats(filteredData);
    updateAllCharts(newStats);

    const newTimelineData = calculateTimelineStats(filteredData);
    updateTimelineChart(newTimelineData);

    updateChartLabel(customerNames, shopAreaNames);
  }

  function updateAllCharts(stats) {
    // Update MWS Status Chart
    const customerProgressData = stats.customerProgress;
    const customerLabels = Object.keys(customerProgressData);
    const customerAvgProgress = Object.values(customerProgressData);
    const customerColors = customerLabels.map((label) => generateColor(label));
    if (mwsStatusChart) {
      mwsStatusChart.data.labels = customerLabels;
      mwsStatusChart.data.datasets[0].data = customerAvgProgress;
      mwsStatusChart.data.datasets[0].backgroundColor = customerColors;
      mwsStatusChart.update();
    }

    // Update MWS Status Bar Chart
    const statusPercentageData = stats.status.total === 0 ? [0, 0, 0] : [(stats.status.pending / stats.status.total) * 100, (stats.status.inProgress / stats.status.total) * 100, (stats.status.completed / stats.status.total) * 100];
    if (mwsStatusBarChart) {
      mwsStatusBarChart.data.datasets[0].data = statusPercentageData;
      mwsStatusBarChart.update();
    }

    // Update Urgency Chart
    const urgencyData = [stats.urgency.urgent, stats.urgency.regular];
    if (mwsUrgencyChart) {
      mwsUrgencyChart.data.datasets[0].data = urgencyData;
      mwsUrgencyChart.update();
    }

    // Update Shop Area Chart
    const shopAreaLabels = Object.keys(stats.shopAreaDistribution);
    const shopAreaData = Object.values(stats.shopAreaDistribution);
    const shopAreaColors = shopAreaLabels.map((label) => generateColor(label));
    if (mwsShopAreaChart) {
      mwsShopAreaChart.data.labels = shopAreaLabels;
      mwsShopAreaChart.data.datasets[0].data = shopAreaData;
      mwsShopAreaChart.data.datasets[0].backgroundColor = shopAreaColors;
      mwsShopAreaChart.update();
    }
  }

  function updateTimelineChart(timelineData) {
    if (mwsTimelineChart) {
      mwsTimelineChart.data.labels = timelineData.labels;
      mwsTimelineChart.data.datasets = timelineData.datasets;
      mwsTimelineChart.update();
    }
  }

  function updateChartLabel(customerNames = [], shopAreaNames = []) {
    const label = document.getElementById("customer-chart-label");
    if (!label) return;
    const year = yearFilter.value;
    let customerText = "Semua Customer";
    if (customerNames.length > 0) {
      customerText = customerNames.length > 2 ? `${customerNames.length} customer terpilih` : customerNames.join(", ");
    }
    let shopAreaText = "Semua Shop Area";
    if (shopAreaNames.length > 0) {
      shopAreaText = shopAreaNames.length > 2 ? `${shopAreaNames.length} shop area terpilih` : shopAreaNames.join(", ");
    }
    let yearText = year ? ` | ${year}` : " | Semua Tahun";
    label.textContent = `- ${customerText} | ${shopAreaText}${yearText}`;
  }

  // Inisialisasi Chart
  function initializeCharts() {
    const ctxDoughnut = document.getElementById("mwsStatusChart");
    if (ctxDoughnut) {
      mwsStatusChart = new Chart(ctxDoughnut, {
        type: "doughnut",
        data: {
          labels: [],
          datasets: [
            {
              label: "Rata-rata Progress MWS (%)",
              data: [],
              backgroundColor: [],
              hoverOffset: 4,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "right" },
            datalabels: {
              color: "#fff",
              font: { weight: "bold" },
              formatter: (value) => (value > 0 ? `${value.toFixed(1)}%` : null),
            },
            title: { display: true, text: "% Progress MWS per Customer", font: { size: 14 } },
            tooltip: {
              callbacks: {
                label: function (context) {
                  let label = context.dataset.label || "";
                  if (label) label += ": ";
                  if (context.parsed !== null) label += `${context.parsed.toFixed(1)}%`;
                  return label;
                },
              },
            },
          },
        },
      });
    }

    const ctxBar = document.getElementById("mwsStatusBarChart");
    if (ctxBar) {
      mwsStatusBarChart = new Chart(ctxBar, {
        type: "bar",
        data: { labels: statusConfig.labels, datasets: [{ label: "% Progress Work Sheet", data: [], backgroundColor: statusConfig.colors, borderWidth: 1 }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          scales: {
            y: { beginAtZero: true, max: 100, ticks: { stepSize: 25, callback: (value) => value + "%", color: "#333" } },
            x: { ticks: { color: "#333" } },
          },
          plugins: {
            legend: { display: false },
            title: { display: true, text: "% Progress Work Sheet", font: { size: 14 } },
            datalabels: { anchor: "end", align: "top", color: "#4A5568", font: { weight: "bold" }, formatter: (value) => (value > 0 ? `${value.toFixed(1)}%` : null) },
          },
        },
      });
    }

    const ctxUrgency = document.getElementById("mwsUrgencyChart");
    if (ctxUrgency) {
      mwsUrgencyChart = new Chart(ctxUrgency, {
        type: "doughnut",
        data: { labels: urgencyConfig.labels, datasets: [{ label: "Jumlah", data: [], backgroundColor: urgencyConfig.colors, hoverOffset: 4 }] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { datalabels: { color: "#fff", font: { weight: "bold" } }, title: { display: true, text: "Jumlah Urgensi", font: { size: 14 } } },
        },
      });
    }

    // Inisialisasi Chart Shop Area Baru
    const ctxShopArea = document.getElementById("mwsShopAreaChart");
    if (ctxShopArea) {
      mwsShopAreaChart = new Chart(ctxShopArea, {
        type: "pie",
        data: {
          labels: [],
          datasets: [{ label: "Jumlah per Shop Area", data: [], backgroundColor: [], hoverOffset: 4 }],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              position: "right",
            },
            datalabels: {
              color: "#fff",
              font: { weight: "bold" },
              formatter: (value) => (value > 0 ? value : null),
            },
            title: {
              display: true,
              text: "Jumlah per Shop Area",
              font: { size: 14 },
            },
          },
        },
      });
    }

    const ctxTimeline = document.getElementById("mwsTimelineChart");
    if (ctxTimeline) {
      mwsTimelineChart = new Chart(ctxTimeline, {
        type: "bar",
        data: { labels: [], datasets: [] },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            title: { display: true, text: "Linimasa MWS per Customer dan Total", font: { size: 16 } },
            datalabels: { display: false },
            tooltip: { mode: "index", intersect: false },
          },
          scales: {
            x: { stacked: false, ticks: { color: "#333" } },
            y: { beginAtZero: true, stacked: false, ticks: { stepSize: 1, color: "#333" } },
          },
        },
      });
    }

    updateFilteredData([], [], yearFilter.value);
  }

  // Panggil fungsi inisialisasi utama.
  initializeCharts();
}
