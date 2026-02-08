G21         ; Set units to millimeters
G90         ; Use incremental positioning
G00 X0 Y0   ; Home


; Draw the square
G00 X50 Y80  ; Move to starting position
G01 X90 Y80  ; Move to right corner
G01 X90 Y40  ; Move to top-right corner
G01 X50 Y40  ; Move to top-left corner
G01 X50 Y80   ; Move back to origin

; Draw a circle in the box
G00 X70 Y30        ; Move to circle top
G02 X70.1 y30 R30  ; Draw a full circle with radius 30mm

; Draw some diagonal lines
G00 X70 Y40     ; Move to circle top center
G01 X50 Y80   ; Move to bottom-left corner
G00 X70 Y40   ; Move to cirle top center
G01 X90 Y80    ; Move to bottom-left corner

; Finish
G00 X10 Y10  ; Move back to origin