// Component 1 JavaScript – Audio Upload, Transcription, and Extraction

document.addEventListener('DOMContentLoaded', function () {
    const uploadArea = document.getElementById('audioUploadArea');
    const fileInput = document.getElementById('audioFileInput');
    const processingSection = document.getElementById('processingSection');
    const resultsSection = document.getElementById('resultsSection');
    const progressFill = document.getElementById('extractionProgressFill');
    const progressPercent = document.getElementById('extractionProgressPercent');
    const currentStage = document.getElementById('extractionCurrentStage');

    if (!uploadArea || !fileInput) return;

    uploadArea.addEventListener('click', () => fileInput.click());

    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.background = 'rgba(107, 68, 35, 0.1)';
    });

    uploadArea.addEventListener('dragleave', () => {
        uploadArea.style.background = '';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.background = '';
        if (e.dataTransfer.files.length) handleAudioFile(e.dataTransfer.files[0]);
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length) handleAudioFile(e.target.files[0]);
    });

    async function handleAudioFile(file) {
        if (!file.type.startsWith('audio/')) {
            alert('Please upload an audio file.');
            return;
        }

        // Show processing UI
        uploadArea.style.display = 'none';
        processingSection.style.display = 'block';
        resultsSection.style.display = 'none';

        try {
            // Step 1: Transcribe
            updateProgress(20, 'Transcribing audio...');
            const transcriptData = await transcribeAudio(file);

            if (!transcriptData || !transcriptData.transcript) {
                throw new Error('Transcription failed or returned empty result.');
            }

            const englishText = transcriptData.transcript;
            const originalText = transcriptData.original_transcript || englishText;
            const lang = transcriptData.detected_language || 'en';

            // Step 2: Extract Legal Data
            updateProgress(60, 'Extracting legal resources...');
            const extractData = await extractLegalResources(englishText, originalText, lang);

            // Step 3: Show Results
            updateProgress(100, 'Completed');
            displayResults(transcriptData, extractData);

            processingSection.style.display = 'none';
            resultsSection.style.display = 'block';

        } catch (error) {
            console.error('Processing error:', error);
            alert('Error processing audio: ' + error.message);
            uploadArea.style.display = 'block';
            processingSection.style.display = 'none';
        }
    }

    function updateProgress(percent, stage) {
        progressFill.style.width = percent + '%';
        progressPercent.textContent = percent + '%';
        currentStage.textContent = stage;
    }

    async function transcribeAudio(file) {
        const formData = new FormData();
        formData.append('audio', file);
        formData.append('language', 'auto');

        const response = await fetch(window.API_TRANSCRIBE, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) throw new Error('Transcription API error');
        return await response.json();
    }

    async function extractLegalResources(englishText, originalText, lang) {
        const response = await fetch(window.API_EXTRACT, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                english_transcript: englishText,
                original_transcript: originalText,
                detected_lang: lang
            })
        });

        if (!response.ok) throw new Error('Extraction API error');
        const result = await response.json();
        return result.data;
    }

    function displayResults(transcript, extract) {
        // Transcript
        document.getElementById('caseTranscript').textContent = transcript.transcript;

        // Legal Elements Grid
        const grid = document.getElementById('legalElementsGrid');
        grid.innerHTML = '';

        // Check if we have structured_data
        const data = extract.structured_data || {};
        const precedents = data.binding_precedents || [];
        const procedures = data.procedural_resources || [];

        const elements = [
            { label: 'Total Resources', value: extract.summary?.split(' ')[1] || '0' },
            { label: 'Binding Precedents', value: precedents.length },
            { label: 'Procedural Rules', value: procedures.length },
            { label: 'Defense Points', value: data.defense_resources?.length || 0 }
        ];

        elements.forEach(el => {
            const item = document.createElement('div');
            item.className = 'info-item';
            item.innerHTML = `
        <span class="info-label">${el.label}</span>
        <span class="info-value">${el.value}</span>
      `;
            grid.appendChild(item);
        });

        // Actus Reus & Mens Rea (From procedure or landmark summary if available)
        document.getElementById('actusReusValue').textContent = "Refer to Procedural resources for Actus Reus requirements.";
        document.getElementById('mensReaValue').textContent = "Mental intent requirements are linked to the specific Penal Code sections in Defense resources.";

        // Punishment
        document.getElementById('punishmentValue').textContent = procedures.length > 0 ? procedures[0].title : 'See Statutory Analysis';

        // Precedents
        const precedentsList = document.getElementById('precedentsList');
        precedentsList.innerHTML = '<h5>Relevant Precedents</h5>';

        if (precedents.length > 0) {
            precedents.forEach(p => {
                const pEl = document.createElement('div');
                pEl.className = 'similar-case-item';
                pEl.style.marginBottom = '10px';
                pEl.innerHTML = `
          <div class="case-details">
            <h4>${p.title}</h4>
            <p>${p.excerpt?.substring(0, 200)}...</p>
            <small style="color: var(--primary);">Reference: ${p.section || 'N/A'}</small>
          </div>
        `;
                precedentsList.appendChild(pEl);
            });
        } else {
            precedentsList.innerHTML += '<p>No specific precedents indexed for this cluster.</p>';
        }
    }
});
