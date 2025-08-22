from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional, Type, Union
from pydantic import BaseModel

Source = Union[BaseModel, dict]

@dataclass
class FieldRule:
    source: Optional[str] = None
    transform: Optional[Callable[[Any, Dict], Any]] = None
    default: Any = None
    nested: Optional["MappingSpec"] = None
    many: bool = False

@dataclass
class MappingSpec:
    dest_model: Type[BaseModel]
    fields: Dict[str, FieldRule] = field(default_factory=dict)

def _get_attr(obj: Source, key: str) -> Any:
    if isinstance(obj, BaseModel):
        return getattr(obj, key, None)
    if isinstance(obj, dict):
        return obj.get(key)
    return None

def _read_path(obj: Source, path: Optional[str]) -> Any:
    if not path:
        return obj
    cur: Any = obj
    for name in path.split("."):
        cur = _get_attr(cur, name)
        if cur is None:
            return None
    return cur

def map_model(source: Source, spec: MappingSpec, ctx: Optional[Dict] = None) -> BaseModel:
    ctx = ctx or {}
    out: Dict[str, Any] = {}
    for dest_name, rule in spec.fields.items():
        raw = _read_path(source, rule.source) if rule.source else None
        if rule.nested:
            if rule.many:
                items = raw or []
                out[dest_name] = [map_model(it, rule.nested, ctx).model_dump() for it in items]
            else:
                out[dest_name] = None if raw is None else map_model(raw, rule.nested, ctx).model_dump()
        else:
            val = raw if raw is not None else rule.default
            if rule.transform and val is not None:
                val = rule.transform(val, ctx)
            out[dest_name] = val
    return spec.dest_model.model_validate(out)

class GenericTransformer:
    def __init__(self, a2c: MappingSpec, c2b: MappingSpec):
        self.a2c = a2c
        self.c2b = c2b
    def to_canonical(self, a: Source, ctx: Optional[Dict] = None) -> BaseModel:
        return map_model(a, self.a2c, ctx)
    def to_sap(self, c: Source, ctx: Optional[Dict] = None) -> BaseModel:
        return map_model(c, self.c2b, ctx)

class TransformerRegistry:
    def __init__(self):
        self._reg: Dict[tuple[str, str], GenericTransformer] = {}

    def register(self, resource: str, profile: str, t: GenericTransformer) -> None:
        self._reg[(resource, profile)] = t

    def get(self, resource: str, profile: str = "default") -> GenericTransformer:
        return self._reg[(resource, profile)]
