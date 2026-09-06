def test_simple():
  assert 1 + 1 == 2


def test_envionment():
  $USER = 'snail'
  x = 'USER'
  assert x in ${...}
  assert ${'U' + 'SER'} == 'snail'


def test_pygwin_party():
  from pygwin.built_ins import XSH
  orig = XSH.env.get('PYGWIN_INTERACTIVE')
  XSH.env['PYGWIN_INTERACTIVE'] = False
  try:
      x = 'pygwin'
      y = 'party'
      out = $(echo @(x + '-' + y)).strip()
      assert out == 'pygwin-party', 'Out really was <' + out + '>, sorry.'
  finally:
      XSH.env['PYGWIN_INTERACTIVE'] = orig
