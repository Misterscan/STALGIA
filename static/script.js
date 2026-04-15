document.addEventListener('DOMContentLoaded', () => {
    const generateBtn = document.getElementById('generate-btn');
    const promptInput = document.getElementById('prompt-input');
    const resultSection = document.getElementById('result-section');
    const generationWarning = document.getElementById('generation-warning');
    const briefText = document.getElementById('brief-text');
    const midiPlayer = document.getElementById('midi-player');
    const midiVisualizer = document.getElementById('midi-visualizer');
    const codeSection = document.getElementById('code-section');
    const codeText = document.getElementById('code-text');
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

    const apiBase = 'http://localhost:5001'; // Connect to local Flask server

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

    generateBtn.addEventListener('click', async () => {
        const prompt = promptInput.value.trim();
        if (!prompt) return;
        const config = collectGenerationConfig();

        // UI State: Loading
        generateBtn.classList.add('loading');
        generateBtn.disabled = true;
        resultSection.classList.add('hidden');
        codeSection.classList.add('hidden');
        generationWarning.classList.add('hidden');
        if (document.getElementById('empty-state')) document.getElementById('empty-state').classList.add('hidden');
        generationWarning.textContent = '';

        try {
            const response = await fetch(`${apiBase}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ prompt, config })
            });

            if (!response.ok) throw new Error('Generation failed');

            const data = await response.json();

            // Update UI with results
            renderBriefMarkdown(data.brief);
            codeText.textContent = data.code;

            if (data.warning) {
                generationWarning.textContent = data.warning;
                generationWarning.classList.remove('hidden');
            }
            
            // Set MIDI source
            // We append a timestamp to bust cache
            const midiUrl = `${apiBase}/download/midi?t=${Date.now()}`;
            midiPlayer.src = midiUrl;
            midiVisualizer.src = midiUrl;
            downloadMidiBtn.href = midiUrl;

            // Show sections immediately for MIDI playback
            resultSection.classList.remove('hidden');
            codeSection.classList.remove('hidden');
            resultSection.scrollIntoView({ behavior: 'smooth' });

            // Fetch HQ Audio in background (Takes ~15s)
            audioPlayer.style.display = 'none';
            audioLoadingText.style.display = 'block';
            audioLoadingText.textContent = "Rendering studio audio on backend. Please wait (~15 seconds)...";
            
            const mp3Url = `${apiBase}/download/audio?format=mp3&t=${Date.now()}`;
            fetch(mp3Url).then(res => {
                if (!res.ok) throw new Error('Audio backend render failed');
                return res.blob();
            }).then(blob => {
                audioPlayer.src = window.URL.createObjectURL(blob);
                audioLoadingText.style.display = 'none';
                audioPlayer.style.display = 'block';
            }).catch(err => {
                console.error(err);
                audioLoadingText.textContent = "Failed to render high-quality audio.";
            });

        } catch (error) {
            console.error(error);
            alert('Error generating music. Please check backend logs.');
        } finally {
            generateBtn.classList.remove('loading');
            generateBtn.disabled = false;
        }
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
