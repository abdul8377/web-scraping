from app.utils import normalize_url, safe_filename, slugify


def test_slugify_removes_accents() -> None:
    assert slugify("Información Hidrológica Diaria") == "informacion-hidrologica-diaria"


def test_safe_filename_keeps_extension() -> None:
    assert safe_filename("reporte diario.csv") == "reporte_diario.csv"


def test_normalize_url_removes_fragment() -> None:
    assert normalize_url("https://www.senamhi.gob.pe/main.php?p=estaciones#section") == (
        "https://www.senamhi.gob.pe/main.php?p=estaciones"
    )
