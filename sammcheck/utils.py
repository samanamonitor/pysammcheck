def str2array(a):
    arr=[]
    s=''
    quote = False
    escape = False
    for i in a:
        if not escape:
            if i == ' ' and not quote:
                arr += [s]
                s = ''
                continue
            elif i == '\\':
                escape = True
                continue
            elif i == '\'' or i == '"':
                quote = not quote
                continue
        if escape:
            if i != ' ' and i != '\\' and i != '\'' and i != '"':
                s += "\\"
        s += i
    if s != '':
        arr += [s]
    return arr
