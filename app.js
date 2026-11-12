// ============================================================
// キャラクター シルエットクイズ - Frontend Script
// 【ポケモン / 妖怪ウォッチ / ドラクエ / マリオ / オールスター】
// ============================================================

// --- 効果音システム (Web Audio API) ---
class SoundEffects {
  constructor() {
    this.enabled = true;
    this.ctx = null;
  }

  init() {
    if (!this.ctx) {
      const AudioContext = window.AudioContext || window.webkitAudioContext;
      this.ctx = new AudioContext();
    }
    if (this.ctx.state === "suspended") {
      this.ctx.resume();
    }
  }

  playTone(freq, type, duration, startTime = 0) {
    if (!this.enabled) return;
    this.init();
    const osc = this.ctx.createOscillator();
    const gain = this.ctx.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, this.ctx.currentTime + startTime);
    gain.gain.setValueAtTime(0.15, this.ctx.currentTime + startTime);
    gain.gain.exponentialRampToValueAtTime(0.001, this.ctx.currentTime + startTime + duration);
    osc.connect(gain);
    gain.connect(this.ctx.destination);
    osc.start(this.ctx.currentTime + startTime);
    osc.stop(this.ctx.currentTime + startTime + duration);
  }

  playJingle() {
    if (!this.enabled) return;
    this.playTone(523.25, "triangle", 0.12, 0.0);
    this.playTone(659.25, "triangle", 0.12, 0.1);
    this.playTone(783.99, "triangle", 0.20, 0.2);
  }

  playCorrect() {
    if (!this.enabled) return;
    const notes = [523.25, 659.25, 783.99, 1046.50];
    notes.forEach((f, i) => {
      this.playTone(f, "sine", 0.18, i * 0.08);
    });
  }

  playWrong() {
    if (!this.enabled) return;
    this.playTone(180, "sawtooth", 0.18, 0.0);
    this.playTone(140, "sawtooth", 0.25, 0.18);
  }

  playAlmost() {
    if (!this.enabled) return;
    this.playTone(330, "sine", 0.15, 0.0);
    this.playTone(392, "sine", 0.25, 0.15);
  }

  playClick() {
    if (!this.enabled) return;
    this.playTone(800, "sine", 0.04, 0);
  }
}

const sfx = new SoundEffects();

// --- アプリケーション状態 ---
const state = {
  score: 0,
  streak: 0,
  maxStreak: 0,
  correctCount: 0,
  currentQuestion: null,
  hintsUsed: 0,
  questionStartTime: null,
  timerInterval: null,
  answered: false,
  category: "pokemon",   // 'pokemon', 'yokai', 'dq', 'mario', 'all'
  formFilter: "all",     // ポケモン用
  currentCollectionCat: "pokemon"
};

// DOM 要素
const elements = {
  appTitle: document.getElementById("app-title"),
  appLogoIcon: document.getElementById("app-logo-icon"),
  speechBubbleText: document.getElementById("speech-bubble-text"),
  categoryBadge: document.getElementById("category-badge"),
  formIndicatorBadge: document.getElementById("form-indicator-badge"),
  pokemonSubfilterArea: document.getElementById("pokemon-subfilter-area"),
  scoreDisplay: document.getElementById("score-display"),
  streakDisplay: document.getElementById("streak-display"),
  timerDisplay: document.getElementById("timer-display"),
  characterImg: document.getElementById("character-img"),
  resultOverlay: document.getElementById("result-overlay"),
  resultBadge: document.getElementById("result-badge"),
  resultName: document.getElementById("result-name"),
  resultGenus: document.getElementById("result-genus"),
  resultScorePopup: document.getElementById("result-score-popup"),
  textAnswerInput: document.getElementById("text-answer-input"),
  textSubmitBtn: document.getElementById("text-submit-btn"),
  characterDatalist: document.getElementById("character-datalist"),
  answerFeedback: document.getElementById("answer-feedback"),
  nextActionArea: document.getElementById("next-action-area"),
  nextQuestionBtn: document.getElementById("next-question-btn"),
  finishGameBtn: document.getElementById("finish-game-btn"),
  soundToggleBtn: document.getElementById("sound-toggle-btn"),
  // ヒント関連
  hintsDisplayArea: document.getElementById("hints-display-area"),
  hintAttr1Btn: document.getElementById("hint-attr1-btn"),
  hintAttr1BtnText: document.getElementById("hint-attr1-btn-text"),
  hintGenusBtn: document.getElementById("hint-genus-btn"),
  hintGenusBtnText: document.getElementById("hint-genus-btn-text"),
  hintFlavorBtn: document.getElementById("hint-flavor-btn"),
  hintFlavorBtnText: document.getElementById("hint-flavor-btn-text"),
  hintAttr1Reveal: document.getElementById("hint-attr1-reveal"),
  hintGenusReveal: document.getElementById("hint-genus-reveal"),
  hintFlavorReveal: document.getElementById("hint-flavor-reveal"),
  // 図鑑
  collectionGrid: document.getElementById("collection-grid"),
  collectionProgressBar: document.getElementById("collection-progress-bar"),
  collectionCollectedText: document.getElementById("collection-collected-text"),
  collectionTotalText: document.getElementById("collection-total-text"),
  collectionRateText: document.getElementById("collection-rate-text"),
  navCollectionCount: document.getElementById("nav-collection-count"),
  // リーダーボード＆統計
  leaderboardTbody: document.getElementById("leaderboard-tbody"),
  statTotalAnswers: document.getElementById("stat-total-answers"),
  statAccuracy: document.getElementById("stat-accuracy"),
  statAvgTime: document.getElementById("stat-avg-time"),
  topCorrectList: document.getElementById("top-correct-list"),
  topWrongList: document.getElementById("top-wrong-list"),
  // モーダル
  rankingModal: document.getElementById("ranking-modal"),
  modalFinalScore: document.getElementById("modal-final-score"),
  modalFinalCorrect: document.getElementById("modal-final-correct"),
  modalFinalStreak: document.getElementById("modal-final-streak"),
  playerNameInput: document.getElementById("player-name-input"),
  submitScoreBtn: document.getElementById("submit-score-btn"),
  cancelScoreBtn: document.getElementById("cancel-score-btn"),
  // SQL探検
  sqlQueryInput: document.getElementById("sql-query-input"),
  sqlExecBtn: document.getElementById("sql-exec-btn"),
  sqlMetaInfo: document.getElementById("sql-meta-info"),
  sqlThead: document.getElementById("sql-thead"),
  sqlTbody: document.getElementById("sql-tbody")
};

// ==========================================
// 1. クイズ出題＆回答ロジック
// ==========================================

async function fetchNextQuestion() {
  resetQuestionUI();
  try {
    const res = await fetch(`/api/quiz/question?category=${state.category}&form=${state.formFilter}`);
    const data = await res.json();
    state.currentQuestion = data;
    renderQuestion(data);
  } catch (err) {
    console.error("問題取得エラー:", err);
    alert("問題の取得に失敗しました。サーバーが起動しているか確認してください。");
  }
}

function resetQuestionUI() {
  state.answered = false;
  state.hintsUsed = 0;
  clearInterval(state.timerInterval);

  elements.resultOverlay.classList.add("hidden");
  elements.resultOverlay.classList.remove("wrong");
  elements.nextActionArea.classList.add("hidden");
  elements.answerFeedback.classList.add("hidden");
  elements.answerFeedback.textContent = "";

  elements.textAnswerInput.value = "";
  elements.textAnswerInput.disabled = false;
  elements.textSubmitBtn.disabled = false;
  setTimeout(() => elements.textAnswerInput.focus(), 50);

  elements.characterImg.className = "character-image silhouette";
  elements.characterImg.src = "";

  elements.hintsDisplayArea.classList.add("hidden");
  elements.hintAttr1Btn.disabled = false;
  elements.hintGenusBtn.disabled = false;
  elements.hintFlavorBtn.disabled = false;
  elements.hintAttr1Reveal.classList.add("hidden");
  elements.hintGenusReveal.classList.add("hidden");
  elements.hintFlavorReveal.classList.add("hidden");

  elements.timerDisplay.textContent = "0.0s";
}

function renderQuestion(q) {
  elements.characterImg.src = q.image_url;
  sfx.playJingle();

  // カテゴリバナー＆ラベルの設定
  const meta = q.meta;
  elements.speechBubbleText.textContent = meta.banner;
  elements.categoryBadge.className = `cat-tag ${q.category}`;
  elements.categoryBadge.textContent = `${meta.badge_icon} ${meta.title}`;

  // ヒントボタンテキストの動的更新
  elements.hintAttr1BtnText.textContent = `ヒント1: ${meta.attr1_label}を見る`;
  elements.hintGenusBtnText.textContent = `ヒント2: ${meta.genus_label}を見る`;
  elements.hintFlavorBtnText.textContent = `ヒント3: ${meta.flavor_label}を見る`;

  // ポケモンの特殊姿バッジ
  if (q.category === "pokemon" && q.form_type && q.form_type !== "normal") {
    elements.formIndicatorBadge.className = `form-tag ${q.form_type}`;
    elements.formIndicatorBadge.textContent = `⚡ ${q.hints.form_hint}`;
    elements.formIndicatorBadge.classList.remove("hidden");
  } else {
    elements.formIndicatorBadge.classList.add("hidden");
  }

  // タイマースタート
  state.questionStartTime = Date.now();
  state.timerInterval = setInterval(() => {
    const elapsed = ((Date.now() - state.questionStartTime) / 1000).toFixed(1);
    elements.timerDisplay.textContent = `${elapsed}s`;
  }, 100);
}

// 回答送信
async function submitAnswer() {
  if (state.answered) return;
  const chosenName = elements.textAnswerInput.value.trim();
  if (!chosenName) {
    elements.textAnswerInput.focus();
    return;
  }

  state.answered = true;
  clearInterval(state.timerInterval);

  const timeTakenMs = Date.now() - state.questionStartTime;

  try {
    const res = await fetch("/api/quiz/answer", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        character_id: state.currentQuestion.character_id,
        chosen_name: chosenName,
        hints_used: state.hintsUsed,
        time_taken_ms: timeTakenMs,
        current_streak: state.streak
      })
    });
    const result = await res.json();
    handleAnswerResult(result);
  } catch (err) {
    console.error("判定エラー:", err);
    alert("判定中にエラーが発生しました");
  }
}

function handleAnswerResult(result) {
  elements.characterImg.className = "character-image revealed";
  elements.textAnswerInput.disabled = true;
  elements.textSubmitBtn.disabled = true;

  if (result.is_correct) {
    sfx.playCorrect();
    state.score += result.earned_score;
    state.streak += 1;
    state.correctCount += 1;
    if (state.streak > state.maxStreak) {
      state.maxStreak = state.streak;
    }

    elements.resultOverlay.classList.remove("wrong");
    elements.resultBadge.textContent = "せいかい！🎉";
    elements.resultScorePopup.textContent = `+${result.earned_score} pts!`;
    elements.answerFeedback.classList.add("hidden");
  } else {
    if (result.almost) {
      sfx.playAlmost();
      elements.answerFeedback.textContent = result.almost_message;
      elements.answerFeedback.classList.remove("hidden");
    } else {
      sfx.playWrong();
      elements.answerFeedback.classList.add("hidden");
    }
    state.streak = 0;

    elements.resultOverlay.classList.add("wrong");
    elements.resultBadge.textContent = "ざんねん…！❌";
    elements.resultScorePopup.textContent = "+0 pts";
  }

  elements.resultName.textContent = result.character.name_ja;
  elements.resultGenus.textContent = `${result.character.genus || ""} [クリア回数: ${result.character.captured_count}回]`;
  elements.resultOverlay.classList.remove("hidden");

  elements.scoreDisplay.textContent = state.score.toLocaleString();
  elements.streakDisplay.textContent = state.streak;

  elements.nextActionArea.classList.remove("hidden");
  elements.nextQuestionBtn.focus();

  updateCollectionNavCount();
}

// ヒント機能
function setupHintHandlers() {
  elements.hintAttr1Btn.addEventListener("click", () => {
    if (state.answered || !state.currentQuestion) return;
    sfx.playClick();
    state.hintsUsed += 1;
    elements.hintAttr1Btn.disabled = true;
    elements.hintsDisplayArea.classList.remove("hidden");

    const meta = state.currentQuestion.meta;
    const hints = state.currentQuestion.hints;
    let text = `${meta.attr1_label}: ${hints.attribute1}`;
    if (hints.attribute2) text += ` / ${hints.attribute2}`;
    elements.hintAttr1Reveal.textContent = text;
    elements.hintAttr1Reveal.classList.remove("hidden");
  });

  elements.hintGenusBtn.addEventListener("click", () => {
    if (state.answered || !state.currentQuestion) return;
    sfx.playClick();
    state.hintsUsed += 1;
    elements.hintGenusBtn.disabled = true;
    elements.hintsDisplayArea.classList.remove("hidden");

    const meta = state.currentQuestion.meta;
    elements.hintGenusReveal.textContent = `${meta.genus_label}: ${state.currentQuestion.hints.genus || "不明"}`;
    elements.hintGenusReveal.classList.remove("hidden");
  });

  elements.hintFlavorBtn.addEventListener("click", () => {
    if (state.answered || !state.currentQuestion) return;
    sfx.playClick();
    state.hintsUsed += 1;
    elements.hintFlavorBtn.disabled = true;
    elements.hintsDisplayArea.classList.remove("hidden");

    elements.hintFlavorReveal.textContent = `${state.currentQuestion.hints.flavor_text || ""}`;
    elements.hintFlavorReveal.classList.remove("hidden");
  });
}

// ==========================================
// 2. 図鑑 / コレクション一覧
// ==========================================

async function loadCollection(category = state.currentCollectionCat) {
  state.currentCollectionCat = category;
  try {
    const res = await fetch(`/api/collection?category=${category}`);
    const data = await res.json();

    elements.collectionProgressBar.style.width = `${data.completion_rate}%`;
    elements.collectionCollectedText.textContent = data.captured;
    elements.collectionTotalText.textContent = data.total;
    elements.collectionRateText.textContent = `${data.completion_rate}%`;

    renderCollectionGrid(data.characters);
  } catch (err) {
    console.error("図鑑取得エラー:", err);
  }
}

function renderCollectionGrid(characters) {
  elements.collectionGrid.innerHTML = "";
  characters.forEach(c => {
    const card = document.createElement("div");
    const isCaptured = c.captured_count > 0;
    card.className = `pokedex-card ${isCaptured ? "captured" : "unseen"}`;

    const nameStr = isCaptured ? c.name_ja : "？？？？";
    const countBadge = isCaptured ? `<div class="dex-count">クリア: ${c.captured_count}回</div>` : "";
    const attrBadge = isCaptured && c.attribute1 ? `<span class="type-badge">${c.attribute1}</span>` : "";

    card.innerHTML = `
      <img src="${c.image_url}" alt="${nameStr}" loading="lazy">
      <div class="dex-name">${nameStr}</div>
      <div>${attrBadge}</div>
      ${countBadge}
    `;
    elements.collectionGrid.appendChild(card);
  });
}

async function updateCollectionNavCount() {
  try {
    const res = await fetch(`/api/collection?category=all`);
    const data = await res.json();
    elements.navCollectionCount.textContent = `${data.captured}/${data.total}`;
  } catch (e) {}
}

async function loadCharacterNamesForDatalist(category = "all") {
  try {
    const res = await fetch(`/api/character/names?category=${category}`);
    const data = await res.json();
    elements.characterDatalist.innerHTML = "";
    data.names.forEach(name => {
      const opt = document.createElement("option");
      opt.value = name;
      elements.characterDatalist.appendChild(opt);
    });
  } catch (e) {}
}

// ==========================================
// 3. ランキング＆統計
// ==========================================

async function loadLeaderboardAndStats() {
  try {
    const resLb = await fetch("/api/leaderboard");
    const dataLb = await resLb.json();
    renderLeaderboard(dataLb.leaderboard);

    const resSt = await fetch("/api/stats");
    const dataSt = await resSt.json();
    renderStats(dataSt);
  } catch (err) {
    console.error("統計読み込みエラー:", err);
  }
}

function renderLeaderboard(list) {
  elements.leaderboardTbody.innerHTML = "";
  if (!list || list.length === 0) {
    elements.leaderboardTbody.innerHTML = '<tr><td colspan="7" style="text-align:center;">まだ記録がありません。一番乗りを目指そう！</td></tr>';
    return;
  }

  list.forEach((entry, idx) => {
    const rank = idx + 1;
    const rankIcon = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : rank;
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td><strong>${rankIcon}</strong></td>
      <td>${escapeHtml(entry.player_name)}</td>
      <td><span class="cat-tag">${escapeHtml(entry.difficulty)}</span></td>
      <td><strong>${entry.score.toLocaleString()}</strong></td>
      <td>${entry.correct_count}問</td>
      <td>${entry.max_streak}連続</td>
      <td>${entry.created_at_jp || ""}</td>
    `;
    elements.leaderboardTbody.appendChild(tr);
  });
}

function renderStats(st) {
  elements.statTotalAnswers.textContent = st.total_answers;
  elements.statAccuracy.textContent = `${st.accuracy_percent}%`;
  elements.statAvgTime.textContent = `${st.avg_time_sec}s`;

  elements.topCorrectList.innerHTML = "";
  if (st.top_correct && st.top_correct.length > 0) {
    st.top_correct.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.name_ja} (${item.correct_count}回)`;
      elements.topCorrectList.appendChild(li);
    });
  } else {
    elements.topCorrectList.innerHTML = "<li>まだデータがありません</li>";
  }

  elements.topWrongList.innerHTML = "";
  if (st.top_wrong && st.top_wrong.length > 0) {
    st.top_wrong.forEach(item => {
      const li = document.createElement("li");
      li.textContent = `${item.name_ja} (${item.wrong_count}回)`;
      elements.topWrongList.appendChild(li);
    });
  } else {
    elements.topWrongList.innerHTML = "<li>まだデータがありません</li>";
  }
}

// ==========================================
// 4. SQL探検コンソール
// ==========================================

async function executeSql(query) {
  elements.sqlMetaInfo.textContent = "クエリ実行中...";
  elements.sqlThead.innerHTML = "";
  elements.sqlTbody.innerHTML = "";

  try {
    const res = await fetch("/api/sql/execute", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query })
    });
    const result = await res.json();

    if (!result.success) {
      elements.sqlMetaInfo.textContent = `❌ エラー: ${result.error}`;
      elements.sqlMetaInfo.style.color = "#ef4444";
      return;
    }

    elements.sqlMetaInfo.textContent = `✔ 実行成功: ${result.row_count} 件取得 (最大100件表示)`;
    elements.sqlMetaInfo.style.color = "#10b981";

    const headerTr = document.createElement("tr");
    result.columns.forEach(col => {
      const th = document.createElement("th");
      th.textContent = col;
      headerTr.appendChild(th);
    });
    elements.sqlThead.appendChild(headerTr);

    result.data.forEach(row => {
      const tr = document.createElement("tr");
      result.columns.forEach(col => {
        const td = document.createElement("td");
        td.textContent = row[col] !== null ? row[col] : "NULL";
        tr.appendChild(td);
      });
      elements.sqlTbody.appendChild(tr);
    });
  } catch (err) {
    elements.sqlMetaInfo.textContent = `❌ 通信エラー: ${err.message}`;
    elements.sqlMetaInfo.style.color = "#ef4444";
  }
}

// ==========================================
// 5. イベントリスナー登録 & テーマ切り替え
// ==========================================

function switchGameMode(category) {
  state.category = category;

  // テーマCSSの切り替え
  document.body.className = `theme-${category}`;

  // ヘッダーアイコン・タイトルの更新
  const icons = {
    pokemon: "🔴",
    yokai: "👻",
    dq: "⚔️",
    mario: "🍄",
    all: "🌟"
  };
  elements.appLogoIcon.textContent = icons[category] || "🎮";

  // ポケモン用サブフィルターの表示/非表示
  if (category === "pokemon") {
    elements.pokemonSubfilterArea.classList.remove("hidden");
  } else {
    elements.pokemonSubfilterArea.classList.add("hidden");
  }

  // 入力プレースホルダーの更新
  const placeholders = {
    pokemon: "ポケモンの名前を入力 (例: ピカチュウ / メガリザードンX)",
    yokai: "妖怪の名前を入力 (例: ジバニャン / コマさん / ブシニャン)",
    dq: "モンスターの名前を入力 (例: スライム / キングスライム / ゾーマ)",
    mario: "キャラクター名を入力 (例: マリオ / クッパ / ヨッシー)",
    all: "キャラクターの名前を入力 (カタカナ/ひらがなOK)"
  };
  elements.textAnswerInput.placeholder = placeholders[category] || placeholders["all"];

  // サジェストdatalistの更新
  loadCharacterNamesForDatalist(category);

  // 新しい問題を取得
  fetchNextQuestion();
}

function setupEventListeners() {
  // タブ切り替え
  document.querySelectorAll(".tab-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      sfx.playClick();
      document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
      document.querySelectorAll(".tab-content").forEach(c => c.classList.remove("active"));

      btn.classList.add("active");
      const targetTabId = btn.dataset.tab;
      document.getElementById(targetTabId).classList.add("active");

      if (targetTabId === "collection-tab") loadCollection();
      if (targetTabId === "ranking-tab") loadLeaderboardAndStats();
      if (targetTabId === "quiz-tab") {
        setTimeout(() => elements.textAnswerInput.focus(), 100);
      }
    });
  });

  // 4大ゲームモード切り替えボタン
  document.querySelectorAll(".game-mode-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      sfx.playClick();
      document.querySelectorAll(".game-mode-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      switchGameMode(btn.dataset.category);
    });
  });

  // ポケモン用フォームフィルター (通常 / メガ / キョダイ)
  document.querySelectorAll(".pill-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      sfx.playClick();
      document.querySelectorAll(".pill-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      state.formFilter = btn.dataset.form;
      fetchNextQuestion();
    });
  });

  // 図鑑カテゴリ切り替えボタン
  document.querySelectorAll(".cat-switch-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      sfx.playClick();
      document.querySelectorAll(".cat-switch-btn").forEach(b => b.classList.remove("active"));
      btn.classList.add("active");
      loadCollection(btn.dataset.cat);
    });
  });

  // 回答送信 (ボタン & Enterキー)
  elements.textSubmitBtn.addEventListener("click", () => submitAnswer());
  elements.textAnswerInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      submitAnswer();
    }
  });

  // 次の問題ボタン
  elements.nextQuestionBtn.addEventListener("click", () => {
    sfx.playClick();
    fetchNextQuestion();
  });

  // グローバルEnterキー (回答済みならEnterで次へ進む)
  window.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && state.answered && !elements.nextActionArea.classList.contains("hidden")) {
      if (elements.rankingModal.classList.contains("hidden")) {
        e.preventDefault();
        fetchNextQuestion();
      }
    }
  });

  // 成績登録モーダル
  elements.finishGameBtn.addEventListener("click", () => {
    sfx.playClick();
    elements.modalFinalScore.textContent = state.score.toLocaleString();
    elements.modalFinalCorrect.textContent = state.correctCount;
    elements.modalFinalStreak.textContent = state.maxStreak;
    elements.rankingModal.classList.remove("hidden");
  });

  // モーダル: 登録
  elements.submitScoreBtn.addEventListener("click", async () => {
    const name = elements.playerNameInput.value.trim() || "名無しプレイヤー";
    try {
      await fetch("/api/leaderboard", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          player_name: name,
          score: state.score,
          correct_count: state.correctCount,
          max_streak: state.maxStreak,
          category: state.category
        })
      });
      elements.rankingModal.classList.add("hidden");
      document.querySelector('[data-tab="ranking-tab"]').click();
      state.score = 0;
      state.streak = 0;
      state.maxStreak = 0;
      state.correctCount = 0;
      elements.scoreDisplay.textContent = "0";
      elements.streakDisplay.textContent = "0";
    } catch (err) {
      alert("ランキング登録に失敗しました");
    }
  });

  // モーダル: キャンセル
  elements.cancelScoreBtn.addEventListener("click", () => {
    elements.rankingModal.classList.add("hidden");
    state.score = 0;
    state.streak = 0;
    state.maxStreak = 0;
    state.correctCount = 0;
    elements.scoreDisplay.textContent = "0";
    elements.streakDisplay.textContent = "0";
    fetchNextQuestion();
  });

  // 音声トグル
  elements.soundToggleBtn.addEventListener("click", () => {
    sfx.enabled = !sfx.enabled;
    elements.soundToggleBtn.textContent = sfx.enabled ? "🔊 音声: ON" : "🔇 音声: OFF";
  });

  // SQLコンソール
  elements.sqlExecBtn.addEventListener("click", () => {
    const query = elements.sqlQueryInput.value.trim();
    if (query) executeSql(query);
  });

  document.querySelectorAll(".preset-btn").forEach(btn => {
    btn.addEventListener("click", () => {
      sfx.playClick();
      const sql = btn.dataset.sql;
      elements.sqlQueryInput.value = sql;
      executeSql(sql);
    });
  });

  setupHintHandlers();
}

function escapeHtml(str) {
  if (!str) return "";
  return str.replace(/[&<>"']/g, m => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
  }[m]));
}

// 起動
window.addEventListener("DOMContentLoaded", () => {
  setupEventListeners();
  loadCharacterNamesForDatalist("pokemon");
  fetchNextQuestion();
  updateCollectionNavCount();
});
