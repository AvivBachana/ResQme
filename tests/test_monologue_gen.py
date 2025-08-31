import os
from src.resqme.pipelines.llm.monologue_generator import MonologueGenerator

def test_import_and_type():
    # Just verifies the module can be imported and class constructed with a tiny DataFrame
    import pandas as pd
    df = pd.DataFrame({"s1":[1,0]}, index=["flu"])
    gen = MonologueGenerator(df)
    assert "flu" in gen.diseases()
