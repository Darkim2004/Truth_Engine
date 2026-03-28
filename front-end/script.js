// Endpoint del Backend (Flask)
const BACKEND_URL = "http://127.0.0.1:5000/elabora";

async function processData() {
    const input = document.getElementById('testoInput').value.trim();
    const btn = document.getElementById('inviaBtn');
    const label = document.getElementById('btnLabel');
    const loader = document.getElementById('loader');
    const container = document.getElementById('resultContainer');

    if (input.length < 5) return alert("Inserisci un testo valido.");

    // UI Start
    btn.disabled = true;
    loader.classList.remove('hidden');
    label.innerText = "ANALISI IN CORSO...";
    container.classList.add('hidden');

    // --- MODALITÀ TEST (front-end/test-case/) ---
    if (input.startsWith("test_")) {
        try {
            const scenario = input.split("_")[1];

            const response = await fetch(`./test-case/${scenario}.json`);

            if (!response.ok) throw new Error("File test non trovato");

            const data = await response.json();

            setTimeout(() => {
                renderDashboard(data);
                resetUI(btn, loader, label);
            }, 1200);
            return;
        } catch (e) {
            console.error("Test Error:", e);
            alert("Errore: Verifica che il file sia in front-end/test-case/" + input.split("_")[1] + ".json");
            resetUI(btn, loader, label);
            return;
        }
    }

    // --- FLUSSO REALE ---
    try {
        // 1. Analisi AI (Groq)
        const resAI = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CONFIG.API_KEY}`
            },
            body: JSON.stringify({
                model: CONFIG.MODEL,
                messages: [{ role: "user", content: `Analizza claim da: ${input}` }],
                response_format: { type: "json_object" }
            })
        });

        const dataAI = await resAI.json();
        const extractedClaims = JSON.parse(dataAI.choices[0].message.content);

        // 2. Invio al Backend
        const resBackend = await fetch(BACKEND_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(extractedClaims)
        });

        if (!resBackend.ok) throw new Error("Backend Offline");

        const finalResult = await resBackend.json();
        renderDashboard(finalResult);

    } catch (err) {
        console.error(err);
        alert("Errore di sistema o Backend non raggiungibile.");
    } finally {
        resetUI(btn, loader, label);
    }
}

function renderDashboard(data) {
    const container = document.getElementById('resultContainer');
    const arco = document.getElementById('gaugeArco');
    const percentuale = document.getElementById('percentualeTesto');
    const verdetto = document.getElementById('verdettoTesto');
    const lista = document.getElementById('listaFonti');

    container.classList.remove('hidden');

    // Animazione Gauge
    const gradi = (data.affidabilita * 1.8) - 90;

    setTimeout(() => {
        arco.style.transform = `rotate(${gradi}deg)`;
        arco.style.borderColor = data.colore;
        percentuale.innerText = `${data.affidabilita}%`;
        percentuale.style.color = data.colore;
        verdetto.innerText = data.verdetto;
        verdetto.style.color = data.colore;
    }, 150);

    // Fonti
    lista.innerHTML = '<p class="text-[10px] uppercase font-bold text-slate-500 tracking-[0.2em] mb-4">Fonti Verificate</p>';
    data.fonti.forEach(f => {
        const card = document.createElement('div');
        card.className = "bg-[#070a13]/60 border border-slate-700 p-5 rounded-[1.5rem] shadow-lg hover:border-slate-500 transition-all group text-left";
        card.innerHTML = `
            <div class="flex justify-between items-center mb-3">
                <span class="text-white font-bold text-xs uppercase italic">${f.nome}</span>
                <span class="text-[8px] bg-white/10 px-2 py-1 rounded text-slate-400 font-bold tracking-widest uppercase">Verified</span>
            </div>
            <p class="text-slate-400 text-[11px] mb-4 italic leading-relaxed">"${f.snippet}"</p>
            <a href="${f.url}" target="_blank" class="text-rose-500 text-[10px] font-black uppercase tracking-widest flex items-center gap-1 group-hover:gap-2 transition-all">
                Consulta Fonte →
            </a>
        `;
        lista.appendChild(card);
    });
}

function resetUI(btn, loader, label) {
    btn.disabled = false;
    loader.classList.add('hidden');
    label.innerText = "AVVIA SCANSIONE";
}


function renderDashboard(data) {
    const arcoProgress = document.getElementById('gaugeArcoProgress');
    const percentualeTesto = document.getElementById('percentualeTesto');
    const container = document.getElementById('resultContainer');

    container.classList.remove('hidden');

    // --- IL TRUCCO DELLA PRECISIONE ---
    // Chiediamo al browser la lunghezza esatta del tracciato disegnato
    const pathLength = arcoProgress.getTotalLength();

    // Reset: lo facciamo sparire (offset = lunghezza totale)
    arcoProgress.style.strokeDasharray = pathLength;
    arcoProgress.style.strokeDashoffset = pathLength;

    // Calcolo millimetrico: 
    // Se affidabilità è 12%, l'offset deve essere il 88% della lunghezza totale
    const targetOffset = pathLength - (data.affidabilita * pathLength / 100);

    setTimeout(() => {
        // Facciamo partire l'animazione
        arcoProgress.style.strokeDashoffset = targetOffset;

        // Numero e colori
        percentualeTesto.innerText = data.affidabilita + "%";
        percentualeTesto.style.color = data.colore;
        percentualeTesto.classList.add('number-ready');

        document.getElementById('verdettoTesto').innerText = data.verdetto;
        document.getElementById('verdettoTesto').style.color = data.colore;
    }, 150);
}

// Gestione del tasto INVIO nella textarea
document.getElementById('testoInput').addEventListener('keydown', function (event) {
    // Controlla se è stato premuto Invio (keyCode 13)
    // Se vuoi permettere l'invio a capo con SHIFT + INVIO, aggiungi !event.shiftKey
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault(); // Impedisce di andare a capo nella textarea
        processData(); // Lancia la funzione principale
    }
});

const maxDash = 251.32;
// Se data.affidabilita è 12, l'offset deve essere il 12% del percorso rimosso dal totale
const offset = maxDash - (data.affidabilita * maxDash / 100);
arcoProgress.style.strokeDashoffset = offset;