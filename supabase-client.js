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
if (window.supabase && typeof window.supabase.createClient === "function") {
  try {
    supabaseClient = window.supabase.createClient(SUPABASE_CONFIG.url, SUPABASE_CONFIG.anonKey);
    console.log("💎 Supabase client successfully initialized.");
  } catch (err) {
    console.error("Failed to initialize Supabase client:", err);
  }
} else {
  console.warn("Supabase library not loaded yet. Waiting for script load...");
}

// Global state
let currentAuthUser = null;

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
  authStateListeners.forEach(fn => {
    try { fn(user); } catch (e) { console.error("Auth listener error:", e); }
  });
}

// Authentication API
const LeenardoAuth = {
  /**
   * Get current authenticated user
   */
  async getUser() {
    if (!supabaseClient) return null;
    try {
      const { data: { session } } = await supabaseClient.auth.getSession();
      currentAuthUser = session ? session.user : null;
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
      // Automatically sync local words to cloud after login
      LeenardoDB.syncLocalWordsToCloud(data.user.id).catch(err => {
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
   */
  async saveWordToCloud(userId, item) {
    if (!supabaseClient || !userId || !item || !item.word) return false;
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
        return false;
      }
      return true;
    } catch (e) {
      console.error("Exception in saveWordToCloud:", e);
      return false;
    }
  },

  /**
   * Delete a word from Supabase
   */
  async removeWordFromCloud(userId, wordText) {
    if (!supabaseClient || !userId || !wordText) return false;
    try {
      const { error } = await supabaseClient
        .from("saved_words")
        .delete()
        .eq("user_id", userId)
        .eq("word", wordText.trim());

      if (error) {
        console.error("Error deleting word from Supabase:", error);
        return false;
      }
      return true;
    } catch (e) {
      console.error("Exception in removeWordFromCloud:", e);
      return false;
    }
  },

  /**
   * Sync local storage words to Supabase upon user sign-in
   */
  async syncLocalWordsToCloud(userId) {
    if (!supabaseClient || !userId) return;
    const STORAGE_KEY = "leenardo_saved_words_v1";
    let localWords = [];
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      localWords = raw ? JSON.parse(raw) : [];
    } catch (e) {
      localWords = [];
    }

    // Index existing local words to preserve rich client metadata (fromLang, toLang, root, rootTranslation)
    const localMap = new Map();
    localWords.forEach(w => {
      if (w && w.word) {
        localMap.set(w.word.toLowerCase().trim(), w);
      }
    });

    const activeTarget = (typeof window !== "undefined" && window.targetLang) ? window.targetLang : "tr";
    const activeSupport = (typeof window !== "undefined" && window.supportLang) ? window.supportLang : "en";

    if (!Array.isArray(localWords) || localWords.length === 0) {
      // If local is empty, pull cloud words to local and attach active fallback languages
      const cloudWords = await this.getCloudWords(userId);
      if (cloudWords.length > 0) {
        const enriched = cloudWords.map(cw => {
          const existing = localMap.get((cw.word || "").toLowerCase().trim());
          return {
            ...cw,
            fromLang: (existing && existing.fromLang) || cw.fromLang || activeTarget,
            toLang: (existing && existing.toLang) || cw.toLang || activeSupport,
            root: (existing && existing.root) || cw.root || "",
            rootTranslation: (existing && existing.rootTranslation) || cw.rootTranslation || ""
          };
        });
        localStorage.setItem(STORAGE_KEY, JSON.stringify(enriched));
        if (typeof updateSavedWordBadges === "function") updateSavedWordBadges();
        if (typeof renderSavedWordsList === "function") renderSavedWordsList();
      }
      return;
    }

    // Upsert each local word to cloud
    for (const item of localWords) {
      if (item && item.word) {
        await this.saveWordToCloud(userId, item);
      }
    }

    // Pull combined list from cloud and merge with rich local metadata
    const updatedCloudWords = await this.getCloudWords(userId);
    const enriched = updatedCloudWords.map(cw => {
      const existing = localMap.get((cw.word || "").toLowerCase().trim());
      return {
        ...cw,
        id: (existing && existing.id) || cw.id,
        fromLang: (existing && existing.fromLang) || cw.fromLang || activeTarget,
        toLang: (existing && existing.toLang) || cw.toLang || activeSupport,
        root: (existing && existing.root) || cw.root || "",
        rootTranslation: (existing && existing.rootTranslation) || cw.rootTranslation || ""
      };
    });

    localStorage.setItem(STORAGE_KEY, JSON.stringify(enriched));

    if (typeof updateSavedWordBadges === "function") updateSavedWordBadges();
    if (typeof renderSavedWordsList === "function") renderSavedWordsList();
    console.log(`✅ Synced ${enriched.length} words with cloud.`);
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
    // Check initial session
    const { data: { session } } = await supabaseClient.auth.getSession();
    if (session && session.user) {
      notifyAuthStateListeners(session.user);
    }

    // Listen to real-time auth changes
    supabaseClient.auth.onAuthStateChange((event, session) => {
      const user = session ? session.user : null;
      notifyAuthStateListeners(user);
      if (event === "SIGNED_IN" && user) {
        LeenardoDB.syncLocalWordsToCloud(user.id);
      }
    });
  }
});
