from __future__ import annotations


class DomainError(Exception):
    """Erro de domínio — entradas válidas mas regras de negócio violadas."""


class InvalidLoanParametersError(DomainError):
    """Parâmetros de empréstimo inválidos (ex: entrada >= valor do imóvel)."""


class BacenUnavailableError(DomainError):
    """API SGS BACEN inacessível e sem cache disponível."""


class ScrapeError(DomainError):
    """Erro genérico de scraping."""


class ScrapeBlocked(ScrapeError):
    """Scraper foi bloqueado pelo site (Cloudflare, 403, captcha)."""


class ScrapeTimeout(ScrapeError):
    """Timeout de rede ao chamar o site."""


class NoResultsError(ScrapeError):
    """Site respondeu mas sem resultados utilizáveis."""
