const form = document.getElementById("extract-form");
const submitBtn = document.getElementById("submit-btn");
const statusBox = document.getElementById("status");

function setStatus(message, type = "info") {
  statusBox.textContent = message;
  statusBox.className = `status ${type}`;
}

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const formData = new FormData(form);

  submitBtn.disabled = true;
  setStatus("Extrayendo datos y preparando el ZIP...", "info");

  try {
    const response = await fetch("/extract", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(errorText || "No se pudo completar la extracción.");
    }

    const blob = await response.blob();
    const contentDisposition = response.headers.get("content-disposition") || "";
    const fileNameMatch = contentDisposition.match(/filename="?([^\"]+)"?/i);
    const fileName = fileNameMatch ? fileNameMatch[1] : "senamhi_export.zip";

    const url = window.URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = fileName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);

    setStatus("Descarga completada.", "success");
  } catch (error) {
    console.error(error);
    setStatus(`Error: ${error.message}`, "error");
  } finally {
    submitBtn.disabled = false;
  }
});
