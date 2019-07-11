def acre_ft2(x,x_unit='Ac'):
    conv = {
        'Ac' : 43560.0,
        'ft2' : 1.0/43560
    }
    return(conv[x_unit] * x)

def gal_ft3(x,x_unit='gal'):
    conv = {
        'gal' : 1/7.48,
        'ft3' : 7.48
    }
    return(conv[x_unit] * x)