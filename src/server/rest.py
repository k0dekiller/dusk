from collections.abc import Callable
from typing import Any, Final, Literal, overload
from functools import wraps
import inspect

from flask import Response, jsonify, request

type body = dict[str, Any]
type response = Response | tuple[Response | str, int] | str

class err:
    """The namespace that contains all the error codes."""
    class param:
        """The namespace that contains all parameter-related error codes."""
        missing: Final = "param.missing"
        class value:
            """The namespace that contains all value-related error codes."""
            invalid: Final = "param.value.invalid"
            invalid_type: Final = "param.value.invalid_type"
            not_unique: Final = "param.value.not_unique"
    class resource:
        """The namespace that contains all resource-related error codes."""
        already_exists: Final = "param.resource.already_exists"

def result(success: bool, body: body) -> body:
    """Adds the `success` key to the given `body` and returns it."""
    body["success"] = success
    return body
@overload
def success(data: body) -> body:
    """Adds the `"success": True` key to the given `body` and returns it."""
@overload
def success() -> body:
    """Adds the `"success": True` key to a new body and returns it."""
@overload
def success(data: None) -> body:
    """Adds the `"success": True` key to a new body and returns it."""
def success(data: body | None = None) -> body:
    """Adds the `"success": True` key to the given `body` (or creates a new one if not given) and returns it."""
    return result(True, {"data": data} if data is not None else {})
def error(code: str, *, desc: str | None = None, params: list[str] | str | None = None) -> body:
    """Returns a new body with the `code`, `desc` and `params` keys."""
    body: body = {"code": code}
    if desc is not None:
        body["desc"] = desc
    if params is not None:
        body["params"] = params if isinstance(params, list) else [params]
    return result(False, {"error": body})
def require(*args: str, src: Literal["json"] = "json") -> Callable[..., Callable[..., response]]:
    """Generates a wrapper that checks if all arguments `args` are present in the given source `src`, and returns an error if not."""
    def decorator(f: Callable[..., response]) -> Callable[..., response]:
        def _params(f: Callable[..., Any]) -> dict[str, Any]:
            all = inspect.signature(f).parameters
            return {all[arg].name: {"type": all[arg].annotation, "def": all[arg].default} for arg in args}
        params = _params(f)
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> response:
            # grab data
            data: body
            match src:
                case "json":
                    data = request.get_json() or {}
            # check for missing params
            for name, param in params.items():
                if name in data:
                    value: object = data[name]
                    if isinstance(value, param["type"]):
                        kwargs[name] = value
                    else:
                        return jsonify(error(
                            err.param.value.invalid_type,
                            desc = f"Parameter \"{name}\" is {type(value).__name__ if value is not None else "missing"}, expected {param["type"].__name__}",
                            params = name
                        )), 400
                else:
                    if param["def"] == inspect.Parameter.empty:
                        return jsonify(error(
                            err.param.missing,
                            desc = f"Missing required parameter {repr(name)}",
                            params = name
                        )), 400
                    else:
                        kwargs[name] = param["def"]
            # proceed with original function and pass obtained parameters
            return f(*args, **kwargs)
        return wrapper
    return decorator