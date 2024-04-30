from pydantic import BaseModel


class TerraformResource(BaseModel):

    @staticmethod
    def get_terraform_name() -> str:
        raise RuntimeError("Not implemented")
