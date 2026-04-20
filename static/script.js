document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const promptInput = document.getElementById('prompt-input');
    const resultSection = document.getElementById('result-section');
    const generationWarning = document.getElementById('generation-warning');
    const briefText = document.getElementById('brief-text');
    const codeSection = document.getElementById('code-section');
    const codeText = document.getElementById('code-text');
    const renderCodeBtn = document.getElementById('render-code-btn');
    const revisionRequest = document.getElementById('revision-request');
    const reviseBtn = document.getElementById('revise-btn');
    const regenerateBtn = document.getElementById('regenerate-btn');
    const downloadMidiBtn = document.getElementById('download-midi');
    const audioPlayer = document.getElementById('audio-player');
    const audioLoadingText = document.getElementById('audio-loading-text');
    const configGenre = document.getElementById('config-genre');
    const configMood = document.getElementById('config-mood');
    const configTempo = document.getElementById('config-tempo');
    const configKey = document.getElementById('config-key');
    const configStructure = document.getElementById('config-structure');
    const configInstruments = document.getElementById('config-instruments');
    const configNotes = document.getElementById('config-notes');

    const apiBase = ''; // Use relative path for local server
    const generationState = {
        prompt: '',
        config: {},
        brief: '',
        code: ''
    };

    const examples = {
        dreamy_lofi: "A chill lo-fi hip hop beat at 80 BPM. Soft, jazzy electric piano seventh chords playing a relaxed progression, layered over a slow, simple drum beat.",
        upbeat_synthwave: "An upbeat, driving 80s synthwave track at 130 BPM. It features a fast, pulsing 16th-note synth bassline, a catchy bright synthesizer melody, and a driving four-on-the-floor drum beat.",
        cinematic_orchestral: "A slow, grandiose cinematic string progression at 60 BPM. Long, sustained minor and major chords swelling out slowly to create a sense of scale and heroism.",
        energetic_punk: "A fast and aggressive pop punk rock loop at 160 BPM. Distorted electric guitar power chords playing eighth notes, over loud rock drum patterns.",
        classical_piano: "A delicate classical piece for solo acoustic grand piano at 100 BPM. It features fast, flowing A minor arpeggios that rise and fall gracefully.",
        heavy_dubstep: "A heavy, booming dubstep track at 140 BPM. It features a slow, half-time beat with a massive snare drum, and aggressive, modulating electronic synthesizer growls.",
        shuffle_blues: "A 12-bar blues classic in E major at 110 BPM. Shuffle feel with an electric guitar playing the rhythmic shuffle riff, a piano adding turnarounds, and straight blues drums.",
    };

    const exampleSelect = document.getElementById('example-select');
    if (exampleSelect) {
        exampleSelect.addEventListener('change', (e) => {
            const key = e.target.value;
            if (key && examples[key]) {
                promptInput.value = examples[key];
            }
        });
    }

    async function loadTags() {
        try {
            const response = await fetch(`${apiBase}/tags`);
            if (!response.ok) return;
            const tags = await response.json();

            if (tags.genre) {
                tags.genre.forEach(g => {
                    const opt = document.createElement('option');
                    opt.value = g;
                    opt.textContent = g;
                    configGenre.appendChild(opt);
                });
            }
            if (tags.mood) {
                tags.mood.forEach(m => {
                    const opt = document.createElement('option');
                    opt.value = m;
                    opt.textContent = m;
                    configMood.appendChild(opt);
                });
            }
            if (tags.structure) {
                tags.structure.forEach(s => {
                    const opt = document.createElement('option');
                    opt.value = s;
                    opt.textContent = s;
                    configStructure.appendChild(opt);
                });
            }
            if (tags.key || tags.scale) {
                const keysAndScales = [];
                if (tags.key) tags.key.forEach(k => keysAndScales.push((k.key || k) + (k.description ? ` - ${k.description.split('.')[0]}` : '')));
                if (tags.scale) tags.scale.forEach(s => keysAndScales.push((s.scale || s) + (s.description ? ` - ${s.description.split('.')[0]}` : '')));
                keysAndScales.forEach(item => {
                    const opt = document.createElement('option');
                    // Use just the key name for the value, not the description, to keep prompt concise
                    opt.value = item.split(' - ')[0];
                    opt.textContent = item;
                    configKey.appendChild(opt);
                });
            }
            
            if (tags.instruments) {
                tags.instruments.forEach(inst => {
                    const group = document.createElement('optgroup');
                    const instName = inst.instrument || inst;
                    group.label = instName;
                    
                    if (inst.textures && Array.isArray(inst.textures)) {
                        inst.textures.forEach(texture => {
                            const opt = document.createElement('option');
                            const val = `${texture} ${instName}`;
                            opt.value = val;
                            opt.textContent = val;
                            group.appendChild(opt);
                        });
                    } else {
                        const opt = document.createElement('option');
                        opt.value = instName;
                        opt.textContent = instName;
                        group.appendChild(opt);
                    }
                    configInstruments.appendChild(group);
                });
            }
        } catch (e) {
            console.error('Error loading tags:', e);
        }
    }

    loadTags();

    function collectGenerationConfig() {
        // Collect array of selected options for instruments
        const selectedInstruments = Array.from(configInstruments.selectedOptions).map(opt => opt.value);

        return {
            genre: configGenre.value,
            mood: configMood.value,
            tempo: configTempo.value.trim(),
            key: configKey.value,
            structure: configStructure.value,
            instruments: selectedInstruments.join(', '),
            notes: configNotes.value.trim()
        };
    }

    function renderBriefMarkdown(markdown) {
        if (window.marked && typeof window.marked.parse === 'function') {
            const renderedHtml = window.marked.parse(markdown);

            if (window.DOMPurify && typeof window.DOMPurify.sanitize === 'function') {
                briefText.innerHTML = window.DOMPurify.sanitize(renderedHtml);
                return;
            }

            briefText.innerHTML = renderedHtml;
            return;
        }

        briefText.textContent = markdown;
    }
    
    // We remove the target code returned in the Musical Brief and just show the natural language description there..
    function extractBriefDescription(briefMarkdown) {
        const lines = briefMarkdown.split('\n');
        const descriptionLines = [];
        for (const line of lines) {
            if (line.trim().startsWith('```')) break;
            descriptionLines.push(line);
        }
        return descriptionLines.join('\n').trim();
    }

    function setActionButtonsDisabled(disabled) {
        [generateBtn, renderCodeBtn, reviseBtn, regenerateBtn].forEach(btn => {
            if (btn) btn.disabled = disabled;
        });
    }

    function showError(message) {
        generationWarning.textContent = message;
        generationWarning.classList.remove('hidden');
    }

    function clearWarning() {
        generationWarning.textContent = '';
        generationWarning.classList.add('hidden');
    }

    function updateOutputState(data, fallbackBrief = '') {
        generationState.brief = data.brief || fallbackBrief || generationState.brief;
        generationState.code = data.code || codeText.value;
        renderBriefMarkdown(extractBriefDescription(generationState.brief));
        codeText.value = generationState.code;

        const midiUrl = `${apiBase}/download/midi?t=${Date.now()}`;
        downloadMidiBtn.href = midiUrl;

        resultSection.classList.remove('hidden');
        codeSection.classList.remove('hidden');
        resultSection.scrollIntoView({ behavior: 'smooth' });
    }

    async function refreshAudioPreview() {
        audioPlayer.style.display = 'none';
        audioLoadingText.style.display = 'block';
        audioLoadingText.textContent = 'Rendering studio audio on backend. Please wait (~15 seconds)...';

        try {
            const mp3Url = `${apiBase}/download/audio?format=mp3&t=${Date.now()}`;
            const response = await fetch(mp3Url);
            if (!response.ok) throw new Error('Audio backend render failed');

            const blob = await response.blob();
            audioPlayer.src = window.URL.createObjectURL(blob);
            audioLoadingText.style.display = 'none';
            audioPlayer.style.display = 'block';
        } catch (err) {
            console.error(err);
            audioLoadingText.textContent = 'Failed to render high-quality audio.';
        }
    }

    async function performGenerationRequest(url, payload, options = {}) {
        const { loadingText, keepVisibleBrief = '' } = options;

        if (loadingText) {
            audioPlayer.style.display = 'none';
            audioLoadingText.style.display = 'block';
            audioLoadingText.textContent = loadingText;
        }

        setActionButtonsDisabled(true);
        generateBtn.classList.add('loading');
        clearWarning();

        try {
            const response = await fetch(url, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            const data = await response.json().catch(() => ({}));

            if (!response.ok) {
                throw new Error(data.error || 'Request failed');
            }

            updateOutputState(data, keepVisibleBrief);

            if (data.warning) {
                showError(data.warning);
            }

            await refreshAudioPreview();
        } catch (error) {
            console.error(error);
            showError(error.message || 'Something went wrong. Please check backend logs.');
        } finally {
            generateBtn.classList.remove('loading');
            setActionButtonsDisabled(false);
        }
    }

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;
        const config = collectGenerationConfig();
        generationState.prompt = prompt;
        generationState.config = config;

        // UI State: Loading
        resultSection.classList.add('hidden');
        codeSection.classList.add('hidden');
        if (document.getElementById('empty-state')) document.getElementById('empty-state').classList.add('hidden');

        await performGenerationRequest(`${apiBase}/generate`, { prompt, config }, {
            loadingText: 'Rendering studio audio on backend. Please wait (~15 seconds)...'
        });
    });

    renderCodeBtn.addEventListener('click', async () => {
        const editedCode = codeText.value.trim();
        if (!editedCode) {
            showError('MusicPy code is empty.');
            return;
        }

        generationState.code = editedCode;
        await performGenerationRequest(`${apiBase}/render-code`, {
            code: editedCode,
            brief: generationState.brief
        }, {
            loadingText: 'Rendering updated code and rebuilding audio preview...',
            keepVisibleBrief: generationState.brief
        });
    });

    reviseBtn.addEventListener('click', async () => {
        if (!generationState.prompt) {
            showError('Generate a composition first before asking STALGIA for targeted changes.');
            return;
        }

        await performGenerationRequest(`${apiBase}/revise`, {
            prompt: generationState.prompt,
            config: generationState.config,
            brief: generationState.brief,
            code: codeText.value,
            request: revisionRequest.value.trim(),
            mode: 'change'
        }, {
            loadingText: 'STALGIA is revising the composition and rebuilding audio...',
            keepVisibleBrief: generationState.brief
        });
    });

    regenerateBtn.addEventListener('click', async () => {
        if (!generationState.prompt) {
            showError('Create a composition first before asking STALGIA to rewrite it.');
            return;
        }

        await performGenerationRequest(`${apiBase}/revise`, {
            prompt: generationState.prompt,
            config: generationState.config,
            brief: generationState.brief,
            code: codeText.value,
            request: revisionRequest.value.trim(),
            mode: 'regenerate'
        }, {
            loadingText: 'STALGIA is generating a fresh variation and rebuilding audio...'
        });
    });

    // Handle Audio Downloads
    document.querySelectorAll('.audio-download').forEach(btn => {
        btn.addEventListener('click', async () => {
            const format = btn.getAttribute('data-format');
            const downloadUrl = `${apiBase}/download/audio?format=${format}&t=${Date.now()}`;
            
            // Show loading state on the button
            const originalText = btn.textContent;
            btn.textContent = 'Rendering...';
            btn.disabled = true;
            btn.style.opacity = '0.7';
            btn.style.cursor = 'wait';

            try {
                // Fetch the blob asynchronously so the user knows something is happening
                const response = await fetch(downloadUrl);
                if (!response.ok) throw new Error('Download failed');
                
                const blob = await response.blob();
                const blobUrl = window.URL.createObjectURL(blob);
                
                // Trigger actual download via blob url
                const link = document.createElement('a');
                link.href = blobUrl;
                link.download = `output.${format}`;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                window.URL.revokeObjectURL(blobUrl);
            } catch (error) {
                console.error(error);
                alert(`Error rendering ${format.toUpperCase()}. Please check backend logs.`);
            } finally {
                // Reset button state
                btn.textContent = originalText;
                btn.disabled = false;
                btn.style.opacity = '1';
                btn.style.cursor = 'pointer';
            }
        });
    });
});
