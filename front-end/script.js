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

    try {
        console.log("[DEBUG] Chiamata a:", BACKEND_URL);

        // Timeout di 2 minuti — la pipeline può essere lenta
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
            // Leggiamo il messaggio di errore dal server
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
        console.log("[DEBUG] Dati ricevuti dal backend:", data);

        // Se il backend risponde, mostriamo i dati
        renderDashboard(data);

    } catch (err) {
        console.error("[DEBUG] Errore:", err);
        if (err.name === 'AbortError') {
            alert("Timeout: l'analisi ha impiegato troppo tempo (>2 min). Riprova.");
        } else if (err.message === 'Failed to fetch' || err.message.includes('NetworkError')) {
            alert("Errore di rete: il server non è raggiungibile.\n\nAssicurati che il server Flask sia attivo su http://127.0.0.1:5001\n(avvia con: python app.py)");
        } else {
            alert("Errore durante l'analisi: " + err.message);
        }
    } finally {
        btn.disabled = false;
        loader.classList.add('hidden');
        label.innerText = "AVVIA SCANSIONE";
    }
}

function renderDashboard(data) {
    // Rendiamo visibile il container e scrolliamo verso i risultati
    const resultContainer = document.getElementById('resultContainer');
    resultContainer.classList.remove('hidden');

    // Scroll aggressivo ai risultati — setTimeout per dare tempo al browser di renderizzare
    setTimeout(() => {
        resultContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Fallback: forza scroll diretto
        const rect = resultContainer.getBoundingClientRect();
        const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
        window.scrollTo({ top: scrollTop + rect.top - 20, behavior: 'smooth' });
    }, 200);

    // Recuperiamo i dati con nomi flessibili (mapping)
    const score = data.affidabilita ?? data.score ?? 0;
    const verdetto = data.verdetto ?? data.label ?? "Analisi completata";
    const colore = data.colore ?? data.color ?? "#6366f1";
    const fonti = data.fonti ?? [];

    // Aggiorniamo il tachimetro
    const arco = document.getElementById('gaugeArcoProgress');
    const pathLength = 251.32;
    const offset = pathLength - (score * pathLength / 100);

    setTimeout(() => {
        arco.style.strokeDashoffset = offset;
        document.getElementById('percentualeTesto').innerText = score + "%";
        document.getElementById('percentualeTesto').style.color = colore;
        document.getElementById('verdettoTesto').innerText = verdetto;
        document.getElementById('verdettoTesto').style.color = colore;
    }, 100);

    // Render fonti
    const lista = document.getElementById('listaFonti');
    lista.innerHTML = `<p class="text-[9px] uppercase font-bold text-slate-500 tracking-[0.3em] mb-4">Fonti Rilevate</p>`;

    if (fonti.length === 0) {
        lista.innerHTML += `<p class="text-slate-600 text-[11px] italic">Nessuna fonte specifica trovata, verdetto basato su analisi cross-referencing.</p>`;
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
                <a href="${f.url}" target="_blank" class="text-indigo-400 text-[9px] font-black uppercase tracking-widest hover:text-white transition-colors">Vai alla fonte</a>
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
    label.innerText = "Avvia Scansione";
}

// Supporto tasto Enter
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