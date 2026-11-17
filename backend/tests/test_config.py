from app.config import Settings, production_problems

STRONG_SECRET = "a" * 64


def test_local_never_blocked():
    assert production_problems(Settings(environment="local")) == []


def test_prod_blocks_defaults():
    problems = production_problems(Settings(environment="prod", llm_provider="mock",
                                            jwt_secret="change-me-in-production", demo_password="demo123"))
    assert len(problems) == 3


def test_prod_blocks_template_placeholders():
    s = Settings(environment="prod", llm_provider="sagemaker",
                 jwt_secret="REPLACE_ME", demo_password="REPLACE_ME")
    assert len(production_problems(s)) == 2


def test_prod_ok_with_real_values():
    s = Settings(environment="prod", llm_provider="sagemaker",
                 jwt_secret=STRONG_SECRET, demo_password="Xk29fPq81LmZ")
    assert production_problems(s) == []
