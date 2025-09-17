"""Testes unitários para BaseTenantModel."""
import threading
import uuid

from django.apps import apps as django_apps
from django.db import connection, models
from django.test import TransactionTestCase, override_settings

from iabank.core.factories import TenantFactory
from iabank.core.models import BaseTenantModel


@override_settings(
    DATABASES={
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": ":memory:",
        }
    }
)
class BaseTenantModelTests(TransactionTestCase):
    """Casos de teste para comportamento multi-tenant base."""

    reset_sequences = True
    model = None
    _history_model = None

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        attrs = {
            "__module__": "iabank.core.models",
            "name": models.CharField(max_length=128),
            "Meta": type(
                "Meta",
                (),
                {
                    "app_label": "core",
                    "db_table": "tests_dummy_tenant_model",
                },
            ),
        }

        cls.model = type("DummyTenantModel", (BaseTenantModel,), attrs)
        cls._history_model = cls.model.history.model

        with connection.schema_editor() as schema_editor:
            schema_editor.create_model(cls.model)
            schema_editor.create_model(cls._history_model)

    @classmethod
    def tearDownClass(cls):
        with connection.schema_editor() as schema_editor:
            schema_editor.delete_model(cls._history_model)
            schema_editor.delete_model(cls.model)

        app_models = django_apps.all_models.get("core", {})
        app_models.pop(cls.model.__name__.lower(), None)

        super().tearDownClass()

    def setUp(self):
        self.model = self.__class__.model
        self.tenant = TenantFactory()
        self._thread = threading.current_thread()
        self._previous_tenant = getattr(self._thread, "tenant", None)

    def tearDown(self):
        if self._previous_tenant is not None:
            setattr(self._thread, "tenant", self._previous_tenant)
        elif hasattr(self._thread, "tenant"):
            delattr(self._thread, "tenant")

    def test_save_without_tenant_id_uses_thread_context(self):
        """Salvar sem tenant_id deve usar contexto atual do tenant."""
        setattr(self._thread, "tenant", self.tenant)

        instance = self.model(name="Registro teste")
        instance.save()

        self.assertEqual(instance.tenant_id, self.tenant.id)

    def test_save_without_context_raises_value_error(self):
        """Salvar sem tenant_id e sem contexto deve falhar."""
        instance = self.model(name="Registro sem contexto")

        with self.assertRaisesRegex(ValueError, "tenant_id é obrigatório"):
            instance.save()

    def test_changing_tenant_id_after_creation_raises_error(self):
        """tenant_id não pode ser alterado após criação do registro."""
        setattr(self._thread, "tenant", self.tenant)

        instance = self.model(name="Registro original")
        instance.save()

        novo_tenant_id = uuid.uuid4()
        instance.tenant_id = novo_tenant_id

        with self.assertRaisesRegex(ValueError, "não pode ser alterado"):
            instance.save()
