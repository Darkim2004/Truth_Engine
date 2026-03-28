const BACKEND_URL = "http://127.0.0.1:5001/elabora_completo";
let currentMode = 'testo';

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

async function processData() {
    const inputField = currentMode === 'testo' ? 'testoInput' : 'urlInput';
    const inputVal = document.getElementById(inputField).value.trim();

    const btn = document.getElementById('inviaBtn');
    const label = document.getElementById('btnLabel');
    const loader = document.getElementById('loader');
    const container = document.getElementById('resultContainer');

    if (inputVal.length < 5) return alert("Inserisci un input valido.");

    // --- LOGICA TEST CASE ---
    if (inputVal.startsWith("test_")) {
        const scenario = inputVal.split("_")[1];
        btn.disabled = true;
        loader.classList.remove('hidden');
        try {
            const response = await fetch(`./test-case/${scenario}.json`);
            const data = await response.json();
            setTimeout(() => {
                renderDashboard(data);
                resetUI(btn, loader, label);
            }, 1000);
            return;
        } catch (e) {
            alert("Test non trovato.");
            resetUI(btn, loader, label);
            return;
        }
    }
    // --- FLUSSO REALE: Backend fa tutto (Groq claims → DuckDuckGo → Core Engine → verdetto) ---
    btn.disabled = true;
    loader.classList.remove('hidden');
    label.innerText = "ANALISI IN CORSO...";
    container.classList.add('hidden');

    try {
        // Chiamata unica al backend che fa: Groq claims → DuckDuckGo → fetch → score → verdetto
        console.log("[DEBUG] Invio richiesta al backend...", BACKEND_URL);
        console.log("[DEBUG] Payload:", { mode: currentMode, data: inputVal });

        const resBackend = await fetch(BACKEND_URL, {
            method: 'POST',
            mode: 'cors',
            headers: {
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            },
            body: JSON.stringify({ mode: currentMode, data: inputVal })
        });

        console.log("[DEBUG] Risposta ricevuta. Status:", resBackend.status);
        const finalData = await resBackend.json();
        console.log("[DEBUG] Dati ricevuti:", finalData);

        if (!resBackend.ok) throw new Error(finalData.error || "Errore backend");

        renderDashboard(finalData);

    } catch (err) {
        console.error("[DEBUG] ❌ ERRORE:", err);
        alert("Errore durante l'analisi: " + err.message);
    } finally {
        resetUI(btn, loader, label);
    }
}

function renderDashboard(data) {
    document.getElementById('resultContainer').classList.remove('hidden');
    const arco = document.getElementById('gaugeArcoProgress');
    const percentualeTesto = document.getElementById('percentualeTesto');
    const verdettoTesto = document.getElementById('verdettoTesto');

    const pathLength = 251.32;
    const offset = pathLength - (data.affidabilita * pathLength / 100);

    // Applichiamo i cambiamenti con un piccolo delay per l'effetto wow
    setTimeout(() => {
        // --- QUI SISTEMIAMO IL COLORE ---
        arco.style.stroke = data.colore; // Imposta il colore (es. #10b981)
        arco.style.strokeDashoffset = offset; // Muove la lancetta

        percentualeTesto.innerText = data.affidabilita + "%";
        percentualeTesto.style.color = data.colore;

        verdettoTesto.innerText = data.verdetto;
        verdettoTesto.style.color = data.colore;
    }, 150);
    const lista = document.getElementById('listaFonti');
    lista.innerHTML = `<p class="text-[9px] uppercase font-bold text-slate-500 tracking-[0.3em] mb-4">Fonti Analizzate</p>`;

    data.fonti.forEach(f => {
        const card = document.createElement('div');
        card.className = "bg-[#070a13]/60 border border-slate-800 p-5 rounded-3xl mb-4 text-left hover:border-indigo-500/50 transition-all group";

        card.innerHTML = `
            <div class="flex justify-between items-start mb-2">
                <h4 class="text-white font-black text-xs uppercase italic tracking-wide">${f.nome}</h4>
                <span class="text-[8px] bg-slate-800 text-slate-400 px-2 py-1 rounded-full font-bold uppercase">Verificato</span>
            </div>
            <p class="text-slate-400 text-[11px] leading-relaxed mb-4">"${f.snippet}"</p>
            ${f.url ? `
                <a href="${f.url}" target="_blank" class="inline-flex items-center gap-2 text-indigo-400 text-[9px] font-black uppercase tracking-widest hover:text-white transition-colors">
                    Vai alla fonte 
                    <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"></path></svg>
                </a>
            ` : ''}
        `;
        lista.appendChild(card);
    });
}

function resetUI(btn, loader, label) {
    btn.disabled = false;
    loader.classList.add('hidden');
    label.innerText = "Avvia Scansione";
}

// Invio con tasto Enter
document.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey && (document.activeElement.id === 'testoInput' || document.activeElement.id === 'urlInput')) {
        e.preventDefault();
        processData();
    }
});

function resetAll() {
    // 1. Pulisce gli input
    document.getElementById('testoInput').value = "";
    document.getElementById('urlInput').value = "";

    // 2. Nasconde i risultati
    document.getElementById('resultContainer').classList.add('hidden');

    // 3. Resetta il tachimetro (opzionale per pulizia visiva)
    const arco = document.getElementById('gaugeArcoProgress');
    arco.style.strokeDashoffset = "251.32";

    // 4. Riporta l'URL alla normalità (senza parametri ?text=...)
    const cleanUrl = window.location.protocol + "//" + window.location.host + window.location.pathname;
    window.history.pushState({ path: cleanUrl }, '', cleanUrl);

    // 5. Riporta il focus sul campo testo
    document.getElementById('testoInput').focus();
}

