import logging
import sys

# Codes couleur ANSI pour le terminal
RESET_SEQ = "\033[0m"
COLOR_SEQ = "\033[1;%dm"
BOLD_SEQ = "\033[1m"

# Couleurs par niveau de log
COLORS = {
    'WARNING': 33,  # Jaune
    'INFO': 32,     # Vert
    'DEBUG': 36,    # Cyan
    'CRITICAL': 35, # Violet
    'ERROR': 31     # Rouge
}

class ColoredFormatter(logging.Formatter):
    """
    Formateur de logs personnalisé qui ajoute des couleurs ANSI selon le niveau du log.
    """
    def __init__(self, fmt: str, datefmt: str = None):
        super().__init__(fmt, datefmt)

    def format(self, record):
        level_name = record.levelname
        # Si le niveau a une couleur définie, on l'applique au niveau de log
        if level_name in COLORS:
            color_code = COLORS[level_name]
            # On colorise la balise de niveau ex: [INFO]
            record.levelname = f"{COLOR_SEQ % color_code}{level_name}{RESET_SEQ}"
        return super().format(record)


def setup_logger(name: str = "ast-ai", level: int = logging.INFO) -> logging.Logger:
    """
    Configure et retourne un logger standardisé en couleur pour l'application AST-AI.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(level)

        # Le format inclut le nom du module et le message
        format_str = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        formatter = ColoredFormatter(fmt=format_str, datefmt="%Y-%m-%d %H:%M:%S")

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)
        logger.propagate = False

    return logger

# Instance partagée par défaut
logger = setup_logger()
