def pluralize(n, next="note"):
    if n == 1:
        return("1 " + next)
    else:
        return(str(n) + " " + next + "s")

for i in range(10):
    print("Trash contains " + pluralize(i, "note"))

