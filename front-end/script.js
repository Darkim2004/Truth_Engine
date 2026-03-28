async function processData() {
    const inputText = document.getElementById('inputMain').value;
    const btn = document.getElementById('btnAnalyze');
    const label = document.getElementById('btnLabel');
    const loader = document.getElementById('loader');

    if (inputText.length < 10) return alert("Testo troppo corto per essere verificato!");

    // UI Start
    btn.disabled = true;
    loader.classList.remove('hidden');
    label.innerText = "ELABORAZIONE...";

    // Prompt ottimizzato per il Backend di Andrea
    const prompt = `Analizza questo testo: "${inputText}". 
    Rileva la lingua. Estrai i 3 claim principali. Genera query di ricerca Google nella stessa lingua del testo.
    Restituisci SOLO un JSON con questa struttura:
    {
      "metadata": { "language": "sigla", "timestamp": "${new Date().toISOString()}" },
      "original_content": { "full_text": "${inputText.replace(/"/g, '\\"')}" },
      "analysis": [
        { "id": 1, "claim": "testo", "search_query": "query per google" }
      ]
    }`;

    try {
        // Chiamata a Groq (Gratis e veloce)
        const response = await fetch("https://api.groq.com/openai/v1/chat/completions", {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${CONFIG.API_KEY}`
            },
            body: JSON.stringify({
                model: CONFIG.MODEL,
                messages: [
                    { role: "system", content: "Sei un generatore di JSON puro per un backend di fact-checking." },
                    { role: "user", content: prompt }
                ],
                response_format: { type: "json_object" }
            })
        });

        const data = await response.json();
        const finalContent = data.choices[0].message.content;

        // --- MAGIA: CREAZIONE DEL FILE input.json ---
        const blob = new Blob([finalContent], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');

        // Andrea vuole il file chiamato esattamente "input.json"
        a.href = url;
        a.download = "input.json";

        document.body.appendChild(a);
        a.click(); // Scarica il file automaticamente
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        label.innerText = "DATI INVIATI!";
        alert("File input.json generato correttamente per il backend!");

    } catch (error) {
        console.error("ERRORE:", error);
        alert("Errore nella generazione dei dati: " + error.message);
    } finally {
        btn.disabled = false;
        loader.classList.add('hidden');
        label.innerText = "VERIFICA L'INFORMAZIONE";
    }
}