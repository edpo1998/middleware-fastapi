
from sqlmodel import SQLModel
from .naming import metadata as _metadata

SQLModel.metadata = _metadata


from app.core.database import bootstrap_app__scheme, mcs_scheme
