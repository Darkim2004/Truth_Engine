// Truth Shield Frontend v2.1 — served via Flask
const BACKEND_URL = "/elabora_completo";
const ARC_LENGTH = 251.32;
let currentMode = 'testo';

function safeHttpUrl(url) {
    try {
        const parsed = new URL(url);
        return ['http:', 'https:'].includes(parsed.protocol) ? parsed.href : '#';
    } catch (_) {
        return '#';
    }
}

function appendTextElement(parent, tagName, className, text) {
    const element = document.createElement(tagName);
    element.className = className;
    element.textContent = text;
    parent.appendChild(element);
    return element;
}

function showError(message) {
    const banner = document.getElementById('errorBanner');
    const text = document.getElementById('errorText');
    if (!banner || !text) return;

    text.textContent = message;
    banner.classList.remove('hidden');
}

function hideError() {
    const banner = document.getElementById('errorBanner');
    if (banner) banner.classList.add('hidden');
}

async function processData() {
    const inputField = currentMode === 'testo' ? 'testoInput' : 'urlInput';
    const inputVal = document.getElementById(inputField).value.trim();
    const btn = document.getElementById('inviaBtn');
    const label = document.getElementById('btnLabel');
    const loader = document.getElementById('loader');
    const container = document.getElementById('resultContainer');

    hideError();

    if (inputVal.length < 5) {
        showError("Inserisci un input valido.");
        return;
    }

    // UI Reset
    btn.disabled = true;
    loader.classList.remove('hidden');
    label.textContent = "AVVIO ANALISI...";
    container.classList.add('hidden');

    // --- LOGICA TEST CASE (Simulazione locale) ---
    if (inputVal.startsWith("test_")) {
        const scenario = inputVal.split("_")[1]; // es: 'vero' o 'falso'

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
            showError("Errore test case: file /test-case/" + scenario + ".json non trovato.");
            resetUI(btn, loader, label);
            return;
        }
    }

    // --- FLUSSO REALE (Chiamata al Backend Flask) ---
    let timeoutId;
    try {
        const controller = new AbortController();
        timeoutId = setTimeout(() => controller.abort(), 120000);

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
        console.error("Errore analisi:", err);
        if (err.name === 'AbortError') {
            showError("Timeout: l'analisi ha impiegato troppo tempo (>2 min).");
        } else {
            showError("Errore durante l'analisi: " + err.message);
        }
    } finally {
        if (timeoutId) clearTimeout(timeoutId);
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
    const pathLength = ARC_LENGTH;
    const offset = pathLength - (score * pathLength / 100);

    const percentages = data.dettagli?.percentages || { truth: 0, falsity: 0, uncertainty: 0 };

    setTimeout(() => {
        // Applichiamo il colore dinamico solo ai testi, lasciando il gradiente nativo all'arco
        arco.style.stroke = "url(#gaugeGradient)"; // Ripristina il gradiente per sicurezza
        arco.style.strokeDashoffset = offset;

        const pctTesto = document.getElementById('percentualeTesto');
        pctTesto.textContent = score + "%";
        pctTesto.style.color = gaugeColor;

        const verdTesto = document.getElementById('verdettoTesto');
        verdTesto.textContent = verdetto;
        verdTesto.style.color = gaugeColor;

        // Statistiche dettagliate a sinistra
        document.getElementById('txtTruth').textContent = (percentages.truth || 0) + "%";
        document.getElementById('barTruth').style.width = (percentages.truth || 0) + "%";

        document.getElementById('txtFalsity').textContent = (percentages.falsity || 0) + "%";
        document.getElementById('barFalsity').style.width = (percentages.falsity || 0) + "%";

        document.getElementById('txtUncertainty').textContent = (percentages.uncertainty || 0) + "%";
        document.getElementById('barUncertainty').style.width = (percentages.uncertainty || 0) + "%";
    }, 100);

    const lista = document.getElementById('listaFonti');
    lista.replaceChildren();
    appendTextElement(
        lista,
        'p',
        'text-[9px] uppercase font-bold text-slate-500 tracking-[0.3em] mb-4',
        'Fonti Rilevate'
    );

    const fonti = data.fonti || [];

    if (fonti.length === 0) {
        appendTextElement(
            lista,
            'p',
            'text-slate-600 text-[11px] italic',
            'Nessuna fonte specifica trovata.'
        );
    } else {
        fonti.forEach(f => {
            const card = document.createElement('div');
            card.className = "bg-[#070a13]/60 border border-slate-800 p-5 rounded-3xl mb-4 text-left hover:border-indigo-500/50 transition-all";

            const header = document.createElement('div');
            header.className = 'flex justify-between items-start mb-2 gap-3';
            appendTextElement(
                header,
                'h4',
                'text-white font-black text-xs uppercase italic tracking-wide',
                f.nome || 'Fonte'
            );
            appendTextElement(
                header,
                'span',
                'text-[8px] bg-slate-800 text-slate-400 px-2 py-1 rounded-full font-bold uppercase',
                'Live'
            );

            appendTextElement(
                card,
                'p',
                'text-slate-400 text-[11px] leading-relaxed mb-4',
                `"${f.snippet || 'Dettaglio non disponibile'}"`
            );

            const link = appendTextElement(
                card,
                'a',
                'text-indigo-400 text-[9px] font-black uppercase tracking-widest hover:text-white transition-colors',
                'Vai alla fonte'
            );
            link.href = safeHttpUrl(f.url || '#');
            link.target = '_blank';
            link.rel = 'noopener noreferrer';

            card.prepend(header);
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
    const isText = mode === 'testo';

    btnT.classList.toggle('tab-active', isText);
    btnT.classList.toggle('text-slate-500', !isText);
    btnU.classList.toggle('tab-active', !isText);
    btnU.classList.toggle('text-slate-500', isText);
    contT.classList.toggle('hidden', !isText);
    contU.classList.toggle('hidden', isText);
}

function resetUI(btn, loader, label) {
    btn.disabled = false;
    loader.classList.add('hidden');
    label.textContent = "AVVIA SCANSIONE";
}

document.addEventListener('keydown', (e) => {
    if (e.key !== 'Enter') return;

    const activeId = document.activeElement.id;
    const shouldSubmitText = activeId === 'testoInput' && (e.ctrlKey || e.metaKey);
    const shouldSubmitUrl = activeId === 'urlInput';

    if (shouldSubmitText || shouldSubmitUrl) {
        e.preventDefault();
        processData();
    }
});

function resetAll() {
    hideError();
    document.getElementById('testoInput').value = "";
    document.getElementById('urlInput').value = "";
    document.getElementById('resultContainer').classList.add('hidden');
    const arco = document.getElementById('gaugeArcoProgress');
    arco.style.strokeDashoffset = String(ARC_LENGTH);
    document.getElementById('testoInput').focus();
}
