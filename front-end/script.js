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

    // --- MODALITÀ TEST ---
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
            console.error(e);
            alert("Errore file test.");
            resetUI(btn, loader, label);
            return;
        }
    }

    // --- FLUSSO REALE ---
    try {
        const resAI = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CONFIG.API_KEY}`
            },
            body: JSON.stringify({
                model: CONFIG.MODEL,
                messages: [{ role: "user", content: `Analizza e restituisci SOLO JSON con claim da: ${input}` }],
                response_format: { type: "json_object" }
            })
        });

        const dataAI = await resAI.json();
        const extractedClaims = JSON.parse(dataAI.choices[0].message.content);

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
        alert("Errore di comunicazione con il server.");
    } finally {
        resetUI(btn, loader, label);
    }
}

function renderDashboard(data) {
    const container = document.getElementById('resultContainer');
    const arcoProgress = document.getElementById('gaugeArcoProgress');
    const percentualeTesto = document.getElementById('percentualeTesto');
    const verdettoTesto = document.getElementById('verdettoTesto');
    const lista = document.getElementById('listaFonti');

    container.classList.remove('hidden');

    // Animazione Arco SVG
    const pathLength = 251.32;
    const targetOffset = pathLength - (data.affidabilita * pathLength / 100);

    setTimeout(() => {
        arcoProgress.style.strokeDashoffset = targetOffset;
        percentualeTesto.innerText = `${data.affidabilita}%`;
        percentualeTesto.style.color = data.colore;
        percentualeTesto.style.opacity = "1";
        percentualeTesto.classList.add('number-ready');
        verdettoTesto.innerText = data.verdetto;
        verdettoTesto.style.color = data.colore;
    }, 150);

    // Fonti
    lista.innerHTML = '<p class="text-[10px] uppercase font-bold text-slate-500 tracking-[0.2em] mb-4">Fonti Verificate</p>';
    data.fonti.forEach(f => {
        const card = document.createElement('div');
        card.className = "bg-[#070a13]/60 border border-slate-700 p-5 rounded-[1.5rem] shadow-lg text-left";
        card.innerHTML = `
            <div class="flex justify-between items-center mb-3">
                <span class="text-white font-bold text-xs uppercase italic">${f.nome}</span>
                <span class="text-[8px] bg-white/10 px-2 py-1 rounded text-slate-400 font-bold uppercase tracking-widest">Verified</span>
            </div>
            <p class="text-slate-400 text-[11px] mb-4 italic italic">"${f.snippet}"</p>
            <a href="${f.url}" target="_blank" class="text-rose-500 text-[10px] font-black uppercase tracking-widest">Consulta Fonte →</a>
        `;
        lista.appendChild(card);
    });
}

function resetUI(btn, loader, label) {
    btn.disabled = false;
    loader.classList.add('hidden');
    label.innerText = "AVVIA SCANSIONE";
}

// Gestione tasto Invio
document.getElementById('testoInput').addEventListener('keydown', function (event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        processData();
    }
});