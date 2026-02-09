-- Historical chart display
-- View pitch and resonance trends over time

local FernCharts = {}

-- Create trend chart
function FernChartsCreateTrend(data, options)
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = options.width or 600
    local height = options.height or 400
    local x = (res.w - width) / 2
    local y = (res.h - height) / 2

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
        fillColor = { red = 0.08, green = 0.1, blue = 0.08, alpha = 0.95 },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.3, green = 0.5, blue = 0.4, alpha = 0.6 },
        strokeWidth = 1,
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Title
    canvas[#canvas + 1] = {
        type = "text",
        text = options.title or "Pitch Trend",
        textColor = { red = 0.7, green = 0.9, blue = 0.7, alpha = 1 },
        textSize = 18,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = 15,
            w = width - 40,
            h = 30
        }
    }

    -- Draw chart area
    local chartX = 60
    local chartY = 60
    local chartW = width - 100
    local chartH = height - 120

    -- Chart background
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.05, green = 0.08, blue = 0.05, alpha = 0.5 },
        frame = {
            x = chartX,
            y = chartY,
            w = chartW,
            h = chartH
        }
    }

    -- Grid lines
    local gridColor = { red = 0.2, green = 0.3, blue = 0.25, alpha = 0.3 }

    -- Horizontal grid lines
    for i = 1, 4 do
        local yPos = chartY + (chartH * i / 4)
        canvas[#canvas + 1] = {
            type = "line",
            action = "stroke",
            strokeColor = gridColor,
            strokeWidth = 1,
            path = {
                { x = chartX, y = yPos },
                { x = chartX + chartW, y = yPos }
            }
        }
    end

    -- Vertical grid lines
    for i = 1, 7 do
        local xPos = chartX + (chartW * i / 8)
        canvas[#canvas + 1] = {
            type = "line",
            action = "stroke",
            strokeColor = gridColor,
            strokeWidth = 1,
            path = {
                { x = xPos, y = chartY },
                { x = xPos, y = chartY + chartH }
            }
        }
    end

    -- Target range band
    if options.targetMin and options.targetMax then
        local yMin = chartY + chartH - ((options.targetMin / 350) * chartH)
        local yMax = chartY + chartH - ((options.targetMax / 350) * chartH)
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = 0.2, green = 0.6, blue = 0.3, alpha = 0.15 },
            frame = {
                x = chartX,
                y = yMax,
                w = chartW,
                h = yMin - yMax
            }
        }
    end

    -- Draw data line
    if data and #data > 1 then
        local values = {}
        for _, d in ipairs(data) do
            table.insert(values, d.value)
        end

        local minVal = math.min(unpack(values))
        local maxVal = math.max(unpack(values))
        local range = maxVal - minVal
        if range == 0 then range = 1 end

        local points = {}
        local stepX = chartW / (#data - 1)

        for i, d in ipairs(data) do
            local x = chartX + ((i - 1) * stepX)
            local y = chartY + chartH - (((d.value - minVal) / range) * chartH)
            table.insert(points, { x = x, y = y })
        end

        -- Line path
        local pathString = "M " .. points[1].x .. " " .. points[1].y
        for i = 2, #points do
            pathString = pathString .. " L " .. points[i].x .. " " .. points[i].y
        end

        canvas[#canvas + 1] = {
            type = "path",
            action = "stroke",
            strokeColor = { red = 0.3, green = 0.8, blue = 0.5, alpha = 1 },
            strokeWidth = 2,
            path = pathString
        }

        -- Data points
        for i, d in ipairs(data) do
            local x = chartX + ((i - 1) * stepX)
            local y = chartY + chartH - (((d.value - minVal) / range) * chartH)

            local pointColor = { red = 0.3, green = 0.8, blue = 0.5, alpha = 1 }
            if options.targetMin and options.targetMax then
                if d.value >= options.targetMin and d.value <= options.targetMax then
                    pointColor = { red = 0.2, green = 0.8, blue = 0.4, alpha = 1 }
                else
                    pointColor = { red = 0.9, green = 0.4, blue = 0.3, alpha = 1 }
                end
            end

            canvas[#canvas + 1] = {
                type = "circle",
                action = "fill",
                fillColor = pointColor,
                frame = {
                    x = x - 4,
                    y = y - 4,
                    w = 8,
                    h = 8
                }
            }
        end
    end

    -- Y-axis labels
    if data and #data > 0 then
        local values = {}
        for _, d in ipairs(data) do
            table.insert(values, d.value)
        end
        local minVal = math.min(unpack(values))
        local maxVal = math.max(unpack(values))

        canvas[#canvas + 1] = {
            type = "text",
            text = string.format("%.0f", maxVal),
            textColor = { red = 0.5, green = 0.6, blue = 0.5, alpha = 1 },
            textSize = 10,
            textFont = "SF Mono",
            frame = {
                x = 10,
                y = chartY,
                w = 40,
                h = 15
            }
        }

        canvas[#canvas + 1] = {
            type = "text",
            text = string.format("%.0f", minVal),
            textColor = { red = 0.5, green = 0.6, blue = 0.5, alpha = 1 },
            textSize = 10,
            textFont = "SF Mono",
            frame = {
                x = +10,
                y = chartY + chartH - 15,
                w = 40,
                h = 15
            }
        }
    end

    -- X-axis labels (dates)
    if data and #data > 0 then
        local labelCount = math.min(5, #data)
        local step = math.floor(#data / labelCount)

        for i = 1, labelCount do
            local idx = (i - 1) * step + 1
            if idx <= #data then
                local x = chartX + ((idx - 1) * (chartW / (#data - 1)))
                local dateStr = data[idx].date or ""

                canvas[#canvas + 1] = {
                    type = "text",
                    text = dateStr,
                    textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
                    textSize = 10,
                    textFont = "SF Mono",
                    frame = {
                        x = x - 30,
                        y = chartY + chartH + 5,
                        w = 60,
                        h = 15
                    }
                }
            end
        end
    end

    -- Legend
    local legendY = height - 25
    canvas[#canvas + 1] = {
        type = "text",
        text = "● In range  ○ Out of range",
        textColor = { red = 0.5, green = 0.6, blue = 0.55, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = legendY,
            w = width - 40,
            h = 20
        }
    }

    return canvas
end

-- Create resonance chart
function FernChartsCreateResonance(data, options)
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = options.width or 500
    local height = options.height or 400
    local x = (res.w - width) / 2
    local y = (res.h - height) / 2

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
        fillColor = { red = 0.08, green = 0.1, blue = 0.08, alpha = 0.95 },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Title
    canvas[#canvas + 1] = {
        type = "text",
        text = "Resonance Profile",
        textColor = { red = 0.7, green = 0.9, blue = 0.7, alpha = 1 },
        textSize = 18,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = 15,
            w = width - 40,
            h = 30
        }
    }

    -- Formant values display
    local centerX = width / 2
    local startY = 80

    local formants = {
        { name = "F1", value = data.f1 or 0, color = { red = 0.6, green = 0.75, blue = 0.8 } },
        { name = "F2", value = data.f2 or 0, color = { red = 0.7, green = 0.65, blue = 0.8 } },
        { name = "F3", value = data.f3 or 0, color = { red = 0.8, green = 0.7, blue = 0.6 } }
    }

    for i, f in ipairs(formants) do
        local yPos = startY + (i - 1) * 80

        -- Label
        canvas[#canvas + 1] = {
            type = "text",
            text = f.name .. ":",
            textColor = { red = 0.5, green = 0.6, blue = 0.55, alpha = 1 },
            textSize = 24,
            textFont = "SF Mono",
            frame = {
                x = 30,
                y = yPos,
                w = 50,
                h = 40
            }
        }

        -- Value
        canvas[#canvas + 1] = {
            type = "text",
            text = string.format("%.0f Hz", f.value),
            textColor = f.color,
            textSize = 24,
            textFont = "SF Mono",
            frame = {
                x = 100,
                y = yPos,
                w = 150,
                h = 40
            }
        }

        -- Bar visualization
        local barMax = 4000
        local barWidth = (f.value / barMax) * (width - 200)
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = f.color,
            frame = {
                x = 250,
                y = yPos + 15,
                w = barWidth,
                h = 15
            }
        }
    end

    return canvas
end

return FernCharts
