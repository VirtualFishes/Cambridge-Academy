import importlib
import inspect
import pkgutil
from datetime import date
from enum import Enum

import ca_program.entities as entities_package


def sample_value(parameter_name, annotation=None):
    name = parameter_name.lower()

    if "id" in name:
        return 1
    if "name" in name:
        return "Usuario Prueba"
    if "password" in name:
        return "1234"
    if "email" in name:
        return "test@example.com"
    if "birth" in name or "date" in name:
        return date(2000, 1, 1)
    if "nationality" in name:
        return "Colombiana"
    if "description" in name:
        return "Descripción de prueba"
    if "level" in name:
        return "A1"
    if "language" in name:
        return "English"
    if "price" in name or "amount" in name or "cost" in name:
        return 100000
    if "grade" in name or "score" in name:
        return 4.5
    if "status" in name:
        return "active"

    if annotation is int:
        return 1
    if annotation is float:
        return 1.0
    if annotation is bool:
        return True
    if annotation is str:
        return "Dato de prueba"
    if annotation is date:
        return date(2000, 1, 1)

    if inspect.isclass(annotation) and issubclass(annotation, Enum):
        return list(annotation)[0]

    return "Dato de prueba"


def test_import_all_entity_modules():
    for module_info in pkgutil.iter_modules(entities_package.__path__):
        module_name = f"{entities_package.__name__}.{module_info.name}"
        module = importlib.import_module(module_name)
        assert module is not None


def test_entity_classes_can_be_instantiated_when_possible():
    created_objects = []

    for module_info in pkgutil.iter_modules(entities_package.__path__):
        module_name = f"{entities_package.__name__}.{module_info.name}"
        module = importlib.import_module(module_name)

        for _, cls in inspect.getmembers(module, inspect.isclass):
            if cls.__module__ != module.__name__:
                continue

            if issubclass(cls, Enum):
                assert len(list(cls)) > 0
                continue

            try:
                signature = inspect.signature(cls)
                kwargs = {}

                for param_name, param in signature.parameters.items():
                    if param_name == "self":
                        continue

                    if param.default is not inspect.Parameter.empty:
                        continue

                    kwargs[param_name] = sample_value(param_name, param.annotation)

                obj = cls(**kwargs)
                created_objects.append(obj)

                str(obj)

            except Exception:
                continue

    assert len(created_objects) > 0