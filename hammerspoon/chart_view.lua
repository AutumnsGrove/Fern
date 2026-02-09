-- Chart View Module
-- Full-screen chart display with keyboard navigation
-- View: Pitch Trend, Resonance Profile, Session Summary
-- Navigation: Arrow keys, Numbers for time range, H for help

local FernChartView = {}

-- State
local state = {
    canvas = nil,
    visible = false,
    currentView = "trend",  -- "trend", "resonance", "summary", "help"
    timeRange = 7,          -- Days: 7, 30, 90
    chartData = nil,
    trendCanvas = nil,
    resonanceCanvas = nil,
    summaryCanvas = nil,
    helpCanvas = nil
}

-- Time range options
local timeRanges = {
    { days = 7, label = "7D" },
    { days = 30, label = "30D" },
    { days = 90, label = "90D" },
    { days = 365, label = "1Y" }
}

-- View configurations
local viewConfigs = {
    trend = {
        title = "Pitch Trend",
        hotkey = "1",
        keyLabel = "[1]"
    },
    resonance = {
        title = "Resonance Profile",
        hotkey = "2",
        keyLabel = "[2]"
    },
    summary = {
        title = "Session Summary",
        hotkey = "3",
        keyLabel = "[3]"
    },
    help = {
        title = "Help",
        hotkey = "H",
        keyLabel = "[H]"
    }
}

-- Create main chart view canvas
function FernChartViewCreate()
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = res.w - 100
    local height = res.h - 150
    local x = 50
    local y = 75

    state.canvas = hs.canvas.new({
        x = x,
        y = y,
        w = width,
        h = height
    })

    state.canvas:backgroundColor({ red = 0.08, green = 0.1, blue = 0.08, alpha = 0.95 })
    state.canvas:roundedRectRadii(16)

    return state.canvas
end

-- Create trend chart (larger, full-featured)
function FernChartViewCreateTrend(data, options)
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = res.w - 140
    local height = res.h - 240
    local x = 70
    local y = 110

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
        fillColor = { red = 0.06, green = 0.08, blue = 0.06, alpha = 0.98 },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.3, green = 0.5, blue = 0.4, alpha = 0.7 },
        strokeWidth = 2,
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    end

    -- Title bar background
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.1, green = 0.15, blue = 0.12, alpha = 0.8 },
        frame = {
            x = 0,
            y = 0,
            w = width,
            h = 45
        },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Main title
    canvas[#canvas + 1] = {
        type = "text",
        text = options.title or "Pitch Trend",
        textColor = { red = 0.7, green = 0.9, blue = 0.7, alpha = 1 },
        textSize = 22,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = 12,
            w = 300,
            h = 30
        }
    }

    -- Time range indicator
    local rangeLabel = "Time Range: "
    for _, tr in ipairs(timeRanges) do
        if tr.days == options.timeRange then
            rangeLabel = rangeLabel .. "[" .. tr.label .. "]"
        else
            rangeLabel = rangeLabel .. " " .. tr.label .. " "
        end
    end
    canvas[#canvas + 1] = {
        type = "text",
        text = rangeLabel,
        textColor = { red = 0.5, green = 0.7, blue = 0.6, alpha = 1 },
        textSize = 12,
        textFont = "SF Mono",
        frame = {
            x = width - 280,
            y = 17,
            w = 260,
            h = 20
        }
    }

    -- Chart area
    local chartX = 70
    local chartY = 70
    local chartW = width - 120
    local chartH = height - 140

    -- Chart background
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.04, green = 0.06, blue = 0.04, alpha = 0.6 },
        frame = {
            x = chartX,
            y = chartY,
            w = chartW,
            h = chartH
        }
    }

    -- Grid lines
    local gridColor = { red = 0.15, green = 0.25, blue = 0.2, alpha = 0.4 }

    for i = 1, 5 do
        local yPos = chartY + (chartH * i / 5)
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

    for i = 1, 9 do
        local xPos = chartX + (chartW * i / 10)
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
        local maxFreq = 400
        local yMin = chartY + chartH - ((options.targetMin / maxFreq) * chartH)
        local yMax = chartY + chartH - ((options.targetMax / maxFreq) * chartH)
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = 0.2, green = 0.6, blue = 0.3, alpha = 0.12 },
            frame = {
                x = chartX,
                y = yMax,
                w = chartW,
                h = yMin - yMax
            }
        }

        -- Target boundary lines
        canvas[#canvas + 1] = {
            type = "line",
            action = "stroke",
            strokeColor = { red = 0.3, green = 0.7, blue = 0.4, alpha = 0.5 },
            strokeWidth = 1,
            path = {
                { x = chartX, y = yMin },
                { x = chartX + chartW, y = yMin }
            }
        }
        canvas[#canvas + 1] = {
            type = "line",
            action = "stroke",
            strokeColor = { red = 0.3, green = 0.7, blue = 0.4, alpha = 0.5 },
            strokeWidth = 1,
            path = {
                { x = chartX, y = yMax },
                { x = chartX + chartW, y = yMax }
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

        -- Padding for visualization
        local paddedMin = math.max(0, minVal - range * 0.1)
        local paddedMax = maxVal + range * 0.1
        local paddedRange = paddedMax - paddedMin
        if paddedRange == 0 then paddedRange = 1 end

        local points = {}
        local stepX = chartW / (#data - 1)

        for i, d in ipairs(data) do
            local x = chartX + ((i - 1) * stepX)
            local y = chartY + chartH - (((d.value - paddedMin) / paddedRange) * chartH)
            table.insert(points, { x = x, y = y })
        end

        -- Area fill under line
        local areaPath = "M " .. chartX .. " " .. (chartY + chartH)
        for _, p in ipairs(points) do
            areaPath = areaPath .. " L " .. p.x .. " " .. p.y
        end
        areaPath = areaPath .. " L " .. (chartX + chartW) .. " " .. (chartY + chartH) .. " Z"

        canvas[#canvas + 1] = {
            type = "path",
            action = "fill",
            fillColor = { red = 0.2, green = 0.6, blue = 0.4, alpha = 0.15 },
            path = areaPath
        }

        -- Line path
        local pathString = "M " .. points[1].x .. " " .. points[1].y
        for i = 2, #points do
            pathString = pathString .. " L " .. points[i].x .. " " .. points[i].y
        end

        canvas[#canvas + 1] = {
            type = "path",
            action = "stroke",
            strokeColor = { red = 0.3, green = 0.85, blue = 0.5, alpha = 1 },
            strokeWidth = 2.5,
            path = pathString
        }

        -- Data points with gradient coloring
        for i, d in ipairs(data) do
            local x = chartX + ((i - 1) * stepX)
            local y = chartY + chartH - (((d.value - paddedMin) / paddedRange) * chartH)

            local pointColor = { red = 0.3, green = 0.85, blue = 0.5, alpha = 1 }
            if options.targetMin and options.targetMax then
                if d.value >= options.targetMin and d.value <= options.targetMax then
                    pointColor = { red = 0.2, green = 0.9, blue = 0.4, alpha = 1 }
                else
                    pointColor = { red = 0.95, green = 0.4, blue = 0.3, alpha = 1 }
                end
            end

            canvas[#canvas + 1] = {
                type = "circle",
                action = "fill",
                fillColor = pointColor,
                frame = {
                    x = x - 5,
                    y = y - 5,
                    w = 10,
                    h = 10
                }
            }

            -- Glow effect
            canvas[#canvas + 1] = {
                type = "circle",
                action = "fill",
                fillColor = { red = pointColor.red, green = pointColor.green, blue = pointColor.blue, alpha = 0.2 },
                frame = {
                    x = x - 10,
                    y = y - 10,
                    w = 20,
                    h = 20
                }
            }
        end
    end

    -- Y-axis labels
    local yLabels = { "400", "300", "200", "100", "0" }
    for i, label in ipairs(yLabels) do
        local yPos = chartY + chartH - ((tonumber(label) / 400) * chartH)
        canvas[#canvas + 1] = {
            type = "text",
            text = label,
            textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
            textSize = 11,
            textFont = "SF Mono",
            frame = {
                x = 15,
                y = yPos - 8,
                w = 45,
                h = 16
            }
        }
    end

    -- X-axis labels (dates)
    if data and #data > 0 then
        local labelCount = 6
        local step = math.floor(#data / labelCount)

        for i = 1, labelCount do
            local idx = (i - 1) * step + 1
            if idx <= #data and data[idx].date then
                local x = chartX + ((idx - 1) * (chartW / (#data - 1)))
                local dateStr = string.sub(data[idx].date, 6, 10)  -- MM-DD format

                canvas[#canvas + 1] = {
                    type = "text",
                    text = dateStr,
                    textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
                    textSize = 11,
                    textFont = "SF Mono",
                    frame = {
                        x = x - 25,
                        y = chartY + chartH + 10,
                        w = 50,
                        h = 16
                    }
                }
            end
        end
    end

    -- Legend
    local legendY = height - 35
    canvas[#canvas + 1] = {
        type = "text",
        text = "● In Range  ○ Out of Range",
        textColor = { red = 0.5, green = 0.6, blue = 0.55, alpha = 1 },
        textSize = 12,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = legendY,
            w = 250,
            h = 20
        }
    }

    -- Stats
    if data and #data > 0 then
        local statsText = ""
        local total, inRange = 0, 0
        local sum, values = 0, {}
        for _, d in ipairs(data) do
            total = total + 1
            sum = sum + d.value
            table.insert(values, d.value)
            if options.targetMin and options.targetMax and d.value >= options.targetMin and d.value <= options.targetMax then
                inRange = inRange + 1
            end
        end

        local avg = total > 0 and string.format("%.0f", sum / total) or "--"
        local rangePct = total > 0 and string.format("%.0f%%", (inRange / total) * 100) or "--"

        statsText = string.format("Avg: %s Hz  |  In Range: %s", avg, rangePct)

        canvas[#canvas + 1] = {
            type = "text",
            text = statsText,
            textColor = { red = 0.5, green = 0.7, blue = 0.6, alpha = 1 },
            textSize = 12,
            textFont = "SF Mono",
            frame = {
                x = width - 280,
                y = legendY,
                w = 260,
                h = 20
            }
        }
    end

    return canvas
end

-- Create resonance profile chart
function FernChartViewCreateResonance(data, options)
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = res.w - 140
    local height = res.h - 240
    local x = 70
    local y = 110

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
        fillColor = { red = 0.06, green = 0.08, blue = 0.06, alpha = 0.98 },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.4, green = 0.5, blue = 0.6, alpha = 0.7 },
        strokeWidth = 2,
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Title bar
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.1, green = 0.12, blue = 0.15, alpha = 0.8 },
        frame = {
            x = 0,
            y = 0,
            w = width,
            h = 45
        },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    canvas[#canvas + 1] = {
        type = "text",
        text = "Resonance Profile",
        textColor = { red = 0.7, green = 0.85, blue = 0.9, alpha = 1 },
        textSize = 22,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = 12,
            w = 250,
            h = 30
        }
    }

    -- Formant visualization area
    local startY = 80
    local barMax = 5000
    local centerX = width / 2

    local formants = {
        { name = "F1", value = data.f1 or 0, color = { red = 0.5, green = 0.75, blue = 0.85 } },
        { name = "F2", value = data.f2 or 0, color = { red = 0.6, green = 0.65, blue = 0.85 } },
        { name = "F3", value = data.f3 or 0, color = { red = 0.7, green = 0.6, blue = 0.75 } }
    }

    -- Formant rows
    for i, f in ipairs(formants) do
        local yPos = startY + (i - 1) * 120

        -- Label
        canvas[#canvas + 1] = {
            type = "text",
            text = f.name,
            textColor = { red = 0.6, green = 0.7, blue = 0.7, alpha = 1 },
            textSize = 28,
            textFont = "SF Mono",
            frame = {
                x = 30,
                y = yPos,
                w = 60,
                h = 45
            }
        }

        -- Value
        canvas[#canvas + 1] = {
            type = "text",
            text = string.format("%.0f Hz", f.value),
            textColor = f.color,
            textSize = 28,
            textFont = "SF Mono",
            frame = {
                x = 100,
                y = yPos,
                w = 180,
                h = 45
            }
        }

        -- Bar background
        local barBgX = 300
        local barBgW = width - 350
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = 0.15, green = 0.2, blue = 0.2, alpha = 0.5 },
            frame = {
                x = barBgX,
                y = yPos + 35,
                w = barBgW,
                h = 25
            }
        }

        -- Value bar
        local barWidth = (f.value / barMax) * barBgW
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = f.color.red, green = f.color.green, blue = f.color.blue, alpha = 0.8 },
            frame = {
                x = barBgX,
                y = yPos + 35,
                w = barWidth,
                h = 25
            }
        }

        -- Range markers (typical formant ranges)
        local typicalRanges = {
            F1 = { min = 200, max = 1000 },
            F2 = { min = 800, max = 2500 },
            F3 = { min = 2200, max = 3500 }
        }
        local range = typicalRanges[f.name]
        if range then
            local minX = barBgX + (range.min / barMax) * barBgW
            local maxX = barBgX + (range.max / barMax) * barBgW

            canvas[#canvas + 1] = {
                type = "rectangle",
                action = "fill",
                fillColor = { red = 0.3, green = 0.8, blue = 0.4, alpha = 0.3 },
                frame = {
                    x = minX,
                    y = yPos + 35,
                    w = maxX - minX,
                    h = 25
                }
            }
        end
    end

    -- Formant scatter plot
    local plotX = width - 280
    local plotY = startY + 30
    local plotSize = 200

    -- Plot background
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.08, green = 0.1, blue = 0.12, alpha = 0.6 },
        frame = {
            x = plotX,
            y = plotY,
            w = plotSize,
            h = plotSize
        }
    }

    -- Plot border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.3, green = 0.4, blue = 0.5, alpha = 0.5 },
        strokeWidth = 1,
        frame = {
            x = plotX,
            y = plotY,
            w = plotSize,
            h = plotSize
        }
    }

    -- Plot labels
    canvas[#canvas + 1] = {
        type = "text",
        text = "F2 →",
        textColor = { red = 0.4, green = 0.5, blue = 0.5, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = plotX + plotSize - 40,
            y = plotY + plotSize + 5,
            w = 40,
            h = 15
        }
    }

    canvas[#canvas + 1] = {
        type = "text",
        text = "↑ F1",
        textColor = { red = 0.4, green = 0.5, blue = 0.5, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = plotX - 35,
            y = plotY + plotSize - 40,
            w = 35,
            h = 15
        }
    }

    -- Data point
    if data.f1 and data.f2 then
        local px = plotX + (data.f2 / 3500) * plotSize
        local py = plotY + plotSize - (data.f1 / 1200) * plotSize

        canvas[#canvas + 1] = {
            type = "circle",
            action = "fill",
            fillColor = { red = 0.5, green = 0.8, blue = 0.6, alpha = 0.8 },
            frame = {
                x = px - 8,
                y = py - 8,
                w = 16,
                h = 16
            }
        }

        -- Crosshairs
        canvas[#canvas + 1] = {
            type = "line",
            action = "stroke",
            strokeColor = { red = 0.4, green = 0.6, blue = 0.5, alpha = 0.4 },
            strokeWidth = 1,
            path = {
                { x = px, y = plotY },
                { x = px, y = plotY + plotSize }
            }
        }
        canvas[#canvas + 1] = {
            type = "line",
            action = "stroke",
            strokeColor = { red = 0.4, green = 0.6, blue = 0.5, alpha = 0.4 },
            strokeWidth = 1,
            path = {
                { x = plotX, y = py },
                { x = plotX + plotSize, y = py }
            }
        }
    end

    return canvas
end

-- Create session summary view
function FernChartViewCreateSummary(data, options)
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = res.w - 140
    local height = res.h - 240
    local x = 70
    local y = 110

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
        fillColor = { red = 0.06, green = 0.08, blue = 0.06, alpha = 0.98 },
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.4, green = 0.5, blue = 0.5, alpha = 0.7 },
        strokeWidth = 2,
        roundedRectRadii = { xRadius = 12, yRadius = 12 }
    }

    -- Title
    canvas[#canvas + 1] = {
        type = "text",
        text = "Session Summary",
        textColor = { red = 0.7, green = 0.9, blue = 0.85, alpha = 1 },
        textSize = 22,
        textFont = "SF Mono",
        frame = {
            x = 20,
            y = 15,
            w = 250,
            h = 35
        }
    }

    -- Period label
    local periodLabel = "Last " .. options.timeRange .. " days"
    canvas[#canvas + 1] = {
        type = "text",
        text = periodLabel,
        textColor = { red = 0.5, green = 0.6, blue = 0.55, alpha = 1 },
        textSize = 14,
        textFont = "SF Mono",
        frame = {
            x = width - 150,
            y = 20,
            w = 130,
            h = 25
        }
    }

    -- Stats grid
    local stats = data.stats or {}
    local statItems = {
        { label = "Total Sessions", value = stats.sessions or 0, color = { red = 0.6, green = 0.75, blue = 0.8 } },
        { label = "Total Time", value = stats.totalTime or "0m", color = { red = 0.6, green = 0.8, blue = 0.7 } },
        { label = "Avg Pitch", value = (stats.avgPitch and string.format("%.0f Hz", stats.avgPitch) or "--"), color = { red = 0.7, green = 0.7, blue = 0.8 } },
        { label = "In Range", value = (stats.inRangePct and string.format("%.0f%%", stats.inRangePct) or "--"), color = { red = 0.5, green = 0.8, blue = 0.6 } },
        { label = "Best Day", value = stats.bestDay or "--", color = { red = 0.8, green = 0.6, blue = 0.7 } },
        { label = "Streak", value = (stats.streak and stats.streak .. " days" or "--"), color = { red = 0.7, green = 0.65, blue = 0.8 } }
    }

    local startX = 30
    local startY = 70
    local colW = (width - 80) / 3
    local rowH = 100

    for i, item in ipairs(statItems) do
        local col = (i - 1) % 3
        local row = math.floor((i - 1) / 3)
        local xPos = startX + col * colW
        local yPos = startY + row * rowH

        -- Card background
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = 0.1, green = 0.12, blue = 0.12, alpha = 0.5 },
            frame = {
                x = xPos,
                y = yPos,
                w = colW - 20,
                h = rowH - 15
            }
        }

        -- Label
        canvas[#canvas + 1] = {
            type = "text",
            text = item.label,
            textColor = { red = 0.45, green = 0.5, blue = 0.5, alpha = 1 },
            textSize = 12,
            textFont = "SF Mono",
            frame = {
                x = xPos + 15,
                y = yPos + 15,
                w = colW - 50,
                h = 18
            }
        }

        -- Value
        canvas[#canvas + 1] = {
            type = "text",
            text = tostring(item.value),
            textColor = item.color,
            textSize = 28,
            textFont = "SF Mono",
            frame = {
                x = xPos + 15,
                y = yPos + 38,
                w = colW - 50,
                h = 40
            }
        }
    end

    -- Recent sessions table
    local tableY = startY + 220
    local tableH = height - tableY - 40

    canvas[#canvas + 1] = {
        type = "text",
        text = "Recent Sessions",
        textColor = { red = 0.5, green = 0.6, blue = 0.55, alpha = 1 },
        textSize = 14,
        textFont = "SF Mono",
        frame = {
            x = 30,
            y = tableY,
            w = 200,
            h = 20
        }
    }

    -- Table header
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "fill",
        fillColor = { red = 0.1, green = 0.15, blue = 0.12, alpha = 0.6 },
        frame = {
            x = 30,
            y = tableY + 25,
            w = width - 60,
            h = 25
        }
    }

    canvas[#canvas + 1] = {
        type = "text",
        text = "Date",
        textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 40,
            y = tableY + 28,
            w = 100,
            h = 18
        }
    }

    canvas[#canvas + 1] = {
        type = "text",
        text = "Duration",
        textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 180,
            y = tableY + 28,
            w = 80,
            h = 18
        }
    }

    canvas[#canvas + 1] = {
        type = "text",
        text = "Avg Pitch",
        textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 300,
            y = tableY + 28,
            w = 80,
            h = 18
        }
    }

    canvas[#canvas + 1] = {
        type = "text",
        text = "In Range",
        textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
        textSize = 11,
        textFont = "SF Mono",
        frame = {
            x = 420,
            y = tableY + 28,
            w = 80,
            h = 18
        }
    }

    -- Session rows
    local sessions = data.sessions or {}
    for i = 1, math.min(#sessions, 8) do
        local rowY = tableY + 52 + (i - 1) * 28
        local s = sessions[i]

        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = 0.08, green = 0.1, blue = 0.08, alpha = 0.3 },
            frame = {
                x = 30,
                y = rowY,
                w = width - 60,
                h = 25
            }
        }

        canvas[#canvas + 1] = {
            type = "text",
            text = s.date or "--",
            textColor = { red = 0.6, green = 0.7, blue = 0.65, alpha = 1 },
            textSize = 11,
            textFont = "SF Mono",
            frame = {
                x = 40,
                y = rowY + 6,
                w = 100,
                h = 16
            }
        }

        canvas[#canvas + 1] = {
            type = "text",
            text = s.duration or "--",
            textColor = { red = 0.6, green = 0.7, blue = 0.65, alpha = 1 },
            textSize = 11,
            textFont = "SF Mono",
            frame = {
                x = 180,
                y = rowY + 6,
                w = 80,
                h = 16
            }
        }

        canvas[#canvas + 1] = {
            type = "text",
            text = s.avgPitch or "--",
            textColor = { red = 0.6, green = 0.7, blue = 0.65, alpha = 1 },
            textSize = 11,
            textFont = "SF Mono",
            frame = {
                x = 300,
                y = rowY + 6,
                w = 80,
                h = 16
            }
        }

        local inRangeColor = s.inRange and { red = 0.3, green = 0.8, blue = 0.5, alpha = 1 } or { red = 0.8, green = 0.4, blue = 0.3, alpha = 1 }
        canvas[#canvas + 1] = {
            type = "text",
            text = s.inRange and "Yes" or "No",
            textColor = inRangeColor,
            textSize = 11,
            textFont = "SF Mono",
            frame = {
                x = 420,
                y = rowY + 6,
                w = 80,
                h = 16
            }
        }
    end

    return canvas
end

-- Create help overlay
function FernChartViewCreateHelp()
    local screen = hs.screen.mainScreen()
    local res = screen:fullFrame()

    local width = 450
    local height = 400
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
        fillColor = { red = 0.08, green = 0.1, blue = 0.08, alpha = 0.98 },
        roundedRectRadii = { xRadius = 16, yRadius = 16 }
    }

    -- Border
    canvas[#canvas + 1] = {
        type = "rectangle",
        action = "stroke",
        strokeColor = { red = 0.4, green = 0.6, blue = 0.5, alpha = 0.8 },
        strokeWidth = 2,
        roundedRectRadii = { xRadius = 16, yRadius = 16 }
    }

    -- Title
    canvas[#canvas + 1] = {
        type = "text",
        text = "Keyboard Shortcuts",
        textColor = { red = 0.7, green = 0.9, blue = 0.7, alpha = 1 },
        textSize = 24,
        textFont = "SF Mono",
        frame = {
            x = 25,
            y = 20,
            w = 400,
            h = 35
        }
    }

    -- Help items
    local helpItems = {
        { keys = "1", desc = "Pitch Trend view" },
        { keys = "2", desc = "Resonance Profile" },
        { keys = "3", desc = "Session Summary" },
        { keys = "7 / 3", desc = "7 day range" },
        { keys = "8 / 0", desc = "30 day range" },
        { keys = "9 / -", desc = "90 day range" },
        { keys = "← / →", desc = "Previous/Next view" },
        { keys = "H", desc = "Show this help" },
        { keys = "ESC / Q", desc = "Close chart view" }
    }

    for i, item in ipairs(helpItems) do
        local yPos = 75 + (i - 1) * 35

        -- Key
        canvas[#canvas + 1] = {
            type = "rectangle",
            action = "fill",
            fillColor = { red = 0.15, green = 0.25, blue = 0.18, alpha = 0.8 },
            frame = {
                x = 25,
                y = yPos,
                w = 80,
                h = 28
            }
        }

        canvas[#canvas + 1] = {
            type = "text",
            text = item.keys,
            textColor = { red = 0.5, green = 0.8, blue = 0.6, alpha = 1 },
            textSize = 14,
            textFont = "SF Mono",
            frame = {
                x = 35,
                y = yPos + 4,
                w = 60,
                h = 22
            }
        }

        -- Description
        canvas[#canvas + 1] = {
            type = "text",
            text = item.desc,
            textColor = { red = 0.6, green = 0.7, blue = 0.65, alpha = 1 },
            textSize = 14,
            textFont = "SF Mono",
            frame = {
                x = 120,
                y = yPos + 4,
                w = 300,
                h = 22
            }
        }
    end

    -- Footer
    canvas[#canvas + 1] = {
        type = "text",
        text = "Press H or ESC to close",
        textColor = { red = 0.4, green = 0.5, blue = 0.45, alpha = 1 },
        textSize = 12,
        textFont = "SF Mono",
        frame = {
            x = 25,
            y = height - 35,
            w = 400,
            h = 20
        }
    }

    return canvas
end

-- Show chart view
function FernChartViewShow(view, data)
    if state.visible and state.canvas then
        state.canvas:delete()
    end

    state.currentView = view or "trend"
    state.chartData = data

    local chartOptions = {
        title = viewConfigs[state.currentView].title,
        timeRange = state.timeRange
    }

    -- Load target range from config or use defaults
    chartOptions.targetMin = FernConfig and FernConfig.targetMin or 80
    chartOptions.targetMax = FernConfig and FernConfig.targetMax or 250

    if state.currentView == "trend" then
        state.canvas = FernChartViewCreateTrend(data, chartOptions)
    elseif state.currentView == "resonance" then
        state.canvas = FernChartViewCreateResonance(data, chartOptions)
    elseif state.currentView == "summary" then
        state.canvas = FernChartViewCreateSummary(data, chartOptions)
    elseif state.currentView == "help" then
        state.canvas = FernChartViewCreateHelp()
    end

    state.canvas:show()
    state.visible = true
end

-- Hide chart view
function FernChartViewHide()
    if state.canvas then
        state.canvas:hide()
        state.visible = false
    end
end

-- Toggle chart view
function FernChartViewToggle(view, data)
    if state.visible and state.currentView == view then
        FernChartViewHide()
    else
        FernChartViewShow(view, data)
    end
end

-- Set time range
function FernChartViewSetTimeRange(days)
    state.timeRange = days
    return state.timeRange
end

-- Get current state
function FernChartViewGetState()
    return {
        visible = state.visible,
        view = state.currentView,
        timeRange = state.timeRange
    }
end

-- Handle keyboard input
function FernChartViewHandleKey(key)
    local views = { "trend", "resonance", "summary" }
    local currentIdx = 1
    for i, v in ipairs(views) do
        if v == state.currentView then
            currentIdx = i
            break
        end
    end

    if key == "right" or key == "l" then
        currentIdx = currentIdx % #views + 1
        FernChartViewShow(views[currentIdx], state.chartData)
    elseif key == "left" or key == "h" then
        currentIdx = currentIdx - 1
        if currentIdx < 1 then currentIdx = #views end
        FernChartViewShow(views[currentIdx], state.chartData)
    elseif key == "1" then
        FernChartViewShow("trend", state.chartData)
    elseif key == "2" then
        FernChartViewShow("resonance", state.chartData)
    elseif key == "3" then
        FernChartViewShow("summary", state.chartData)
    elseif key == "7" or key == "3" then
        FernChartViewSetTimeRange(7)
        FernChartViewShow(state.currentView, state.chartData)
    elseif key == "8" or key == "0" then
        FernChartViewSetTimeRange(30)
        FernChartViewShow(state.currentView, state.chartData)
    elseif key == "9" or key == "-" then
        FernChartViewSetTimeRange(90)
        FernChartViewShow(state.currentView, state.chartData)
    elseif key == "escape" or key == "q" then
        FernChartViewHide()
    elseif key == "h" or key == "?" then
        if state.currentView == "help" then
            FernChartViewShow(views[currentIdx], state.chartData)
        else
            FernChartViewShow("help", state.chartData)
        end
    end
end

-- Cleanup
function FernChartViewCleanup()
    if state.canvas then
        state.canvas:delete()
        state.canvas = nil
    end
    state.visible = false
end

return FernChartView
