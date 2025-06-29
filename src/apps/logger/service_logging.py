import functools
import traceback


def _method_logger(method):
    @functools.wraps(method)
    def wrapper(*args, **kwargs):
        try:
            return method(*args, **kwargs)
        except Exception as e:
            stack_trace = "".join(traceback.format_exception(None, e, e.__traceback__))
            # adminLogger.error(f"Service error in {method.__name__}: {e}\nStack trace:\n{stack_trace}")
            raise e

    return wrapper


class LoggingMeta(type):
    def __new__(cls, name, bases, dct):
        for attr_name, attr_value in dct.items():
            if callable(attr_value):
                dct[attr_name] = _method_logger(attr_value)
        return super().__new__(cls, name, bases, dct)
