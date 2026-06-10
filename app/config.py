from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """
    Classe de configuration utilisant Pydantic Settings.
    Elle valide et charge les variables nécessaires au projet.
    """

    # -------------------------------------------------------------
    # VARIABLES DE LA BASE DE DONNÉES
    # -------------------------------------------------------------
    db_host: str = Field(default="localhost", validation_alias="DB_HOST")
    db_port: int = Field(default=5433, validation_alias="DB_PORT")
    db_name: str = Field(default="ast_ai", validation_alias="DB_NAME")
    db_user: str = Field(default="ast_ai_user", validation_alias="DB_USER")
    db_password: str = Field(default="ast_ai_password_secret", validation_alias="DB_PASSWORD")

    # -------------------------------------------------------------
    # VARIABLE DU LLM (Ollama)
    # -------------------------------------------------------------
    ollama_url: str = Field(default="http://localhost:11434", validation_alias="OLLAMA_URL")
    ollama_model: str = Field(default="qwen2.5:7b", validation_alias="OLLAMA_MODEL")
    # -------------------------------------------------------------
    # RÈGLES METIER & GARDE-FOUS (GUARDRAILS)
    # -------------------------------------------------------------
    vip_refund_percent: int = Field(default=20, validation_alias="VIP_REFUND_PERCENT")
    allow_standard_refund: bool = Field(default=False, validation_alias="ALLOW_STANDARD_REFUND")


    # -------------------------------------------------------------
    # CONFIGURATION DE PYDANTIC
    # -------------------------------------------------------------
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore les variables d'environnement supplémentaires présentes qui ne sont pas définies ici
        extra="ignore"
    )

    # -------------------------------------------------------------
    # PROPRIÉTÉ DYNAMIQUE (DSN)
    # -------------------------------------------------------------
    @property
    def database_url(self) -> str:
        """
        Construit et renvoie l'URL de connexion complète pour PostgreSQL.
        """
        return f"postgresql://{self.db_user}:{self.db_password}@{self.db_host}:{self.db_port}/{self.db_name}"

# On crée une instance unique qui sera importée dans tout le projet
settings = Settings()
