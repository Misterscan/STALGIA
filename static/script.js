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
        if (downloadMidiBtn) downloadMidiBtn.href = midiUrl;

        resultSection.classList.remove('hidden');
        codeSection.classList.remove('hidden');
        resultSection.scrollIntoView({ behavior: 'smooth' });

        // Enable exports in the dropdown menu
        enableExportMenus();
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
            updateStatusText(loadingText);
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

            updateStatusText('Rendering studio audio on backend...');
            await refreshAudioPreview();
            updateStatusText('System Ready');
        } catch (error) {
            console.error(error);
            showError(error.message || 'Something went wrong. Please check backend logs.');
            updateStatusText('Generation failed.');
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

        // Disable exports during new generation
        disableExportMenus();

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
        btn.addEventListener('click', async (e) => {
            if (btn.classList.contains('disabled')) {
                e.stopPropagation();
                return;
            }
            const format = btn.getAttribute('data-format');
            const downloadUrl = `${apiBase}/download/audio?format=${format}&t=${Date.now()}`;
            
            // Show loading state on the button / menu item
            const originalText = btn.textContent;
            btn.textContent = btn.tagName === 'LI' ? `Exporting ${format.toUpperCase()}...` : 'Rendering...';
            btn.classList.add('disabled');
            if (btn.tagName !== 'LI') {
                btn.disabled = true;
                btn.style.opacity = '0.7';
                btn.style.cursor = 'wait';
            }
            updateStatusText(`Rendering and downloading ${format.toUpperCase()}...`);

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
                updateStatusText('System Ready');
            } catch (error) {
                console.error(error);
                alert(`Error rendering ${format.toUpperCase()}. Please check backend logs.`);
                updateStatusText('Export failed.');
            } finally {
                // Reset button state
                btn.textContent = originalText;
                btn.classList.remove('disabled');
                if (btn.tagName !== 'LI') {
                    btn.disabled = false;
                    btn.style.opacity = '1';
                    btn.style.cursor = 'pointer';
                }
            }
        });
    });

    // --- STATUS BAR HELPER ---
    function updateStatusText(msg) {
        const statusText = document.getElementById('status-text');
        if (statusText) {
            statusText.textContent = msg;
        }
    }

    // --- MENU DROPDOWN LOGIC ---
    const menuItems = document.querySelectorAll('.menu-bar .menu-item');
    let activeMenu = null;

    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.stopPropagation();
            if (e.target.tagName === 'LI') {
                if (e.target.classList.contains('disabled')) {
                    return;
                }
                closeAllMenus();
                return;
            }

            if (activeMenu === item) {
                closeAllMenus();
            } else {
                closeAllMenus();
                item.classList.add('active');
                activeMenu = item;
            }
        });

        item.addEventListener('mouseenter', () => {
            if (activeMenu && activeMenu !== item) {
                closeAllMenus();
                item.classList.add('active');
                activeMenu = item;
            }
        });
    });

    document.addEventListener('click', () => {
        closeAllMenus();
    });

    function closeAllMenus() {
        menuItems.forEach(item => {
            item.classList.remove('active');
        });
        activeMenu = null;
    }

    // --- EXPORT ENABLE/DISABLE HELPERS ---
    function disableExportMenus() {
        const exportMidi = document.getElementById('menu-export-midi');
        const exportMp3 = document.getElementById('menu-export-mp3');
        const exportWav = document.getElementById('menu-export-wav');
        const exportFlac = document.getElementById('menu-export-flac');
        
        [exportMidi, exportMp3, exportWav, exportFlac].forEach(el => {
            if (el) el.classList.add('disabled');
        });
    }

    function enableExportMenus() {
        const exportMidi = document.getElementById('menu-export-midi');
        const exportMp3 = document.getElementById('menu-export-mp3');
        const exportWav = document.getElementById('menu-export-wav');
        const exportFlac = document.getElementById('menu-export-flac');
        
        [exportMidi, exportMp3, exportWav, exportFlac].forEach(el => {
            if (el) el.classList.remove('disabled');
        });
    }

    // --- FILE MENU ACTIONS ---
    const menuNewComposition = document.getElementById('menu-new-composition');
    if (menuNewComposition) {
        menuNewComposition.addEventListener('click', () => {
            promptInput.value = '';
            if (exampleSelect) exampleSelect.value = '';
            if (configGenre) configGenre.value = '';
            if (configMood) configMood.value = '';
            if (configTempo) configTempo.value = '';
            if (configKey) configKey.value = '';
            if (configStructure) configStructure.value = '';
            if (configNotes) configNotes.value = '';
            
            if (configInstruments) {
                Array.from(configInstruments.options).forEach(opt => opt.selected = false);
            }

            const disclosure = document.querySelector('.params-disclosure');
            if (disclosure) disclosure.open = false;

            if (resultSection) resultSection.classList.add('hidden');
            if (codeSection) codeSection.classList.add('hidden');
            
            const emptyState = document.getElementById('empty-state');
            if (emptyState) emptyState.classList.remove('hidden');

            generationState.prompt = '';
            generationState.config = {};
            generationState.brief = '';
            generationState.code = '';

            disableExportMenus();
            updateStatusText('System Ready');
        });
    }

    const menuExportMidi = document.getElementById('menu-export-midi');
    if (menuExportMidi) {
        menuExportMidi.addEventListener('click', (e) => {
            if (menuExportMidi.classList.contains('disabled')) return;
            const midiUrl = `${apiBase}/download/midi?t=${Date.now()}`;
            const link = document.createElement('a');
            link.href = midiUrl;
            link.download = `output.mid`;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        });
    }

    // --- EDIT MENU ACTIONS ---
    const menuClearPrompt = document.getElementById('menu-clear-prompt');
    if (menuClearPrompt) {
        menuClearPrompt.addEventListener('click', () => {
            promptInput.value = '';
        });
    }

    const menuClearConfig = document.getElementById('menu-clear-config');
    if (menuClearConfig) {
        menuClearConfig.addEventListener('click', () => {
            if (configGenre) configGenre.value = '';
            if (configMood) configMood.value = '';
            if (configTempo) configTempo.value = '';
            if (configKey) configKey.value = '';
            if (configStructure) configStructure.value = '';
            if (configNotes) configNotes.value = '';
            if (configInstruments) {
                Array.from(configInstruments.options).forEach(opt => opt.selected = false);
            }
        });
    }

    // --- VIEW MENU ACTIONS ---
    const menuToggleCode = document.getElementById('menu-toggle-code');
    if (menuToggleCode) {
        menuToggleCode.addEventListener('click', () => {
            if (codeSection) {
                codeSection.classList.toggle('hidden');
            }
        });
    }

    const menuToggleConfig = document.getElementById('menu-toggle-config');
    if (menuToggleConfig) {
        menuToggleConfig.addEventListener('click', () => {
            const disclosure = document.querySelector('.params-disclosure');
            if (disclosure) {
                disclosure.open = !disclosure.open;
            }
        });
    }

    const menuToggleStatusbar = document.getElementById('menu-toggle-statusbar');
    if (menuToggleStatusbar) {
        menuToggleStatusbar.addEventListener('click', () => {
            const statusbar = document.getElementById('app-status-bar');
            if (statusbar) {
                statusbar.classList.toggle('hidden');
            }
        });
    }

    // --- HELP MENU & DIALOG MODALS ---
    const menuQuickHelp = document.getElementById('menu-quick-help');
    const menuAbout = document.getElementById('menu-about');
    const menuExit = document.getElementById('menu-exit');
    
    const dialogOverlay = document.getElementById('dialog-overlay');
    const aboutDialog = document.getElementById('about-dialog');
    const helpDialog = document.getElementById('help-dialog');
    const shutdownDialog = document.getElementById('shutdown-dialog');
    const shutdownScreen = document.getElementById('shutdown-screen');

    if (menuQuickHelp && helpDialog && dialogOverlay) {
        menuQuickHelp.addEventListener('click', () => {
            helpDialog.classList.remove('hidden');
            dialogOverlay.classList.remove('hidden');
        });
    }

    if (menuAbout && aboutDialog && dialogOverlay) {
        menuAbout.addEventListener('click', () => {
            aboutDialog.classList.remove('hidden');
            dialogOverlay.classList.remove('hidden');
        });
    }

    if (menuExit && shutdownDialog && dialogOverlay) {
        menuExit.addEventListener('click', () => {
            shutdownDialog.classList.remove('hidden');
            dialogOverlay.classList.remove('hidden');
        });
    }

    const closeDialogs = () => {
        if (aboutDialog) aboutDialog.classList.add('hidden');
        if (helpDialog) helpDialog.classList.add('hidden');
        if (shutdownDialog) shutdownDialog.classList.add('hidden');
        if (dialogOverlay) dialogOverlay.classList.add('hidden');
    };

    document.querySelectorAll('.close-dialog-btn').forEach(btn => {
        btn.addEventListener('click', closeDialogs);
    });

    if (dialogOverlay) {
        dialogOverlay.addEventListener('click', closeDialogs);
    }

    const btnTurnOff = document.getElementById('btn-turn-off');
    if (btnTurnOff && shutdownScreen) {
        btnTurnOff.addEventListener('click', () => {
            closeDialogs();
            shutdownScreen.classList.remove('hidden');
        });
    }

    const btnRestart = document.getElementById('btn-restart');
    if (btnRestart) {
        btnRestart.addEventListener('click', () => {
            window.location.reload();
        });
    }

    if (shutdownScreen) {
        shutdownScreen.addEventListener('click', () => {
            window.location.reload();
        });
    }
});
