from pydantic import BaseModel


class TerraformResource(BaseModel):
    terraform_resource_name: str

    @staticmethod
    def get_terraform_name() -> str:
        raise RuntimeError("Not implemented")
