from django.test import TestCase

def assert_raise_error(expected_error):
    def wrapper(func):
        def inner(test: TestCase, *args, **kwargs):
            try:
                func(test)
                test.assertTrue(False)
            
            except Exception as error:
                test.assertEqual(error.__class__, expected_error.__class__)
                test.assertEqual(str(error), str(expected_error))
        return inner
    return wrapper
