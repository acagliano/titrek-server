

def convert_SI(val, unit_in, unit_out):
    SI = {'km':1., 'ly':9460700000000., 'pc':30856678534800., 'Mpc':30856678534800000000.}
    if not (unit_in,unit_out) in SI:
      return False
    return val*SI[unit_in]/SI[unit_out]
