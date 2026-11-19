document.addEventListener("DOMContentLoaded", function () {
  const form = document.getElementById("multiStepForm");
  const steps = ["step1", "step2", "step3"];
  let currentStep =
    parseInt(new URLSearchParams(window.location.search).get("step") || "1") -
    1;

  function showStep(index) {
    steps.forEach((step, i) => {
      document.getElementById(step).classList.toggle("active", i === index);
    });
    updateIndicators(index);
    window.history.replaceState(null, null, `?step=${index + 1}`);
  }

  function updateIndicators(index) {
    document
      .getElementById("step1-indicator")
      .classList.toggle("active", index >= 0);
    document
      .getElementById("step2-indicator")
      .classList.toggle("active", index >= 1);
    document
      .getElementById("step3-indicator")
      .classList.toggle("active", index >= 2);
  }

  function populateReview() {
    const reviewContent = document.getElementById("review-content");
    if (!reviewContent) return;

    const firstName = form.querySelector('[name="first_name"]')?.value || "";
    const lastName = form.querySelector('[name="last_name"]')?.value || "";
    const email = form.querySelector('[name="email"]')?.value || "";
    const phone = form.querySelector('[name="phone"]')?.value || "";
    const grantType = form.querySelector('[name="grant_type"]')?.value || "";
    const amount = form.querySelector('[name="amount_requested"]')?.value || "";
    const description = form.querySelector('[name="description"]')?.value || "";

    reviewContent.innerHTML = `
      <ul class="list-group">
        <li class="list-group-item"><strong>Name:</strong> ${firstName} ${lastName}</li>
        <li class="list-group-item"><strong>Email:</strong> ${email}</li>
        <li class="list-group-item"><strong>Phone:</strong> ${phone}</li>
        <li class="list-group-item"><strong>Grant Type:</strong> ${grantType}</li>
        <li class="list-group-item"><strong>Amount Requested:</strong> $${amount}</li>
        <li class="list-group-item"><strong>Reason:</strong> ${description}</li>
      </ul>
    `;
  }

  async function submitStep(stepData, isFinal = false) {
    try {
      const res = await fetch("", {
        method: "POST",
        body: stepData,
      });

      const text = await res.text();
      let json;
      try {
        json = JSON.parse(text);
      } catch (e) {
        console.error("Non-JSON response:", text);
        alert("An unexpected server error occurred.");
        return false;
      }

      if (!res.ok) {
        alert("Error: " + (json.error || "Please check your inputs."));
        return false;
      }

      if (json.redirect) {
        window.location.href = json.redirect;
        return true;
      }

      // If it's a successful step 1 or step 2 save, advance manually
      if (!isFinal) {
        return true;
      }

      return false;
    } catch (err) {
      console.error("Network error:", err);
      alert("Network error. Please try again.");
      return false;
    }
  }

  // Next Step / Submit handler
  form.addEventListener("submit", async function (e) {
    e.preventDefault();

    const currentFormStepId = steps[currentStep];
    const formStepElement = document.getElementById(currentFormStepId);

    // Validate current visible step fields with browser built-in constraints
    const inputs = formStepElement.querySelectorAll("input, select, textarea");
    let valid = true;
    inputs.forEach((input) => {
      if (!input.checkValidity()) {
        input.reportValidity();
        valid = false;
      }
    });

    if (!valid) return;

    const formData = new FormData(form);
    formData.append("step", (currentStep + 1).toString());

    const isFinalStep = currentStep === 2;

    if (isFinalStep) {
      const certifyBox = document.getElementById("certify");
      if (certifyBox && !certifyBox.checked) {
        alert("You must certify that the information is true and accurate.");
        return;
      }
    }

    // Submit via AJAX
    const success = await submitStep(formData, isFinalStep);

    if (success && !isFinalStep) {
      currentStep++;
      if (currentStep === 2) {
        populateReview(); // Populate summary right before showing step 3
      }
      showStep(currentStep);
    }
  });

  // Global Next Step hook linked to buttons if using onclick="nextStep()"
  window.nextStep = function (targetStepNum) {
    form.requestSubmit(); // Triggers the submit event listener above cleanly
  };

  // Previous Step
  window.prevStep = function (targetPrevNum) {
    currentStep = Math.max(0, targetPrevNum - 1);
    showStep(currentStep);
  };

  // Initial display setup on page load
  showStep(currentStep);
});
