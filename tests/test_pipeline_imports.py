def test_pipeline_import():
    # Ensure the package-based pipeline is importable after cleanup
    from pipelines.enhanced_web_search_pipeline import Pipeline  # noqa: F401
