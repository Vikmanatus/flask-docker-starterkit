from flask_starterkit.main.helpers import super_complex_function


def test_super_complex_function():
    assert super_complex_function("World !") == "Hello World !"
