-- Live overlay display
-- Real-time pitch and resonance visualization

local FernOverlay = {}

-- Create overlay canvas
function FernOverlayCreate()
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = 320
    local height = 200
    local x = res.w - width - 50
    local y = res.h - height - 100

    local canvas = hs.canvas.new({
        x = x,
        y = y,
        w = width,
        h = height
    })

    -- Background
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.1, green = 0.15, blue = 0.12, alpha = 0.9 },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.3, green = 0.6, blue = 0.4, alpha = 0.8 },
        strokeWidth = 2,
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Title bar
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.15, green = 0.25, blue = 0.18, alpha = 1 },
        frame = {
            x = 0,
            y = 0,
            w = width,
            h = 30
        },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Title
    canvas[#canvas + 1] = {
        type = "text",
        text = "🌿 Fern",
        textColor = { red = 0.6, green = 0.9, blue = 0.6, alpha = 1 },
        textSize = 14,
        textFont = "SF Mono",
        frame = {
            x = 15,
            y = 8,
            w = 100,
            h = 20
        }
    }

    -- Status indicator
    canvas[#canvas + 1] = {
        type = "circle",
        action = "fill",
        fillColor = { red = 0.2, green = 0.8, blue = 0.3, alpha = 1 },
        frame = {
            x = width - 35,
            y = 10,
            w = 12,
            h = 12
        }
    }

    -- Pitch value
    canvas[#canvas + 1] = {
        type = "text",
        text = "0.0",
        textColor = { red = 0.9, green = 0.95, blue = 0.9, alpha = 1 },
        textSize = 48,
        textFont = "SF Mono",
        frame = {
            x = 15,
            y = 45,
            w = 200,
            h = 60
        }
    }

    -- Pitch unit
    canvas[#canvas + 1] = {
        type = "text",
        text = "Hz",
        textColor = { red = 0.5, green = 0.7, blue = 0.6, alpha = 1 },
        textSize = 16,
        textFont = "SF Mono",
        frame = {
            x = 175,
            y = 55,
            w = 40,
            h = 25
        }
    }

    -- Range indicator
    canvas[#canvas + 1] = {
        type = "text",
        text = "Target: 80 - 250 Hz",
        textColor = { red = 0.5, green = 0.7, blue = 0.6, alpha = 1 },
        textSize = 12,
        textFont = "SF Mono",
        frame = {
            x = 15,
            y = 100,
            w = 200,
            h = 20
        }
    }

    -- In range / out of range status
    canvas[#canvas + 1] = {
        type = "text",
        text = "IN RANGE",
        textColor = { red = 0.2, green = 0.8, blue = 0.4, alpha = 1 },
        textSize = 14,
        textFont = "SF Mono",
        frame = {
            x = 15,
            y = 125,
            w = 150,
            h = 25
        }
    }

    -- Formants row
    canvas[#canvas + 1] = {
        type = "text",
        text = "Formants:",
        textColor = { red = 0.4, green = 0.55, blue = 0.5, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 15,
            y = 155,
            w = 80,
            h = 18
        }
    }

    -- F1 value
    canvas[#canvas + 1] = {
        type = "text",
        text = "F1: --",
        textColor = { red = 0.6, green = 0.75, blue = 0.8, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 95,
            y = 155,
            w = 60,
            h = 18
        }
    }

    -- F2 value
    canvas[#canvas + 1] = {
        type = "text",
        text = "F2: --",
        textColor = { red = 0.7, green = 0.65, blue = 0.8, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 155,
            y = 155,
            w = 60,
            h = 18
        }
    }

    -- F3 value
    canvas[#canvas + 1] = {
        type = "text",
        text = "F3: --",
        textColor = { red = 0.8, green = 0.7, blue = 0.6, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 215,
            y = 155,
            w = 60,
            h = 18
        }
    }

    return canvas
end

-- Update overlay with new data
function FernOverlayUpdate(canvas, data)
    if not canvas or not data then return end

    -- Index mapping for canvas elements:
    -- 1: background, 2: border, 3: title bar, 4: title, 5: status dot
    -- 6: pitch value, 7: pitch unit, 8: range text, 9: status text
    -- 10: formants label, 11: F1, 12: F2, 13: F3

    -- Update pitch
    local pitchText = string.format("%.1f", data.currentPitch or 0)
    canvas[6].text = pitchText

    -- Update status color
    local statusColor
    if data.inRange then
        statusColor = { red = 0.2, green = 0.8, blue = 0.4, alpha = 1 } -- Green
        canvas[9].text = "IN RANGE"
    else
        statusColor = { red = 0.9, green = 0.35, blue = 0.25, alpha = 1 } -- Red/Orange
        canvas[9].text = "OUT OF RANGE"
    end
    canvas[9].textColor = statusColor
    canvas[5].fillColor = statusColor

    -- Update target range
    local targetText = string.format("Target: %.0f - %.0f Hz", data.targetMin or 80, data.targetMax or 250)
    canvas[8].text = targetText

    -- Update formants
    if data.currentF1 and data.currentF1 > 0 then
        canvas[11].text = string.format("F1: %.0f", data.currentF1)
    else
        canvas[11].text = "F1: --"
    end

    if data.currentF2 and data.currentF2 > 0 then
        canvas[12].text = string.format("F2: %.0f", data.currentF2)
    else
        canvas[12].text = "F2: --"
    end

    if data.currentF3 and data.currentF3 > 0 then
        canvas[13].text = string.format("F3: %.0f", data.currentF3)
    else
        canvas[13].text = "F3: --"
    end
end

-- Create mini overlay for compact display
function FernOverlayCreateMini()
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = 180
    local height = 60
    local x = res.w - width - 30
    local y = res.h - height - 30

    local canvas = hs.canvas.new({
        x = x,
        y = y,
        w = width,
        h = height
    })

    -- Background
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.1, green = 0.15, blue = 0.12, alpha = 0.85 },
        roundedRectRadii = { xRadius = 8, yRadius = 8 }
    }

    -- Pitch value (large)
    canvas[#canvas + 1] = {
        type = "text",
        text = "0 Hz",
        textColor = { red = 0.9, green = 0.95, blue = 0.9, alpha = 1 },
        textSize = 28,
        textFont = "SF Mono",
        frame = {
            x = 15,
            y = 15,
            w = 120,
            h = 35
        }
    }

    -- Status indicator
    canvas[#canvas + 1] = {
        type = "circle",
        action = "fill",
        fillColor = { red = 0.3, green = 0.6, blue = 0.4, alpha = 1 },
        frame = {
            x = width - 25,
            y = 24,
            w = 14,
            h = 14
        }
    }

    return canvas
end

-- Update mini overlay
function FernOverlayUpdateMini(canvas, data)
    if not canvas or not data then return end

    local pitchText = string.format("%.0f Hz", data.currentPitch or 0)
    canvas[2].text = pitchText

    if data.inRange then
        canvas[3].fillColor = { red = 0.2, green = 0.8, blue = 0.3, alpha = 1 }
    else
        canvas[3].fillColor = { red = 0.9, green = 0.35, blue = 0.25, alpha = 1 }
    end
end

-- Animation helpers
function FernOverlayAnimateIn(canvas)
    canvas:show()
    local frame = canvas:frame()
    canvas:frame({
        x = frame.x,
        y = frame.y + 20,
        w = frame.w,
        h = frame.h
    })
    canvas:frame(frame)
end

function FernOverlayAnimateOut(canvas)
    canvas:hide()
end

-- Position helpers
function FernOverlaySetPosition(canvas, position)
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()
    local frame = canvas:frame()

    local positions = {
        ["top left"] = { x = 50, y = 50 },
        ["top right"] = { x = res.w - frame.w - 50, y = 50 },
        ["bottom left"] = { x = 50, y = res.h - frame.h - 50 },
        ["bottom right"] = { x = res.w - frame.w - 50, y = res.h - frame.h - 50 },
        ["center"] = { x = (res.w - frame.w) / 2, y = (res.h - frame.h) / 2 }
    }

    local pos = positions[position] or positions["top right"]
    canvas:frame({
        x = pos.x,
        y = pos.y,
        w = frame.w,
        h = frame.h
    })
end

-- Draggable overlay
function FernOverlayMakeDraggable(canvas)
    canvas:clickActivate(true)

    canvas:mouseCallback(function(event)
        if event.type == "leftMouseDown" then
            canvas:startDrag()
        end
    end)
end

return FernOverlay
