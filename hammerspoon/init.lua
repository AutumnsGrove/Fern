-- Fern Hammerspoon configuration
-- Main entry point for the GUI layer

-- Global configuration
FernConfig = {
    -- Hotkeys
    startCaptureHotkey = { {"ctrl", "alt", "shift"}, "F" },
    stopCaptureHotkey = { {"ctrl", "alt", "shift"}, "S" },
    toggleOverlayHotkey = { {"ctrl", "alt", "shift"}, "O" },

    -- WebSocket settings
    websocketHost = "localhost",
    websocketPort = 8765,

    -- Display settings
    overlayPosition = "top right",
    overlayOpacity = 0.85,
    overlayDuration = 3,

    -- Colors (Fern theme - forest greens)
    colors = {
        inRange = { red = 0.2, green = 0.8, blue = 0.4 },
        outOfRange = { red = 0.9, green = 0.3, blue = 0.2 },
        neutral = { red = 0.3, green = 0.6, blue = 0.8 },
        background = { red = 0.1, green = 0.15, blue = 0.1 },
        text = { red = 0.9, green = 0.95, blue = 0.9 }
    }
}

-- State
local state = {
    isCapturing = false,
    currentPitch = 0,
    currentF1 = 0,
    currentF2 = 0,
    currentF3 = 0,
    inRange = false,
    targetMin = 80,
    targetMax = 250,
    websocket = nil,
    overlay = nil,
    timer = nil
}

-- Load required modules
require("overlay")

-- Initialize Fern
function FernInit()
    print("[Fern] Initializing...")

    -- Connect WebSocket
    FernConnectWebSocket()

    -- Setup hotkeys
    FernSetupHotkeys()

    -- Show initial status
    FernShowStatus()

    print("[Fern] Ready!")
end

-- WebSocket connection
function FernConnectWebSocket()
    local ok, websocket = pcall(require, "websocket")

    if not ok then
        print("[Fern] WebSocket library not found, using polling mode")
        FernStartPolling()
        return
    end

    -- Simple WebSocket implementation for Hammerspoon
    -- Uses hs.socket for communication
    local socket = require("hs.socket")
    local json = require("hs.json")

    state.websocket = {
        connected = false,
        callbacks = {}
    }

    -- For now, use signal file polling as fallback
    FernStartPolling()
end

-- Polling mode for signal files
function FernStartPolling()
    -- Check for updates every 0.5 seconds
    state.timer = hs.timer.doEvery(0.5, FernCheckSignalFiles)
end

function FernCheckSignalFiles()
    -- Check capture active signal
    local captureFile = io.open("/tmp/fern_capture_active", "r")
    if captureFile then
        local content = captureFile:read("*a")
        captureFile:close()

        local status = hs.json.decode(content)
        if status.active and not state.isCapturing then
            state.isCapturing = true
            FernOnCaptureStarted(status)
        elseif not status.active and state.isCapturing then
            state.isCapturing = false
            FernOnCaptureStopped()
        end
    elseif state.isCapturing then
        state.isCapturing = false
        FernOnCaptureStopped()
    end

    -- Check results file
    local resultsFile = io.open("/tmp/fern_results", "r")
    if resultsFile then
        local content = resultsFile:read("*a")
        resultsFile:close()

        local results = hs.json.decode(content)
        FernUpdateDisplay(results)
    end
end

-- Hotkey setup
function FernSetupHotkeys()
    -- Start capture
    hs.hotkey.bind(
        FernConfig.startCaptureHotkey[1],
        FernConfig.startCaptureHotkey[2],
        "Start voice capture",
        function()
            FernStartCapture()
        end
    )

    -- Stop capture
    hs.hotkey.bind(
        FernConfig.stopCaptureHotkey[1],
        FernConfig.stopCaptureHotkey[2],
        "Stop voice capture",
        function()
            FernStopCapture()
        end
    )

    -- Toggle overlay
    hs.hotkey.bind(
        FernConfig.toggleOverlayHotkey[1],
        FernConfig.toggleOverlayHotkey[2],
        "Toggle Fern overlay",
        function()
            FernToggleOverlay()
        end
    )

    print("[Fern] Hotkeys configured")
end

-- Capture control
function FernStartCapture()
    print("[Fern] Starting capture...")

    state.isCapturing = true

    -- Signal file
    FernWriteCaptureSignal(true)

    -- Update display
    FernUpdateDisplay({
        median_pitch = 0,
        in_range = true,
        status = "capturing"
    })

    -- Show overlay
    FernShowOverlay()
end

function FernStopCapture()
    print("[Fern] Stopping capture...")

    state.isCapturing = false

    -- Signal file
    FernWriteCaptureSignal(false)

    -- Hide overlay
    FernHideOverlay()
end

function FernWriteCaptureSignal(active)
    local file = io.open("/tmp/fern_capture_active", "w")
    if file then
        local status = {
            active = active,
            timestamp = os.date("%Y-%m-%dT%H:%M:%S"),
            target_min = state.targetMin,
            target_max = state.targetMax
        }
        file:write(hs.json.encode(status))
        file:close()
    end
end

-- Event handlers
function FernOnCaptureStarted(status)
    if status.target_min then state.targetMin = status.target_min end
    if status.target_max then state.targetMax = status.target_max end
    FernShowOverlay()
end

function FernOnCaptureStopped()
    FernHideOverlay()
end

-- Display updates
function FernUpdateDisplay(results)
    if not results then return end

    state.currentPitch = results.median_pitch or 0
    state.currentF1 = results.f1_mean or 0
    state.currentF2 = results.f2_mean or 0
    state.currentF3 = results.f3_mean or 0
    state.inRange = results.in_range or false

    FernRefreshOverlay()
end

-- Overlay management
function FernShowOverlay()
    if not state.overlay then
        state.overlay = FernOverlayCreate()
    end
    state.overlay:show()
end

function FernHideOverlay()
    if state.overlay then
        state.overlay:hide()
    end
end

function FernToggleOverlay()
    if state.overlay and state.overlay:isShowing() then
        FernHideOverlay()
    else
        FernShowOverlay()
    end
end

function FernRefreshOverlay()
    if state.overlay then
        FernOverlayUpdate(state.overlay, state)
    end
end

-- Status notification
function FernShowStatus()
    local title = "🌿 Fern"
    local message = string.format(
        "Ready to track your voice.\n\nCapture: %s\nTarget: %.0f - %.0f Hz",
        state.isCapturing and "Active" or "Inactive",
        state.targetMin,
        state.targetMax
    )

    hs.notify.new({
        title = title,
        informativeText = message,
        withdrawAfter = 5
    }):send()
end

-- Cleanup
function FernCleanup()
    print("[Fern] Cleaning up...")

    if state.timer then
        state.timer:stop()
    end

    FernWriteCaptureSignal(false)

    if state.overlay then
        state.overlay:delete()
    end

    print("[Fern] Cleanup complete")
end

-- Event bindings
hs.urlregister.setShouldLaunchCallback(function(scheme, host, path)
    return scheme == "fern"
end)

-- Initialize on load
FernInit()

-- Cleanup on reload
hs.audiodevice.watcher.set(function(device, event)
    if event == "deviceRemoved" then
        if state.isCapturing then
            FernStopCapture()
            hs.notify.new({
                title = "Fern",
                informativeText = "Audio device disconnected. Capture stopped.",
                withdrawAfter = 5
            }):send()
        end
    end
end)

print("[Fern] Configuration loaded")
