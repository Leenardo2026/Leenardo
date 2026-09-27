/**
 * Authentication Modal & UI Controller for leenardo.com
 */

(function () {
  // Inject HTML markup for the Auth Modal
  function injectAuthModal() {
    if (document.getElementById("auth-modal-overlay")) return;

    const modalHTML = `
      <div id="auth-modal-overlay" class="auth-modal-overlay" role="dialog" aria-modal="true" aria-labelledby="auth-modal-title">
        <div class="auth-modal-box">
          <div class="auth-modal-header">
            <h3 class="auth-modal-title" id="auth-modal-title">Welcome to Leenardo</h3>
            <button class="auth-modal-close-btn" id="auth-modal-close" aria-label="Close">&times;</button>
          </div>

          <div class="auth-tabs-nav" id="auth-tabs-nav">
            <button class="auth-tab-btn active" data-tab="signin" id="tab-btn-signin">Sign In</button>
            <button class="auth-tab-btn" data-tab="signup" id="tab-btn-signup">Create Account</button>
          </div>

          <div class="auth-modal-body">
            <div id="auth-alert" class="auth-alert"></div>

            <!-- Sign In Form -->
            <form id="form-signin" class="auth-form-panel active">
              <div class="auth-input-group">
                <label class="auth-input-label" for="signin-email">Email Address</label>
                <input class="auth-input-field" type="email" id="signin-email" required placeholder="you@example.com" autocomplete="email">
              </div>
              <div class="auth-input-group">
                <label class="auth-input-label" for="signin-password">Password</label>
                <input class="auth-input-field" type="password" id="signin-password" required placeholder="••••••••" autocomplete="current-password">
              </div>
              <button type="submit" class="auth-submit-btn" id="btn-submit-signin">
                <span>Sign In</span> →
              </button>
              <a class="auth-footer-link" id="link-forgot-password">Forgot your password?</a>
            </form>

            <!-- Sign Up Form -->
            <form id="form-signup" class="auth-form-panel">
              <div class="auth-input-group">
                <label class="auth-input-label" for="signup-name">Full Name</label>
                <input class="auth-input-field" type="text" id="signup-name" placeholder="Mia Yilmaz" autocomplete="name">
              </div>
              <div class="auth-input-group">
                <label class="auth-input-label" for="signup-email">Email Address</label>
                <input class="auth-input-field" type="email" id="signup-email" required placeholder="you@example.com" autocomplete="email">
              </div>
              <div class="auth-input-group">
                <label class="auth-input-label" for="signup-password">Create Password (min. 6 characters)</label>
                <input class="auth-input-field" type="password" id="signup-password" required minlength="6" placeholder="••••••••" autocomplete="new-password">
              </div>
              <button type="submit" class="auth-submit-btn" id="btn-submit-signup">
                <span>Create Free Account</span> ✨
              </button>
            </form>

            <!-- Forgot Password Form -->
            <form id="form-forgot" class="auth-form-panel">
              <p style="font-size:0.85rem; color:var(--slate-600); margin-bottom:0.75rem;">
                Enter your registered email address and we'll send you a link to reset your password.
              </p>
              <div class="auth-input-group">
                <label class="auth-input-label" for="forgot-email">Email Address</label>
                <input class="auth-input-field" type="email" id="forgot-email" required placeholder="you@example.com">
              </div>
              <button type="submit" class="auth-submit-btn" id="btn-submit-forgot">
                <span>Send Reset Link</span> 📧
              </button>
              <a class="auth-footer-link" id="link-back-to-signin">← Back to Sign In</a>
            </form>
          </div>
        </div>
      </div>
    `;

    document.body.insertAdjacentHTML("beforeend", modalHTML);
    setupModalEvents();
  }

  // Setup modal interactivity
  function setupModalEvents() {
    const overlay = document.getElementById("auth-modal-overlay");
    const closeBtn = document.getElementById("auth-modal-close");
    const tabsNav = document.getElementById("auth-tabs-nav");
    const tabBtns = tabsNav.querySelectorAll(".auth-tab-btn");

    const formSignIn = document.getElementById("form-signin");
    const formSignUp = document.getElementById("form-signup");
    const formForgot = document.getElementById("form-forgot");

    const linkForgot = document.getElementById("link-forgot-password");
    const linkBack = document.getElementById("link-back-to-signin");

    // Close logic
    function closeModal() {
      overlay.classList.remove("show");
      clearAlert();
    }

    if (closeBtn) closeBtn.onclick = closeModal;
    if (overlay) {
      overlay.onclick = (e) => {
        if (e.target === overlay) closeModal();
      };
    }
    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && overlay && overlay.classList.contains("show")) {
        closeModal();
      }
    });

    // Switch tab
    function switchTab(tabKey) {
      clearAlert();
      tabBtns.forEach(b => b.classList.remove("active"));
      [formSignIn, formSignUp, formForgot].forEach(f => f.classList.remove("active"));

      if (tabKey === "signin") {
        tabsNav.style.display = "flex";
        document.getElementById("tab-btn-signin").classList.add("active");
        formSignIn.classList.add("active");
        document.getElementById("auth-modal-title").textContent = "Sign In to Leenardo";
      } else if (tabKey === "signup") {
        tabsNav.style.display = "flex";
        document.getElementById("tab-btn-signup").classList.add("active");
        formSignUp.classList.add("active");
        document.getElementById("auth-modal-title").textContent = "Join Leenardo";
      } else if (tabKey === "forgot") {
        tabsNav.style.display = "none";
        formForgot.classList.add("active");
        document.getElementById("auth-modal-title").textContent = "Reset Password";
      }
    }

    tabBtns.forEach(btn => {
      btn.onclick = () => switchTab(btn.dataset.tab);
    });

    if (linkForgot) linkForgot.onclick = () => switchTab("forgot");
    if (linkBack) linkBack.onclick = () => switchTab("signin");

    // Form Submissions
    formSignIn.onsubmit = async (e) => {
      e.preventDefault();
      clearAlert();
      const email = document.getElementById("signin-email").value.trim();
      const password = document.getElementById("signin-password").value;
      const submitBtn = document.getElementById("btn-submit-signin");

      try {
        submitBtn.disabled = true;
        submitBtn.textContent = "Signing In...";
        await LeenardoAuth.signIn(email, password);
        closeModal();
        showGlobalToast("Welcome back!");
      } catch (err) {
        showAlert(err.message || "Failed to sign in. Check your email & password.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "<span>Sign In</span> →";
      }
    };

    formSignUp.onsubmit = async (e) => {
      e.preventDefault();
      clearAlert();
      const name = document.getElementById("signup-name").value.trim();
      const email = document.getElementById("signup-email").value.trim();
      const password = document.getElementById("signup-password").value;
      const submitBtn = document.getElementById("btn-submit-signup");

      try {
        submitBtn.disabled = true;
        submitBtn.textContent = "Creating Account...";
        const res = await LeenardoAuth.signUp(email, password, name);
        if (res?.user && !res?.session) {
          showAlert("Account created! Please check your email to confirm your account.", "success");
        } else {
          closeModal();
          showGlobalToast("Welcome to Leenardo!");
        }
      } catch (err) {
        showAlert(err.message || "Could not complete registration.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "<span>Create Free Account</span> →";
      }
    };

    formForgot.onsubmit = async (e) => {
      e.preventDefault();
      clearAlert();
      const email = document.getElementById("forgot-email").value.trim();
      const submitBtn = document.getElementById("btn-submit-forgot");

      try {
        submitBtn.disabled = true;
        submitBtn.textContent = "Sending Link...";
        await LeenardoAuth.resetPassword(email);
        showAlert("Password reset link sent! Check your email inbox.", "success");
      } catch (err) {
        showAlert(err.message || "Could not send reset email.", "error");
      } finally {
        submitBtn.disabled = false;
        submitBtn.innerHTML = "<span>Send Reset Link</span> →";
      }
    };
  }

  function showAlert(msg, type = "error") {
    const el = document.getElementById("auth-alert");
    if (!el) return;
    el.textContent = msg;
    el.className = `auth-alert ${type}`;
  }

  function clearAlert() {
    const el = document.getElementById("auth-alert");
    if (!el) return;
    el.textContent = "";
    el.className = "auth-alert";
  }

  function openAuthModal(defaultTab = "signin") {
    injectAuthModal();
    const overlay = document.getElementById("auth-modal-overlay");
    if (overlay) {
      overlay.classList.add("show");
      const tabBtn = document.querySelector(`.auth-tab-btn[data-tab="${defaultTab}"]`);
      if (tabBtn) tabBtn.click();
    }
  }

  function showGlobalToast(msg) {
    if (typeof showToast === "function") {
      showToast(msg);
      return;
    }
    // Simple toast fallback
    let toast = document.getElementById("leenardo-toast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "leenardo-toast";
      toast.style.cssText = "position:fixed;bottom:24px;right:24px;background:#1B3644;color:#F5F2EC;padding:10px 18px;border-radius:0;border:1px solid #E0DDD6;font-size:0.85rem;font-weight:600;z-index:999999;box-shadow:none;transition:opacity 0.3s ease;";
      document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.opacity = "1";
    setTimeout(() => { toast.style.opacity = "0"; }, 3000);
  }

  // Render Header Auth Button / Dropdown
  function renderHeaderAuthButton(containerId = "header-auth-container") {
    const container = document.getElementById(containerId);
    if (!container) return;

    if (!currentAuthUser) {
      // Logged Out UI
      container.innerHTML = `
        <button class="btn-header-auth" id="btn-open-login" onclick="window.LeenardoUI.openAuthModal('signin')">
          <span>Sign In</span>
        </button>
      `;
    } else {
      // Logged In UI
      const name = currentAuthUser.user_metadata?.full_name || currentAuthUser.email.split("@")[0];
      const initial = name.charAt(0).toUpperCase();

      container.innerHTML = `
        <div style="position:relative; display:inline-block;">
          <button class="btn-header-auth" id="btn-user-profile-menu">
            <span class="auth-user-avatar">${initial}</span>
            <span style="max-width:120px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">${name}</span>
            <span style="font-size:0.6rem; opacity:0.7;">▼</span>
          </button>
          <div class="auth-user-dropdown" id="auth-dropdown-menu">
            <div class="auth-dropdown-header">
              <div class="auth-dropdown-name">${name}</div>
              <div class="auth-dropdown-email">${currentAuthUser.email}</div>
            </div>
            <button class="auth-dropdown-item" id="auth-menu-words" onclick="window.LeenardoUI.handleMyWordsClick()">
              My Saved Words
            </button>
            <button class="auth-dropdown-item danger" id="auth-menu-logout" onclick="window.LeenardoUI.handleSignOut()">
              Sign Out
            </button>
          </div>
        </div>
      `;

      const btnMenu = document.getElementById("btn-user-profile-menu");
      const dropdown = document.getElementById("auth-dropdown-menu");
      if (btnMenu && dropdown) {
        btnMenu.onclick = (e) => {
          e.stopPropagation();
          dropdown.classList.toggle("show");
        };
        document.addEventListener("click", () => {
          dropdown.classList.remove("show");
        });
      }
    }
  }

  // Handle words click
  function handleMyWordsClick() {
    if (typeof openVocabNotebook === "function") {
      openVocabNotebook("words");
    } else {
      // Redirect to article page with notebook or open local modal
      window.location.href = "article.html#notebook";
    }
  }

  // Handle sign out
  async function handleSignOut() {
    try {
      await LeenardoAuth.signOut();
      showGlobalToast("Signed out successfully.");
    } catch (e) {
      console.error("Sign out error:", e);
    }
  }

  // Expose global methods
  window.LeenardoUI = {
    openAuthModal,
    renderHeaderAuthButton,
    handleMyWordsClick,
    handleSignOut
  };

  // Listen to auth changes and update header buttons automatically
  if (typeof onAuthStateChange === "function") {
    onAuthStateChange(() => {
      renderHeaderAuthButton("header-auth-container");
    });
  }

  // Auto-initialize on DOM ready
  document.addEventListener("DOMContentLoaded", () => {
    injectAuthModal();
    renderHeaderAuthButton("header-auth-container");
  });
})();
