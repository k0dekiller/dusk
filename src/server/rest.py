from collections.abc import Callable
from typing import Any, Final, Literal
from functools import wraps
import inspect

from flask import Response, jsonify, request

type body = dict[str, Any]
type response = Response | tuple[Response | str, int] | str

class err:
    class param:
        missing: Final = "param.missing"
        class value:
            invalid: Final = "param.value.invalid"
            invalid_type: Final = "param.value.invalid_type"
            not_unique: Final = "param.value.not_unique"

def result(success: bool, body: body) -> body:
    body["success"] = success
    return body
def success(data: body | None = None) -> body:
    return result(True, {"data": data} if data is not None else {})
def error(code: str, *, desc: str | None = None, params: list[str] | str | None = None) -> body:
    body: body = {"code": code}
    if desc is not None:
        body["desc"] = desc
    if params is not None:
        body["params"] = params if isinstance(params, list) else [params]
    return result(False, {"error": body})
def require(*args: str, src: Literal["json"] = "json") -> Callable[..., Callable[..., response]]:
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
                            desc = f"Parameter {repr(name)} is {repr(type(value))}, expected {repr(param["type"])}",
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