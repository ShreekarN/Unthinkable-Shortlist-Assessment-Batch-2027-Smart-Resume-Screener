const loginEmail = document.getElementById("loginEmail");
const loginPassword = document.getElementById("loginPassword");
const loginBtn = document.getElementById("loginBtn");
const loginStatus = document.getElementById("loginStatus");

loginBtn.addEventListener("click", login);

async function login() {
  const email = loginEmail.value.trim();
  const password = loginPassword.value.trim();

  if (!email || !password) {
    loginStatus.textContent = "Enter email and password.";
    return;
  }

  loginBtn.disabled = true;
  loginStatus.textContent = "Signing in...";

  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Login failed");
    }

    window.location.href = "/";
  } catch (error) {
    loginStatus.textContent = error.message;
  } finally {
    loginBtn.disabled = false;
  }
}
