from labrea import Option


def test_apply():
    y_if_negative_else_z = Option('X').bind(lambda x: Option('Y') if x < 0 else Option('Z'))
    assert y_if_negative_else_z.evaluate({'X': 1, 'Y': 2, 'Z': 3}) == 3
    assert y_if_negative_else_z.evaluate({'X': -1, 'Y': 2, 'Z': 3}) == 2
