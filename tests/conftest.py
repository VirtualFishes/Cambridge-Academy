import pytest

from app.services.auth_service import AuthService
from app.services.profesor_service import ProfesorService
from app.services.estudiante_service import EstudianteService
from app.services.curso_service import CursoService
from app.services.inscripcion_service import InscripcionService
from app.services.pago_service import PagoService
from app.services.account_service import AccountService


@pytest.fixture
def auth_service():
    return AuthService()


@pytest.fixture
def profesor_service():
    return ProfesorService()


@pytest.fixture
def estudiante_service():
    return EstudianteService()


@pytest.fixture
def curso_service():
    return CursoService()


@pytest.fixture
def inscripcion_service():
    return InscripcionService()


@pytest.fixture
def pago_service():
    return PagoService()


@pytest.fixture
def account_service():
    return AccountService()