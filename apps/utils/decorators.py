from django.test import TestCase
from django.core.cache import cache

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


def cache_result(key: str, timeout=None):
    def wrapper(func):
        def inner(*args, **kwargs):
            cached_result = cache.get(key)
            if cached_result:
                return cached_result
            
            result = func(*args, **kwargs)
            cache.set(key, result, timeout)
            return result
        return inner
    return wrapper
