G21         ; Set units to millimeters
G91         ; Use incremental positioning
G00 X0 Y0   ; Home


; Draw the square
G00 X50 Y80  ; Move to starting position
G01 X40 Y0   ; Move to right corner
G01 X0 Y-40  ; Move to top-right corner
G01 X-40 Y0  ; Move to top-left corner
G01 X0 Y40   ; Move back to origin

; Draw a circle in the box
G00 X20 Y-50    ; Move to circle top
G02 X.1 y0 R30  ; Draw a full circle with radius 30mm

; Draw some diagonal lines
G00 X0 Y10     ; Move to circle top center
G01 X-20 Y40   ; Move to bottom-left corner
G00 X20 Y-40   ; Move to cirle top center
G01 X20 Y40    ; Move to bottom-left corner

; Finish
G00 X-90 Y-80  ; Move back to origin