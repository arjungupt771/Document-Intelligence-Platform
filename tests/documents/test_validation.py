from app.documents.validation import validate_file

MAX_FILE_SIZE = 10 * 1024 * 1024


def test_valid_pdf_is_accepted():
    result = validate_file("invoice.pdf", 2 * 1024 * 1024)

    assert result.valid is True
    assert result.error_code is None
    assert result.reason is None


def test_file_over_size_limit_is_rejected():
    result = validate_file("invoice.pdf", 11 * 1024 * 1024)

    assert result.valid is False
    assert result.error_code == "FILE_TOO_LARGE"
    assert result.reason == "File size exceeds the maximum allowed size"


def test_unsupported_file_type_is_rejected():
    result = validate_file("invoice.exe", 2 * 1024 * 1024)

    assert result.valid is False
    assert result.error_code == "UNSUPPORTED_TYPE"
    assert result.reason == "Unsupported file type"


def test_empty_file_is_rejected():
    result = validate_file("invoice.pdf", 0)

    assert result.valid is False
    assert result.error_code == "EMPTY_FILE"
    assert result.reason == "File is empty"


def test_filename_with_path_component_is_rejected():
    result = validate_file("../invoice.pdf", 1024)

    assert result.valid is False
    assert result.error_code == "INVALID_FILENAME"


def test_absolute_path_filename_is_rejected():
    result = validate_file("/tmp/invoice.pdf", 1024)

    assert result.valid is False
    assert result.error_code == "INVALID_FILENAME"


def test_filename_with_control_character_is_rejected():
    result = validate_file("invoice\n.pdf", 1024)

    assert result.valid is False
    assert result.error_code == "INVALID_FILENAME"


def test_empty_filename_is_rejected():
    result = validate_file("", 1024)

    assert result.valid is False
    assert result.error_code == "INVALID_FILENAME"

def test_filename_with_windows_path_component_is_rejected():
    result = validate_file(r"..\invoice.pdf", 1024)

    assert result.valid is False
    assert result.error_code == "INVALID_FILENAME"


def test_filename_with_windows_directory_separator_is_rejected():
    result = validate_file(r"folder\invoice.pdf", 1024)

    assert result.valid is False
    assert result.error_code == "INVALID_FILENAME"