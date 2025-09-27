from pytestarch import get_evaluable_architecture
import importlib


class BaseArchTest:
    """Base class for architecture tests with common utilities and constants."""

    REPO_ROOT = "."
    SRC_ROOT = "src"
    ROOT = "batch_inference_server"

    @classmethod
    def _evaluable(cls):
        """Get evaluable architecture for the project."""
        return get_evaluable_architecture(cls.REPO_ROOT, f"{cls.REPO_ROOT}/{cls.SRC_ROOT}")

    @classmethod
    def _is_empty_package(cls, module_name):
        """Check if a module/package is empty or doesn't exist."""
        try:
            mod = importlib.import_module(module_name)
            attrs = [a for a in dir(mod) if not a.startswith('__') and a not in ('__init__', '__pycache__')]
            return not attrs
        except Exception:
            return True

    @classmethod
    def _assert_rule_if_package_exists(cls, rule_func, module_name, ev=None):
        """Assert a rule only if the target package exists and is not empty."""
        if ev is None:
            ev = cls._evaluable()
        if not cls._is_empty_package(module_name):
            rule_func(ev).assert_applies(ev)
