import pytest
import pandas as pd
from main import load_dataframe, main
from pathlib import Path
from typing import Dict

@pytest.fixture
def create_test_files(tmp_path: Path) -> Dict[str, str]:
    csv_path = tmp_path / "test.csv"
    csv_path.write_text("col1,col2\n1,a\n2,b")
    
    unsupported_path = tmp_path / "test.txt"
    unsupported_path.write_text("some text")
    
    return {"csv": str(csv_path), "unsupported": str(unsupported_path)}

def test_load_dataframe_csv(create_test_files: Dict[str, str]) -> None:
    df = load_dataframe(create_test_files["csv"])
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (2, 2)
    assert list(df.columns) == ["col1", "col2"]

def test_load_dataframe_unsupported_file(create_test_files: Dict[str, str]) -> None:
    with pytest.raises(ValueError, match="Unsupported file type: '.txt'"):
        load_dataframe(create_test_files["unsupported"])

def test_load_dataframe_non_existent_file() -> None:
    with pytest.raises(FileNotFoundError):
        load_dataframe("non_existent_file.csv")

def test_main_function_with_args(capsys, monkeypatch, create_test_files: Dict[str, str]) -> None:
    """
    Test the main function with command-line arguments.
    """
    # Use monkeypatch to simulate command-line arguments
    monkeypatch.setattr(
        "sys.argv",
        [
            "drift_detector",
            "--reference",
            create_test_files["csv"],
            "--target",
            create_test_files["csv"],
        ],
    )
    main()
    captured = capsys.readouterr()
    
    assert "Loading reference file" in captured.out
    assert "Reference DataFrame loaded successfully. Shape: (2, 2)" in captured.out
    assert "Loading target file" in captured.out
    assert "Target DataFrame loaded successfully. Shape: (2, 2)" in captured.out
