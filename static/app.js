const page = {
  modelSelect: document.getElementById("model-select"),
  message: document.getElementById("message"),
  sendButton: document.getElementById("send"),
  error: document.getElementById("error"),
};

function showStatus(elementId, isReady, text) {
  const status = document.getElementById(elementId);
  status.textContent = text;
  status.classList.toggle("ready", isReady);
}

async function loadConnectionStatus() {
  const response = await fetch("/api/status");
  const status = await response.json();

  showStatus(
    "openrouter-status",
    status.openrouter_ready,
    status.openrouter_ready ? "OpenRouter: المفتاح جاهز" : "OpenRouter: أضف المفتاح إلى .env",
  );
  showStatus(
    "lago-status",
    status.lago_ready,
    status.lago_ready ? "Lago: جاهز لاستقبال الاستخدام" : "Lago: غير مربوط بعد",
  );
}

async function loadFreeModels() {
  const response = await fetch("/api/models");
  const result = await response.json();
  if (!response.ok) {
    throw new Error(result.detail || "تعذر تحميل قائمة النماذج.");
  }

  page.modelSelect.replaceChildren();
  for (const model of result.models) {
    const option = document.createElement("option");
    option.value = model.id;
    option.textContent = model.name;
    page.modelSelect.appendChild(option);
  }
  page.modelSelect.disabled = false;
  showSelectedModel();
}

function showSelectedModel() {
  const selectedModel = page.modelSelect.value;
  document.getElementById("model-id").textContent = selectedModel
    ? `المعرّف المرسل إلى OpenRouter: ${selectedModel}`
    : "";
}

function showChatResult(result) {
  document.getElementById("answer").textContent = result.answer || "لم يُرجع النموذج نصًا.";
  document.getElementById("input-tokens").textContent = result.usage.input_tokens.toLocaleString();
  document.getElementById("output-tokens").textContent = result.usage.output_tokens.toLocaleString();
  document.getElementById("total-tokens").textContent = result.usage.total_tokens.toLocaleString();
  document.getElementById("provider-cost").textContent = `$${result.provider_cost.toFixed(2)}`;
  document.getElementById("customer-charge").textContent =
    `سعر تجريبي للعميل حسب معادلة التطبيق: $${result.demo_customer_charge.toFixed(6)}. هذا سعر افتراضي للتعلم، وليس سعر النموذج.`;
  document.getElementById("lago-result").textContent = result.lago.message;
  document.getElementById("result").hidden = false;
}

async function sendMessage() {
  const message = page.message.value.trim();
  page.error.textContent = "";

  if (!message) {
    page.error.textContent = "اكتب سؤالًا أولًا.";
    return;
  }

  page.sendButton.disabled = true;
  page.sendButton.textContent = "بانتظار النموذج…";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: message, model_id: page.modelSelect.value }),
    });
    const result = await response.json();

    if (!response.ok) {
      throw new Error(result.detail || "فشل الطلب.");
    }
    showChatResult(result);
  } catch (error) {
    page.error.textContent = error.message;
  } finally {
    page.sendButton.disabled = false;
    page.sendButton.textContent = "إرسال السؤال";
  }
}

page.modelSelect.addEventListener("change", showSelectedModel);
page.sendButton.addEventListener("click", sendMessage);

loadConnectionStatus().catch(() => {
  showStatus("openrouter-status", false, "تعذر الاتصال بالباك إند");
  showStatus("lago-status", false, "تعذر الاتصال بالباك إند");
});

loadFreeModels().catch((error) => {
  page.modelSelect.replaceChildren(new Option("تعذر تحميل النماذج", ""));
  page.error.textContent = error.message;
});
