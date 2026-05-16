// AI Cover Visualizer - jQuery Version

$(document).ready(function() {
    console.log('🎵 AI Cover Visualizer initialized');
    
    // State
    var state = {
        audioFile: null,
        imageFile: null,
        currentJobId: null,
        isProcessing: false,
        ws: null
    };
    
    // DOM Elements
    var $audioInput = $('#audioInput');
    var $imageInput = $('#imageInput');
    var $audioDropZone = $('#audioDropZone');
    var $imageDropZone = $('#imageDropZone');
    var $generateBtn = $('#generateBtn');
    var $cancelBtn = $('#cancelBtn');
    
    // Initialize WebSocket
    initWebSocket();
    
    // Event Bindings
    bindEvents();
    
    function bindEvents() {
        console.log('Binding events...');
        
        // File input changes
        $audioInput.on('change', function(e) {
            handleFileSelect(e.target.files[0], 'audio');
        });
        
        $imageInput.on('change', function(e) {
            handleFileSelect(e.target.files[0], 'image');
        });
        
        // Drag and drop
        setupDragAndDrop($audioDropZone, 'audio');
        setupDragAndDrop($imageDropZone, 'image');
        
        // Remove buttons
        $('.remove-btn').on('click', function(e) {
            e.stopPropagation();
            var type = $(this).data('type');
            removeFile(type);
        });
        
        // Range inputs
        $('#barCount').on('input', function() {
            $('#barCountValue').text($(this).val());
        });
        
        $('#glowIntensity').on('input', function() {
            $('#glowIntensityValue').text($(this).val() + '%');
        });
        
        $('#barSensitivity').on('input', function() {
            $('#barSensitivityValue').text($(this).val() + '%');
        });
        
        // Preset buttons
        $('.preset-btn').on('click', function() {
            var preset = $(this).data('preset');
            applyPreset(preset);
        });
        
        // GPU mode selector
        $('#gpuMode').on('change', function() {
            var mode = $(this).val();
            var infoText = '';
            
            switch(mode) {
                case 'amd':
                    infoText = 'AMD GPU mode selected (h264_amf). Great for RX 6000/7000 series!';
                    break;
                case 'nvidia':
                    infoText = 'NVIDIA GPU mode selected (h264_nvenc). Great for GTX 10 series or newer!';
                    break;
                default:
                    infoText = 'CPU mode works on any system but is slower than GPU encoding.';
            }
            
            $('#gpuInfo').text(infoText);
        });
        
        // Generate button
        $generateBtn.on('click', generateVideo);
        
        // Cancel button
        $cancelBtn.on('click', cancelGeneration);
        
        // Download button - use programmatic download
        $('#downloadBtn').on('click', function(e) {
            e.preventDefault();
            var downloadUrl = $(this).attr('href');
            var filename = $(this).attr('download') || 'visualizer-video.mp4';
            
            if (downloadUrl && downloadUrl !== '#') {
                // Create a temporary link and trigger download
                var tempLink = document.createElement('a');
                tempLink.href = downloadUrl;
                tempLink.download = filename;
                tempLink.style.display = 'none';
                document.body.appendChild(tempLink);
                tempLink.click();
                document.body.removeChild(tempLink);
                
                log('Download started: ' + filename, 'success');
            } else {
                showError('Download URL not available. Please try again.');
            }
        });
    }
    
    function setupDragAndDrop($zone, type) {
        $zone.on('dragover', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).addClass('dragover');
        });
        
        $zone.on('dragleave', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('dragover');
        });
        
        $zone.on('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            $(this).removeClass('dragover');
            
            var files = e.originalEvent.dataTransfer.files;
            if (files.length > 0) {
                handleFileSelect(files[0], type);
            }
        });
    }
    
    function handleFileSelect(file, type) {
        if (!file) return;
        
        console.log('File selected:', type, file.name);
        
        if (type === 'audio') {
            state.audioFile = file;
            $('#audioUploadContent').addClass('d-none');
            $('#audioFileInfo').removeClass('d-none');
            $('#audioFileInfo .file-name').text(file.name);
            $('#audioFileInfo .file-size').text(formatFileSize(file.size));
            log('Audio file loaded: ' + file.name);
        } else {
            state.imageFile = file;
            
            // Show preview
            var reader = new FileReader();
            reader.onload = function(e) {
                $('#imageFileInfo .preview-img').attr('src', e.target.result);
            };
            reader.readAsDataURL(file);
            
            $('#imageUploadContent').addClass('d-none');
            $('#imageFileInfo').removeClass('d-none');
            $('#imageFileInfo .file-name').text(file.name);
            $('#imageFileInfo .file-size').text(formatFileSize(file.size));
            log('Image file loaded: ' + file.name);
        }
        
        updateGenerateButton();
    }
    
    function removeFile(type) {
        if (type === 'audio') {
            state.audioFile = null;
            $audioInput.val('');
            $('#audioFileInfo').addClass('d-none');
            $('#audioUploadContent').removeClass('d-none');
        } else {
            state.imageFile = null;
            $imageInput.val('');
            $('#imageFileInfo').addClass('d-none');
            $('#imageUploadContent').removeClass('d-none');
            $('#imageFileInfo .preview-img').attr('src', '');
        }
        updateGenerateButton();
    }
    
    function formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        var k = 1024;
        var sizes = ['Bytes', 'KB', 'MB', 'GB'];
        var i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
    
    function applyPreset(preset) {
        // Update active button
        $('.preset-btn').removeClass('active');
        $('.preset-btn[data-preset="' + preset + '"]').addClass('active');
        
        // Apply settings
        switch(preset) {
            case 'youtube':
                $('#resolution').val('1920x1080');
                $('#fps').val('30');
                $('#barCount').val('64');
                break;
            case 'tiktok':
                $('#resolution').val('1080x1920');
                $('#fps').val('30');
                $('#barCount').val('48');
                break;
            case 'instagram':
                $('#resolution').val('1080x1080');
                $('#fps').val('30');
                $('#barCount').val('48');
                break;
        }
        
        // Update display values
        $('#barCountValue').text($('#barCount').val());
        log('Applied preset: ' + preset);
    }
    
    function updateGenerateButton() {
        if (state.audioFile && state.imageFile) {
            $generateBtn.prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>Generate Video');
        } else {
            $generateBtn.prop('disabled', true).html('<i class="bi bi-lock me-2"></i>Select Files First');
        }
    }
    
    function initWebSocket() {
        var protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        var wsUrl = protocol + '//' + window.location.host + '/music-visualizer';
        
        try {
            state.ws = new WebSocket(wsUrl);
            
            state.ws.onopen = function() {
                console.log('WebSocket connected');
            };
            
            state.ws.onmessage = function(event) {
                var data = JSON.parse(event.data);
                handleWebSocketMessage(data);
            };
            
            state.ws.onclose = function() {
                console.log('WebSocket disconnected, reconnecting in 3s...');
                setTimeout(initWebSocket, 3000);
            };
            
            state.ws.onerror = function(error) {
                console.error('WebSocket error:', error);
            };
        } catch(e) {
            console.error('Failed to connect WebSocket:', e);
        }
    }
    
    function handleWebSocketMessage(data) {
        if (data.jobId !== state.currentJobId) return;
        
        switch(data.type) {
            case 'progress':
                updateProgress(data.value, data.message);
                break;
            case 'log':
                log(data.message);
                break;
            case 'error':
                log('Error: ' + data.message, 'error');
                break;
            case 'complete':
                handleComplete(data);
                break;
            case 'cancelled':
                handleCancelled();
                break;
        }
    }
    
    function generateVideo() {
        if (!state.audioFile || !state.imageFile) return;
        
        // Reset UI
        $('#successSection').hide();
        $('#errorSection').hide();
        $('#progressSection').fadeIn();
        
        // Update buttons
        $generateBtn.prop('disabled', true).html('<i class="bi bi-hourglass-split me-2"></i>Uploading...');
        $cancelBtn.show().prop('disabled', false);
        
        log('Starting upload...');
        
        // Upload files
        var formData = new FormData();
        formData.append('audio', state.audioFile);
        formData.append('image', state.imageFile);
        
        $.ajax({
            url: 'api/upload',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            success: function(uploadData) {
                state.currentJobId = uploadData.jobId;
                log('Files uploaded successfully');
                updateProgress(0, 'Starting video generation...');
                $generateBtn.html('<i class="bi bi-gear-fill me-2"></i>Generating...');
                
                // Start generation
                var settings = {
                    resolution: $('#resolution').val(),
                    fps: parseInt($('#fps').val()),
                    barCount: parseInt($('#barCount').val()),
                    glowIntensity: parseInt($('#glowIntensity').val()),
                    barSensitivity: parseInt($('#barSensitivity').val()),
                    gpuMode: $('#gpuMode').val()
                };
                
                $.ajax({
                    url: 'api/generate',
                    type: 'POST',
                    contentType: 'application/json',
                    data: JSON.stringify({
                        jobId: state.currentJobId,
                        audioFilename: uploadData.audio.filename,
                        imageFilename: uploadData.image.filename,
                        settings: settings
                    }),
                    success: function() {
                        console.log('Generation started');
                    },
                    error: function(xhr) {
                        showError('Failed to start generation: ' + xhr.responseText);
                        resetUI();
                    }
                });
            },
            error: function(xhr) {
                showError('Upload failed: ' + xhr.responseText);
                resetUI();
            }
        });
    }
    
    function updateProgress(percent, message) {
        $('#progressBar').css('width', percent + '%');
        $('#progressPercent').text(Math.round(percent) + '%');
        if (message) {
            $('#statusText').text(message);
        }
        
        // Change color based on progress
        var $bar = $('#progressBar');
        $bar.removeClass('bg-info bg-primary bg-warning bg-success');
        
        if (percent < 30) {
            $bar.addClass('bg-info');
        } else if (percent < 70) {
            $bar.addClass('bg-primary');
        } else if (percent < 100) {
            $bar.addClass('bg-warning');
        } else {
            $bar.addClass('bg-success').removeClass('progress-bar-animated');
        }
    }
    
    function log(message, type) {
        type = type || 'info';
        var timestamp = new Date().toLocaleTimeString();
        var colorClass = type === 'error' ? 'text-danger' : (type === 'success' ? 'text-success' : 'text-light');
        
        var $entry = $('<div class="log-entry">')
            .html('<span class="text-muted">[' + timestamp + ']</span> <span class="' + colorClass + '">' + message + '</span>');
        
        $('#logConsole').append($entry);
        $('#logConsole').scrollTop($('#logConsole')[0].scrollHeight);
    }
    
    function handleComplete(data) {
        if (data.success) {
            updateProgress(100, 'Complete!');
            log('Video generation complete!', 'success');
            
            $('#progressSection').hide();
            $('#successSection').fadeIn();
            $('#downloadBtn')
                .attr('href', data.downloadUrl)
                .attr('download', data.filename);
        } else {
            showError(data.error || 'Generation failed');
        }
        
        resetUI();
    }
    
    function handleCancelled() {
        log('Generation cancelled by user', 'error');
        updateProgress(0, 'Cancelled');
        resetUI();
    }
    
    function cancelGeneration() {
        if (!state.currentJobId) return;
        
        $cancelBtn.prop('disabled', true).html('<i class="bi bi-hourglass-split me-2"></i>Cancelling...');
        
        $.ajax({
            url: 'api/cancel/' + state.currentJobId,
            type: 'POST',
            error: function() {
                console.error('Cancel request failed');
            }
        });
    }
    
    function showError(message) {
        $('#errorText').text(message);
        $('#errorSection').fadeIn();
        log('Error: ' + message, 'error');
    }
    
    function resetUI() {
        state.isProcessing = false;
        state.currentJobId = null;
        
        $generateBtn.prop('disabled', false).html('<i class="bi bi-play-fill me-2"></i>Generate Video');
        $cancelBtn.hide().html('<i class="bi bi-stop-fill me-2"></i>Cancel');
        
        updateGenerateButton();
    }
    
    // Initial log
    log('Visualizer ready. Select files to begin.');
});
