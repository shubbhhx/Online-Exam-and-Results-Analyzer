(function () {
  const questions = Array.from(document.querySelectorAll(".exam-question"));
  const nextBtn = document.getElementById("nextBtn");
  const prevBtn = document.getElementById("prevBtn");
  const counter = document.getElementById("questionCounter");
  const timerEl = document.getElementById("timer");

  if (!questions.length) return;

  let index = 0;
  const durationMinutes = parseInt(timerEl?.dataset.minutes || "0", 10);
  let remainingSeconds = durationMinutes * 60;

  function render() {
    questions.forEach((q, i) => {
      q.classList.toggle("active", i === index);
    });
    if (counter) {
      counter.textContent = `Question ${index + 1} of ${questions.length}`;
    }
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.disabled = index === questions.length - 1;
  }

  function tick() {
    if (!timerEl || remainingSeconds < 0) return;
    const minutes = Math.floor(remainingSeconds / 60);
    const seconds = remainingSeconds % 60;
    timerEl.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;
    remainingSeconds -= 1;
    if (remainingSeconds >= 0) {
      setTimeout(tick, 1000);
    } else {
      const form = document.getElementById("examForm");
      const loader = document.getElementById("pageLoader");
      if (loader) {
        loader.classList.add("is-visible");
      }
      if (form) form.submit();
    }
  }

  if (nextBtn) {
    nextBtn.addEventListener("click", () => {
      if (index < questions.length - 1) {
        index += 1;
        render();
      }
    });
  }

  if (prevBtn) {
    prevBtn.addEventListener("click", () => {
      if (index > 0) {
        index -= 1;
        render();
      }
    });
  }

  render();
  if (timerEl && durationMinutes > 0) {
    tick();
  }
})();
