/**
 * Supabase Client & Database Services for leenardo.com
 * Handles User Authentication and Cloud Saved Words Synchronization
 */

const SUPABASE_CONFIG = {
  url: "https://vkddnvpqnccstcjnqfyq.supabase.co",
  anonKey: "sb_publishable_wPeD9aYQWmnAJYf1pqDxvQ_PiPm-GC-"
};
window.SUPABASE_CONFIG = SUPABASE_CONFIG;

// Initialize the Supabase Client if library is available
let supabaseClient = null;
let sessionCheckPromise = null;

function checkInitialSession() {
  if (!sessionCheckPromise && supabaseClient) {
    sessionCheckPromise = supabaseClient.auth.getSession().then(({ data }) => {
      const user = data && data.session ? data.session.user : null;
      notifyAuthStateListeners(user);
      return user;
    }).catch(err => {
      console.warn("getSession error:", err);
      notifyAuthStateListeners(null);
      return null;
    });
  }
  return sessionCheckPromise;
}

if (window.supabase && typeof window.supabase.createClient === "function") {
  try {
    supabaseClient = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);
    console.log("💎 Supabase client successfully initialized.");
    checkInitialSession();
  } catch (err) {
    console.error("Failed to initialize Supabase client:", err);
  }
} else {
  console.warn("Supabase library not loaded yet. Waiting for script load...");
}

// Global state
let currentAuthUser = null;
if (typeof window !== "undefined") {
  window.currentAuthUser = null;
}

// User state listeners
const authStateListeners = [];
function onAuthStateChange(listener) {
  if (typeof listener === "function") {
    authStateListeners.push(listener);
    if (currentAuthUser !== null) {
      try { listener(currentAuthUser); } catch(e) {}
    }
  }
}

function notifyAuthStateListeners(user) {
  currentAuthUser = user;
  if (!user) {
    sessionCheckPromise = null;
  }
  if (typeof window !== "undefined") {
    window.currentAuthUser = user;
  }
  authStateListeners.forEach(fn => {
    try { fn(user); } catch (e) { console.error("Auth listener error:", e); }
  });
}

// Authentication API
const LeenardoAuth = {
  /**
   * Get current authenticated user (synchronous)
   */
  getCurrentUser() {
    return currentAuthUser || (typeof window !== "undefined" ? window.currentAuthUser : null);
  },

  /**
   * Wait for session check to complete if in flight, or return current user
   */
  async waitForSession() {
    if (currentAuthUser) return currentAuthUser;
    if (sessionCheckPromise) {
      const sessUser = await sessionCheckPromise;
      if (sessUser) return sessUser;
    }
    if (supabaseClient) return await this.getUser();
    return null;
  },

  /**
   * Get current authenticated user (asynchronous check against session)
   */
  async getUser() {
    if (!supabaseClient) return null;
    try {
      const { data: { session } } = await supabaseClient.auth.getSession();
      currentAuthUser = session ? session.user : null;
      if (typeof window !== "undefined") {
        window.currentAuthUser = currentAuthUser;
      }
      return currentAuthUser;
    } catch (e) {
      console.error("Error getting session:", e);
      return null;
    }
  },

  /**
   * Sign up with email & password
   */
  async signUp(email, password, fullName = "") {
    if (!supabaseClient) throw new Error("Supabase client is not initialized.");
    const { data, error } = await supabaseClient.auth.signUp({
      email,
      password,
      options: {
        data: { full_name: fullName }
      }
    });
    if (error) throw error;
    if (data && data.user) {
      notifyAuthStateListeners(data.user);
    }
    return data;
  },

  /**
   * Sign in with email & password
   */
  async signIn(email, password) {
    if (!supabaseClient) throw new Error("Supabase client is not initialized.");
    const { data, error } = await supabaseClient.auth.signInWithPassword({
      email,
      password
    });
    if (error) throw error;
    if (data && data.user) {
      notifyAuthStateListeners(data.user);
      // Automatically sync pending words to cloud after login
      LeenardoDB.syncPendingWordsToCloud(data.user.id).catch(err => {
        console.warn("Background word sync warning:", err);
      });
    }
    return data;
  },

  /**
   * Sign out
   */
  async signOut() {
    if (!supabaseClient) return;
    sessionCheckPromise = null;
    const { error } = await supabaseClient.auth.signOut();
    if (error) console.error("Sign out error:", error);
    notifyAuthStateListeners(null);
  },

  /**
   * Send password reset email
   */
  async resetPassword(email) {
    if (!supabaseClient) throw new Error("Supabase client is not initialized.");
    const { data, error } = await supabaseClient.auth.resetPasswordForEmail(email, {
      redirectTo: window.location.origin
    });
    if (error) throw error;
    return data;
  }
};

// Database API for Saved Words
const LeenardoDB = {
  /**
   * Fetch all saved words from Supabase for the active user
   */
  async getCloudWords(userId) {
    if (!supabaseClient || !userId) return [];
    try {
      const { data, error } = await supabaseClient
        .from("saved_words")
        .select("*")
        .eq("user_id", userId)
        .order("created_at", { ascending: false });

      if (error) {
        console.error("Error fetching words from Supabase:", error);
        return [];
      }

      // Format back to application's word item structure
      return (data || []).map(row => ({
        id: "w_" + encodeURIComponent(row.word.toLowerCase()),
        word: row.word,
        translation: row.translation || "",
        contextSentence: row.context_sentence || "",
        articleId: row.article_id || "",
        level: row.level || "A1",
        createdAt: new Date(row.created_at).getTime()
      }));
    } catch (e) {
      console.error("Exception in getCloudWords:", e);
      return [];
    }
  },

  /**
   * Save or update a word in Supabase
   * @returns {Promise<{success: boolean, error: any}>}
   */
  async saveWordToCloud(userId, item) {
    if (!supabaseClient || !userId || !item || !item.word) {
      return { success: false, error: "Missing required parameters" };
    }
    try {
      const payload = {
        user_id: userId,
        word: item.word.trim(),
        translation: item.translation || "",
        context_sentence: item.contextSentence || "",
        article_id: item.articleId || "",
        level: item.level || "A1"
      };

      const { data, error } = await supabaseClient
        .from("saved_words")
        .upsert(payload, { onConflict: "user_id, word" });

      if (error) {
        console.error("Error saving word to Supabase:", error);
        return { success: false, error };
      }
      return { success: true, error: null };
    } catch (e) {
      console.error("Exception in saveWordToCloud:", e);
      return { success: false, error: e };
    }
  },

  /**
   * Delete a word from Supabase
   */
  async removeWordFromCloud(userId, wordText) {
    if (!supabaseClient || !userId || !wordText) {
      console.warn("removeWordFromCloud: Missing required parameters", { userId, wordText });
      return { success: false, count: 0, error: "Missing required parameters" };
    }
    try {
      const cleanWord = wordText.trim();
      const { data, error, count } = await supabaseClient
        .from("saved_words")
        .delete({ count: "exact" })
        .eq("user_id", userId)
        .eq("word", cleanWord)
        .select();

      const affected = (data && Array.isArray(data)) ? data.length : (count || 0);

      console.log("Supabase delete response:", {
        word: cleanWord,
        userId: userId,
        data: data,
        count: count,
        affected: affected,
        error: error
      });

      if (error) {
        console.error("Error deleting word from Supabase:", error);
        return { success: false, count: 0, error };
      }

      return {
        success: affected >= 1,
        count: affected,
        data: data,
        error: null
      };
    } catch (e) {
      console.error("Exception in removeWordFromCloud:", e);
      return { success: false, count: 0, error: e };
    }
  },

  /**
   * Retry pending local storage words to Supabase upon valid session confirmation.
   * Uploads ONLY items with pendingSync: true to avoid resurrecting deleted words.
   */
  async syncPendingWordsToCloud(userId) {
    if (!supabaseClient || !userId) return;
    const STORAGE_KEY = "leenardo_saved_words_v1";
    let localWords = [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      localWords = raw ? JSON.parse(raw) : [];
    } catch (e) {
      localWords = [];
    }

    if (!Array.isArray(localWords) || localWords.length === 0) return;

    let hasChanges = false;
    for (const item of localWords) {
      if (item && item.word && item.pendingSync) {
        const res = await this.saveWordToCloud(userId, item);
        if (res && res.success) {
          delete item.pendingSync;
          hasChanges = true;
        }
      }
    }

    if (hasChanges) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(localWords));
      if (typeof updateSavedWordBadges === "function") updateSavedWordBadges();
      if (typeof renderSavedWordsList === "function") renderSavedWordsList();
      console.log("✅ Successfully synced pending local words to cloud.");
    }
  },

  /**
   * Legacy alias: safely synchronizes only pending items
   */
  async syncLocalWordsToCloud(userId) {
    return this.syncPendingWordsToCloud(userId);
  }
};

// Article Issue Reporting Service
const LeenardoReports = {
  /**
   * Submit an article issue report
   * @param {Object} report
   * @param {string} report.articleId - Story ID
   * @param {string} report.targetLang - Active target language
   * @param {string} report.supportLang - Active translation language
   * @param {string} report.cefrLevel - Active CEFR level (A1, A2, etc.)
   * @param {string} report.issueType - Type of issue
   * @param {string} [report.notes] - Optional user description
   * @returns {Promise<{success: boolean, error?: any}>}
   */
  async submitArticleReport({ articleId, targetLang, supportLang, cefrLevel, issueType, notes }) {
    if (!articleId || !issueType) {
      return { success: false, error: "Missing required fields" };
    }

    if (supabaseClient) {
      try {
        const user = currentAuthUser || (await LeenardoAuth.getUser());
        const payload = {
          article_id: articleId,
          target_lang: targetLang || "en",
          support_lang: supportLang || "tr",
          cefr_level: cefrLevel || "A1",
          issue_type: issueType,
          notes: notes ? notes.trim().slice(0, 1000) : null,
          user_id: user ? user.id : null,
          user_email: user ? user.email : null,
          status: "pending"
        };

        const { data, error } = await supabaseClient
          .from("article_reports")
          .insert([payload]);

        if (error) {
          console.warn("Supabase insert error on article_reports:", error);
          // Return success gracefully so user reading experience is not broken
          return { success: true, queued: true, note: "Report acknowledged" };
        }
        return { success: true, data };
      } catch (err) {
        console.error("Failed to submit report to Supabase:", err);
        return { success: true, queued: true, error: err.message };
      }
    }

    console.log("💎 Article report acknowledged (offline/local fallback):", { articleId, issueType, cefrLevel });
    return { success: true, queued: true };
  }
};

// Export services globally
window.LeenardoAuth = LeenardoAuth;
window.LeenardoDB = LeenardoDB;
window.LeenardoReports = LeenardoReports;

// Setup initial auth session listener when library loads
document.addEventListener("DOMContentLoaded", async () => {
  if (!supabaseClient && window.supabase && typeof window.supabase.createClient === "function") {
    try {
      supabaseClient = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);
    } catch (e) {}
  }

  if (supabaseClient) {
    // Check initial session and retry pending words if user is authenticated
    checkInitialSession().then(user => {
      if (user) {
        LeenardoDB.syncPendingWordsToCloud(user.id).catch(() => {});
      }
    });

    // Listen to real-time auth changes
    supabaseClient.auth.onAuthStateChange((event, session) => {
      const user = session ? session.user : null;
      notifyAuthStateListeners(user);
      if ((event === "SIGNED_IN" || event === "INITIAL_SESSION") && user) {
        LeenardoDB.syncPendingWordsToCloud(user.id).catch(() => {});
      }
    });
  }
});
