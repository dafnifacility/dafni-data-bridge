class TokenAuth:

    def __init__(self, token: str| None):
        if not token:
            raise ValueError("CEDA token not provided")
        self.token=token

    def headers(self) -> dict[str,str]:
        return {
            "Authorization": f"Bearer {self.token}",
        }