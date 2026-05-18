// SAF ISBN scanner — frontend logic.
// Minimal, geen frameworks.

(function () {
  "use strict";

  // ---- Compare page: max 2 bronnen selecteerbaar ----
  const compareForm = document.getElementById("compareForm");
  if (compareForm) {
    const checkboxes = compareForm.querySelectorAll(".source-checkbox");
    const submitBtn = document.getElementById("submitBtn");

    function updateState() {
      const checked = compareForm.querySelectorAll(".source-checkbox:checked");
      const count = checked.length;

      // Update submit button
      submitBtn.disabled = count === 0;
      if (count === 0) {
        submitBtn.textContent = "Selecteer minstens 1 bron";
      } else if (count === 1) {
        submitBtn.textContent = "Verder met 1 bron →";
      } else if (count === 2) {
        submitBtn.textContent = "Verder met 2 bronnen (merge) →";
      }

      // Visuele feedback op card-niveau
      checkboxes.forEach(function (cb) {
        const card = cb.closest(".source-card");
        if (cb.checked) {
          card.classList.add("selected");
          card.classList.remove("disabled");
        } else if (count >= 2) {
          // max bereikt: disable rest
          card.classList.add("disabled");
          card.classList.remove("selected");
          cb.disabled = true;
        } else {
          card.classList.remove("selected", "disabled");
          cb.disabled = false;
        }
      });
    }

    checkboxes.forEach(function (cb) {
      cb.addEventListener("change", updateState);
    });
    updateState();
  }

  // ---- Confirm page: autofocus op barcode ----
  // (de bibliothecaris heeft barcode-scanner in hand)
  const barcodeInput = document.getElementById("barcode");
  if (barcodeInput) {
    barcodeInput.focus();
  }
})();
