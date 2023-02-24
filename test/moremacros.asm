

!macro RECUR @val {
    !if @val #= 1
        RECUR 0
        !warn Recur 1
    !else
        !warn Recur 0
    !endif
}

RECUR 1

; TODO: Test byte selection operators
