"""Authentication routes."""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.usuario_schema import TokenResponse, UsuarioCreate, UsuarioOut
from app.services.usuario_service import autenticar_usuario, criar_usuario, obter_usuario_atual
from app.utils.seguranca import criar_token_acesso

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UsuarioOut)
def register(dados: UsuarioCreate, db: Session = Depends(get_db)):
    return criar_usuario(db, dados)


@router.post("/login", response_model=TokenResponse)
def login(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = autenticar_usuario(db, form.username, form.password)
    if not usuario:
        raise HTTPException(status_code=401, detail="E-mail ou senha inválidos.")
    return TokenResponse(access_token=criar_token_acesso(str(usuario.id)))


@router.get("/me", response_model=UsuarioOut)
def me(usuario=Depends(obter_usuario_atual)):
    return usuario
