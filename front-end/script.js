// Truth Shield Frontend v2.1 — served via Flask
const BACKEND_URL = "/elabora_completo";
let currentMode = 'testo';

async function processData() {
    const inputField = currentMode === 'testo' ? 'testoInput' : 'urlInput';
    const inputVal = document.getElementById(inputField).value.trim();
    const btn = document.getElementById('inviaBtn');
    const label = document.getElementById('btnLabel');
    const loader = document.getElementById('loader');
    const container = document.getElementById('resultContainer');

    if (inputVal.length < 5) return alert("Inserisci un input valido.");

    // UI Reset
    btn.disabled = true;
    loader.classList.remove('hidden');
    label.innerText = "AVVIO ANALISI...";
    container.classList.add('hidden');

    // --- LOGICA TEST CASE (Simulazione locale) ---
    if (inputVal.startsWith("test_")) {
        const scenario = inputVal.split("_")[1]; // es: 'vero' o 'falso'
        console.log("[DEBUG] Modalità TEST attivata:", scenario);

        try {
            // Cerca i file nella cartella test-case (es: test-case/vero.json)
            const response = await fetch(`./test-case/${scenario}.json`);
            if (!response.ok) throw new Error("File di test non trovato");

            const data = await response.json();

            // Simula un'attesa di 1.5 secondi per dare realismo
            setTimeout(() => {
                renderDashboard(data);
                resetUI(btn, loader, label);
            }, 1500);
            return; // Esci dalla funzione, non chiamare il backend reale
        } catch (e) {
            alert("Errore Test Case: Assicurati che esista il file /test-case/" + scenario + ".json");
            resetUI(btn, loader, label);
            return;
        }
    }

    // --- FLUSSO REALE (Chiamata al Backend Flask) ---
    try {
        console.log("[DEBUG] Chiamata reale a:", BACKEND_URL);

        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 120000);

        const response = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ mode: currentMode, data: inputVal }),
            signal: controller.signal
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            let serverMsg = "Errore sconosciuto dal server.";
            try {
                const errData = await response.json();
                serverMsg = errData.error || serverMsg;
            } catch (_) {
                serverMsg = `HTTP ${response.status}: ${response.statusText}`;
            }
            throw new Error(serverMsg);
        }

        const data = await response.json();
        renderDashboard(data);

    } catch (err) {
        console.error("[DEBUG] Errore:", err);
        if (err.name === 'AbortError') {
            alert("Timeout: l'analisi ha impiegato troppo tempo (>2 min).");
        } else {
            alert("Errore durante l'analisi: " + err.message);
        }
    } finally {
        resetUI(btn, loader, label);
    }
}

function renderDashboard(data) {
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.classList.remove('hidden');

    // 1. Recuperiamo lo score (es. 85)
    const score = data.affidabilita ?? data.score ?? 0;
    const verdetto = data.verdetto ?? data.label ?? "Analisi completata";

    // 2. LOGICA COLORE DINAMICO (Qui succede la magia)
    let gaugeColor = "#ef4444"; // Rosso (Default)
    if (score >= 75) {
        gaugeColor = "#10b981"; // Verde (Affidabile)
    } else if (score >= 40) {
        gaugeColor = "#f59e0b"; // Giallo/Arancio (Dubbio)
    }

    // 3. Applichiamo il colore e l'animazione
    const arco = document.getElementById('gaugeArcoProgress');
    const pathLength = 251.32;
    const offset = pathLength - (score * pathLength / 100);

    const percentages = data.dettagli?.percentages || { truth: 0, falsity: 0, uncertainty: 0 };

    setTimeout(() => {
        // Applichiamo il colore dinamico solo ai testi, lasciando il gradiente nativo all'arco
        arco.style.stroke = "url(#gaugeGradient)"; // Ripristina il gradiente per sicurezza
        arco.style.strokeDashoffset = offset;

        const pctTesto = document.getElementById('percentualeTesto');
        pctTesto.innerText = score + "%";
        pctTesto.style.color = gaugeColor;

        const verdTesto = document.getElementById('verdettoTesto');
        verdTesto.innerText = verdetto;
        verdTesto.style.color = gaugeColor;

        // Statistiche dettagliate a sinistra
        document.getElementById('txtTruth').innerText = (percentages.truth || 0) + "%";
        document.getElementById('barTruth').style.width = (percentages.truth || 0) + "%";

        document.getElementById('txtFalsity').innerText = (percentages.falsity || 0) + "%";
        document.getElementById('barFalsity').style.width = (percentages.falsity || 0) + "%";

        document.getElementById('txtUncertainty').innerText = (percentages.uncertainty || 0) + "%";
        document.getElementById('barUncertainty').style.width = (percentages.uncertainty || 0) + "%";
    }, 100);

    const lista = document.getElementById('listaFonti');
    lista.innerHTML = `<p class="text-[9px] uppercase font-bold text-slate-500 tracking-[0.3em] mb-4">Fonti Rilevate</p>`;

    const fonti = data.fonti || [];

    if (fonti.length === 0) {
        lista.innerHTML += `<p class="text-slate-600 text-[11px] italic">Nessuna fonte specifica trovata.</p>`;
    } else {
        fonti.forEach(f => {
            const card = document.createElement('div');
            card.className = "bg-[#070a13]/60 border border-slate-800 p-5 rounded-3xl mb-4 text-left hover:border-indigo-500/50 transition-all";
            card.innerHTML = `
                <div class="flex justify-between items-start mb-2">
                    <h4 class="text-white font-black text-xs uppercase italic tracking-wide">${f.nome || 'Fonte'}</h4>
                    <span class="text-[8px] bg-slate-800 text-slate-400 px-2 py-1 rounded-full font-bold uppercase">Live</span>
                </div>
                <p class="text-slate-400 text-[11px] leading-relaxed mb-4">"${f.snippet || 'Dettaglio non disponibile'}"</p>
                <a href="${f.url || '#'}" target="_blank" class="text-indigo-400 text-[9px] font-black uppercase tracking-widest hover:text-white transition-colors">Vai alla fonte</a>
            `;
            lista.appendChild(card);
        });
    }
}

function switchMode(mode) {
    if (currentMode === mode) return;
    currentMode = mode;
    const btnT = document.getElementById('tabTesto');
    const btnU = document.getElementById('tabUrl');
    const contT = document.getElementById('containerTesto');
    const contU = document.getElementById('containerUrl');

    if (mode === 'testo') {
        btnT.classList.add('tab-active');
        btnU.classList.remove('tab-active');
        btnU.classList.add('text-slate-500');
        contT.classList.remove('hidden');
        contU.classList.add('hidden');
    } else {
        btnU.classList.add('tab-active');
        btnU.classList.remove('text-slate-500');
        btnT.classList.remove('tab-active');
        btnT.classList.add('text-slate-500');
        contU.classList.remove('hidden');
        contT.classList.add('hidden');
    }
}

function resetUI(btn, loader, label) {
    btn.disabled = false;
    loader.classList.add('hidden');
    label.innerText = "AVVIA SCANSIONE";
}

document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        const activeId = document.activeElement.id;
        if (activeId === 'testoInput' || activeId === 'urlInput') {
            e.preventDefault();
            processData();
        }
    }
});

function resetAll() {
    document.getElementById('testoInput').value = "";
    document.getElementById('urlInput').value = "";
    document.getElementById('resultContainer').classList.add('hidden');
    const arco = document.getElementById('gaugeArcoProgress');
    arco.style.strokeDashoffset = "251.32";
    const cleanUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
    window.history.pushState({ path: cleanUrl }, '', cleanUrl);
    document.getElementById('testoInput').focus();
}